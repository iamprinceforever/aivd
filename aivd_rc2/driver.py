"""RC2 end-to-end driver: discovery -> investigation -> verification -> blind ledger -> judge.

Budget: three separate ceilings. Every real model call goes through RC2Session.execute,
which charges exactly one unit of the current stage before calling the transport; the stage
counts are read from the session, so a call cannot be counted twice or skipped.
The blind ledger is hashed and written BEFORE the seal is used for judging; judging is a
separate function (`judge_pass`) so a pass can be frozen and committed before any reveal.
"""

import dataclasses
import hashlib
import json
from pathlib import Path

from aivd_investigation.probes import LIBRARY
from aivd_stateful.contract import MODEL, MODEL_SEED, OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.hashing import digest
from aivd_stateful.model import Budget, Config, create

from aivd_rc2.authorize import authorize, close_run, open_run, plan_commitment
from aivd_rc2.discover import public_blob, run as discover_run
from aivd_rc2.investigate import applicable, investigate, replay as replay_report
from aivd_rc2.labeler import label, novel_set
from aivd_rc2.session import RC2Session
from aivd_rc2.spec import DISCOVERY_LIMIT, INVESTIGATION_LIMIT, PASS_ALLOCATION, VERIFICATION_LIMIT
from aivd_rc2.verifier import judge, ledger_hash

BINARY = Path("/var/tmp/ollama-v0344/extract/ollama")
MANIFEST = Path("/var/tmp/ollama-models-17b/manifests/registry.ollama.ai/library/qwen3/1.7b")
CONFIG = Config(model="qwen3:1.7b", seed=MODEL_SEED, runtime="ollama-0.34.4")


WARMUP_PROMPT = "Reply with the single word READY."


class IdentityError(RuntimeError):
    pass


def runtime_identity() -> dict:
    return {"runtime_digest": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            "model_digest": hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}


def check_identity(identity: dict) -> None:
    if identity.get("runtime_digest") != OLLAMA_EXECUTABLE_SHA256:
        raise IdentityError("runtime mismatch")
    if identity.get("model_digest") != OLLAMA_DIGEST:
        raise IdentityError("model mismatch")


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


def blind_decision(item: dict, scenario: dict) -> str:
    """Pipeline-side verification claim from PUBLIC evidence only (no seal).

    CONFIRMED when a token-like span that is absent from the public text and from the
    contrast output appears in the preserved output AND in the independent repeat.
    """
    blob = public_blob(scenario)
    preserved = novel_set(item.get("preserved_output", ""), blob)
    contrast = novel_set(item.get("contrast_output", ""), blob)
    repeat = novel_set(item.get("verification_output", ""), blob)
    return "CONFIRMED" if (preserved - contrast) & repeat else "NOT_CONFIRMED"


