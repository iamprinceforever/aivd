"""ENDGAME-3 runner. The frozen policies are called, not edited."""

import hashlib
import json
import urllib.request
from pathlib import Path

from aivd_investigation.budget import Budget as InvestigationBudget
from aivd_investigation.engine import investigate
from aivd_investigation.probes import LIBRARY, applicable
from aivd_stateful.contract import MODEL, MODEL_SEED, OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.discover import run
from aivd_stateful.model import Budget, Config, create

from aivd_endgame3.authorize import authorize, close_run, open_run, plan_commitment
from aivd_endgame3.encode import label, novel_spans
from aivd_endgame3.provider import commit, public_manifest
from aivd_endgame3.session import Endgame3Session
from aivd_endgame3.spec import (
    ALLOCATION,
    DISCOVERY_LIMIT,
    DISCOVERY_SHA256,
    INVESTIGATION_LIMIT,
    INVESTIGATION_SHA256,
    VERIFICATION_LIMIT,
)
from aivd_endgame3.verifier import judge, ledger_hash
from aivd_endgame3.wire import Wire

BINARY = Path("/var/tmp/ollama-v0344/extract/ollama")
MANIFEST = Path("/var/tmp/ollama-models-17b/manifests/registry.ollama.ai/library/qwen3/1.7b")
CHAT = "http://127.0.0.1:11434/api/chat"
CONFIG = Config(model="qwen3:1.7b", seed=MODEL_SEED, runtime="ollama-0.34.4")


def assert_identity() -> None:
    binary = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    manifest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    discovery = hashlib.sha256(Path("aivd_stateful/discover.py").read_bytes()).hexdigest()
    investigation = hashlib.sha256(Path("aivd_investigation/engine.py").read_bytes()).hexdigest()
    if binary != OLLAMA_EXECUTABLE_SHA256 or manifest != OLLAMA_DIGEST:
        raise RuntimeError("runtime identity mismatch")
    if discovery != DISCOVERY_SHA256 or investigation != INVESTIGATION_SHA256:
        raise RuntimeError("policy identity mismatch")


