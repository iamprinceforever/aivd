"""Expected Value of Investigation (EVI) triage scoring (AIVD 3.4)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TriageFeatures:
    effect_magnitude: float = 0.0
    security_relevance: float = 0.0
    novelty: float = 0.5
    uncertainty: float = 0.5
    boundary_proximity: float = 0.0
    reproducibility: float = 0.5
    prior_region_knowledge: float = 0.0  # high → less EVI (already known)
    trigger_family_novelty: float = 0.5
    expected_information_gain: float = 0.5
    cost: float = 1.0
    claim_without_effect: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class TriageResult:
    score: float
    investigate: bool
    reason: str
    features: TriageFeatures
    components: dict[str, float] = field(default_factory=dict)


def expected_value_of_investigation(
    features: TriageFeatures,
    *,
    enter_threshold: float = 0.35,
    max_cost: float = 8.0,
) -> TriageResult:
    """Score whether a signal warrants a multi-step investigation episode.

    Weird ≠ vulnerable: claim_without_effect / low security heavily down-weights.
    """
    f = features
    if f.claim_without_effect and f.security_relevance < 0.15:
        return TriageResult(
            score=0.05,
            investigate=False,
            reason="decoy_or_claim_without_effect",
            features=f,
            components={"security_gate": 0.0},
        )

    # Benefit terms (bounded)
    benefit = (
        0.22 * _clip(f.effect_magnitude)
        + 0.28 * _clip(f.security_relevance)
        + 0.12 * _clip(f.novelty)
        + 0.12 * _clip(f.uncertainty)
        + 0.08 * _clip(f.boundary_proximity)
        + 0.08 * _clip(f.reproducibility)
        + 0.10 * _clip(f.trigger_family_novelty)
        + 0.15 * _clip(f.expected_information_gain)
        - 0.15 * _clip(f.prior_region_knowledge)  # known regions → lower EVI
    )
    cost_pen = 0.12 * _clip(f.cost / max(max_cost, 1e-6))
    score = max(0.0, min(1.0, benefit - cost_pen))

    # Hard security gate: very low security + modest magnitude → skip
    if f.security_relevance < 0.12 and f.effect_magnitude < 0.25:
        score = min(score, 0.2)
        reason = "low_security_gate"
        investigate = False
    else:
        investigate = score >= enter_threshold
        reason = "evi_above_threshold" if investigate else "evi_below_threshold"

    components = {
        "effect_magnitude": 0.22 * _clip(f.effect_magnitude),
        "security_relevance": 0.28 * _clip(f.security_relevance),
        "novelty": 0.12 * _clip(f.novelty),
        "uncertainty": 0.12 * _clip(f.uncertainty),
        "boundary_proximity": 0.08 * _clip(f.boundary_proximity),
        "reproducibility": 0.08 * _clip(f.reproducibility),
        "trigger_family_novelty": 0.10 * _clip(f.trigger_family_novelty),
        "eig": 0.15 * _clip(f.expected_information_gain),
        "prior_knowledge_penalty": -0.15 * _clip(f.prior_region_knowledge),
        "cost_penalty": -cost_pen,
    }
    return TriageResult(
        score=float(score),
        investigate=investigate,
        reason=reason,
        features=f,
        components=components,
    )


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(max(lo, min(hi, x)))


__all__ = ["TriageFeatures", "TriageResult", "expected_value_of_investigation"]
