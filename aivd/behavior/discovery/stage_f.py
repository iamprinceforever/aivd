"""Stage F harness. It does not execute, and it does not build a corpus.

A valid Source-A seal is not in this repository. Measurement stops before
apply_micro. Source B, Source C, and historical bodies are rejected.
"""

from __future__ import annotations

from typing import Any, Mapping

from aivd.behavior.discovery.constants import DISCOVERY_BANK_HASH, PROTOCOL_VERSION
from aivd.behavior.discovery.errors import BlindnessBroken

WAITING = "STAGE F WAITING FOR INDEPENDENT SEALED SOURCE-A CORPUS"
EXECUTION_ENABLED = False

_REQUIRED = (
    "provider_id",
    "commitment",
    "ciphertext",
    "candidate_count",
    "order_commitment",
    "bank_hash",
    "protocol_version",
    "source_class",
    "timestamp",
    "manufactured_in_repository",
)
_BANNED_FIELDS = (
    "plaintext",
    "body",
    "body_key",
    "body_keys",
    "programs",
    "signature",
    "content_id",
    "seed",
    "expected_signature",
    "target_label",
)


class ExperimenterView:
    """What the experimenter may hold. No plaintext and no decryption key."""

    def __init__(self, commitment: str, handles: tuple[str, ...]) -> None:
        object.__setattr__(self, "commitment", commitment)
        object.__setattr__(self, "handles", handles)

    def __getattr__(self, name: str) -> Any:
        if name in {"plaintext", "body", "key", "seed", "ciphertext", "content_id"}:
            raise BlindnessBroken(name)
        raise AttributeError(name)


def assess_corpus(envelope: Mapping[str, Any] | None) -> dict[str, Any]:
    if envelope is None:
        return _stopped("no corpus supplied", structurally_complete=False, reasons=["missing corpus"])
    reasons: list[str] = []
    if envelope.get("source_class") != "A":
        reasons.append("source is not A")
    if envelope.get("manufactured_in_repository") is not False:
        reasons.append("corpus was manufactured for this repository")
    if envelope.get("locally_generated") or envelope.get("planner_generated"):
        reasons.append("local or planner corpus")
    if envelope.get("historical_bodies") or envelope.get("filtered_for_study") or envelope.get("target_directed"):
        reasons.append("filtered or historical corpus")
    for field in _REQUIRED:
        if field not in envelope:
            reasons.append(f"missing {field}")
    if "bank_hash" in envelope and envelope.get("bank_hash") != DISCOVERY_BANK_HASH:
        reasons.append("bank hash does not match the freeze")
    if "protocol_version" in envelope and envelope.get("protocol_version") != PROTOCOL_VERSION:
        reasons.append("protocol version does not match the freeze")
    if not isinstance(envelope.get("ciphertext", b""), (bytes, bytearray)) or "ciphertext" not in envelope:
        if "ciphertext" in envelope:
            reasons.append("ciphertext is not opaque bytes")
    for field in _BANNED_FIELDS:
        if field in envelope:
            reasons.append(f"experimenter-visible {field}")
    complete = not reasons
    reason = "structurally complete but measurement is not bound" if complete else "; ".join(reasons)
    return _stopped(reason, structurally_complete=complete, reasons=reasons)


def run_stage_f(envelope: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate a seal, then stop. This function does not call apply_micro."""
    if EXECUTION_ENABLED:
        raise RuntimeError("Stage F execution is not authorized in this tree")
    result = assess_corpus(envelope)
    result["discovery_performed"] = False
    result["apply_micro_calls"] = 0
    result["execution_enabled"] = False
    result["claim"] = None
    return result


def bind_measurement_environment() -> None:
    raise BlindnessBroken("no external measurement environment is available")


def _stopped(reason: str, *, structurally_complete: bool, reasons: list[str]) -> dict[str, Any]:
    return {
        "status": WAITING,
        "accepted_for_execution": False,
        "structurally_complete": structurally_complete,
        "reasons": reasons,
        "reason": reason,
        "discovery_performed": False,
        "apply_micro_calls": 0,
        "execution_enabled": False,
        "claim": None,
        "bank_hash": DISCOVERY_BANK_HASH,
        "protocol_version": PROTOCOL_VERSION,
    }
