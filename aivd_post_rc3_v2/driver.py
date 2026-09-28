"""V2 driver. Same frozen stage order as POST-RC3, with exact failure-stage accounting.

Does not change which prompts are sent or how candidates are scored.
"""

import dataclasses
import json
from pathlib import Path

from aivd_investigation.probes import LIBRARY
from aivd_stateful.model import Budget, BudgetExhausted, Config, create

from aivd_rc3.discover import public_blob, run as discover_run
from aivd_rc3.driver import blind_decision, blind_evidence, blind_reason
from aivd_rc3.investigate import applicable, investigate, replay as replay_report
from aivd_rc3.labeler import label
from aivd_rc3.provider import SWAP_SENTINEL
from aivd_rc3.verifier import ledger_hash

from aivd_post_rc3.authorize import authorize, close_run, open_run, plan_commitment
from aivd_post_rc3.config import (
    DISCOVERY_LIMIT,
    INVESTIGATION_LIMIT,
    MODEL_ALLOCATION,
    REPRO_CALLS_PER_MODEL,
    REPRO_SCENARIO_COUNT,
    REPRO_STAGE_NAME,
    VERIFICATION_LIMIT,
    VERIFY_COST,
)
from aivd_post_rc3.driver import repro_subset
from aivd_post_rc3.groq_client import request_contract
from aivd_post_rc3.stop import check_authorization, check_candidate_ids_unique
from aivd_post_rc3_v2 import EXPERIMENT_ID
from aivd_post_rc3_v2.accounting import (
    BUDGET_POLICY,
    FAILURE_STATUS,
    assert_invariants,
    assign_successful,
    empty_stage_calls,
)
from aivd_post_rc3_v2.bind import bind
from aivd_post_rc3_v2.session import V2Session

CONFIG = Config(model="groq", seed=0, runtime="groq-openai-v1")


def _investigation_body(candidate: dict) -> dict:
    body = {
        "candidate_id": candidate["candidate_id"],
        "trajectory_id": candidate["trajectory_id"],
        "turn_ids": list(candidate["turn_ids"]),
        "prior_slot": bool(candidate.get("prior_slot")),
        "auth_slot": bool(candidate.get("auth_slot")),
        "transition_slot": bool(candidate.get("transition_slot")),
    }
    if candidate.get("branch_id"):
        body["branch_id"] = candidate["branch_id"]
    return body


def _accounting(session, stage_calls, stages_completed, failure_stage, final_status) -> dict:
    attempts = list(session.attempts)
    successful = [item for item in attempts if item["success"]]
    return {
        "calls": session.calls,
        "stage_calls": dict(stage_calls),
        "api_attempts": len(attempts),
        "retry_attempts": sum(1 for item in attempts if item["retry_of"]),
        "successful_responses": len(successful),
        "recording_failures": session.recording_failures,
        "stage_budget_consumed": sum(item["budget_consumed"] for item in attempts),
        "budget_policy": BUDGET_POLICY,
        "attempts": attempts,
        "requests": list(session.records),
        "failure_stage": failure_stage,
        "failure_report": session.last_failure,
        "final_status": final_status,
        "stages_completed": list(stages_completed),
        "discovery_completed": "discovery" in stages_completed,
    }


def _fail(stage_calls, session, stage):
    assign_successful(stage_calls, session.calls, stage)
    return stage, FAILURE_STATUS[stage]


