"""Mechanical claim ceiling. A flag is not isolation, and a missing history check is not readiness."""

from __future__ import annotations


def evaluate(
    manifest: dict,
    *,
    leakage_clean: bool,
    corpus_valid: bool,
    sealed: bool,
    architecture: str = "same_interpreter",
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
    env_ready = all(value == "VERIFIED" for value in manifest["environment"].values())
    history_ok = manifest["provider_history_isolation"] == "VERIFIED"
    if architecture == "same_interpreter":
        status = "SAME_INTERPRETER_INVALID"
    elif architecture == "logical_only":
        status = "LOGICAL_ONLY_SEPARATION"
    elif not history_ok:
        status = "HISTORY_ISOLATION_UNVERIFIED"
    elif architecture == "process":
        status = "PROCESS_ISOLATED"
    elif architecture == "filesystem" and env_ready and leakage_clean and corpus_valid and sealed:
        status = "SOURCE_D_READY"
    elif architecture == "filesystem":
        status = "PROVIDER_ISOLATED"
    else:
        status = "SAME_INTERPRETER_INVALID"
    return {"missing": missing, "status": status}
