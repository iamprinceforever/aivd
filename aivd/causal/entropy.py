"""Behavioral / hypothesis / causal entropy; uncertainty reduction per cost."""
from __future__ import annotations

import math
from typing import Sequence

from aivd.causal.hypotheses import HypothesisSpace


def shannon(probs: Sequence[float]) -> float:
    s = sum(max(0.0, float(p)) for p in probs)
    if s <= 0:
        return 0.0
    ent = 0.0
    for p in probs:
        q = max(0.0, float(p)) / s
        if q > 0:
            ent -= q * math.log(q, 2)
    return float(ent)


def hypothesis_entropy(space: HypothesisSpace) -> float:
    return float(space.entropy())


def behavioral_entropy(region_visit_fracs: Sequence[float]) -> float:
    return shannon(region_visit_fracs)


def causal_entropy(edge_confidences: Sequence[float]) -> float:
    """Uncertainty over which edges are real causes (use complementary mass)."""
    if not edge_confidences:
        return 0.0
    # Treat each confidence as P(edge is causal); entropy of Bernoulli mix
    return float(sum(shannon([c, 1.0 - c]) for c in edge_confidences) / len(edge_confidences))


def uncertainty_reduction_per_cost(entropy_before: float, entropy_after: float, cost: float) -> float:
    return float(max(0.0, entropy_before - entropy_after) / max(0.25, float(cost)))
