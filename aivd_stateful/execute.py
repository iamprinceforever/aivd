"""Authorized STATEFUL-1 runner. Refuses to start unless the pinned runtime matches."""

import hashlib
import json
import urllib.request
from pathlib import Path

from aivd_stateful.authorize import authorize_execution, close_session, open_session, plan_commitment
from aivd_stateful.behaviors import corpus_commitment, public_manifest, seal_document
from aivd_stateful.contract import (
    HOLDOUT_CALLS,
    MODEL,
    OLLAMA_DIGEST,
    OLLAMA_EXECUTABLE_SHA256,
    SMOKE_CALLS,
)
from aivd_stateful.discover import run
from aivd_stateful.evaluate import evaluate, ledger_hash
from aivd_stateful.model import Budget
from aivd_stateful.smoke import run_smoke

BINARY = Path("/var/tmp/ollama-v0344/extract/ollama")
MANIFEST = Path("/var/tmp/ollama-models-17b/manifests/registry.ollama.ai/library/qwen3/1.7b")
CHAT = "http://127.0.0.1:11434/api/chat"


def assert_identity() -> None:
    binary = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    manifest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    if binary != OLLAMA_EXECUTABLE_SHA256 or manifest != OLLAMA_DIGEST:
        raise RuntimeError("pinned model or runtime does not match")


def ollama_transport(request: dict) -> tuple:
    payload = json.dumps(request).encode()
    call = urllib.request.Request(CHAT, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def main(root: Path) -> dict:
    assert_identity()
    from aivd_stateful.session import Session

    commitment = corpus_commitment()
    token = authorize_execution(
        explicit=True,
        experiment_id="STATEFUL-1",
        plan_hash=plan_commitment(commitment),
        corpus_commitment=commitment,
    )
    root.mkdir(parents=True, exist_ok=True)
    open_session(token)
    try:
        smoke_session = Session(root / "smoke", ollama_transport, Budget(limit=SMOKE_CALLS))
        smoke = run_smoke(smoke_session)
        if not smoke["checks"]["pass"]:
            return {"smoke": smoke, "holdout": None, "status": "FAILED"}
        holdout_session = Session(root / "holdout", ollama_transport, Budget(limit=HOLDOUT_CALLS))
        ledger = run(public_manifest(), holdout_session)
        ledger["calls"] = holdout_session.calls
        ledger["budget_limit"] = HOLDOUT_CALLS
        ledger["frozen_hash"] = ledger_hash(ledger)
        (root / "ledger.json").write_text(json.dumps(ledger, sort_keys=True), encoding="utf-8")
        scored = evaluate(ledger, seal_document(), commitment)
    finally:
        close_session()
    return {
        "model": MODEL,
        "model_digest": OLLAMA_DIGEST,
        "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
        "corpus_commitment": commitment,
        "plan_hash": plan_commitment(commitment),
        "smoke": smoke,
        "smoke_calls": smoke["calls"],
        "holdout_calls": ledger["calls"],
        "ledger_hash": ledger["frozen_hash"],
        "scored": scored,
        "decisions": ledger["decisions"],
        "retained": len(ledger["retained"]),
        "verified": ledger["verified"],
        "rejected": ledger["rejected"],
        "status": "SCORED",
    }
