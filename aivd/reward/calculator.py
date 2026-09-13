"""RewardCalculator: logs all components; optional WM information gain; hacking flags."""
from __future__ import annotations

from typing import Any, Optional

from aivd.core.config import RewardWeights
from aivd.core.types import FindingStatus, RewardBreakdown
from aivd.reward.formula import compute_reward


class RewardCalculator:
    """Extends compute_reward without breaking old weight names."""

    def __init__(self, weights: RewardWeights | None = None):
        self.weights = weights or RewardWeights()
        self.history: list[dict[str, Any]] = []

    def compute(
        self,
        *,
        information_gain: float,
        delta_coverage: float,
        novelty: float,
        delta_uncertainty: float,
        security_relevance: float,
        repro_score: float,
        status: FindingStatus | str,
        redundancy: float,
        low_info: float,
        invalid: float,
        repetition: float,
        normalized_cost: float = 0.0,
        impact: float = 0.0,
        coverage_gain: float | None = None,
        duplicate_behavior: float = 0.0,
        uncertainty_before: float | None = None,
        uncertainty_after: float | None = None,
        use_wm_ig: bool = False,
    ) -> RewardBreakdown:
        w = self.weights
        # Prefer world-model IG when available
        ig = float(information_gain)
        if use_wm_ig and uncertainty_before is not None and uncertainty_after is not None:
            ig = float(max(0.0, uncertainty_before - uncertainty_after))

        cov = float(coverage_gain) if coverage_gain is not None else float(delta_coverage)
        dup = float(duplicate_behavior) if duplicate_behavior > 0 else float(redundancy)

        breakdown = compute_reward(
            information_gain=ig,
            delta_coverage=cov,
            novelty=novelty,
            delta_uncertainty=delta_uncertainty,
            security_relevance=security_relevance,
            repro_score=repro_score,
            status=status,
            redundancy=dup,
            low_info=low_info,
            invalid=invalid,
            repetition=repetition,
            normalized_cost=normalized_cost,
            weights=w,
        )
        # Optional impact term only when w_impact > 0 (keeps v2 totals by default)
        impact_term = float(getattr(w, "w_impact", 0.0) or 0.0) * float(max(0.0, min(1.0, impact)))
        if impact_term:
            breakdown.total = float(breakdown.total + impact_term)
        breakdown.weights = {**breakdown.weights, "impact": impact}

        components = breakdown.model_dump()
        hack = self.detect_reward_hacking(
            reward_total=breakdown.total,
            information_gain=ig,
            security_relevance=float(security_relevance),
        )
        record = {
            "components": components,
            "impact": impact,
            "wm_ig": use_wm_ig,
            "reward_hacking_flag": hack,
        }
        self.history.append(record)
        breakdown.weights = {**breakdown.weights, "reward_hacking_flag": float(hack)}
        return breakdown

    @staticmethod
    def detect_reward_hacking(
        *,
        reward_total: float,
        information_gain: float,
        security_relevance: float,
        reward_threshold: float = 0.35,
        evidence_eps: float = 0.08,
        prev_reward: float | None = None,
    ) -> bool:
        """Flag when reward is high/rising but IG and security evidence stay flat."""
        evidence_flat = information_gain < evidence_eps and security_relevance < evidence_eps
        high = reward_total >= reward_threshold
        rising = prev_reward is not None and reward_total > prev_reward + 0.05
        return bool(evidence_flat and (high or rising))
