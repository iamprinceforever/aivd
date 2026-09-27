"""Run the frozen end-goal protocol. Prints no sealed values."""

import hashlib
import json
import urllib.request
from pathlib import Path

from aivd_endgame.authorize import production_session
from aivd_endgame.discovery import run
from aivd_endgame.interface import BlindInterface
from aivd_endgame.preregistration import preregistration_hash
from aivd_endgame.provider import read_seal, write_root
from aivd_endgame.spec import (
    MAX_MODEL_CALLS,
    MODEL,
    MODEL_DIGEST,
    PREREGISTRATION_HASH,
    RUNTIME_DIGEST,
    RUNTIME_VERSION,
)
from aivd_endgame.verifier import verify

URL = "http://127.0.0.1:11434/api/chat"
REPORT = Path("/workspace/artifacts/reports/endgame_result.json")
ROOT = Path("/tmp/endgame")


class Stop(Exception):
    pass


def transport(body: bytes) -> tuple[int, bytes]:
    call = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def _public_result(payload: dict, root: Path) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if (root / "seal.json").exists():
        corpus = read_seal(root)
        for scenario in corpus["scenarios"]:
            if scenario["protected_value"] in encoded:
                raise Stop("refusing to write a sealed value")
    REPORT.write_text(encoded + "\n", encoding="utf-8")


def main() -> None:
    if preregistration_hash() != PREREGISTRATION_HASH:
        raise Stop("preregistration mismatch")
    binary = hashlib.sha256(Path("/var/tmp/ollama-v0344/extract/ollama").read_bytes()).hexdigest()
    if binary != RUNTIME_DIGEST:
        raise Stop("runtime mismatch")
    with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=10) as response:
        version = json.loads(response.read())["version"]
    if version != RUNTIME_VERSION:
        raise Stop("runtime mismatch")
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10) as response:
        tags = json.loads(response.read())["models"]
    match = [item for item in tags if item.get("name") == MODEL]
    if len(match) != 1 or match[0].get("digest") != MODEL_DIGEST:
        raise Stop("model digest mismatch")
    commitment = write_root(ROOT)
    print("COMMITMENT", commitment, flush=True)
    evidence = ROOT / "raw"
    interface = None
    request = dict(
        explicit=True,
        experiment_id="ENDGAME",
        preregistration=PREREGISTRATION_HASH,
        model=MODEL,
        model_digest=MODEL_DIGEST,
        runtime_digest=RUNTIME_DIGEST,
        max_calls=MAX_MODEL_CALLS,
    )
    try:
        with production_session(**request) as authorization:
            interface = BlindInterface(ROOT, transport, authorization, evidence)
            ledger = run(interface)
            calls = interface.calls
            failures = list(interface.failures)
        ledger_hash = hashlib.sha256(json.dumps(ledger, sort_keys=True).encode()).hexdigest()
        (ROOT / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
        checked = verify(ROOT, ledger)
    except Stop:
        raise
    except Exception as exc:
        _public_result(
            {
                "status": "INCONCLUSIVE",
                "reason": type(exc).__name__,
                "commitment": commitment,
                "preregistration": PREREGISTRATION_HASH,
                "model_calls": 0 if interface is None else interface.calls,
            },
            ROOT,
        )
        print("INCONCLUSIVE", type(exc).__name__, flush=True)
        return
    payload = {
        "status": "EXECUTED",
        "preregistration": PREREGISTRATION_HASH,
        "commitment": commitment,
        "ledger_hash": ledger_hash,
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "runtime_digest": RUNTIME_DIGEST,
        "model_calls": calls,
        "budget": MAX_MODEL_CALLS,
        "candidates_retained": len(ledger["candidates"]),
        "candidates_discarded": len(ledger["discarded"]),
        "recording_failures": failures,
        "integrity_failures": len(failures),
        "primary": checked["primary"],
        "relation": checked["relation"],
        "targets_sealed": checked["targets_sealed"],
        "targets_discovered": checked["targets_discovered"],
        "targets_verified": checked["targets_verified"],
        "targets_missed": checked["targets_missed"],
        "false_positive_count": len(checked["false_positives"]),
        "false_positive_reasons": [item["reason"] for item in checked["false_positives"]],
        "ambiguous_count": len(checked["ambiguous"]),
        "verified_candidate_ids": [item["candidate_id"] for item in checked["verified"]],
        "contamination": "NONE",
    }
    _public_result(payload, ROOT)
    print("RESULT", checked["primary"], calls, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print("STOP", exc, flush=True)
        raise SystemExit(2)
