"""Structural checks only. This module does not decide whether an artifact holds."""

from __future__ import annotations

FORBIDDEN_FIELDS = {
    "aivd_finding",
    "expected",
    "expected_result",
    "label",
    "leak_location",
    "provider_result",
    "security_result",
    "target",
    "vulnerable",
    "vulnerability",
}


class SchemaError(ValueError):
    pass


def _reject_fields(obj: dict, where: str) -> None:
    for key in obj:
        if key in FORBIDDEN_FIELDS:
            raise SchemaError(f"{where} contains a forbidden field")


def validate_artifact(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise SchemaError("artifact must be an object")
    _reject_fields(raw, "artifact")
    if not isinstance(raw.get("program"), str) or raw["program"] == "":
        raise SchemaError("program is required")
    if not isinstance(raw.get("public_input"), str):
        raise SchemaError("public input is required")
    channel = raw.get("private_channel")
    if channel is not None:
        if not isinstance(channel, (list, tuple)) or len(channel) != 4:
            raise SchemaError("private channel is malformed")
        if any(not isinstance(item, (bytes, bytearray)) or len(item) == 0 for item in channel):
            raise SchemaError("private channel is malformed")
    policy = raw.get("policy")
    if policy is not None:
        if not isinstance(policy, dict):
            raise SchemaError("policy is malformed")
        _reject_fields(policy, "policy")
        alike = policy.get("alike")
        observations = policy.get("observations")
        if not isinstance(alike, list) or len(alike) < 2:
            raise SchemaError("policy is malformed")
        if not isinstance(observations, dict):
            raise SchemaError("policy is malformed")
        if any(name not in observations for name in alike):
            raise SchemaError("policy is malformed")
    projections = raw.get("projections")
    if projections is not None:
        if not isinstance(projections, (list, tuple)) or len(projections) != 4:
            raise SchemaError("projections are malformed")
        if any(not isinstance(item, str) for item in projections):
            raise SchemaError("projections are malformed")
    return {
        "policy": None
        if policy is None
        else {"alike": list(policy["alike"]), "observations": dict(policy["observations"])},
        "private_channel": None if channel is None else tuple(bytes(item) for item in channel),
        "program": raw["program"],
        "projections": None if projections is None else tuple(projections),
        "public_input": raw["public_input"],
        "sealed_provider_result": raw.get("sealed_provider_result"),
    }
