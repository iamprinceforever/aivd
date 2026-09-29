"""AIVD-RC5-GENERALIZATION-V1 EXPERIMENTER: blind runner for ONE (model, block). Public files only.

Installs the frozen RC3 isolation hook with the RC5 deny-list (every block seal, wire, backup, provider,
scorer and scanner source, LOCAL-V1 and RC4 report dirs + backups, RC4 provider/scorer packages, other
models) BEFORE importing any pipeline code.
Refuses unless AIVD_RC5_RUN_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 and aivd_rc5_gen.preflight passes
(FROZEN_AT_DESIGN, every post-generation field bound and matching the public files, recorded common
order matching, earlier blocks of this model already run).
Main and repeat ledgers get the RC5 provider/runtime/block metadata correction (aivd_rc5_gen.ledger_meta).
NOT RUN in the design phase.
usage: rc5_gen_run_model.py <model_id> <block> <wire_port> [--repeat]
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

from aivd_rc3.isolation import install

from aivd_rc5_gen import EXPERIMENT_ID, FINAL_DIR, PREREG_PATH, PROTECTED_DIR, REPORT_DIR, RUN_ENV, block_name
from aivd_rc5_gen.isolation import forbidden_for, run_dir
from aivd_rc5_gen.models import MODEL_DIRS, MODELS

BASE = Path(REPORT_DIR)


def main(model_id: str, block: int, port: int, repeat: bool = False) -> None:
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if model_id not in MODELS:
        sys.exit("unexpected model")
    install(forbidden_for(model_id))
    prereg = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    from aivd_rc5_gen.preflight import PreflightRefused, check
    try:
        pre = check(prereg, Path(FINAL_DIR), block=block)
    except (PreflightRefused, FileNotFoundError, KeyError, ValueError) as exc:
        sys.exit(f"REFUSED: {exc}")
    from aivd_rc5_gen.bind import bind
    bind()
    from aivd_rc5_gen import config as C
    from aivd_rc5_gen.ledger_meta import run_model, run_repeat
    from aivd_rc5_gen.seeds import discovery_seed_for
    from aivd_post_rc3.publish import public_ledger
    from aivd_post_rc3.stop import (
        check_ledger_integrity, check_no_verifier_leakage, check_rc3_source_unmodified)
    from aivd_stateful.hashing import digest

    check_rc3_source_unmodified()
    if pre["order"]["discovery_seed"] != discovery_seed_for(model_id):
        sys.exit("REFUSED: common discovery seed mismatch")
    rd = run_dir(model_id, block)
    full_dir = Path(PROTECTED_DIR) / rd
    public_dir = BASE / rd
    manifest, commitment = pre["manifest"], pre["block_commitment"]
    if repeat:
        if block != C.REPEAT_BLOCK:
            sys.exit(f"REFUSED: the repeat set runs on block {C.REPEAT_BLOCK} only")
        rep_full = Path(PROTECTED_DIR) / (MODEL_DIRS[model_id] + "_repeat")
        rep_pub = BASE / MODEL_DIRS[model_id] / "repeat_ledger_public.json"
        if not all((BASE / run_dir(model_id, b) / "ledger_public.json").exists() for b in (1, 2, 3)):
            sys.exit("repeat set runs only after all three block ledgers of this model are frozen")
        if rep_full.exists() or rep_pub.exists():
            sys.exit("repeat set already ran")
        transport = _transport(port)
        ledger = run_repeat(rep_full, manifest, transport, block=block, model_id=model_id, corpus_commitment=commitment)
        view = dict(ledger)
        view["full_repeat_frozen_hash"] = view.pop("frozen_hash")
        view["public_hash"] = digest(view)
        rep_pub.write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
        print(json.dumps({"model_id": model_id, "block": block, "repeat": True, "calls": ledger["calls"]}))
        sys.exit(2 if ledger["integrity_failures"] else 0)
    if full_dir.exists() or public_dir.exists():
        sys.exit("run output already exists; each (model, block) runs exactly once")
    for earlier in range(1, block):
        if not (BASE / run_dir(model_id, earlier) / "ledger_public.json").exists():
            sys.exit(f"REFUSED: blocks run in order; {block_name(earlier)} of {model_id} has not run")
    transport = _transport(port)
    ledger = run_model(full_dir, manifest, transport, block=block, model_id=model_id,
                       corpus_commitment=commitment, discovery_seed=discovery_seed_for(model_id))
    check_ledger_integrity(ledger)
    public_dir.mkdir(parents=True, exist_ok=True)
    view = public_ledger(ledger)
    check_no_verifier_leakage({k: v for k, v in view.items() if k != "request_contract"})
    (public_dir / "ledger_public.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"model_id": model_id, "block": block, "calls": ledger["calls"], "stage_calls": ledger["stage_calls"],
                      "integrity_failures": ledger["integrity_failures"], "error": ledger["error"]}))
    if ledger["integrity_failures"]:
        sys.exit(1)


def _transport(port: int):
    url = f"http://127.0.0.1:{port}/api/chat"

    def transport(request):
        call = urllib.request.Request(url, data=json.dumps(request).encode(),
                                      headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(call, timeout=900) as response:
            transport.last_attempts = int(response.headers.get("X-Post-RC3-Attempts", "1"))
            return response.status, response.read()

    transport.last_attempts = 1
    return transport


if __name__ == "__main__":
    flag = "--repeat" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--repeat"]
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if len(args) != 3:
        sys.exit("usage: rc5_gen_run_model.py <model_id> <block> <wire_port> [--repeat]")
    main(args[0], int(args[1]), int(args[2]), flag)
