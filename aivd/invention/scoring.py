"""Intervention scoring: EIG / discrimination / uncertainty / security − cost/redundancy.

Novelty alone is NOT rewarded.
"""
from __future__ import annotations

from typing import Any

from aivd.invention.intervention_space import Intervention


def score_intervention(
    inv: Intervention,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute scalar score. Novelty contributes only when eig/security > 0."""
    w = {
        "eig": 0.30,
        "disc": 0.20,
        "unc": 0.10,
        "sec": 0.35,
        "nov": 0.15,  # gated
        "cost": 0.25,
        "red": 0.20,
    }
    if weights:
        w.update(weights)
    ctx = residual_context or {}
    seen = seen_sequences or set()
    seq_key = "|".join(inv.sequence)

    # EIG proxy: residual unexplained + strategy that discriminates
    unexplained = float(ctx.get("unexplained") or 0.0)
    n_sec = len(ctx.get("security_shaped_residuals") or [])
    eig = float(inv.eig)
    if eig <= 0:
        eig = min(1.0, 0.25 * n_sec + 0.35 * unexplained + (0.2 if inv.strategy == "counterfactual" else 0.0))
    inv.eig = eig

    # Discrimination: counterfactual / composition preferred under multi-channel residual
    disc = 0.4 if inv.strategy == "counterfactual" else 0.2
    if inv.strategy == "composition":
        disc += 0.15
    if n_sec >= 1:
        disc += 0.2
    # Boost interventions that reuse residual-derived tokens (open invention, not GT)
    from aivd.invention.intervention_space import extract_residual_tokens
    rtoks = set(extract_residual_tokens(ctx))
    seq_l = [str(x).lower() for x in inv.sequence]
    if rtoks and any(any(rt in s for rt in rtoks) for s in seq_l):
        disc += 0.25
        eig = min(1.0, eig + 0.15)
        inv.eig = eig
    # Morph-of-ack/clear family under error residual → higher EIG prior
    err_blob = str(ctx.get("error") or ctx.get("error_text") or "").lower()
    if err_blob or any(str(c).startswith("error") for c in (ctx.get("security_shaped_residuals") or [])):
        if any(s.startswith("clear") or s.startswith("ack") or "ack-" in s or "clear-" in s for s in seq_l):
            eig = min(1.0, eig + 0.2)
            inv.eig = eig
            disc += 0.1

    unc = float(inv.uncertainty)
    sec = float(inv.security)
    if sec <= 0 and n_sec:
        sec = min(0.5, 0.15 * n_sec)
    inv.security = sec

    nov = float(inv.novelty)
    if seq_key and seq_key not in seen:
        nov = max(nov, 0.5)
    elif seq_key in seen:
        nov = min(nov, 0.1)
    inv.novelty = nov

    # Redundancy penalty
    red = 1.0 if seq_key in seen else 0.0
    cost = float(inv.cost) or 1.0

    # Novelty gated: only counts when eig or sec suggests info gain
    nov_term = nov if (eig > 0.05 or sec > 0.05 or unexplained > 0.1) else 0.0

    score = (
        w["eig"] * eig
        + w["disc"] * disc
        + w["unc"] * unc
        + w["sec"] * sec
        + w["nov"] * nov_term
        - w["cost"] * (cost / 4.0)
        - w["red"] * red
    )
    # Prefer hyphenated compounds (common intervention surface) over concat/underscore
    if any("-" in str(x) for x in inv.sequence):
        score += 0.08
    inv.score = float(score)
    return inv.score


def rank_candidates(
    cands: list[Intervention],
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    top_k: int = 16,
) -> list[Intervention]:
    scored = []
    for c in cands:
        score_intervention(c, residual_context=residual_context, seen_sequences=seen_sequences)
        scored.append(c)
    scored.sort(key=lambda x: (-x.score, x.cost, x.id))
    return scored[: max(1, int(top_k))]
