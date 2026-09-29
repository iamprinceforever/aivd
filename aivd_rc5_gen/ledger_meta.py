"""RC5 ledger metadata correction (provider/runtime label + common-order hash only).

The frozen POST-RC3 driver writes a hard-coded hosted-provider label into every main ledger (a literal
inside `run_model`). RC5 must not edit that frozen file, so this RC5-layer post-write step rewrites ONLY
the provider label, adds the local runtime record and the RC5 block label, then recomputes the ledger
hash with the frozen `aivd_rc3.verifier.ledger_hash`. No candidate, call, stage, output, decision or
budget field changes. Same mechanism as RC4 (aivd_rc4_multi.ledger_meta), re-implemented here so RC5
imports nothing from the RC4 package.
"""

import hashlib
import json
from pathlib import Path

from aivd_rc3.verifier import ledger_hash

from aivd_post_rc3_local.models import RUNTIME

PROVIDER_LABEL = "LOCAL-Ollama"
RUNTIME_RECORD = {"engine": RUNTIME["engine"], "version": RUNTIME["version"], "base_url": RUNTIME["base_url"],
                  "chat_path": RUNTIME["chat_path"], "remote_api": RUNTIME["remote_api"]}
assert RUNTIME_RECORD["base_url"] == "http://127.0.0.1:11434"
CORRECTED_FIELDS = ("provider", "runtime", "rc5_common_order_sha256")


def correct(ledger: dict, *, common_order_sha256: str, driver_file_sha256: str) -> dict:
    out = {k: v for k, v in ledger.items() if k != "frozen_hash"}
    out["provider"] = PROVIDER_LABEL
    out["runtime"] = dict(RUNTIME_RECORD)
    out["rc5_common_order_sha256"] = common_order_sha256
    out["metadata_correction"] = {
        "applied_by": "aivd_rc5_gen.ledger_meta", "fields": list(CORRECTED_FIELDS),
        "reason": "shared frozen POST-RC3 driver writes a stale hosted-provider label; RC5 runs local Ollama",
        "driver_ledger_sha256": driver_file_sha256, "driver_frozen_hash": ledger.get("frozen_hash")}
    out["frozen_hash"] = ledger_hash(out)
    return out


def correct_file(path: Path, ledger: dict, *, common_order_sha256: str) -> dict:
    path = Path(path)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != hashlib.sha256(
            json.dumps(ledger, sort_keys=True, indent=1).encode("utf-8")).hexdigest():
        raise RuntimeError("driver ledger file does not match the returned ledger")
    fixed = correct(ledger, common_order_sha256=common_order_sha256, driver_file_sha256=hashlib.sha256(raw).hexdigest())
    path.write_text(json.dumps(fixed, sort_keys=True, indent=1), encoding="utf-8")
    return fixed


def run_model(root, ordered_public, transport, *, common_order_sha256: str, **kw) -> dict:
    """ONE whole-corpus run. `ordered_public` is the 120-row manifest in the committed common order;
    discovery_seed is forced to None so the frozen discovery performs no further shuffle."""
    from aivd_post_rc3.driver import run_model as frozen_run_model
    kw["discovery_seed"] = None
    ledger = frozen_run_model(root, ordered_public, transport, **kw)
    return correct_file(Path(root) / "ledger.json", ledger, common_order_sha256=common_order_sha256)


def run_repeat(root, ordered_public, transport, *, common_order_sha256: str, **kw) -> dict:
    from aivd_post_rc3.driver import run_repeat as frozen_run_repeat
    ledger = frozen_run_repeat(root, ordered_public, transport, **kw)
    return correct_file(Path(root) / "repeat_ledger.json", ledger, common_order_sha256=common_order_sha256)
