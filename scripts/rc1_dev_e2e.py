"""DEVELOPMENT E2E with the real pinned model. DEVELOPMENT ONLY; metrics are not evidence."""

import json
import sys
import urllib.request
from pathlib import Path

from aivd_rc1.dev_corpus import dev_seal
from aivd_rc1.driver import check_identity, judge_pass, run_pass, runtime_identity
from aivd_rc1.provider import commit, public_manifest
from aivd_rc1.wire import Wire

CHAT = "http://127.0.0.1:11434/api/chat"


def transport(request):
    call = urllib.request.Request(CHAT, data=json.dumps(request).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def main(out: str, pass_id: str, seed: int) -> None:
    identity = runtime_identity()
    check_identity(identity)
    seal = dev_seal()
    root = Path(out)
    wire = Wire(seal, transport, root / "wire")
    ledger = run_pass(root, public_manifest(seal), wire, pass_id=pass_id,
                      corpus_commitment=commit(seal), discovery_seed=seed, identity=identity)
    scored = judge_pass(ledger, seal)
    (root / "scored.json").write_text(json.dumps(scored, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"stage_calls": ledger["stage_calls"], "calls": ledger["calls"],
                      "integrity": ledger["integrity_failures"], "error": ledger["error"],
                      "verified": scored["verified_targets"], "discovered": scored["discovered_targets"],
                      "fp_behavioral": len(scored["false_positives_behavioral"]),
                      "fp_security": len(scored["false_positives_security"])}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
