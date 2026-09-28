"""POST-RC3 blind per-model runner. One process per model.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.

Installs the frozen RC3 audit-hook isolation FIRST (no reading of the protected seal,
the wire dir, or any other model's directories). Loads only the public manifest and
corpus commitment. Talks to the evaluator-side wire proxy over localhost HTTP.
Writes:
  reports/aivd_post_rc3/protected/<model_dir>/...     full ledger + raw (ignored)
  reports/aivd_post_rc3/<model_dir>/ledger_public.json redacted public ledger

usage: post_rc3_run_model.py <model_id> <port> [--repeat]
  --repeat  run the preregistered reproducibility repeat set (OUTSIDE the 96) AFTER the model's
            main public ledger exists; writes protected/<model_dir>_repeat/ and
            <model_dir>/repeat_ledger_public.json
"""

import json
import sys
import urllib.request
from pathlib import Path

from aivd_rc3.isolation import install

from aivd_post_rc3.models import MODEL_DIRS, MODELS

BASE = Path("reports/aivd_post_rc3")


def main(model_id: str, port: int, repeat: bool = False) -> None:
    if model_id not in MODELS:
        sys.exit("unexpected model")
    mdir = MODEL_DIRS[model_id]
    forbidden = [BASE / "protected/final_seal.json", BASE / "protected/wire"]
    for other in MODELS:
        if other != model_id:
            forbidden += [BASE / "protected" / MODEL_DIRS[other], BASE / MODEL_DIRS[other],
                          BASE / "protected" / (MODEL_DIRS[other] + "_repeat")]
    install(forbidden)

    from aivd_post_rc3.driver import run_model
    from aivd_post_rc3.publish import public_ledger
    from aivd_post_rc3.seeds import discovery_seed_for
    from aivd_post_rc3.stop import (check_corpus_commitment, check_ledger_integrity,
                                    check_no_api_key_leakage, check_no_verifier_leakage,
                                    check_rc3_source_unmodified)

    check_rc3_source_unmodified()
    full_dir = BASE / "protected" / mdir
    public_dir = BASE / mdir
    if repeat:
        if not (public_dir / "ledger_public.json").exists():
            sys.exit("repeat set runs only after the model's main ledger is frozen")
        rep_dir = BASE / "protected" / (mdir + "_repeat")
        rep_public = public_dir / "repeat_ledger_public.json"
        if rep_dir.exists() or rep_public.exists():
            sys.exit("repeat set already ran; it runs exactly once")
    elif full_dir.exists() or public_dir.exists():
        sys.exit("model output already exists; each model runs exactly once")
    manifest = json.loads((BASE / "final/public_manifest.json").read_text(encoding="utf-8"))
    commitment = json.loads((BASE / "final/corpus_commitment.json").read_text(encoding="utf-8"))["corpus_commitment"]
    prereg = json.loads((BASE / "final/preregistration.json").read_text(encoding="utf-8"))
    check_corpus_commitment(prereg["corpus_commitment"], commitment)
    url = f"http://127.0.0.1:{port}/api/chat"

    def transport(request):
        call = urllib.request.Request(url, data=json.dumps(request).encode(),
                                      headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(call, timeout=900) as response:
            transport.last_attempts = int(response.headers.get("X-Post-RC3-Attempts", "1"))
            return response.status, response.read()
    transport.last_attempts = 1

    if repeat:
        from aivd_post_rc3.driver import run_repeat
        from aivd_rc3.publish import redact_text
        from aivd_stateful.hashing import digest
        rep = run_repeat(rep_dir, manifest, transport, model_id=model_id, corpus_commitment=commitment)
        if rep["integrity_failures"]:
            print(json.dumps({"model_id": model_id, "repeat_error": rep["error"]}))
            sys.exit(2)
        view = dict(rep)
        view["full_repeat_frozen_hash"] = view.pop("frozen_hash")
        view["public_hash"] = digest(view)
        rep_public.write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
        check_no_api_key_leakage([rep_public])
        print(json.dumps({"model_id": model_id, "repeat_calls": rep["calls"], "api_attempts": rep["api_attempts"],
                          "subset": rep["subset"], "retained": len(rep["retained"])}))
        return
    ledger = run_model(full_dir, manifest, transport, model_id=model_id, corpus_commitment=commitment,
                       discovery_seed=discovery_seed_for(model_id))
    check_ledger_integrity(ledger)
    public_dir.mkdir(parents=True)
    view = public_ledger(ledger)
    check_no_verifier_leakage({k: v for k, v in view.items() if k != "request_contract"})
    out = public_dir / "ledger_public.json"
    out.write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    check_no_api_key_leakage([out])
    print(json.dumps({"model_id": model_id, "stage_calls": ledger["stage_calls"], "calls": ledger["calls"],
                      "api_attempts": ledger["api_attempts"],
                      "integrity_failures": ledger["integrity_failures"], "error": ledger["error"],
                      "full_ledger_hash": ledger["frozen_hash"], "public_ledger_hash": view["public_ledger_hash"],
                      "retained": len(ledger["candidates"]),
                      "verification_ready": sum(c["promotion"] == "VERIFICATION_READY" for c in ledger["candidates"]),
                      "confirmed": sum(c.get("verification_decision") == "CONFIRMED" for c in ledger["candidates"])}))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), "--repeat" in sys.argv[3:])
