"""AIVD-RC5-GENERALIZATION-V1 EXPERIMENTER: blind runner for ONE model over the WHOLE 120-scenario corpus.

Installs the frozen RC3 isolation hook with the RC5 deny-list (block seals, assembled seal, exclusion,
wire, backup, provider/scorer/scanner source, LOCAL-V1 and RC4 report dirs + backups, RC4 code, other
models) BEFORE importing any pipeline code. Refuses unless AIVD_RC5_RUN_AUTHORIZED matches and the
MANDATORY preflight gate passes. The confirmation session subclass (frozen alternate context) is bound
in-process. NOT RUN in the design phase.
usage: rc5_gen_run_model.py <model_id> <wire_port> [--repeat]
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

from aivd_rc3.isolation import install

from aivd_rc5_gen import EXPERIMENT_ID, FINAL_DIR, PREREG_PATH, PROTECTED_DIR, REPORT_DIR, RUN_ENV
from aivd_rc5_gen.isolation import forbidden_for, run_dir
from aivd_rc5_gen.models import MODEL_DIRS, MODELS

BASE = Path(REPORT_DIR)


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


def main(model_id: str, port: int, repeat: bool = False) -> None:
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if model_id not in MODELS:
        sys.exit("unexpected model")
    install(forbidden_for(model_id))
    prereg = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    from aivd_rc5_gen.preflight import PreflightRefused, check
    try:
        pre = check(prereg, Path(FINAL_DIR), model_id=model_id)
    except (PreflightRefused, FileNotFoundError, KeyError, ValueError) as exc:
        sys.exit(f"REFUSED: {exc}")
    from aivd_rc5_gen.confirm import confirm_map
    from aivd_rc5_gen.bind import bind
    bind(confirm_mapping=confirm_map(pre["ordered_manifest"]))
    from aivd_rc5_gen.ledger_meta import run_model, run_repeat
    from aivd_post_rc3.publish import public_ledger
    from aivd_post_rc3.stop import check_ledger_integrity, check_no_verifier_leakage, check_rc3_source_unmodified
    from aivd_stateful.hashing import digest

    check_rc3_source_unmodified()
    ordered, commitment, coh = pre["ordered_manifest"], pre["corpus_commitment"], pre["common_order_sha256"]
    rd = run_dir(model_id)
    full_dir = Path(PROTECTED_DIR) / rd
    public_dir = BASE / rd
    transport = _transport(port)
    if repeat:
        if not (public_dir / "ledger_public.json").exists():
            sys.exit("repeat set runs only after this model's main ledger is frozen")
        rep_full = Path(PROTECTED_DIR) / (MODEL_DIRS[model_id] + "_repeat")
        if rep_full.exists() or (public_dir / "repeat_ledger_public.json").exists():
            sys.exit("repeat set already ran")
        ledger = run_repeat(rep_full, ordered, transport, common_order_sha256=coh, model_id=model_id,
                            corpus_commitment=commitment)
        view = dict(ledger)
        view["full_repeat_frozen_hash"] = view.pop("frozen_hash")
        view["public_hash"] = digest(view)
        (public_dir / "repeat_ledger_public.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
        print(json.dumps({"model_id": model_id, "repeat": True, "calls": ledger["calls"]}))
        sys.exit(2 if ledger["integrity_failures"] else 0)
    if full_dir.exists() or public_dir.exists():
        sys.exit("run output already exists; each model runs exactly once")
    ledger = run_model(full_dir, ordered, transport, common_order_sha256=coh, model_id=model_id,
                       corpus_commitment=commitment, discovery_seed=None)
    check_ledger_integrity(ledger)
    public_dir.mkdir(parents=True, exist_ok=True)
    view = public_ledger(ledger)
    check_no_verifier_leakage({k: v for k, v in view.items() if k != "request_contract"})
    (public_dir / "ledger_public.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    # Exposure by security/benign label is computed by the SCORER (labels are sealed); the experimenter
    # records only the explored count and the preflight's shape-based prediction.
    print(json.dumps({"model_id": model_id, "calls": ledger["calls"], "stage_calls": ledger["stage_calls"],
                      "scenarios_explored": len(set(ledger.get("explored", []))),
                      "predicted_exposed": pre["predicted_exposure"]["exposed_count"],
                      "integrity_failures": ledger["integrity_failures"], "error": ledger["error"]}))
    if ledger["integrity_failures"]:
        sys.exit(1)


if __name__ == "__main__":
    flag = "--repeat" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--repeat"]
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if len(args) != 2:
        sys.exit("usage: rc5_gen_run_model.py <model_id> <wire_port> [--repeat]")
    main(args[0], int(args[1]), flag)
