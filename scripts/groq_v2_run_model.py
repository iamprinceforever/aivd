"""Blind POST-RC3-GROQ-V2 runner. One model. Public manifest only."""

import json
import sys
import urllib.request
from pathlib import Path

from aivd_rc3.isolation import install

from aivd_post_rc3.models import MODEL_DIRS, MODELS
from aivd_post_rc3_v2.bind import bind

BASE = Path("reports/aivd_post_rc3_v2")


def main(model_id: str, port: int, repeat: bool = False) -> None:
    if model_id not in MODELS:
        sys.exit("unexpected model")
    bind()
    mdir = MODEL_DIRS[model_id]
    forbidden = [BASE / "protected/final_seal.json", BASE / "protected/wire"]
    for other in MODELS:
        if other != model_id:
            forbidden += [
                BASE / "protected" / MODEL_DIRS[other],
                BASE / MODEL_DIRS[other],
                BASE / "protected" / (MODEL_DIRS[other] + "_repeat"),
            ]
    install(forbidden)

    from aivd_post_rc3_v2.driver import run_model, run_repeat
    from aivd_post_rc3.publish import public_ledger
    from aivd_post_rc3.stop import (
        check_corpus_commitment,
        check_ledger_integrity,
        check_no_api_key_leakage,
        check_no_verifier_leakage,
        check_rc3_source_unmodified,
    )
    from aivd_post_rc3_v2.seeds import discovery_seed_for
    from aivd_stateful.hashing import digest

    check_rc3_source_unmodified()
    full_dir = BASE / "protected" / (mdir + ("_repeat" if repeat else ""))
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
    prereg = json.loads((BASE / "final/preregistration.json").read_text(encoding="utf-8"))
    check_corpus_commitment(prereg["corpus_commitment"], commitment)
    url = f"http://127.0.0.1:{port}/api/chat"

    def transport(request):
        call = urllib.request.Request(
            url, data=json.dumps(request).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(call, timeout=900) as response:
            transport.last_attempts = int(response.headers.get("X-Post-RC3-Attempts", "1"))
            return response.status, response.read()

    transport.last_attempts = 1
    if repeat:
        ledger = run_repeat(full_dir, manifest, transport, model_id=model_id, corpus_commitment=commitment)
        if ledger["integrity_failures"]:
            print(json.dumps({"model_id": model_id, "repeat_error": ledger["error"]}))
            sys.exit(2)
        view = dict(ledger)
        view["full_repeat_frozen_hash"] = view.pop("frozen_hash")
        view["public_hash"] = digest(view)
        out = public_dir / "repeat_ledger_public.json"
        out.write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
        check_no_api_key_leakage([out])
        print(json.dumps({"model_id": model_id, "repeat": True, "calls": ledger["calls"]}))
        return
    ledger = run_model(
        full_dir, manifest, transport, model_id=model_id,
        corpus_commitment=commitment, discovery_seed=discovery_seed_for(model_id))
    check_ledger_integrity(ledger)
    public_dir.mkdir(parents=True, exist_ok=True)
    view = public_ledger(ledger)
    check_no_verifier_leakage({k: v for k, v in view.items() if k != "request_contract"})
    out = public_dir / "ledger_public.json"
    out.write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    check_no_api_key_leakage([out])
    print(json.dumps({
        "model_id": model_id, "calls": ledger["calls"], "stage_calls": ledger["stage_calls"],
        "integrity_failures": ledger["integrity_failures"], "error": ledger["error"],
        "retained": len(ledger["candidates"]),
    }))
    if ledger["integrity_failures"]:
        sys.exit(1)


if __name__ == "__main__":
    repeat_flag = "--repeat" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--repeat"]
    main(args[0], int(args[1]), repeat_flag)
