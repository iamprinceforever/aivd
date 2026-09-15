"""Family-level bandits: UCB1 and Thompson sampling."""
from __future__ import annotations

import math
import random
from typing import Iterable

from aivd.invention.archive import FamilyArchive
from aivd.invention.family import FamilyBelief


def thompson_sample(belief: FamilyBelief, rng: random.Random) -> float:
    """Draw from Beta(alpha, beta)."""
    # Box-Muller-free: use random.gammavariate for Beta
    a, b = max(1e-3, belief.alpha), max(1e-3, belief.beta)
    try:
        x = rng.gammavariate(a, 1.0)
        y = rng.gammavariate(b, 1.0)
        return x / (x + y)
    except Exception:
        return belief.mean


def ucb_score(belief: FamilyBelief, *, total_pulls: int, c: float = 1.25) -> float:
    """UCB1 score; untested families get +inf priority via large bonus."""
    if belief.n_tested <= 0:
        return 1e9
    bonus = c * math.sqrt(math.log(max(2, total_pulls)) / belief.n_tested)
    return belief.mean + bonus


def select_family_thompson(
    archive: FamilyArchive,
    candidate_fids: Iterable[str],
    *,
    seed: int = 0,
    allow_saturated: bool = False,
) -> str | None:
    rng = random.Random(int(seed) + 404)
    best_fid, best_v = None, -1.0
    for fid in candidate_fids:
        b = archive.beliefs.get(fid)
        if b is None:
            return fid
        if b.saturated and not allow_saturated and not b.revived:
            continue
        v = thompson_sample(b, rng)
        if v > best_v:
            best_v, best_fid = v, fid
    return best_fid


def select_family_ucb(
    archive: FamilyArchive,
    candidate_fids: Iterable[str],
    *,
    allow_saturated: bool = False,
    c: float = 1.25,
) -> str | None:
    total = sum(b.n_tested for b in archive.beliefs.values()) + 1
    best_fid, best_v = None, -1.0
    for fid in candidate_fids:
        b = archive.beliefs.get(fid)
        if b is None:
            return fid
        if b.saturated and not allow_saturated and not b.revived:
            continue
        v = ucb_score(b, total_pulls=total, c=c)
        if v > best_v:
            best_v, best_fid = v, fid
    return best_fid
