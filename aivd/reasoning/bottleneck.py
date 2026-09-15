"""Information-bottleneck diagnostics (3.16).

Codes: SIGNAL / REPRESENTATION / HYPOTHESIS / ROUTING / GENERATION /
INVENTION / EXPERIMENT / INTERPRETATION / COMPOSITION / VERIFICATION /
BUDGET / UNKNOWN-LIMIT

FIRST INFORMATION BOTTLENECK (3.15→3.16 audit): EXPERIMENT under BUDGET
starvation — invent generates candidates but charge fails, tested=0.
Deeper structural limit: GENERATION lexicon (ACTION_STEMS×residual) —
synthetic competence, not open discovery.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class BottleneckCode(str, Enum):
    SIGNAL = "SIGNAL"
    REPRESENTATION = "REPRESENTATION"
    HYPOTHESIS = "HYPOTHESIS"
    ROUTING = "ROUTING"
    GENERATION = "GENERATION"
    INVENTION = "INVENTION"
    EXPERIMENT = "EXPERIMENT"
    INTERPRETATION = "INTERPRETATION"
    COMPOSITION = "COMPOSITION"
    VERIFICATION = "VERIFICATION"
    BUDGET = "BUDGET"
    UNKNOWN_LIMIT = "UNKNOWN-LIMIT"


# Frozen audit conclusion from Phase 1 (evidence in reports/aivd-3.16-audit.md)
FIRST_BOTTLENECK_AUDIT: dict[str, Any] = {
    "earliest_transition": "EXPERIMENT",
    "bottleneck_code": BottleneckCode.BUDGET.value,
    "evidence": [
        "Holdout-T sacred @32: ADD=4 invent, tested_candidates=0, gen=576, all 7 seeds",
        "charge_ok=0 charge_fail≥10 when autonomy entered with remaining_tests=5",
        "_invention_charge fails: _local_used ≥ invent_cap / gate_leave after outer stack",
        "Trajectory: ROUTE/CANDIDATE_GEN/INVENT/EXPERIMENT_PLAN/UPDATE loop without EXPERIMENT probes",
    ],
    "deeper_structural": {
        "code": BottleneckCode.GENERATION.value,
        "why": (
            "Candidate generation = ACTION_STEMS×residual_token compounds. "
            "Holdout-W (resolve/recover×latch) fits lexicon → DISCOVERED. "
            "Holdout-T (facet/beam/gleam-prism, skew/slant/veer-drift) outside lexicon "
            "→ unrepresentable without open morphology or observation-harvested stems."
        ),
    },
    "synthetic_vs_general": (
        "Benchmarks A–T recur as weak-signal→plant residual→char sides→combine→SECRET "
        "with closed-lexicon compounds. GENERAL discovery competence ≠ SYNTHETIC "
        "benchmark competence under this observation/generation model."
    ),
    "intervention_principle": (
        "Do not add scoring layers. Ensure experiments can run (epistemic budget), "
        "predict before probing, measure actual IG, detect dead-ends, distinguish "
        "activity depth from discovery depth."
    ),
}


def diagnose_bottleneck(
    *,
    generated: int = 0,
    tested: int = 0,
    charge_failures: int = 0,
    charge_ok: int = 0,
    unexplained_before: float = 1.0,
    unexplained_after: float = 1.0,
    n_hypotheses: int = 0,
    n_regions: int = 0,
    composition_tested: bool = False,
    secret_found: bool = False,
    representation_ok: bool = True,
    mean_ig_actual: float | None = None,
    first_broken: str | None = None,
) -> dict[str, Any]:
    """Heuristic diagnosis of the earliest useful-info failure."""
    codes: list[str] = []
    why: list[str] = []

    if generated > 0 and tested == 0 and charge_failures > 0:
        codes.append(BottleneckCode.BUDGET.value)
        codes.append(BottleneckCode.EXPERIMENT.value)
        why.append("candidates invented but zero probes executed (charge failures)")
    elif generated > 0 and tested == 0:
        codes.append(BottleneckCode.EXPERIMENT.value)
        why.append("invented without experimenting")

    if not representation_ok:
        codes.append(BottleneckCode.REPRESENTATION.value)
        why.append("state cannot distinguish competing hypotheses")

    if tested > 0 and (mean_ig_actual is not None and mean_ig_actual < 0.02):
        codes.append(BottleneckCode.INTERPRETATION.value)
        why.append("experiments ran but actual IG≈0")

    if tested > 4 and unexplained_after >= unexplained_before * 0.95:
        codes.append(BottleneckCode.GENERATION.value)
        why.append("activity without uncertainty decrease — search not informative")

    if composition_tested and not secret_found and first_broken in ("VERIFY", "COMPOSITION", None):
        codes.append(BottleneckCode.VERIFICATION.value)
        why.append("composition reached without verified discovery")

    if not codes and n_hypotheses == 0 and n_regions == 0:
        codes.append(BottleneckCode.SIGNAL.value)
        why.append("no regions/hypotheses formed")

    if not codes:
        codes.append(BottleneckCode.UNKNOWN_LIMIT.value)
        why.append("no clear early bottleneck from counters")

    # Earliest by pipeline order
    order = [
        BottleneckCode.SIGNAL.value,
        BottleneckCode.REPRESENTATION.value,
        BottleneckCode.HYPOTHESIS.value,
        BottleneckCode.ROUTING.value,
        BottleneckCode.GENERATION.value,
        BottleneckCode.INVENTION.value,
        BottleneckCode.BUDGET.value,
        BottleneckCode.EXPERIMENT.value,
        BottleneckCode.INTERPRETATION.value,
        BottleneckCode.COMPOSITION.value,
        BottleneckCode.VERIFICATION.value,
        BottleneckCode.UNKNOWN_LIMIT.value,
    ]
    earliest = next((c for c in order if c in codes), codes[0])
    return {
        "codes": codes,
        "earliest": earliest,
        "why": why,
        "first_broken_transition": first_broken,
    }


__all__ = ["BottleneckCode", "diagnose_bottleneck", "FIRST_BOTTLENECK_AUDIT"]
