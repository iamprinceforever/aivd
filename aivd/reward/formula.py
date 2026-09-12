"""Multi-term reward with novelty gated by security relevance."""
from __future__ import annotations

from aivd.core.config import RewardWeights
from aivd.core.types import FindingStatus, RewardBreakdown


def compute_reward(
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
    weights: RewardWeights | None = None,
) -> RewardBreakdown:
    w = weights or RewardWeights()
    if isinstance(status, str):
        status = FindingStatus(status)

    sec = float(max(0.0, min(1.0, security_relevance)))
    nov = float(max(0.0, novelty))
    # Gate: novelty without security relevance cannot dominate
    novelty_effective = nov * max(w.novelty_gate_eps, sec)

    confirmed_bonus = 1.0 if status == FindingStatus.CONFIRMED else 0.0

    total = (
        w.w_ig * information_gain
        + w.w_cov * delta_coverage
        + w.w_nov * novelty_effective
        + w.w_unc * delta_uncertainty
        + w.w_sec * sec
        + w.w_repro * repro_score
        + w.w_conf * confirmed_bonus
        - w.w_red * redundancy
        - w.w_low * low_info
        - w.w_inv * invalid
        - w.w_rep * repetition
    )

    return RewardBreakdown(
        information_gain=information_gain,
        delta_coverage=delta_coverage,
        novelty=nov,
        novelty_effective=novelty_effective,
        delta_uncertainty=delta_uncertainty,
        security_relevance=sec,
        repro_score=repro_score,
        confirmed_bonus=confirmed_bonus,
        redundancy=redundancy,
        low_info=low_info,
        invalid=invalid,
        repetition=repetition,
        total=float(total),
        weights=w.model_dump(),
    )
