"""Multi-term reward with novelty gated by security relevance."""
from __future__ import annotations

from aivd.core.config import RewardWeights
from aivd.core.types import FindingStatus, RewardBreakdown


def estimate_normalized_cost(
    prompt: str = "",
    response: str = "",
    *,
    tokens_estimate: float | None = None,
    ref_tokens: float = 4000.0,
) -> float:
    """Normalize estimated token/compute cost to [0, 1].

    Uses ``tokens_estimate`` when provided; otherwise a char/4 heuristic.
    """
    if tokens_estimate is not None:
        tokens = float(tokens_estimate)
    else:
        tokens = (len(prompt or "") + len(response or "")) / 4.0
    if ref_tokens <= 0:
        return 0.0
    return float(max(0.0, min(1.0, tokens / ref_tokens)))


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
    normalized_cost: float = 0.0,
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
    cost = float(max(0.0, min(1.0, normalized_cost)))

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
        - w.w_cost * cost
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
        normalized_cost=cost,
        total=float(total),
        weights=w.model_dump(),
    )
