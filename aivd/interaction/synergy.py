"""Distinguish additive vs synergistic / conditional interaction effects.

Scientific requirement: combination creates NEW effect not explained by
independents — not merely “both cause effects”.
"""
from __future__ import annotations

from typing import Any

from aivd.interaction.representation import InteractionCandidate


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def expected_additive(individual_effects: list[float]) -> float:
    """Independent-effects baseline (noisy-OR / capped sum)."""
    if not individual_effects:
        return 0.0
    # Cap-sum additive model
    s = sum(max(0.0, float(e)) for e in individual_effects)
    # Soft saturation
    return _clip01(1.0 - (1.0 / (1.0 + s)))


def interaction_residual(
    combined: float,
    individual_effects: list[float],
) -> float:
    """Positive residual ⇒ combination exceeds additive expectation."""
    exp = expected_additive(individual_effects)
    return float(combined) - exp


def classify_synergy(
    cand: InteractionCandidate,
    *,
    residual_threshold: float = 0.18,
    security_threshold: float = 0.35,
    secret_hit: bool = False,
) -> dict[str, Any]:
    """Classify synergy type from observed individuals + combined."""
    inds = list(cand.observed_individual) or list(cand.predicted_individual)
    combined = float(cand.observed_combined)
    resid = interaction_residual(combined, inds)
    cand.interaction_residual = resid
    max_ind = max(inds) if inds else 0.0
    sum_ind = sum(max(0.0, e) for e in inds)

    # Default
    kind = "unknown"
    is_sec = False
    note = ""

    if secret_hit and max_ind < 0.95:
        # Secret only in combination strongly suggests synergistic / gated
        if max_ind < security_threshold:
            kind = "synergistic"
            if cand.order in ("ordered", "sequential") or cand.timing in ("sequential", "after_residual"):
                kind = "ordered" if cand.order != "unordered" else "state_gated"
            is_sec = True
            note = "secret_in_combination_not_individuals"
        else:
            kind = "synergistic"
            is_sec = True
            note = "secret_with_partial_individual"
    elif resid >= residual_threshold and combined >= security_threshold:
        if cand.order in ("ordered", "sequential"):
            kind = "ordered"
        elif cand.state:
            kind = "state_gated"
        elif cand.composition == "contextual" or cand.context:
            kind = "contextual"
        else:
            kind = "synergistic"
        is_sec = combined >= security_threshold and resid >= residual_threshold
        note = "positive_interaction_residual"
    elif abs(resid) < residual_threshold and sum_ind > 0.05:
        # Fully explained by independents → ADDITIVE (must NOT claim security interaction)
        kind = "additive"
        is_sec = False
        note = "explained_by_independents"
    elif combined < 0.1 and max_ind < 0.1:
        kind = "none"
        is_sec = False
        note = "no_effect"
    elif combined >= security_threshold and max_ind >= security_threshold * 0.9:
        # One component already sufficient — not an interaction discovery
        kind = "additive"
        is_sec = False
        note = "dominated_by_single_component"
    else:
        kind = "unknown"
        is_sec = False
        note = "inconclusive"

    # Conditional: one weak, one null, combo strong
    if kind in ("synergistic", "unknown") and len(inds) >= 2:
        if min(inds) < 0.1 and max_ind < security_threshold and combined >= security_threshold:
            kind = "conditional"
            is_sec = True
            note = "conditional_on_combination"

    cand.synergy_type = kind
    cand.is_security_interaction = bool(is_sec and kind not in ("additive", "none"))
    cand.classified = True
    return {
        "synergy_type": kind,
        "is_security_interaction": cand.is_security_interaction,
        "interaction_residual": resid,
        "expected_additive": expected_additive(inds),
        "observed_combined": combined,
        "observed_individual": inds,
        "note": note,
    }
