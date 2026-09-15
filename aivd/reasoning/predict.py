"""Predict before experiment — P(outcome|H) discrimination (3.16)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OutcomePrediction:
    intervention_key: str
    p_h1: float
    p_not_h1: float
    p_h2: float
    discrimination: float
    expected_ig: float
    why: str = ""
    hyp_ids: list[str] = field(default_factory=list)


def _effect_prior(inv_meta: dict[str, Any] | None, region_u: float) -> float:
    m = inv_meta or {}
    base = 0.15 + 0.35 * float(region_u)
    if m.get("info_acquisition"):
        base += 0.02  # slight nudge only — must not dominate lexicon compounds
    # residual overlap bonus (general): compounds covering residual evidence
    rov = float(m.get("residual_overlap") or 0.0)
    base += 0.12 * min(1.0, rov)
    return min(0.85, base)


def predict_outcomes(
    intervention: Any,
    *,
    hypotheses: list[dict[str, Any]] | None = None,
    uncertainties: dict[str, float] | None = None,
) -> OutcomePrediction:
    """Predict P(positive|H1), P(positive|¬H1), P(positive|H2) without GT."""
    hyps = list(hypotheses or [])
    unc = uncertainties or {}
    meta = getattr(intervention, "meta", None) or {}
    rid = meta.get("routed_region") or ""
    u = float(unc.get(rid, 0.6))
    key = "|".join(getattr(intervention, "sequence", None) or []) or getattr(intervention, "id", "") or "?"

    open_hyps = [h for h in hyps if h.get("state") in ("open", "active", None)]
    h1 = open_hyps[0] if open_hyps else {"prior": 0.4, "hyp_id": "implicit"}
    h2 = open_hyps[1] if len(open_hyps) > 1 else {"prior": 0.3, "hyp_id": "alt"}

    p_base = _effect_prior(meta, u)
    # Under H1 (region relevant): higher chance of security-shaped effect
    p_h1 = min(0.9, p_base + 0.25 * float(h1.get("prior") or 0.4))
    # Under ¬H1: closer to noise
    p_not = max(0.05, p_base * 0.35)
    # Under H2 (competing): intermediate / different region
    p_h2 = min(0.85, p_base + 0.15 * float(h2.get("prior") or 0.3))

    # Discrimination: total variation between H1 and ¬H1 (and H2)
    disc = abs(p_h1 - p_not) + 0.5 * abs(p_h1 - p_h2)
    # Expected IG proxy: discrimination × uncertainty
    eig = disc * (0.4 + 0.6 * u)

    why = (
        f"I predict before probing: P(+|H1)={p_h1:.2f} P(+|¬H1)={p_not:.2f} "
        f"P(+|H2)={p_h2:.2f} disc={disc:.2f} E[IG]={eig:.2f} region_u={u:.2f}"
    )
    return OutcomePrediction(
        intervention_key=str(key),
        p_h1=float(p_h1),
        p_not_h1=float(p_not),
        p_h2=float(p_h2),
        discrimination=float(disc),
        expected_ig=float(eig),
        why=why,
        hyp_ids=[str(h1.get("hyp_id")), str(h2.get("hyp_id"))],
    )


def choose_discriminating(
    candidates: list[Any],
    *,
    hypotheses: list[dict[str, Any]] | None = None,
    uncertainties: dict[str, float] | None = None,
    budget: int = 4,
    tested_keys: set[str] | None = None,
) -> list[tuple[Any, OutcomePrediction]]:
    """Select interventions that maximize discrimination / expected IG."""
    tested = tested_keys or set()
    scored: list[tuple[Any, OutcomePrediction]] = []
    for inv in candidates:
        key = "|".join(getattr(inv, "sequence", None) or []) or getattr(inv, "id", "")
        if key in tested:
            continue
        pred = predict_outcomes(inv, hypotheses=hypotheses, uncertainties=uncertainties)
        scored.append((inv, pred))
    scored.sort(key=lambda x: -(x[1].discrimination + x[1].expected_ig))
    return scored[: max(0, int(budget))]


__all__ = ["OutcomePrediction", "predict_outcomes", "choose_discriminating"]
