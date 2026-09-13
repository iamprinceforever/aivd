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
    is_new_unique_vuln: bool = False,
    is_new_trigger_family: bool = False,
    same_vuln_same_trigger: bool = False,
    # Exploring same region on a *new* dimension must NOT be penalized as redundancy
    same_region_new_dimension: bool = False,
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

    unique_bonus = 1.0 if is_new_unique_vuln else 0.0
    family_bonus = 1.0 if is_new_trigger_family else 0.0
    # Redundancy for same vuln+same trigger; NOT for same-region new dimension
    same_vt_red = 0.0
    if same_vuln_same_trigger and not same_region_new_dimension:
        same_vt_red = 1.0
    # If exploring new dimension in same region, reduce generic redundancy penalty
    red = float(redundancy)
    if same_region_new_dimension:
        red = red * 0.25

    w_uv = float(getattr(w, "w_unique_vuln", 0.45) or 0.0)
    w_fam = float(getattr(w, "w_new_trigger_family", 0.25) or 0.0)
    w_svt = float(getattr(w, "w_same_vuln_trigger_redundancy", 0.35) or 0.0)

    total = (
        w.w_ig * information_gain
        + w.w_cov * delta_coverage
        + w.w_nov * novelty_effective
        + w.w_unc * delta_uncertainty
        + w.w_sec * sec
        + w.w_repro * repro_score
        + w.w_conf * confirmed_bonus
        + w_uv * unique_bonus
        + w_fam * family_bonus
        - w.w_red * red
        - w_svt * same_vt_red
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
        redundancy=red,
        low_info=low_info,
        invalid=invalid,
        repetition=repetition,
        normalized_cost=cost,
        unique_vuln_bonus=unique_bonus,
        new_trigger_family_bonus=family_bonus,
        same_vuln_trigger_redundancy=same_vt_red,
        total=float(total),
        weights=w.model_dump(),
    )
