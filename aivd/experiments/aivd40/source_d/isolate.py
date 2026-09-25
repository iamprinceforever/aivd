"""Qualify a provider environment. Missing evidence stays missing."""

from __future__ import annotations

from aivd.experiments.aivd40.source_d import SEPARATION

ENVIRONMENT_CHECKS = (
    "aivd_env",
    "filesystem_aivd_mount",
    "git_credentials",
    "historical_target_files",
    "network",
    "prompt_history",
    "reports",
    "working_tree",
)
HISTORY_FIELDS = (
    "aivd_history_access_verified",
    "fresh_context_verified",
    "model_version",
    "prior_history_access_verified",
    "session_identity",
)


def qualify(snapshot: dict) -> dict:
    fields = {}
    for name in ENVIRONMENT_CHECKS:
        if name not in snapshot:
            fields[name] = "NOT_RECORDED"
        elif snapshot[name] is True:
            fields[name] = "VERIFIED"
        else:
            fields[name] = "NOT_VERIFIED"
    history = {}
    for name in HISTORY_FIELDS:
        value = snapshot.get(name, "NOT_RECORDED")
        if value not in {"TRUE", "FALSE", "NOT_RECORDED"}:
            value = "NOT_RECORDED"
        history[name] = value
    if all(history[name] == "TRUE" for name in HISTORY_FIELDS):
        history_status = "VERIFIED"
    else:
        history_status = "NOT_VERIFIED"
    network = snapshot.get("network_endpoints", [])
    return {
        "environment": fields,
        "history": history,
        "network_endpoints": list(network),
        "provider_history_isolation": history_status,
        "separation": SEPARATION,
    }
