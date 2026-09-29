"""AIVD-RC4-MULTI-V1 EXPERIMENTER: blind runner for one model. Public manifest only.

Installs the frozen RC3 isolation hook with the RC4 deny-list (seal, wire, backup, provider and scorer
source, LOCAL-V1 protected store, other models) BEFORE importing any pipeline code.
Refuses unless AIVD_RC4_RUN_AUTHORIZED=AIVD-RC4-MULTI-V1 and the preregistration is FROZEN.
NOT RUN in the design phase.
usage: rc4_multi_run_model.py <model_id> <wire_port> [--repeat]
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

from aivd_rc3.isolation import install

from aivd_rc4_multi import EXPERIMENT_ID, PROTECTED_DIR, REPORT_DIR, RUN_ENV
from aivd_rc4_multi.isolation import forbidden_for
from aivd_post_rc3_local.models import MODEL_DIRS, MODELS

BASE = Path(REPORT_DIR)
PREREG = Path("docs/rc4_multi_v1/PREREGISTRATION.json")


def main(model_id: str, port: int, repeat: bool = False) -> None:
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if model_id not in MODELS:
        sys.exit("unexpected model")
    install(forbidden_for(model_id))
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    if prereg.get("status") != "FROZEN" or not prereg["corpus"].get("corpus_commitment"):
        sys.exit("REFUSED: preregistration not frozen")
    from aivd_rc4_multi.bind import bind
    bind()
    from aivd_post_rc3.driver import run_model, run_repeat
    from aivd_post_rc3.publish import public_ledger
    from aivd_post_rc3.stop import (
        check_corpus_commitment, check_ledger_integrity, check_no_verifier_leakage, check_rc3_source_unmodified)
    from aivd_rc4_multi.seeds import discovery_seed_for
    from aivd_stateful.hashing import digest

    check_rc3_source_unmodified()
    mdir = MODEL_DIRS[model_id]
    full_dir = Path(PROTECTED_DIR) / (mdir + ("_repeat" if repeat else ""))
    public_dir = BASE / mdir
    if repeat:
        if not (public_dir / "ledger_public.json").exists():
            sys.exit("repeat set runs only after the model's main ledger is frozen")
        if full_dir.exists() or (public_dir / "repeat_ledger_public.json").exists():
            sys.exit("repeat set already ran")
    elif full_dir.exists() or public_dir.exists():
        sys.exit("model output already exists; each model runs exactly once")
    manifest = json.loads((BASE / "final/public_manifest.json").read_text(encoding="utf-8"))
    commitment = json.loads((BASE / "final/corpus_commitment.json").read_text(encoding="utf-8"))["corpus_commitment"]
    check_corpus_commitment(prereg["corpus"]["corpus_commitment"], commitment)
    url = f"http://127.0.0.1:{port}/api/chat"

    def transport(request):
        call = urllib.request.Request(url, data=json.dumps(request).encode(),
                                      headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(call, timeout=900) as response:
            transport.last_attempts = int(response.headers.get("X-Post-RC3-Attempts", "1"))
            return response.status, response.read()

    transport.last_attempts = 1
    if repeat:
        ledger = run_repeat(full_dir, manifest, transport, model_id=model_id, corpus_commitment=commitment)
        view = dict(ledger)
        view["full_repeat_frozen_hash"] = view.pop("frozen_hash")
        view["public_hash"] = digest(view)
        (public_dir / "repeat_ledger_public.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
        print(json.dumps({"model_id": model_id, "repeat": True, "calls": ledger["calls"]}))
        sys.exit(2 if ledger["integrity_failures"] else 0)
    ledger = run_model(full_dir, manifest, transport, model_id=model_id,
                       corpus_commitment=commitment, discovery_seed=discovery_seed_for(model_id))
    check_ledger_integrity(ledger)
    public_dir.mkdir(parents=True, exist_ok=True)
    view = public_ledger(ledger)
    check_no_verifier_leakage({k: v for k, v in view.items() if k != "request_contract"})
    (public_dir / "ledger_public.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"model_id": model_id, "calls": ledger["calls"], "stage_calls": ledger["stage_calls"],
                      "integrity_failures": ledger["integrity_failures"], "error": ledger["error"]}))
    if ledger["integrity_failures"]:
        sys.exit(1)


if __name__ == "__main__":
    flag = "--repeat" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--repeat"]
    main(args[0], int(args[1]), flag)