def run_model(root: Path, public: list, transport, *, model_id: str, corpus_commitment: str,
              discovery_seed: int) -> dict:
    bind()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    plan_hash = plan_commitment(corpus_commitment, model_id, MODEL_ALLOCATION)
    token = authorize(explicit=True, experiment_id=EXPERIMENT_ID, plan_hash=plan_hash,
                      corpus_commitment=corpus_commitment, model_id=model_id, allocation=MODEL_ALLOCATION)
    check_authorization(token, EXPERIMENT_ID)
    scenarios = {item["scenario_id"]: item for item in public}
    integrity, error = 0, None
    stage_calls = empty_stage_calls()
    stages_completed = []
    failure_stage = None
    final_status = "COMPLETED"
    discovered = {"decisions": [], "retained": [], "rejected": [], "explored": [], "stop": "NOT_STARTED"}
    prepared, stops = [], []
    session = V2Session(root / "session", transport, Budget(limit=DISCOVERY_LIMIT), model_id=model_id)
    open_run(token)
    try:
        session.set_stage("discovery")
        discovered = discover_run(public, session, config=CONFIG, namespace=model_id + ":",
                                  discovery_seed=discovery_seed)
        check_candidate_ids_unique(discovered["retained"])
        assign_successful(stage_calls, session.calls, "discovery")
        stages_completed.append("discovery")
        stops.append({"stage": "discovery", "reason": discovered["stop"], "completed": True})
        session.budget = Budget(limit=INVESTIGATION_LIMIT)
        session.set_stage("investigation")
        inv_stop = "FRONTIER_EMPTY"
        for candidate in discovered["retained"]:
            scenario = scenarios[candidate["scenario_id"]]
            blob = public_blob(scenario)
            body = _investigation_body(candidate)
            outputs = {"CF-A": candidate["preserved_output"], "CF-B": candidate["contrast_output"]}
            probe_calls = []
            for probe_id in applicable(body):
                if probe_id in outputs:
                    continue
                if session.budget.turn_executions >= INVESTIGATION_LIMIT:
                    inv_stop = "BUDGET_EXHAUSTED"
                    break
                shell = session.trajectories.get(body["branch_id"]) if probe_id == "CF-E" \
                    else session.trajectories.get(body["trajectory_id"])
                if shell is None:
                    raise RuntimeError("retained trajectory is missing")
                updated = session.execute(shell, LIBRARY[probe_id]["text"], "branch",
                                          "preregistered investigation probe")
                outputs[probe_id] = updated.turns[-1].output
                probe_calls.append({"probe_id": probe_id, "trajectory_id": updated.trajectory_id,
                                    "turn_id": updated.turns[-1].turn_id,
                                    "output_hash": updated.turns[-1].output_hash})
            observations = {}
            for probe_id, output in outputs.items():
                peer = outputs.get("CF-B") if probe_id == "CF-A" else outputs.get("CF-A") if probe_id == "CF-B" else None
                observations[probe_id] = label(probe_id, output, blob, peer)
            report = investigate(body, observations, probe_limit=len(observations))
            replay_report(report)
            prepared.append({
                "candidate_id": candidate["candidate_id"], "scenario_id": candidate["scenario_id"],
                "trajectory_id": candidate["trajectory_id"], "turn_ids": candidate["turn_ids"],
                "state_hash": candidate["state_hash"], "contrast_trajectory_id": candidate["contrast_trajectory_id"],
                "contrast_state_hash": candidate["contrast_state_hash"],
                "preserved_output": candidate["preserved_output"], "contrast_output": candidate["contrast_output"],
                "setup_output": candidate.get("setup_output", ""),
                "slots": {k: body.get(k, False) for k in ("prior_slot", "auth_slot", "transition_slot")},
                "branch_id": body.get("branch_id"),
                "probe_calls": probe_calls, "observations": observations,
                "records": report["records"], "hypotheses": report["hypotheses"],
                "promotion": report["promotion"],
            })
            if inv_stop == "BUDGET_EXHAUSTED":
                break
        assign_successful(stage_calls, session.calls, "investigation")
        stages_completed.append("investigation")
        stops.append({"stage": "investigation", "reason": inv_stop, "completed": True})
        session.budget = Budget(limit=VERIFICATION_LIMIT)
        session.set_stage("verification")
        ver_stop = "FRONTIER_EMPTY"
        for item in prepared:
            if item["promotion"] != "VERIFICATION_READY":
                continue
            if session.budget.turn_executions + VERIFY_COST > VERIFICATION_LIMIT:
                ver_stop = "BUDGET_EXHAUSTED"
                break
            preserved = session.trajectories[item["trajectory_id"]]
            base_turns = tuple(turn for turn in preserved.turns if turn.turn_id in item["turn_ids"])
            parent = dataclasses.replace(preserved, turns=base_turns[:-1])
            follow = base_turns[-1].public_input
            updated = session.execute(parent, follow, "verify", "independent verification repeat")
            item["verification"] = {"trajectory_id": updated.trajectory_id, "turn_id": updated.turns[-1].turn_id,
                                    "output_hash": updated.turns[-1].output_hash}
            item["verification_output"] = updated.turns[-1].output
            scenario = scenarios[item["scenario_id"]]
            steps = scenario.get("steps") or []
            swap_root = create(model_id + ":swap:" + item["scenario_id"], CONFIG)
            if steps:
                opened = session.execute(swap_root, SWAP_SENTINEL + "\n" + steps[0], "continue", "source-swap condition setup")
                swapped = session.execute(opened, SWAP_SENTINEL + "\n" + steps[1], "continue", "source-swap condition follow-up")
            else:
                opened = session.execute(swap_root, SWAP_SENTINEL + "\n" + scenario["variants"][0], "continue", "source-swap condition setup")
                swapped = session.execute(opened, SWAP_SENTINEL + "\n" + scenario["probe"], "continue", "source-swap condition follow-up")
            item["swap"] = {"trajectory_id": swapped.trajectory_id, "turn_ids": [turn.turn_id for turn in swapped.turns],
                            "output_hash": swapped.turns[-1].output_hash}
            item["swap_output"] = swapped.turns[-1].output
            item["blind_evidence"] = blind_evidence(item, scenario)
            item["blind_reason"] = blind_reason(item, scenario)
            item["verification_decision"] = blind_decision(item, scenario)
        assign_successful(stage_calls, session.calls, "verification")
        stages_completed.append("verification")
        stops.append({"stage": "verification", "reason": ver_stop, "completed": True})
    except (Exception, BudgetExhausted) as exc:
        stage = session.stage or "discovery"
        failure_stage, final_status = _fail(stage_calls, session, stage)
        integrity, error = 1, type(exc).__name__ + ": " + str(exc)
        stops.append({"stage": stage, "reason": "INFRASTRUCTURE_FAILURE", "completed": False})
    finally:
        close_run()
    if sum(stage_calls.values()) != session.calls:
        integrity, error = 1, (error or "") + " budget accounting mismatch"
    ledger = {
        "experiment_id": EXPERIMENT_ID, "model_id": model_id, "provider": "Groq",
        "corpus_commitment": corpus_commitment, "plan_hash": plan_hash, "discovery_seed": discovery_seed,
        "allocation": {"discovery": DISCOVERY_LIMIT, "investigation": INVESTIGATION_LIMIT,
                       "verification": VERIFICATION_LIMIT, "total": MODEL_ALLOCATION},
        "request_contract": request_contract(),
        "decisions": discovered["decisions"],
        "explored": discovered.get("explored", []), "rejected": discovered["rejected"],
        "candidates": prepared, "stops": stops,
        "integrity_failures": integrity, "error": error,
        **_accounting(session, stage_calls, stages_completed, failure_stage, final_status),
    }
    try:
        assert_invariants(ledger)
    except AssertionError as exc:
        ledger["integrity_failures"] = 1
        ledger["error"] = (ledger["error"] or "") + " invariant: " + str(exc)
    ledger["frozen_hash"] = ledger_hash(ledger)
    (root / "ledger.json").write_text(json.dumps(ledger, sort_keys=True, indent=1), encoding="utf-8")
    return ledger


