"""Mechanical claim ceiling. It never upgrades a missing check."""

from __future__ import annotations


def evaluate(
    manifest: dict,
    *,
    leakage_clean: bool,
    corpus_valid: bool,
    sealed: bool,
    physical_separation: bool = False,
) -> dict:
    missing = []
    if not corpus_valid or not leakage_clean:
        missing.append("corpus")
    for name, value in manifest["environment"].items():
        if value != "VERIFIED":
            missing.append(name)
    if manifest["provider_history_isolation"] != "VERIFIED":
        missing.append("provider_history")
    if not sealed:
        missing.append("sealed")
    if not physical_separation:
        missing.append("physical_separation")
    env_failed = any(value == "NOT_VERIFIED" for value in manifest["environment"].values())
    env_ready = all(value == "VERIFIED" for value in manifest["environment"].values())
    history_values = set(manifest["history"].values())
    if (not corpus_valid) or (not leakage_clean) or env_failed or not env_ready:
        status = "SOURCE_D_INVALID"
    elif manifest["provider_history_isolation"] != "VERIFIED":
        if history_values == {"NOT_RECORDED"}:
            status = "ENGINE_ISOLATED_ONLY"
        else:
            status = "PROVIDER_HISTORY_NOT_VERIFIED"
    elif not sealed:
        status = "PROVIDER_ISOLATED"
    elif physical_separation:
        status = "SOURCE_D_READY"
    else:
        status = "PROVIDER_ISOLATED"
    return {"missing": missing, "status": status}
