"""Open-world diagnostics: representable/generatable/executable/informative.

Codes: REPRESENTATION_INSUFFICIENT, EXPERIMENT_STARVATION, SEARCH_DEAD_END,
REPRESENTABLE, GENERATABLE, EXECUTABLE, INFORMATIVE.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class OpenWorldCode(str, Enum):
    REPRESENTABLE = "REPRESENTABLE"
    GENERATABLE = "GENERATABLE"
    EXECUTABLE = "EXECUTABLE"
    INFORMATIVE = "INFORMATIVE"
    REPRESENTATION_INSUFFICIENT = "REPRESENTATION_INSUFFICIENT"
    EXPERIMENT_STARVATION = "EXPERIMENT_STARVATION"
    SEARCH_DEAD_END = "SEARCH_DEAD_END"


def diagnose_openworld(
    *,
    n_primitives: int = 0,
    generated: int = 0,
    tested: int = 0,
    mean_ig: float = 0.0,
    u_drop: float = 0.0,
    secret_found: bool = False,
    charge_fail: int = 0,
    representation_ok: bool = True,
) -> dict[str, Any]:
    codes: list[str] = []
    if n_primitives > 0:
        codes.append(OpenWorldCode.REPRESENTABLE.value)
    else:
        codes.append(OpenWorldCode.REPRESENTATION_INSUFFICIENT.value)
    if generated > 0:
        codes.append(OpenWorldCode.GENERATABLE.value)
    if tested > 0:
        codes.append(OpenWorldCode.EXECUTABLE.value)
    elif generated > 0:
        codes.append(OpenWorldCode.EXPERIMENT_STARVATION.value)
    if tested > 0 and (mean_ig > 0.01 or u_drop > 0.02 or secret_found):
        codes.append(OpenWorldCode.INFORMATIVE.value)
    if tested > 0 and mean_ig < 0.01 and u_drop < 0.02 and not secret_found:
        codes.append(OpenWorldCode.SEARCH_DEAD_END.value)
    if charge_fail > 0 and tested == 0:
        if OpenWorldCode.EXPERIMENT_STARVATION.value not in codes:
            codes.append(OpenWorldCode.EXPERIMENT_STARVATION.value)
    # Earliest broken transition among the 4
    order = [
        OpenWorldCode.REPRESENTABLE.value,
        OpenWorldCode.GENERATABLE.value,
        OpenWorldCode.EXECUTABLE.value,
        OpenWorldCode.INFORMATIVE.value,
    ]
    broken = None
    for step in order:
        if step not in codes:
            broken = step
            break
    return {
        "codes": codes,
        "first_broken_capability": broken,
        "representation_ok": representation_ok and n_primitives > 0,
        "starvation": OpenWorldCode.EXPERIMENT_STARVATION.value in codes,
        "dead_end": OpenWorldCode.SEARCH_DEAD_END.value in codes,
    }


def success_levels(
    *,
    representable: bool,
    generatable: bool,
    executable: bool,
    informative: bool,
    hyp_discrimination: bool,
    security_relevant: bool,
    reproduced_verified: bool,
) -> dict[str, Any]:
    """Report EACH success level 1–7 separately (brief mandate)."""
    levels = {
        1: {"name": "represent_previously_unrepresentable", "pass": bool(representable)},
        2: {"name": "generate_experiment", "pass": bool(generatable)},
        3: {"name": "execute", "pass": bool(executable)},
        4: {"name": "informative_evidence", "pass": bool(informative)},
        5: {"name": "hypothesis_discrimination", "pass": bool(hyp_discrimination)},
        6: {"name": "security_relevant_discovery", "pass": bool(security_relevant)},
        7: {"name": "reproduce_causal_verify", "pass": bool(reproduced_verified)},
    }
    highest = 0
    for i in range(1, 8):
        if levels[i]["pass"]:
            highest = i
        else:
            break
    return {"levels": levels, "highest_contiguous": highest}


__all__ = ["OpenWorldCode", "diagnose_openworld", "success_levels"]
