"""Evidence update after each TEST observe — feeds adaptive reorder."""
from __future__ import annotations

from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.priority_history import PriorityHistory
from aivd.invention.residual_salience import residual_salience


def update_evidence(
    *,
    residual_context: dict[str, Any] | None,
    archive: FamilyArchive,
    priority_history: PriorityHistory,
    family_id: str,
    candidate_id: str,
    effect: float,
    success: bool,
    obs_meta: dict[str, Any] | None = None,
    features: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update archive, priority, and residual salience after one observation.

    Returns an evidence snapshot used for reorder / traces.
    """
    ctx = dict(residual_context or {})
    meta = dict(obs_meta or {})

    # Fold observation signals into residual context (open evidence, not GT)
    err = meta.get("error") or meta.get("error_text")
    if err and not ctx.get("error"):
        ctx["error"] = err
        ctx["error_text"] = str(err)
    if meta.get("security_shaped_residuals"):
        existing = list(ctx.get("security_shaped_residuals") or [])
        for ch in meta["security_shaped_residuals"]:
            if ch not in existing:
                existing.append(ch)
        ctx["security_shaped_residuals"] = existing

    # Archive family belief
    feats = dict(features or {})
    archive.record(
        family_id,
        effect=float(effect),
        success=bool(success),
        features=feats,
        evidence=str(ctx.get("error") or ""),
    )

    # Priority history for family and candidate
    fam_pri = priority_history.observe(
        f"family:{family_id}",
        effect=float(effect),
        success=bool(success),
        reason="test_observe",
    )
    cand_pri = priority_history.observe(
        f"cand:{candidate_id}",
        effect=float(effect),
        success=bool(success),
        reason="test_observe",
    )

    # Soft-decay other families (not blacklist)
    priority_history.decay_all_except(
        {f"family:{family_id}", f"cand:{candidate_id}"},
        reason="competing_decay",
    )

    # Revival on residual tokens overlapping saturated/decayed families
    from aivd.invention.intervention_space import extract_residual_tokens
    rtoks = extract_residual_tokens(ctx)
    key_feats = {
        f"family:{fid}": (b.features or {})
        for fid, b in archive.beliefs.items()
    }
    revived = priority_history.revive_matching(rtoks, key_feats)
    archive_revived = archive.revive_on_evidence(rtoks)

    sal = residual_salience(ctx)

    return {
        "residual_context": ctx,
        "salience": sal,
        "family_id": family_id,
        "candidate_id": candidate_id,
        "effect": float(effect),
        "success": bool(success),
        "family_priority": fam_pri,
        "candidate_priority": cand_pri,
        "revived_priorities": revived,
        "archive_revived": archive_revived,
        "family_belief": archive.beliefs[family_id].as_dict() if family_id in archive.beliefs else None,
    }
