"""Cross-signal scoring — multi-factor link score (not raw correlation alone)."""
from __future__ import annotations

from typing import Any
import math

from aivd.cross_signal.signals import ActionSignal, ResidualSignal


def temporal_association(
    residual: ResidualSignal,
    action: ActionSignal,
    *,
    co_occurrence: int = 0,
    lag_steps: int = 1,
) -> float:
    """Temporal assoc: residual evidence precedes / co-occurs with action probes."""
    base = 0.0
    if residual.n_observations > 0 and action.n_probes > 0:
        base = 0.25
    if co_occurrence > 0:
        base += min(0.5, 0.15 * co_occurrence)
    # Prefer residual-first (lag >= 0)
    if lag_steps >= 0:
        base += 0.15
    else:
        base += 0.05
    # Strength coupling
    base += 0.2 * min(1.0, residual.strength) * min(1.0, action.strength + 0.1)
    return float(max(0.0, min(1.0, base)))


def conditional_association(
    residual: ResidualSignal,
    action: ActionSignal,
    *,
    p_action_given_residual: float | None = None,
    baseline_action: float = 0.2,
) -> float:
    """P(action region useful | residual evidence) vs baseline."""
    if p_action_given_residual is None:
        # Heuristic from strengths / uncertainty reduction potential
        p = 0.2 + 0.5 * residual.strength * (1.0 - action.uncertainty * 0.5)
        p_action_given_residual = min(0.95, p)
    lift = float(p_action_given_residual) - float(baseline_action)
    return float(max(0.0, min(1.0, 0.5 + lift)))


def delta_similarity(
    residual: ResidualSignal,
    action: ActionSignal,
) -> float:
    """Feature-delta similarity between residual and action evidence vectors."""
    rf = residual.features or {}
    af = action.features or {}
    keys = set(rf) | set(af)
    if not keys:
        # fallback: strength proximity
        return float(max(0.0, 1.0 - abs(residual.strength - action.strength)))
    num = 0.0
    den = 0.0
    for k in keys:
        a = float(rf.get(k) or 0.0)
        b = float(af.get(k) or 0.0)
        num += a * b
        den += a * a + b * b
    if den <= 1e-9:
        return 0.0
    # cosine-like on nonneg features
    return float(max(0.0, min(1.0, num / (math.sqrt(den) + 1e-9))))


def information_gain_estimate(
    residual: ResidualSignal,
    action: ActionSignal,
    *,
    prior_uncertainty: float | None = None,
) -> float:
    """Expected information gain from co-exploring residual↔action."""
    u0 = prior_uncertainty if prior_uncertainty is not None else (
        0.5 * (residual.uncertainty + action.uncertainty)
    )
    # After joint observe, uncertainty drops with both evidence streams
    u1 = u0 * (1.0 - 0.25 * residual.strength) * (1.0 - 0.2 * min(1.0, action.n_probes / 3.0))
    ig = max(0.0, u0 - u1)
    return float(max(0.0, min(1.0, ig * 2.0)))


def uncertainty_reduction(
    before: float,
    after: float,
) -> float:
    return float(max(0.0, min(1.0, before - after)))


def reproducibility_score(
    *,
    n_replications: int = 0,
    n_success: int = 0,
) -> float:
    if n_replications <= 0:
        return 0.2  # unknown
    return float(max(0.0, min(1.0, n_success / max(1, n_replications))))


def cf_consistency_score(
    *,
    a_without_b_effect: float = 0.0,
    b_without_a_effect: float = 0.0,
    joint_effect: float = 0.0,
    distractor_effect: float = 0.0,
    order_reverse_effect: float = 0.0,
) -> float:
    """CF consistency: joint >> individuals; distractors low; order may vary."""
    score = 0.0
    if joint_effect > max(a_without_b_effect, b_without_a_effect) + 0.05:
        score += 0.35
    if a_without_b_effect < 0.15 and b_without_a_effect < 0.15:
        score += 0.25
    if distractor_effect < joint_effect * 0.5:
        score += 0.20
    # order reverse: mild credit either way (consistency of nonzero)
    if order_reverse_effect > 0.0 and joint_effect > 0.0:
        score += 0.20
    elif joint_effect > 0.0:
        score += 0.10
    return float(max(0.0, min(1.0, score)))


def cross_signal_evi(
    link_score: float,
    *,
    u_residual: float = 0.8,
    u_action: float = 0.8,
    uncertainty_reduction_val: float = 0.0,
    reserved: bool = False,
) -> float:
    """CrossSignalEVI for prioritization."""
    return float(
        0.40 * link_score
        + 0.25 * min(u_residual, u_action)
        + 0.20 * uncertainty_reduction_val
        + 0.15 * (1.0 if reserved else 0.3)
    )


def score_pair(
    residual: ResidualSignal,
    action: ActionSignal,
    *,
    co_occurrence: int = 0,
    lag_steps: int = 1,
    n_replications: int = 0,
    n_success: int = 0,
    cf: dict[str, float] | None = None,
    prior_uncertainty: float | None = None,
) -> dict[str, float]:
    """Compute full multi-factor score bundle for a residual↔action pair."""
    cf = cf or {}
    temporal = temporal_association(
        residual, action, co_occurrence=co_occurrence, lag_steps=lag_steps,
    )
    conditional = conditional_association(residual, action)
    delta = delta_similarity(residual, action)
    ig = information_gain_estimate(
        residual, action, prior_uncertainty=prior_uncertainty,
    )
    u_before = 0.5 * (residual.uncertainty + action.uncertainty)
    u_after = u_before * (1.0 - 0.3 * temporal)
    u_red = uncertainty_reduction(u_before, u_after)
    repro = reproducibility_score(n_replications=n_replications, n_success=n_success)
    cf_s = cf_consistency_score(
        a_without_b_effect=float(cf.get("a_without_b") or 0.0),
        b_without_a_effect=float(cf.get("b_without_a") or 0.0),
        joint_effect=float(cf.get("joint") or 0.0),
        distractor_effect=float(cf.get("distractor") or 0.0),
        order_reverse_effect=float(cf.get("order_reverse") or 0.0),
    )
    # causal support: mild from CF joint lift + temporal
    causal = float(min(1.0, 0.5 * cf_s + 0.5 * temporal))
    parts = [
        0.15 * temporal,
        0.18 * conditional,
        0.12 * delta,
        0.15 * ig,
        0.12 * u_red,
        0.12 * repro,
        0.10 * cf_s,
        0.06 * causal,
    ]
    link = float(sum(parts))
    evi = cross_signal_evi(
        link,
        u_residual=residual.uncertainty,
        u_action=action.uncertainty,
        uncertainty_reduction_val=u_red,
    )
    return {
        "temporal_assoc": temporal,
        "conditional_assoc": conditional,
        "delta_similarity": delta,
        "information_gain": ig,
        "uncertainty_reduction": u_red,
        "reproducibility": repro,
        "cf_consistency": cf_s,
        "causal_support": causal,
        "link_score": link,
        "cross_evi": evi,
    }


__all__ = [
    "temporal_association",
    "conditional_association",
    "delta_similarity",
    "information_gain_estimate",
    "uncertainty_reduction",
    "reproducibility_score",
    "cf_consistency_score",
    "cross_signal_evi",
    "score_pair",
]
