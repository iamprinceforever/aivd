"""Dynamic candidate value — multi-factor; no single score dominates.

Factors: EIG, security, uncertainty, residual linkage, family novelty /
underexploration, novelty (gated), history, cost, redundancy, exploration.
"""
from __future__ import annotations

from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.intervention_space import Intervention, extract_residual_tokens
from aivd.invention.priority_history import PriorityHistory
from aivd.invention.residual_salience import residual_salience
from aivd.invention.scoring import score_intervention
from aivd.invention.uncertainty import update_intervention_uncertainty


# Soft weights — intentionally balanced so no single term dominates
_DEFAULT_WEIGHTS = {
    "eig": 0.18,
    "security": 0.16,
    "uncertainty": 0.10,
    "residual_link": 0.12,
    "family_novelty": 0.10,
    "underexplored": 0.10,
    "novelty_gated": 0.06,
    "history": 0.08,
    "exploration": 0.08,
    "priority": 0.10,
    "cost": 0.12,
    "redundancy": 0.10,
    "counterfactual": 0.08,
    "salience": 0.10,
}


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def candidate_value_terms(
    inv: Intervention,
    archive: FamilyArchive,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    priority_history: PriorityHistory | None = None,
) -> dict[str, float]:
    """Compute individual value factors in ~[0, 1] (penalties positive magnitudes)."""
    ctx = residual_context or {}
    seen = seen_sequences or set()
    update_intervention_uncertainty(inv, archive)
    # Base EIG/security via existing scorer (also stamps inv.eig/security/novelty)
    score_intervention(inv, residual_context=ctx, seen_sequences=seen)

    fid = (inv.meta or {}).get("family_id")
    belief = archive.beliefs.get(fid) if fid else None
    feats = (inv.meta or {}).get("family_features") or {}
    rtoks = set(extract_residual_tokens(ctx))
    seq_key = "|".join(inv.sequence)
    sal = residual_salience(ctx)

    eig = _clip01(float(inv.eig))
    security = _clip01(float(inv.security))
    uncertainty = _clip01(float(inv.uncertainty))

    # Graded residual linkage: primary residual token preferred (evidence order, not GT)
    rtoks_list = extract_residual_tokens(ctx)
    blob = " ".join(str(x).lower() for x in inv.sequence)
    residual_link = 0.0
    if rtoks_list:
        primary = rtoks_list[0]
        if primary and primary in blob:
            residual_link = 1.0
        elif any(rt in blob for rt in rtoks_list[1:]):
            residual_link = 0.55
        elif feats.get("residual_linked"):
            residual_link = 0.4
    elif feats.get("residual_linked"):
        residual_link = 0.7
    elif rtoks and any(rt in blob for rt in rtoks):
        residual_link = 0.7

    if belief is None or belief.n_tested == 0:
        family_novelty = 1.0
        underexplored = 1.0
    else:
        family_novelty = 1.0 / (1.0 + belief.n_tested)
        underexplored = _clip01(1.0 - (belief.n_tested / 8.0))

    # Novelty gated on IG / unexplained / salience
    unexplained = float(ctx.get("unexplained") or 0.0)
    ig_gate = eig > 0.05 or security > 0.05 or unexplained > 0.1 or sal["aggregate"] > 0.4
    raw_nov = _clip01(float(inv.novelty))
    if seq_key and seq_key not in seen:
        raw_nov = max(raw_nov, 0.5)
    novelty_gated = raw_nov if ig_gate else 0.0

    # History: prefer mild past success; penalize barren repeatedly-tested families
    history = 0.5
    if belief:
        if belief.n_success > 0:
            history = _clip01(0.5 + 0.4 * belief.mean)
        elif belief.n_tested >= 2:
            history = _clip01(0.5 - 0.15 * min(belief.n_tested, 6))
        if belief.revived:
            history = _clip01(history + 0.2)

    exploration = underexplored * uncertainty
    if belief and belief.saturated and not belief.revived:
        exploration *= 0.25

    priority = 0.5
    if priority_history is not None:
        if fid:
            priority = priority_history.get_priority(f"family:{fid}", default=0.5)
        priority = 0.5 * priority + 0.5 * priority_history.get_priority(
            f"cand:{inv.id}", default=priority
        )

    cost = _clip01(float(inv.cost) / 4.0)
    redundancy = 1.0 if seq_key in seen else 0.0

    counterfactual = 0.0
    if inv.strategy == "counterfactual":
        # Valuable when residual suggests competing hypotheses to discriminate
        n_sec = len(ctx.get("security_shaped_residuals") or [])
        counterfactual = 0.55 + (0.2 if n_sec >= 1 else 0.0) + (0.15 if unexplained > 0.5 else 0.0)
        counterfactual = _clip01(counterfactual)

    salience = _clip01(float(sal["aggregate"]) * (0.5 + 0.5 * residual_link))

    return {
        "eig": eig,
        "security": security,
        "uncertainty": uncertainty,
        "residual_link": residual_link,
        "family_novelty": family_novelty,
        "underexplored": underexplored,
        "novelty_gated": novelty_gated,
        "history": history,
        "exploration": exploration,
        "priority": _clip01(priority),
        "cost": cost,
        "redundancy": redundancy,
        "counterfactual": counterfactual,
        "salience": salience,
    }


