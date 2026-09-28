"""Run ENDGAME-2. Discovery is the frozen policy; the seal stays in this driver."""

import hashlib
import json
import urllib.request
from pathlib import Path

from aivd_stateful.contract import MODEL, OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.discover import run
from aivd_stateful.model import Budget

from aivd_endgame2.authorize import authorize, close_run, open_run, plan_commitment
from aivd_endgame2.provider import commit, public_manifest
from aivd_endgame2.session import EndgameSession
from aivd_endgame2.spec import ALLOCATION, DISCOVERY_SHA256
from aivd_endgame2.verifier import evaluate, ledger_hash
from aivd_endgame2.wire import Wire

BINARY = Path("/var/tmp/ollama-v0344/extract/ollama")
MANIFEST = Path("/var/tmp/ollama-models-17b/manifests/registry.ollama.ai/library/qwen3/1.7b")
CHAT = "http://127.0.0.1:11434/api/chat"


def assert_identity() -> None:
    binary = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    manifest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    discovery = hashlib.sha256(Path("aivd_stateful/discover.py").read_bytes()).hexdigest()
    if binary != OLLAMA_EXECUTABLE_SHA256 or manifest != OLLAMA_DIGEST or discovery != DISCOVERY_SHA256:
        raise RuntimeError("identity mismatch")


def ollama_transport(request: dict) -> tuple:
    payload = json.dumps(request).encode()
    call = urllib.request.Request(CHAT, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def execute(root: Path, seal: dict, transport) -> dict:
    assert_identity()
    commitment = commit(seal)
    token = authorize(
        explicit=True,
        experiment_id="ENDGAME-2",
        plan_hash=plan_commitment(commitment),
        corpus_commitment=commitment,
    )
    public = public_manifest(seal)
    root.mkdir(parents=True, exist_ok=True)
    wire = Wire(seal, transport, root / "wire")
    open_run(token)
    try:
        session = EndgameSession(root / "public", wire, Budget(limit=ALLOCATION))
        ledger = run(public, session)
    finally:
        close_run()
    steps = {item["scenario_id"]: item["steps"] for item in public}
    for candidate in ledger["retained"]:
        candidate["public_steps"] = steps[candidate["scenario_id"]]
    ledger["calls"] = session.calls
    ledger["corpus_commitment"] = commitment
    ledger["frozen_hash"] = ledger_hash(ledger)
    (root / "ledger.json").write_text(json.dumps(ledger, sort_keys=True), encoding="utf-8")
    scored = evaluate(ledger, seal)
    actions = {}
    for record in session.records:
        actions[record["action"]] = actions.get(record["action"], 0) + 1
    return {
        "model": MODEL,
        "model_digest": OLLAMA_DIGEST,
        "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
        "corpus_commitment": commitment,
        "plan_hash": plan_commitment(commitment),
        "ledger_hash": ledger["frozen_hash"],
        "calls": session.calls,
        "allocation": ALLOCATION,
        "actions": actions,
        "retained": len(ledger["retained"]),
        "verified_candidates": len(ledger["verified"]),
        "rejected": ledger["rejected"],
        "scored": scored,
        "wire_calls": wire.calls,
    }
