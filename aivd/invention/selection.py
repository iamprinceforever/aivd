"""Diversity-aware candidate selection.

Score = EIG + security relevance + uncertainty↓ + behavioral novelty
      + family novelty/coverage/uncertainty + cost/redundancy/failure/exploration
Novelty alone is NOT rewarded.
"""
from __future__ import annotations

from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.diversity import diversity_terms
from aivd.invention.family import assign_family, cluster_interventions
from aivd.invention.intervention_space import Intervention, extract_residual_tokens
from aivd.invention.scoring import score_intervention
from aivd.invention.scheduler import FamilyScheduler
from aivd.invention.uncertainty import update_intervention_uncertainty


def diversity_score(
    inv: Intervention,
    archive: FamilyArchive,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    weights: dict[str, float] | None = None,
) -> float:
    """Combine base 3.9 score with family diversity terms (gated novelty)."""
    w = {
        "base": 1.0,
        "fam_nov": 0.18,
        "fam_cov": 0.22,
        "fam_unc": 0.15,
        "beh_nov": 0.10,
        "sat": 0.35,
        "rev": 0.12,
        "hist_fail": 0.15,
        "res_link": 0.20,
    }
    if weights:
        w.update(weights)

    base = score_intervention(
        inv, residual_context=residual_context, seen_sequences=seen_sequences
    )
    terms = diversity_terms(inv, archive, seen_sequences=seen_sequences)
    # Gate family novelty: only counts with base IG/security signal OR unexplained residual
    ctx = residual_context or {}
    unexplained = float(ctx.get("unexplained") or 0.0)
    ig_gate = (inv.eig > 0.05 or inv.security > 0.05 or unexplained > 0.1)
    fam_nov = terms["family_novelty"] if ig_gate else 0.0
    beh_nov = terms["behavioral_novelty"] if ig_gate else 0.0

    fid = (inv.meta or {}).get("family_id")
    belief = archive.beliefs.get(fid) if fid else None
    hist_fail = 0.0
    if belief and belief.n_tested >= 2 and belief.n_success == 0:
        hist_fail = min(1.0, belief.n_tested / 6.0)

    score = (
        w["base"] * base
        + w["fam_nov"] * fam_nov
        + w["fam_cov"] * terms["family_coverage"]
        + w["fam_unc"] * terms["family_uncertainty"]
        + w["beh_nov"] * beh_nov
        + w["rev"] * terms["revival_bonus"]
        + w["res_link"] * terms.get("residual_linked", 0.0) * (1.0 if ig_gate else 0.0)
        - w["sat"] * terms["saturated_penalty"]
        - w["hist_fail"] * hist_fail
    )
    inv.score = float(score)
    inv.meta = dict(inv.meta or {})
    inv.meta["diversity_terms"] = terms
    inv.meta["diversity_score"] = inv.score
    return inv.score


def rank_with_diversity(
    cands: list[Intervention],
    archive: FamilyArchive,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    top_k: int = 16,
) -> list[Intervention]:
    for c in cands:
        update_intervention_uncertainty(c, archive)
        diversity_score(
            c, archive,
            residual_context=residual_context,
            seen_sequences=seen_sequences,
        )
    ranked = sorted(cands, key=lambda x: (-x.score, x.cost, x.id))
    return ranked[: max(1, int(top_k))]


def select_diverse_batch(
    cands: list[Intervention],
    archive: FamilyArchive,
    scheduler: FamilyScheduler,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    batch_size: int = 8,
    exploit_fraction: float = 0.15,
) -> list[Intervention]:
    """Hybrid selection: high-EIG exploit slots + family-scheduled exploration.

    Novelty alone is not rewarded; exploit uses gated diversity_score (EIG/sec base).
    """
    ctx = residual_context or {}
    rtoks = extract_residual_tokens(ctx)
    clusters = cluster_interventions(cands, residual_tokens=rtoks, coarse=True)
    for fid, members in clusters.items():
        feats = (members[0].meta or {}).get("family_features") or {}
        archive.ensure(fid, features=feats)

    scheduler.maybe_revive(rtoks)

    selected: list[Intervention] = []
    selected_ids: set[str] = set()
    remaining = dict(clusters)
    bs = max(1, int(batch_size))
    n_exploit = max(1, int(round(bs * float(exploit_fraction))))

    # --- Exploit: top diversity_score, at most one per family (preserve EIG without collapse) ---
    exploit_ranked = rank_with_diversity(
        cands, archive,
        residual_context=ctx,
        seen_sequences=seen_sequences,
        top_k=min(len(cands), max(n_exploit * 4, 16)),
    )
    exploit_fams: set[str] = set()
    for m in exploit_ranked:
        if len(selected) >= n_exploit:
            break
        if m.id in selected_ids:
            continue
        fid = (m.meta or {}).get("family_id") or ""
        if fid and fid in exploit_fams:
            continue
        selected.append(m)
        selected_ids.add(m.id)
        if fid:
            exploit_fams.add(fid)
        if fid and fid in remaining:
            remaining[fid] = [x for x in remaining[fid] if x.id != m.id]
            if not remaining[fid]:
                remaining.pop(fid, None)

    # --- Explore: family scheduler across under-covered families ---
    while len(selected) < bs and remaining:
        fid = scheduler.allocate_next(list(remaining.keys()))
        if fid is None or fid not in remaining:
            break
        members = [m for m in remaining[fid] if m.id not in selected_ids]
        if not members:
            remaining.pop(fid, None)
            continue
        ranked = rank_with_diversity(
            members, archive,
            residual_context=ctx,
            seen_sequences=seen_sequences,
            top_k=len(members),
        )
        pick = ranked[0]
        selected.append(pick)
        selected_ids.add(pick.id)
        remaining[fid] = [m for m in members if m.id != pick.id]
        if not remaining[fid]:
            remaining.pop(fid, None)

    if len(selected) < bs:
        leftovers = [c for c in cands if c.id not in selected_ids]
        for m in rank_with_diversity(
            leftovers, archive,
            residual_context=ctx,
            seen_sequences=seen_sequences,
            top_k=bs - len(selected),
        ):
            selected.append(m)
            selected_ids.add(m.id)

    return selected[:bs]
