"""Diversity metrics: family novelty, coverage, behavioral novelty (gated)."""
from __future__ import annotations

from typing import Any, Iterable

from aivd.invention.archive import FamilyArchive
from aivd.invention.family import FamilyBelief, extract_family_features
from aivd.invention.intervention_space import Intervention


def family_novelty(belief: FamilyBelief | None, archive: FamilyArchive) -> float:
    """1.0 if family never tested; decays with pulls. Not a sole reward."""
    if belief is None or belief.n_tested == 0:
        return 1.0
    return 1.0 / (1.0 + belief.n_tested)


def family_coverage_bonus(archive: FamilyArchive) -> float:
    """Encourage covering under-covered archive (1 - coverage)."""
    return max(0.0, 1.0 - archive.coverage())


def family_uncertainty_term(belief: FamilyBelief | None) -> float:
    if belief is None:
        return 1.0
    return float(belief.uncertainty)


def behavioral_novelty(inv: Intervention, seen_sequences: set[str] | None) -> float:
    key = "|".join(inv.sequence)
    if not seen_sequences:
        return 0.6
    if key in seen_sequences:
        return 0.0
    return 0.5


def diversity_terms(
    inv: Intervention,
    archive: FamilyArchive,
    *,
    seen_sequences: set[str] | None = None,
) -> dict[str, float]:
    fid = (inv.meta or {}).get("family_id")
    belief = archive.beliefs.get(fid) if fid else None
    feats = (inv.meta or {}).get("family_features") or {}
    residual_linked = bool(feats.get("residual_linked"))
    nov = family_novelty(belief, archive)
    # residual-linked untested families get coverage priority (structure↔evidence, not GT)
    cov = family_coverage_bonus(archive) if (belief is None or belief.n_tested == 0) else 0.15 * family_coverage_bonus(archive)
    if residual_linked and (belief is None or belief.n_tested == 0):
        cov = min(1.0, cov + 0.35)
        nov = min(1.0, nov + 0.2)
    return {
        "family_novelty": nov,
        "family_coverage": cov,
        "family_uncertainty": family_uncertainty_term(belief),
        "behavioral_novelty": behavioral_novelty(inv, seen_sequences),
        "saturated_penalty": 0.5 if (belief and belief.saturated and not belief.revived) else 0.0,
        "revival_bonus": 0.25 if (belief and belief.revived) else 0.0,
        "residual_linked": 1.0 if residual_linked else 0.0,
    }


def summarize_diversity(archive: FamilyArchive, tested: list[Intervention] | None = None) -> dict[str, Any]:
    surfaces: dict[str, int] = {}
    stems: dict[str, int] = {}
    for b in archive.beliefs.values():
        if b.n_tested <= 0:
            continue
        feats = b.features or {}
        surfaces[str(feats.get("surface"))] = surfaces.get(str(feats.get("surface")), 0) + 1
        stems[str(feats.get("stem_bucket"))] = stems.get(str(feats.get("stem_bucket")), 0) + 1
    return {
        "n_families": archive.n_families(),
        "unique_families_tested": archive.unique_tested(),
        "coverage": archive.coverage(),
        "surfaces_tested": surfaces,
        "stems_tested": stems,
        "n_saturated": len(archive.saturated_ids()),
        "n_tested_interventions": len(tested or []),
    }