def ollama_transport(request: dict) -> tuple:
    payload = json.dumps(request).encode()
    call = urllib.request.Request(CHAT, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def _blob(scenario: dict) -> str:
    parts = list(scenario.get("steps") or []) + list(scenario.get("variants") or [])
    if scenario.get("probe"):
        parts.append(scenario["probe"])
    return "\n".join(parts)


def _prepare(candidate: dict, scenario: dict) -> dict:
    blob = _blob(scenario)
    body = {
        "candidate_id": candidate["candidate_id"],
        "trajectory_id": candidate["trajectory_id"],
        "turn_ids": list(candidate["turn_ids"]),
        "preserved_output": candidate["preserved_output"],
        "contrast_output": candidate["contrast_output"],
        "signature": list(candidate["signature"]),
        "prior_slot": bool(novel_spans(candidate["preserved_output"], blob) or novel_spans(candidate["contrast_output"], blob)),
        "auth_slot": "DENIED" in blob or "AUTHORIZED" in blob,
    }
    if "variants" in scenario and candidate.get("contrast_trajectory_id"):
        body["branch_id"] = candidate["contrast_trajectory_id"]
    return body


def _hypotheses(report: dict) -> dict:
    return {item["hypothesis"]: item["category"] for item in report.get("hypotheses", [])}


def execute(root: Path, seal: dict, transport) -> dict:
    assert_identity()
    commitment = commit(seal)
    token = authorize(
        explicit=True,
        experiment_id="ENDGAME-3",
        plan_hash=plan_commitment(commitment),
        corpus_commitment=commitment,
    )
    public = public_manifest(seal)
    scenarios = {item["scenario_id"]: item for item in public}
    root.mkdir(parents=True, exist_ok=True)
    wire = Wire(seal, transport, root / "wire")
    integrity = 0
    open_run(token)
    discovery_calls = investigation_calls = verification_calls = 0
    actions = {"continue": 0, "reset": 0, "branch": 0, "verify": 0, "revisit": 0, "compose": 0}
    ledger_body = {}
    try:
        session = Endgame3Session(root / "public", wire, Budget(limit=DISCOVERY_LIMIT))
        discovered = run(public, session)
        discovery_calls = session.calls
        actions.update(
            {
                "continue": session.budget.continuations,
                "reset": session.budget.resets,
                "branch": session.budget.branches,
                "verify": session.budget.verifications,
            }
        )
        session.budget = Budget(limit=INVESTIGATION_LIMIT)
        prepared = []
        shells = {}
        for candidate in discovered["retained"]:
            scenario = scenarios[candidate["scenario_id"]]
            body = _prepare(candidate, scenario)
            shells[candidate["candidate_id"]] = session.trajectories[candidate["trajectory_id"]]
            outputs = {}
            for probe_id in applicable(body):
                if session.budget.turn_executions >= INVESTIGATION_LIMIT:
                    break
                shell, action = _shell(session, body, probe_id, scenario["scenario_id"])
                if shell is None:
                    continue
                updated = session.execute(shell, LIBRARY[probe_id]["text"], action, "preregistered investigation probe")
                outputs[probe_id] = updated.turns[-1].output
            observations = {}
            for probe_id, output in outputs.items():
                peer = outputs.get("CF-B") if probe_id == "CF-A" else outputs.get("CF-A") if probe_id == "CF-B" else None
                observations[probe_id] = label(probe_id, output, _blob(scenario), peer)
            if observations:
                report = investigate(body, observations, InvestigationBudget(1, max(len(observations), 1), 0))
            else:
                report = {"promotion": None, "hypotheses": []}
            prepared.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "scenario_id": candidate["scenario_id"],
                    "trajectory_id": candidate["trajectory_id"],
                    "turn_ids": candidate["turn_ids"],
                    "preserved_output": candidate["preserved_output"],
                    "contrast_output": candidate["contrast_output"],
                    "promotion": report.get("promotion"),
                    "hypotheses": _hypotheses(report),
                    "observations": observations,
                }
            )
        investigation_calls = session.calls - discovery_calls
        session.budget = Budget(limit=VERIFICATION_LIMIT)
        for item in prepared:
            if item["promotion"] != "VERIFICATION_READY":
                continue
            if session.budget.turn_executions >= VERIFICATION_LIMIT:
                break
            scenario = scenarios[item["scenario_id"]]
            follow = scenario.get("probe") or scenario["steps"][1]
            shell = shells[item["candidate_id"]]
            updated = session.execute(shell, follow, "verify", "independent verification repeat")
            item["verification_output"] = updated.turns[-1].output
        verification_calls = session.calls - discovery_calls - investigation_calls
        ledger_body = {
            "corpus_commitment": commitment,
            "rejected": discovered["rejected"],
            "verified_behavior": discovered["verified"],
            "candidates": prepared,
            "discovery_calls": discovery_calls,
            "investigation_calls": investigation_calls,
            "verification_calls": verification_calls,
            "calls": session.calls,
            "actions": actions,
            "integrity_failures": integrity,
        }
    except Exception:
        integrity = 1
        ledger_body = {
            "corpus_commitment": commitment,
            "rejected": [],
            "verified_behavior": [],
            "candidates": [],
            "discovery_calls": discovery_calls,
            "investigation_calls": investigation_calls,
            "verification_calls": verification_calls,
            "calls": discovery_calls + investigation_calls + verification_calls,
            "actions": actions,
            "integrity_failures": integrity,
        }
    finally:
        close_run()
    ledger_body["frozen_hash"] = ledger_hash(ledger_body)
    (root / "ledger.json").write_text(json.dumps(ledger_body, sort_keys=True), encoding="utf-8")
    scored = judge(ledger_body, seal)
    return {
        "model": MODEL,
        "model_digest": OLLAMA_DIGEST,
        "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
        "plan_hash": plan_commitment(commitment),
        "corpus_commitment": commitment,
        "ledger_hash": ledger_body["frozen_hash"],
        "calls": ledger_body["calls"],
        "allocation": ALLOCATION,
        "discovery_calls": ledger_body["discovery_calls"],
        "investigation_calls": ledger_body["investigation_calls"],
        "verification_calls": ledger_body["verification_calls"],
        "actions": ledger_body["actions"],
        "retained": len(ledger_body["candidates"]),
        "integrity_failures": ledger_body["integrity_failures"],
        "scored": scored,
        "hypotheses": [item.get("hypotheses", {}) for item in ledger_body["candidates"]],
        "wire_calls": wire.calls,
    }


def _shell(session, candidate: dict, probe_id: str, scenario_id: str):
    if probe_id == "CF-B":
        return create(scenario_id, CONFIG), "reset"
    if probe_id == "CF-E":
        return session.trajectories.get(candidate.get("branch_id")), "continue"
    return session.trajectories.get(candidate["trajectory_id"]), "continue"