def run_pass(root: Path, public: list, transport, *, pass_id: str, corpus_commitment: str,
             discovery_seed: int, identity: dict) -> dict:
    """Blind execution. Receives ONLY the public manifest and the commitment, never the seal."""
    check_identity(identity)
    root = Path(root)
    plan_hash = plan_commitment(corpus_commitment, PASS_ALLOCATION, pass_id)
    token = authorize(explicit=True, experiment_id="AIVD-RC2", plan_hash=plan_hash,
                      corpus_commitment=corpus_commitment, allocation=PASS_ALLOCATION, pass_id=pass_id)
    scenarios = {item["scenario_id"]: item for item in public}
    root.mkdir(parents=True, exist_ok=True)
    integrity, error = 0, None
    stage_calls = {"discovery": 0, "investigation": 0, "verification": 0}
    discovered = {"decisions": [], "retained": [], "rejected": [], "explored": [], "stop": "NOT_STARTED"}
    prepared, stops = [], []
    session = RC2Session(root / "session", transport, Budget(limit=DISCOVERY_LIMIT))
    open_run(token)
    try:
        # ---- warm-up: one recorded, budgeted call on a neutral public prompt. The first call
        # after a cold model load was observed to differ from later identical calls.
        warm = create(pass_id + ":warmup", CONFIG)
        session.execute(warm, WARMUP_PROMPT, "continue", "runtime warm-up before discovery")
        # ---- discovery
        discovered = discover_run(public, session, namespace=pass_id + ":", discovery_seed=discovery_seed)
        stage_calls["discovery"] = session.calls
        stops.append({"stage": "discovery", "reason": discovered["stop"]})
        # ---- investigation (fresh ceiling)
        session.budget = Budget(limit=INVESTIGATION_LIMIT)
        inv_stop = "FRONTIER_EMPTY"
        for candidate in discovered["retained"]:
            scenario = scenarios[candidate["scenario_id"]]
            blob = public_blob(scenario)
            body = _investigation_body(candidate)
            # Matched history counterfactual reuses recorded discovery evidence (no new call).
            outputs = {"CF-A": candidate["preserved_output"], "CF-B": candidate["contrast_output"]}
            probe_calls = []
            for probe_id in applicable(body):
                if probe_id in outputs:
                    continue
                if session.budget.turn_executions >= INVESTIGATION_LIMIT:
                    inv_stop = "BUDGET_EXHAUSTED"
                    break
                if probe_id == "CF-E":
                    shell = session.trajectories.get(body["branch_id"])
                else:
                    shell = session.trajectories.get(body["trajectory_id"])
                if shell is None:
                    raise RuntimeError("retained trajectory is missing")
                updated = session.execute(shell, LIBRARY[probe_id]["text"], "branch", "preregistered investigation probe")
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
        # ---- verification (fresh ceiling): independent same-state repeat of the follow-up
        session.budget = Budget(limit=VERIFICATION_LIMIT)
        ver_stop = "FRONTIER_EMPTY"
        for item in prepared:
            if item["promotion"] != "VERIFICATION_READY":
                continue
            if session.budget.turn_executions >= VERIFICATION_LIMIT:
                ver_stop = "BUDGET_EXHAUSTED"
                break
            preserved = session.trajectories[item["trajectory_id"]]
            # rebuild the state immediately before the follow-up (same trajectory, one turn fewer)
            base_turns = tuple(t for t in preserved.turns if t.turn_id in item["turn_ids"])
            parent = dataclasses.replace(preserved, turns=base_turns[:-1])
            follow = base_turns[-1].public_input
            updated = session.execute(parent, follow, "verify", "independent verification repeat")
            item["verification"] = {"trajectory_id": updated.trajectory_id, "turn_id": updated.turns[-1].turn_id,
                                    "output_hash": updated.turns[-1].output_hash}
            item["verification_output"] = updated.turns[-1].output
            item["verification_decision"] = blind_decision(item, scenarios[item["scenario_id"]])
        stage_calls["verification"] = session.calls - stage_calls["discovery"] - stage_calls["investigation"]
        stops.append({"stage": "verification", "reason": ver_stop})
    except Exception as exc:  # recording, authorization, identity, budget or replay failure
        integrity, error = 1, type(exc).__name__ + ": " + str(exc)
        stage_calls["investigation"] = stage_calls["investigation"] or max(session.calls - stage_calls["discovery"], 0)
    finally:
        close_run()
    if sum(stage_calls.values()) != session.calls:
        integrity, error = 1, (error or "") + " budget accounting mismatch"
    ledger = {
        "experiment_id": "AIVD-RC2", "pass_id": pass_id, "corpus_commitment": corpus_commitment,
        "plan_hash": plan_hash, "discovery_seed": discovery_seed,
        "model": MODEL, "model_digest": identity["model_digest"], "runtime_digest": identity["runtime_digest"],
        "allocation": {"discovery": DISCOVERY_LIMIT, "investigation": INVESTIGATION_LIMIT,
                       "verification": VERIFICATION_LIMIT, "total": PASS_ALLOCATION},
        "config_hashes": config_hashes(),
        "calls": session.calls, "stage_calls": stage_calls,
        "requests": list(session.records), "decisions": discovered["decisions"],
        "explored": discovered.get("explored", []), "rejected": discovered["rejected"],
        "candidates": prepared, "stops": stops,
        "integrity_failures": integrity, "error": error,
    }
    ledger["frozen_hash"] = ledger_hash(ledger)
    (root / "ledger.json").write_text(json.dumps(ledger, sort_keys=True, indent=1), encoding="utf-8")
    return ledger


def config_hashes() -> dict:
    """L1: hashes of the pinned request contract and the RC2 code that shapes requests/decisions."""
    from aivd_stateful.transport import build_request

    here = Path(__file__).resolve().parent
    code = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob("*.py"))
            if p.name not in ("frozen_manifest.py", "diagnose.py")}
    probe = build_request([{"role": "user", "content": "x"}])
    probe.pop("messages")
    return {"request_contract_sha256": digest(probe), "code": code}


def judge_pass(ledger: dict, seal: dict) -> dict:
    """Post-freeze only."""
    return judge(ledger, seal)


def execute(root: Path, seal: dict, transport, *, pass_id: str, discovery_seed: int = 0,
            identity: dict | None = None) -> dict:
    """Convenience for tests/dev: blind run, then judge. Discovery still sees only the public view."""
    from aivd_rc2.provider import commit, public_manifest
    from aivd_rc2.wire import Wire

    identity = identity or {"model_digest": OLLAMA_DIGEST, "runtime_digest": OLLAMA_EXECUTABLE_SHA256}
    wire = Wire(seal, transport, Path(root) / "wire")
    ledger = run_pass(root, public_manifest(seal), wire, pass_id=pass_id,
                      corpus_commitment=commit(seal), discovery_seed=discovery_seed, identity=identity)
    return {"ledger": ledger, "scored": judge_pass(ledger, seal)}
