"""Blind pass runner (Phase 10/11). One process per pass.

The process installs an audit hook that forbids reading the protected seal directory and every
other pass's directories BEFORE doing anything else. It loads only the public manifest and the
public corpus commitment, talks to the evaluator-side wire proxy over HTTP, and writes:
  reports/aivd_rc1/protected/<pass>/...   full ledger + raw session (ignored; may hold raw outputs)
  reports/aivd_rc1/<pass>/ledger_public.json   redacted public ledger (committed)
"""

import json
import sys
import urllib.request
from pathlib import Path

from aivd_rc1.isolation import install

PASSES = ("P1", "P2")


def main(pass_id: str, discovery_seed: int, port: int) -> None:
    if pass_id not in PASSES:
        sys.exit("unknown pass")
    others = [p for p in PASSES if p != pass_id]
    forbidden = [Path("reports/aivd_rc1/protected/final_seal.json"), Path("reports/aivd_rc1/protected/wire")]
    for other in others:
        forbidden += [Path(f"reports/aivd_rc1/protected/{other}"), Path(f"reports/aivd_rc1/{other}")]
    install(forbidden)

    from aivd_rc1.driver import check_identity, run_pass, runtime_identity
    from aivd_rc1.publish import public_ledger

    full_dir = Path(f"reports/aivd_rc1/protected/{pass_id}")
    public_dir = Path(f"reports/aivd_rc1/{pass_id}")
    if full_dir.exists() or public_dir.exists():
        sys.exit("pass output already exists; a pass runs exactly once")
    identity = runtime_identity()
    check_identity(identity)
    manifest = json.loads(Path("reports/aivd_rc1/final/public_manifest.json").read_text(encoding="utf-8"))
    commitment = json.loads(Path("reports/aivd_rc1/final/corpus_commitment.json").read_text(encoding="utf-8"))["corpus_commitment"]
    url = f"http://127.0.0.1:{port}/api/chat"

    def transport(request):
        call = urllib.request.Request(url, data=json.dumps(request).encode(),
                                      headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(call, timeout=900) as response:
            return response.status, response.read()

    ledger = run_pass(full_dir, manifest, transport, pass_id=pass_id, corpus_commitment=commitment,
                      discovery_seed=discovery_seed, identity=identity)
    public_dir.mkdir(parents=True)
    view = public_ledger(ledger)
    (public_dir / "ledger_public.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"pass": pass_id, "stage_calls": ledger["stage_calls"], "calls": ledger["calls"],
                      "integrity_failures": ledger["integrity_failures"], "error": ledger["error"],
                      "full_ledger_hash": ledger["frozen_hash"], "public_ledger_hash": view["public_ledger_hash"],
                      "retained": len(ledger["candidates"]),
                      "verification_ready": sum(c["promotion"] == "VERIFICATION_READY" for c in ledger["candidates"]),
                      "confirmed": sum(c.get("verification_decision") == "CONFIRMED" for c in ledger["candidates"])}))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
