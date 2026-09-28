"""POST-RC3 per-model driver. Reuses the FROZEN RC3 pipeline unchanged.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.

Stage functions imported from aivd_rc3 (frozen at AIVD-RC3):
  discovery                aivd_rc3.discover.run
  stateful trajectory      aivd_stateful.model (via the session)
  investigation/hypothesis aivd_rc3.investigate.{applicable,investigate,replay}
  labeling                 aivd_rc3.labeler.label
  blind provenance decision aivd_rc3.driver.{blind_evidence,blind_decision,blind_reason}
  isolated verification    aivd_rc3.verifier.judge (post-freeze, in reveal)

No stage is bypassed and no verifier call is made on an arbitrary candidate: the same
promotion gate (VERIFICATION_READY) and VERIFY_COST source-swap arms are used.
"""

import dataclasses
import json
from pathlib import Path

from aivd_investigation.probes import LIBRARY
from aivd_stateful.model import Budget, Config, create

from aivd_rc3.discover import public_blob, run as discover_run
from aivd_rc3.driver import blind_decision, blind_evidence, blind_reason
from aivd_rc3.investigate import applicable, investigate, replay as replay_report
from aivd_rc3.labeler import label
from aivd_rc3.provider import SWAP_SENTINEL
from aivd_rc3.verifier import ledger_hash

from aivd_post_rc3 import EXPERIMENT_ID
from aivd_post_rc3.authorize import authorize, close_run, open_run, plan_commitment
from aivd_post_rc3.config import (
    DISCOVERY_LIMIT,
    INVESTIGATION_LIMIT,
    MODEL_ALLOCATION,
    VERIFICATION_LIMIT,
    VERIFY_COST,
)
from aivd_post_rc3.groq_client import request_contract
from aivd_post_rc3.session import PostRC3Session
from aivd_post_rc3.stop import (
    check_authorization,
    check_candidate_ids_unique,
    check_corpus_commitment,
    halt,
)

# The evaluation targets remote hosted models; no local runtime digest applies.
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


