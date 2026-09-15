"""Multi-factor interaction scoring — not novelty-only, not Z-like boost."""
from __future__ import annotations

from typing import Any

from aivd.invention.intervention_space import extract_residual_tokens
from aivd.interaction.representation import InteractionCandidate


_WEIGHTS = {
    "eig": 0.16,
    "residual": 0.14,
    "novelty": 0.08,          # gated — must not dominate
    "uncertainty": 0.10,
    "causal_discrimination": 0.12,
    "security": 0.14,
    "underexploration": 0.10,
    "cost": 0.10,             # penalty
    "redundancy": 0.08,       # penalty
    "cross_family": 0.10,
    "prior_evidence": 0.08,
}


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def score_terms(
    cand: InteractionCandidate,
    *,
    residual_context: dict[str, Any] | None = None,
    tested_keys: set[str] | None = None,
    ablation: str | None = None,
) -> dict[str, float]:
    ctx = residual_context or {}
    rtoks = extract_residual_tokens(ctx)
    tested = tested_keys or set()
    inds = list(cand.predicted_individual) or [
        float(c.effect or c.security or 0.0) for c in cand.components
    ]
    max_ind = max(inds) if inds else 0.0
    # EIG: high when individuals weak/uncertain but combo could discriminate
    eig = _clip01(0.35 + 0.4 * (1.0 - max_ind) + 0.2 * float(cand.uncertainty))
    if cand.strategy in ("counterfactual", "sequential", "state_aware"):
        eig = _clip01(eig + 0.15)

    # Residual linkage of components
    blob = " ".join(
        " ".join(str(t) for t in c.sequence) for c in cand.components
    ).lower()
    residual = 0.0
    if rtoks:
        hits = sum(1 for rt in rtoks if rt and rt in blob)
        residual = _clip01(hits / max(1, min(2, len(rtoks))))
    elif ctx.get("unexplained") or ctx.get("security_shaped_residuals"):
        residual = 0.35

    # Cross-family novelty
    fams = set(cand.families or [])
    cross_family = 1.0 if len(fams) >= 2 else 0.25
    novelty = _clip01(0.3 + 0.4 * cross_family + (0.2 if cand.strategy == "novel_cross_family" else 0.0))

    uncertainty = _clip01(float(cand.uncertainty) if cand.uncertainty else 0.55)
    # Causal discrimination potential
    causal = 0.4
    if cand.order in ("ordered", "sequential"):
        causal += 0.25
    if cand.strategy == "counterfactual":
        causal += 0.2
    if cand.state:
        causal += 0.15
    causal = _clip01(causal)

    # Security relevance — from residual shape + mild individual hints, NOT vuln-named
    sec = 0.2
    if ctx.get("security_shaped_residuals"):
        sec += 0.35
    if residual >= 0.5:
        sec += 0.2
    # Mild individual effects can hint state gates without claiming vuln
    if 0.15 <= max_ind < 0.6:
        sec += 0.15
    sec = _clip01(sec)
    cand.security_relevance = sec

    # Underexploration of family pair
    pair_key = "|".join(sorted(cand.component_ids or []))
    under = 0.85 if pair_key not in tested else 0.15

    cost = _clip01((float(cand.cost) - 1.0) / 4.0)
    # Redundancy: same stem buckets
    stems = []
    for c in cand.components:
        feats = (c.meta or {}).get("family_features") or {}
        stems.append(str(feats.get("stem_bucket") or (c.sequence[0] if c.sequence else ""))[:8])
    redundancy = 0.7 if len(stems) >= 2 and stems[0] == stems[1] else 0.15

    prior = _clip01(0.2 + 0.3 * residual + (0.2 if cand.strategy == "residual_linked" else 0.0))

    terms = {
        "eig": eig,
        "residual": residual,
        "novelty": novelty,
        "uncertainty": uncertainty,
        "causal_discrimination": causal,
        "security": sec,
        "underexploration": under,
        "cost": cost,
        "redundancy": redundancy,
        "cross_family": cross_family,
        "prior_evidence": prior,
    }

    # Ablations
    if ablation == "no_eig":
        terms["eig"] = 0.0
    if ablation == "no_residual":
        terms["residual"] = 0.0
        terms["prior_evidence"] = min(terms["prior_evidence"], 0.1)
    if ablation == "no_causal":
        terms["causal_discrimination"] = 0.0
    if ablation == "no_security":
        terms["security"] = 0.0
    if ablation == "novelty_only":
        for k in list(terms):
            if k != "novelty":
                terms[k] = 0.0
        terms["novelty"] = novelty
    if ablation == "no_cross_family":
        terms["cross_family"] = 0.0
        terms["novelty"] = min(terms["novelty"], 0.3)

    cand.eig = eig
    cand.novelty = novelty
    cand.uncertainty = uncertainty
    return terms


def score_interaction(
    cand: InteractionCandidate,
    *,
    residual_context: dict[str, Any] | None = None,
    tested_keys: set[str] | None = None,
    ablation: str | None = None,
) -> float:
    terms = score_terms(
        cand, residual_context=residual_context,
        tested_keys=tested_keys, ablation=ablation,
    )
    w = dict(_WEIGHTS)
    if ablation == "novelty_only":
        score = terms.get("novelty", 0.0)
    else:
        pos = (
            w["eig"] * terms["eig"]
            + w["residual"] * terms["residual"]
            + w["novelty"] * terms["novelty"]
            + w["uncertainty"] * terms["uncertainty"]
            + w["causal_discrimination"] * terms["causal_discrimination"]
            + w["security"] * terms["security"]
            + w["underexploration"] * terms["underexploration"]
            + w["cross_family"] * terms["cross_family"]
            + w["prior_evidence"] * terms["prior_evidence"]
        )
        neg = w["cost"] * terms["cost"] + w["redundancy"] * terms["redundancy"]
        score = float(pos - neg)
    cand.score = score
    cand.meta["score_terms"] = terms
    return score


def rank_interactions(
    cands: list[InteractionCandidate],
    *,
    residual_context: dict[str, Any] | None = None,
    tested_keys: set[str] | None = None,
    ablation: str | None = None,
    top_k: int | None = None,
) -> list[InteractionCandidate]:
    for c in cands:
        score_interaction(
            c, residual_context=residual_context,
            tested_keys=tested_keys, ablation=ablation,
        )
    ranked = sorted(cands, key=lambda x: x.score, reverse=True)
    if top_k is not None:
        ranked = ranked[: max(0, int(top_k))]
    return ranked