def dynamic_candidate_value(
    inv: Intervention,
    archive: FamilyArchive,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    priority_history: PriorityHistory | None = None,
    weights: dict[str, float] | None = None,
    ablation: str | None = None,
) -> float:
    """Scalar multi-factor value. Ablation can zero named groups for A–I studies."""
    w = dict(_DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    # Ablation switches (static vs dynamic studies)
    abl = (ablation or "").lower().strip()
    if abl in ("no_eig",):
        w["eig"] = 0.0
    elif abl in ("no_security",):
        w["security"] = 0.0
    elif abl in ("no_uncertainty",):
        w["uncertainty"] = 0.0
    elif abl in ("no_residual",):
        w["residual_link"] = 0.0
        w["salience"] = 0.0
    elif abl in ("no_family",):
        w["family_novelty"] = 0.0
        w["underexplored"] = 0.0
    elif abl in ("no_novelty",):
        w["novelty_gated"] = 0.0
    elif abl in ("no_history",):
        w["history"] = 0.0
        w["priority"] = 0.0
    elif abl in ("no_exploration",):
        w["exploration"] = 0.0
    elif abl in ("static",):
        # Static = base eig/security/cost only (no adaptive terms)
        for k in list(w.keys()):
            if k not in ("eig", "security", "cost", "redundancy"):
                w[k] = 0.0

    terms = candidate_value_terms(
        inv, archive,
        residual_context=residual_context,
        seen_sequences=seen_sequences,
        priority_history=priority_history,
    )
    score = (
        w["eig"] * terms["eig"]
        + w["security"] * terms["security"]
        + w["uncertainty"] * terms["uncertainty"]
        + w["residual_link"] * terms["residual_link"]
        + w["family_novelty"] * terms["family_novelty"]
        + w["underexplored"] * terms["underexplored"]
        + w["novelty_gated"] * terms["novelty_gated"]
        + w["history"] * terms["history"]
        + w["exploration"] * terms["exploration"]
        + w["priority"] * terms["priority"]
        + w["counterfactual"] * terms["counterfactual"]
        + w["salience"] * terms["salience"]
        - w["cost"] * terms["cost"]
        - w["redundancy"] * terms["redundancy"]
    )
    # Soft saturate so no single runaway term dominates ranking scale
    inv.score = float(score)
    inv.meta = dict(inv.meta or {})
    inv.meta["value_terms"] = terms
    inv.meta["dynamic_value"] = inv.score
    inv.meta["ablation"] = abl or None
    return inv.score