def run_repeat(root: Path, public: list, transport, *, model_id: str, corpus_commitment: str) -> dict:
    bind()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    subset = repro_subset(public, REPRO_SCENARIO_COUNT)
    plan_hash = plan_commitment(corpus_commitment, model_id, REPRO_CALLS_PER_MODEL)
    token = authorize(explicit=True, experiment_id=EXPERIMENT_ID, plan_hash=plan_hash,
                      corpus_commitment=corpus_commitment, model_id=model_id, allocation=REPRO_CALLS_PER_MODEL)
    session = V2Session(root / "session", transport, Budget(limit=REPRO_CALLS_PER_MODEL), model_id=model_id)
    integrity, error, found = 0, None, {"decisions": [], "retained": [], "rejected": [], "explored": [], "stop": "NOT_STARTED"}
    stage_calls = empty_stage_calls()
    stages_completed = []
    failure_stage = None
    final_status = "COMPLETED"
    open_run(token)
    try:
        session.set_stage("discovery")
        found = discover_run(subset, session, config=CONFIG, namespace=model_id + ":" + REPRO_STAGE_NAME + ":",
                             discovery_seed=None)
        assign_successful(stage_calls, session.calls, "discovery")
        stages_completed.append("discovery")
    except Exception as exc:
        failure_stage, final_status = _fail(stage_calls, session, session.stage or "discovery")
        integrity, error = 1, type(exc).__name__ + ": " + str(exc)
    finally:
        close_run()
    # The repeat set is discovery-only. Empty later stages are not claimed as completed.
    ledger = {
        "experiment_id": EXPERIMENT_ID, "stage": REPRO_STAGE_NAME, "model_id": model_id,
        "corpus_commitment": corpus_commitment, "plan_hash": plan_hash,
        "allocation": {"repro_repeat": REPRO_CALLS_PER_MODEL}, "request_contract": request_contract(),
        "subset": [item["scenario_id"] for item in subset],
        "decisions": found["decisions"], "explored": found.get("explored", []),
        "rejected": found["rejected"],
        "retained": [{"scenario_id": cand["scenario_id"], "signature": cand.get("signature"),
                      "slots": {k: cand.get(k, False) for k in ("prior_slot", "auth_slot", "transition_slot")}}
                     for cand in found["retained"]],
        "integrity_failures": integrity, "error": error,
        **_accounting(session, stage_calls, stages_completed, failure_stage,
                     final_status if failure_stage else "REPEAT_COMPLETE"),
    }
    if not failure_stage:
        ledger["final_status"] = "COMPLETED"
        ledger["discovery_completed"] = True
    ledger["frozen_hash"] = ledger_hash(ledger)
    (root / "repeat_ledger.json").write_text(json.dumps(ledger, sort_keys=True, indent=1), encoding="utf-8")
    return ledger