def run_model(root: Path, public: list, transport, *, model_id: str, corpus_commitment: str,
              discovery_seed: int) -> dict:
    """Blind execution for one model. Receives ONLY the public manifest and commitment."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    plan_hash = plan_commitment(corpus_commitment, model_id, MODEL_ALLOCATION)
    token = authorize(explicit=True, experiment_id=EXPERIMENT_ID, plan_hash=plan_hash,
                      corpus_commitment=corpus_commitment, model_id=model_id, allocation=MODEL_ALLOCATION)
    check_authorization(token, EXPERIMENT_ID)
    scenarios = {item["scenario_id"]: item for item in public}
    integrity, error = 0, None
    stage_calls = {"discovery": 0, "investigation": 0, "verification": 0}
    discovered = {"decisions": [], "retained": [], "rejected": [], "explored": [], "stop": "NOT_STARTED"}
    prepared, stops = [], []
    session = PostRC3Session(root / "session", transport, Budget(limit=DISCOVERY_LIMIT), model_id=model_id)
    open_run(token)
    try:
        # No warm-up call: the RC3 warm-up addressed a local Ollama cold-load artifact and would
        # only consume a paid discovery unit on a hosted API (preregistered).
        # ---- discovery (frozen RC3 discovery)
        discovered = discover_run(public, session, config=CONFIG, namespace=model_id + ":",
                                  discovery_seed=discovery_seed)
        check_candidate_ids_unique(discovered["retained"])
        stage_calls["discovery"] = session.calls
        stops.append({"stage": "discovery", "reason": discovered["stop"]})
        # ---- investigation (fresh ceiling; frozen RC3 investigation)
        session.budget = Budget(limit=INVESTIGATION_LIMIT)
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
        stage_calls["investigation"] = session.calls - stage_calls["discovery"]
        stops.append({"stage": "investigation", "reason": inv_stop})
        # ---- verification (fresh ceiling): frozen RC3 independent repeat + source-swap arms
        session.budget = Budget(limit=VERIFICATION_LIMIT)
        ver_stop = "FRONTIER_EMPTY"
        for item in prepared:
            if item["promotion"] != "VERIFICATION_READY":
                continue
            if session.budget.turn_executions + VERIFY_COST > VERIFICATION_LIMIT:
                ver_stop = "BUDGET_EXHAUSTED"
                break
            preserved = session.trajectories[item["trajectory_id"]]
            base_turns = tuple(t for t in preserved.turns if t.turn_id in item["turn_ids"])
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
            item["swap"] = {"trajectory_id": swapped.trajectory_id, "turn_ids": [t.turn_id for t in swapped.turns],
                            "output_hash": swapped.turns[-1].output_hash}
            item["swap_output"] = swapped.turns[-1].output
            item["blind_evidence"] = blind_evidence(item, scenario)
            item["blind_reason"] = blind_reason(item, scenario)
            item["verification_decision"] = blind_decision(item, scenario)
        stage_calls["verification"] = session.calls - stage_calls["discovery"] - stage_calls["investigation"]
        stops.append({"stage": "verification", "reason": ver_stop})
    except Exception as exc:
        integrity, error = 1, type(exc).__name__ + ": " + str(exc)
        stage_calls["investigation"] = stage_calls["investigation"] or max(session.calls - stage_calls["discovery"], 0)
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
        "calls": session.calls, "stage_calls": stage_calls, "api_attempts": session.attempt_charges,
        "requests": list(session.records), "decisions": discovered["decisions"],
        "explored": discovered.get("explored", []), "rejected": discovered["rejected"],
        "candidates": prepared, "stops": stops,
        "integrity_failures": integrity, "error": error,
    }
    ledger["frozen_hash"] = ledger_hash(ledger)
    (root / "ledger.json").write_text(json.dumps(ledger, sort_keys=True, indent=1), encoding="utf-8")
    return ledger


def repro_subset(public: list, count: int) -> list:
    """Preregistered repeat set: the first `count` two-step scenarios in manifest order."""
    return [s for s in public if s.get("steps")][:count]


def run_repeat(root: Path, public: list, transport, *, model_id: str, corpus_commitment: str) -> dict:
    """Preregistered reproducibility repeat set, OUTSIDE the 96. Runs only frozen RC3 discovery
    on the subset, under a fresh namespace and its own ceiling (REPRO_CALLS_PER_MODEL)."""
    from aivd_post_rc3.config import REPRO_CALLS_PER_MODEL, REPRO_SCENARIO_COUNT, REPRO_STAGE_NAME

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    subset = repro_subset(public, REPRO_SCENARIO_COUNT)
    plan_hash = plan_commitment(corpus_commitment, model_id, REPRO_CALLS_PER_MODEL)
    token = authorize(explicit=True, experiment_id=EXPERIMENT_ID, plan_hash=plan_hash,
                      corpus_commitment=corpus_commitment, model_id=model_id, allocation=REPRO_CALLS_PER_MODEL)
    session = PostRC3Session(root / "session", transport, Budget(limit=REPRO_CALLS_PER_MODEL), model_id=model_id)
    integrity, error, found = 0, None, {"decisions": [], "retained": [], "rejected": [], "explored": [], "stop": "NOT_STARTED"}
    open_run(token)
    try:
        found = discover_run(subset, session, config=CONFIG, namespace=model_id + ":" + REPRO_STAGE_NAME + ":",
                             discovery_seed=None)
    except Exception as exc:
        integrity, error = 1, type(exc).__name__ + ": " + str(exc)
    finally:
        close_run()
    ledger = {
        "experiment_id": EXPERIMENT_ID, "stage": REPRO_STAGE_NAME, "model_id": model_id,
        "corpus_commitment": corpus_commitment, "plan_hash": plan_hash,
        "allocation": {"repro_repeat": REPRO_CALLS_PER_MODEL}, "request_contract": request_contract(),
        "subset": [s["scenario_id"] for s in subset], "calls": session.calls,
        "api_attempts": session.attempt_charges, "requests": list(session.records),
        "decisions": found["decisions"], "explored": found.get("explored", []),
        "rejected": found["rejected"],
        "retained": [{"scenario_id": c["scenario_id"], "signature": c.get("signature"),
                      "slots": {k: c.get(k, False) for k in ("prior_slot", "auth_slot", "transition_slot")}}
                     for c in found["retained"]],
        "integrity_failures": integrity, "error": error,
    }
    ledger["frozen_hash"] = ledger_hash(ledger)
    (root / "repeat_ledger.json").write_text(json.dumps(ledger, sort_keys=True, indent=1), encoding="utf-8")
    return ledger


def compare_repeat(main: dict, repeat: dict) -> dict:
    """Within-model reproducibility on the repeat subset (keyed by scenario and step)."""
    subset = set(repeat.get("subset", []))

    def per_scenario(ledger, namespace_marker):
        # Map discovery records to (scenario, action-order) by walking decisions for subset scenarios.
        out = {}
        for rec in ledger.get("requests", []):
            out.setdefault(rec["input_hash"], []).append(rec)
        return out
    main_by_input = per_scenario(main, "")
    rep_by_input = per_scenario(repeat, "")
    # L2: same public input + same message count + same action -> request bodies differ only by
    # model history content; compare request_hash where the preceding content matched.
    l2_checked = l2_matched = bit_eq = bit_n = 0
    for ih, reps in rep_by_input.items():
        mains = main_by_input.get(ih, [])
        for r in reps:
            same_ctx = [m for m in mains if m["message_count"] == r["message_count"] and m["action"] == r["action"]]
            if not same_ctx:
                continue
            bit_n += 1
            bit_eq += any(m["content_sha256"] == r["content_sha256"] for m in same_ctx)
            if r["message_count"] == 1:  # first turn: identical request expected
                l2_checked += 1
                l2_matched += any(m["request_hash"] == r["request_hash"] for m in same_ctx)
    # L3-L5 only over scenarios explored in BOTH runs (the main run may stop at its discovery ceiling
    # before a repeat-set scenario; such scenarios are reported, never counted as a mismatch).
    both = sorted(subset & set(main.get("explored", [])) & set(repeat.get("explored", [])))
    not_in_main = sorted(subset - set(main.get("explored", [])))
    main_ret = {c["scenario_id"] for c in main.get("candidates", []) if c["scenario_id"] in both}
    rep_ret = {c["scenario_id"] for c in repeat.get("retained", []) if c["scenario_id"] in both}
    main_slots = {c["scenario_id"]: c.get("slots") for c in main.get("candidates", []) if c["scenario_id"] in both}
    rep_slots = {c["scenario_id"]: c.get("slots") for c in repeat.get("retained", []) if c["scenario_id"] in both}
    l4_equal = sum(1 for s in both if main_slots.get(s) == rep_slots.get(s))
    l5_equal = sum(1 for s in both if (s in main_ret) == (s in rep_ret))
    return {"compared_scenarios": both, "not_explored_in_main": not_in_main,
            "L2_request_first_turn": {"checked": l2_checked, "matched": l2_matched,
                                      "holds": l2_checked > 0 and l2_checked == l2_matched},
            "L3_retain_explore": {"scenarios": len(both), "holds": bool(both) and main_ret == rep_ret},
            "L4_signature_slots": {"scenarios": len(both), "equal": l4_equal, "holds": bool(both) and l4_equal == len(both)},
            "L5_retain_decision": {"scenarios": len(both), "equal": l5_equal},
            "bitwise_content": {"compared": bit_n, "equal": bit_eq}}
