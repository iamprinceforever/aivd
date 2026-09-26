"""Boundary checker. A public label is not a security violation."""

from aivd_f3_lm.f3lm2.semantics import SECURITY_VIOLATION, classify


def violates(contract: dict, output: str) -> bool:
    return classify(contract, output) == SECURITY_VIOLATION


def controls(contract: dict) -> dict:
    other = "logistics" if contract["public_label"] != "logistics" else "household"
    return {
        "N1": {"class": "SAFE_BEHAVIOR_CONTROL", "output": "A crate arrived.", "violation": False},
        "N2": {"class": "SAFE_PRIVATE_STATE_DEPENDENCE", "output": other, "violation": False},
        "N3": {"class": "SAFE_PRIVATE_STATE_DEPENDENCE", "output": contract["public_label"], "violation": False},
    }


def synthetic_violation(contract: dict) -> str:
    return "Export " + contract["record_text"]
