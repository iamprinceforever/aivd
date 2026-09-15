"""Joint uncertainty U(A), U(B), U(A,B) — do not blindly equalize."""
from __future__ import annotations

from typing import Any


def component_uncertainty(
    *,
    n_probes: int = 0,
    n_variants: int = 0,
    effect_mean: float = 0.0,
    effect_var: float = 0.0,
    characterized: bool = False,
) -> float:
    """Standalone uncertainty in [0, 1]. High when underexplored."""
    if characterized and n_probes >= 2:
        base = 0.15
    elif n_probes >= 2:
        base = 0.35
    elif n_probes == 1:
        base = 0.55
    else:
        base = 0.95
    # Residual variance / weak effect keeps uncertainty up
    if effect_mean < 0.08 and n_probes > 0:
        base = min(1.0, base + 0.15)
    if effect_var > 0.05:
        base = min(1.0, base + 0.1)
    if n_variants <= 1 and n_probes > 0:
        base = min(1.0, base + 0.08)
    return float(max(0.0, min(1.0, base)))


def joint_uncertainty(
    u_a: float,
    u_b: float,
    *,
    linkage: float = 0.5,
    interaction_tested: bool = False,
    interaction_ready: bool = False,
) -> float:
    """U(A,B): joint uncertainty. High when both components matter but combo untested.

    Does NOT equalize: if one component is well-known and the other is not,
    joint uncertainty is dominated by the unknown plus linkage.
    """
    ua, ub = float(u_a), float(u_b)
    link = max(0.0, min(1.0, float(linkage)))
    if interaction_tested:
        return max(0.05, 0.25 * min(ua, ub))
    # Asymmetric: max dominates when linkage high; geometric when independent
    asym = link * max(ua, ub) + (1.0 - link) * (0.5 * (ua + ub))
    geo = (ua * ub) ** 0.5 if ua > 0 and ub > 0 else max(ua, ub)
    u = 0.55 * asym + 0.45 * geo
    if interaction_ready and not interaction_tested:
        # Ready but untested → joint EVI region (standalone may be low)
        u = max(u, 0.55 + 0.25 * link)
    return float(max(0.0, min(1.0, u)))


def joint_evi(
    u_a: float,
    u_b: float,
    u_ab: float,
    *,
    readiness: float = 0.0,
    reserved: bool = False,
    standalone_value_a: float = 0.0,
    standalone_value_b: float = 0.0,
) -> float:
    """Expected value of information for joint test.

    Standalone low + joint high → prioritize reserved combination slot.
    """
    stand = 0.5 * (float(standalone_value_a) + float(standalone_value_b))
    # Joint info gain when U(A,B) high relative to max(U(A),U(B)) after characterization
    gap = float(u_ab) - 0.4 * max(float(u_a), float(u_b))
    evi = max(0.0, gap) * (0.4 + 0.6 * float(readiness))
    if reserved:
        evi *= 1.15
    # Penalize if standalones already high (no joint mystery)
    if stand > 0.5:
        evi *= 0.5
    return float(max(0.0, min(1.5, evi)))


def summarize_uncertainties(hyp: dict[str, Any]) -> dict[str, float]:
    return {
        "U_A": float(hyp.get("u_a") or 0.0),
        "U_B": float(hyp.get("u_b") or 0.0),
        "U_AB": float(hyp.get("u_ab") or 0.0),
        "joint_evi": float(hyp.get("joint_evi") or 0.0),
        "linkage": float(hyp.get("linkage") or 0.0),
    }


__all__ = [
    "component_uncertainty",
    "joint_uncertainty",
    "joint_evi",
    "summarize_uncertainties",
]