def run_fixture(root: Path, events: list, *, model_id: str = "openai/gpt-oss-20b",
                budget_limit: int = 48) -> dict:
    """Synthetic stage script. No network and no discovery policy."""
    bind()
    root = Path(root)
    if root.exists():
        raise FileExistsError(root)

    class Transport:
        def __init__(self):
            self.last_attempts = 1
            self.index = 0

        def __call__(self, request):
            event = events[self.index]
            self.index += 1
            self.last_attempts = 1 + int(event.get("retries", 0))
            outcome = event["outcome"]
            if outcome == "success":
                body = {"model": model_id, "message": {"role": "assistant", "content": "ok"}}
                return 200, json.dumps(body).encode()
            if outcome == "transport_failure":
                raise TimeoutError("synthetic transport failure")
            if outcome == "recording_failure":
                return 200, b""
            raise AssertionError(outcome)

    corpus_commitment = "fixture"
    plan_hash = plan_commitment(corpus_commitment, model_id, MODEL_ALLOCATION)
    token = authorize(explicit=True, experiment_id=EXPERIMENT_ID, plan_hash=plan_hash,
                      corpus_commitment=corpus_commitment, model_id=model_id, allocation=MODEL_ALLOCATION)
    session = V2Session(root / "session", Transport(), Budget(limit=budget_limit), model_id=model_id)
    trajectory = create("fixture", Config(model="fixture", seed=0, runtime="fixture"))
    stage_calls = empty_stage_calls()
    stages_completed = []
    failure_stage = None
    final_status = "COMPLETED"
    current = None
    open_run(token)
    try:
        for event in events:
            if event["stage"] != current:
                if current is not None:
                    assign_successful(stage_calls, session.calls, current)
                    stages_completed.append(current)
                current = event["stage"]
                session.set_stage(current)
            session.execute(trajectory, f"fixture-step-{session.calls}", "continue", "synthetic fixture")
        if current is not None and failure_stage is None:
            assign_successful(stage_calls, session.calls, current)
            stages_completed.append(current)
    except Exception:
        failure_stage, final_status = _fail(stage_calls, session, session.stage or "discovery")
    finally:
        close_run()
    ledger = _accounting(session, stage_calls, stages_completed, failure_stage, final_status)
    ledger["integrity_failures"] = 0 if failure_stage is None else 1
    assert_invariants(ledger)
    return ledger
