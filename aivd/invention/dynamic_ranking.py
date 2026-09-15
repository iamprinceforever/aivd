"""Dynamic ranking — recalculate residual salience + family/candidate value → REORDER."""
from __future__ import annotations

from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.candidate_value import dynamic_candidate_value, candidate_value_terms
from aivd.invention.intervention_space import Intervention
from aivd.invention.priority_history import PriorityHistory
from aivd.invention.residual_salience import residual_salience, salience_linked_stems


def rank_dynamically(
    cands: list[Intervention],
    archive: FamilyArchive,
    *,
    residual_context: dict[str, Any] | None = None,
    seen_sequences: set[str] | None = None,
    priority_history: PriorityHistory | None = None,
    top_k: int | None = None,
    ablation: str | None = None,
    weights: dict[str, float] | None = None,
) -> list[Intervention]:
    """Score and sort candidates by dynamic multi-factor value."""
    for c in cands:
        dynamic_candidate_value(
            c, archive,
            residual_context=residual_context,
            seen_sequences=seen_sequences,
            priority_history=priority_history,
            weights=weights,
            ablation=ablation,
        )
    def _surface_rank(inv: Intervention) -> int:
        seq = inv.sequence or []
        if any("-" in str(t) for t in seq):
            return 0
        if any("_" in str(t) for t in seq):
            return 1
        return 2

    ranked = sorted(cands, key=lambda x: (-x.score, _surface_rank(x), x.cost, x.id))
    if top_k is not None:
        return ranked[: max(1, int(top_k))]
    return ranked


def family_values(
    archive: FamilyArchive,
    *,
    residual_context: dict[str, Any] | None = None,
    priority_history: PriorityHistory | None = None,
) -> dict[str, float]:
    """Family-level aggregate value for scheduler (mean belief + priority + salience link)."""
    ctx = residual_context or {}
    sal = residual_salience(ctx)
    stem_order = salience_linked_stems(ctx)
    stem_rank = {s: i for i, s in enumerate(stem_order)}
    out: dict[str, float] = {}
    for fid, b in archive.beliefs.items():
        feats = b.features or {}
        stem = str(feats.get("stem_bucket") or "")
        pri = 0.5
        if priority_history is not None:
            pri = priority_history.get_priority(f"family:{fid}", default=0.5)
        underex = 1.0 if b.n_tested == 0 else 1.0 / (1.0 + b.n_tested)
        res_link = 1.0 if feats.get("residual_linked") else 0.0
        # GENERAL stem ordering from evidence rank (not hard-coded Holdout stems)
        stem_bonus = 0.0
        if stem in stem_rank and res_link:
            # earlier in salience-linked order → slight bonus; no named stem list
            stem_bonus = max(0.0, 0.25 * (1.0 - stem_rank[stem] / max(1, len(stem_order))))
        sat_pen = 0.35 if (b.saturated and not b.revived) else 0.0
        rev_bon = 0.2 if b.revived else 0.0
        out[fid] = (
            0.30 * b.mean
            + 0.20 * b.uncertainty
            + 0.20 * underex
            + 0.15 * pri
            + 0.10 * res_link * sal["aggregate"]
            + stem_bonus
            + rev_bon
            - sat_pen
        )
    return out


def ranking_snapshot(
    ranked: list[Intervention],
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Compact ranking for search traces."""
    snap = []
    for i, c in enumerate(ranked[:limit]):
        snap.append({
            "rank": i,
            "id": c.id,
            "sequence": list(c.sequence),
            "score": c.score,
            "family_id": (c.meta or {}).get("family_id"),
            "strategy": c.strategy,
            "value_terms": (c.meta or {}).get("value_terms"),
        })
    return snap
