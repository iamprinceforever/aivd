"""Uncertainty helpers for interventions and families."""
from __future__ import annotations

import math
from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.family import FamilyBelief
from aivd.invention.intervention_space import Intervention


def family_uncertainty(belief: FamilyBelief | None) -> float:
    if belief is None:
        return 1.0
    return float(belief.uncertainty)


def entropy_of_means(archive: FamilyArchive) -> float:
    """Shannon entropy of normalized family mean effects (allocation signal)."""
    means = [max(1e-9, b.mean) for b in archive.beliefs.values()]
    if not means:
        return 0.0
    s = sum(means)
    probs = [m / s for m in means]
    h = -sum(p * math.log(p + 1e-12) for p in probs)
    # normalize by log(n)
    return float(h / max(1e-9, math.log(len(probs))))


def intervention_prior_uncertainty(inv: Intervention, archive: FamilyArchive) -> float:
    """High when family untested / high posterior variance."""
    fid = (inv.meta or {}).get("family_id")
    if not fid or fid not in archive.beliefs:
        return 1.0
    return family_uncertainty(archive.beliefs[fid])


def update_intervention_uncertainty(inv: Intervention, archive: FamilyArchive) -> float:
    u = intervention_prior_uncertainty(inv, archive)
    inv.uncertainty = u
    return u
