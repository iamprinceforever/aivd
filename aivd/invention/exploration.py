"""Exploration policies for family-level selection.

Implements / compares: epsilon-greedy, UCB, Thompson, entropy allocation,
novelty-weighted bandit, hierarchical family selection.
"""
from __future__ import annotations

import math
import random
from typing import Any, Iterable

from aivd.invention.archive import FamilyArchive
from aivd.invention.bandit import select_family_thompson, select_family_ucb


EXPLORATION_POLICIES = (
    "epsilon_greedy",
    "ucb",
    "thompson",
    "entropy",
    "novelty_bandit",
    "hierarchical",
)


def _unsaturated(archive: FamilyArchive, fids: list[str], allow_saturated: bool) -> list[str]:
    out = []
    for fid in fids:
        b = archive.beliefs.get(fid)
        if b is None:
            out.append(fid)
            continue
        if allow_saturated or not b.saturated or b.revived:
            out.append(fid)
    return out or list(fids)


def epsilon_greedy_family(
    archive: FamilyArchive,
    candidate_fids: list[str],
    *,
    seed: int = 0,
    epsilon: float = 0.2,
    allow_saturated: bool = False,
) -> str | None:
    rng = random.Random(int(seed) + 17)
    fids = _unsaturated(archive, candidate_fids, allow_saturated)
    if not fids:
        return None
    if rng.random() < epsilon:
        return rng.choice(fids)
    # exploit: highest mean; tie-break untested
    best, best_v = None, -1.0
    for fid in fids:
        b = archive.beliefs.get(fid)
        if b is None or b.n_tested == 0:
            return fid
        if b.mean > best_v:
            best_v, best = b.mean, fid
    return best or fids[0]


def entropy_allocation(
    archive: FamilyArchive,
    candidate_fids: list[str],
    *,
    seed: int = 0,
    allow_saturated: bool = False,
) -> str | None:
    """Prefer families that most reduce global mean-entropy / high uncertainty."""
    rng = random.Random(int(seed) + 29)
    fids = _unsaturated(archive, candidate_fids, allow_saturated)
    if not fids:
        return None
    weights = []
    for fid in fids:
        b = archive.beliefs.get(fid)
        if b is None or b.n_tested == 0:
            weights.append(2.0)
        else:
            weights.append(0.5 + b.uncertainty + (0.3 if b.revived else 0.0))
    total = sum(weights) or 1.0
    r = rng.random() * total
    acc = 0.0
    for fid, w in zip(fids, weights):
        acc += w
        if r <= acc:
            return fid
    return fids[-1]


def novelty_weighted_bandit(
    archive: FamilyArchive,
    candidate_fids: list[str],
    *,
    seed: int = 0,
    allow_saturated: bool = False,
) -> str | None:
    """Thompson sample with novelty weight for never-tested / low-coverage families."""
    rng = random.Random(int(seed) + 41)
    fids = _unsaturated(archive, candidate_fids, allow_saturated)
    if not fids:
        return None
    best, best_v = None, -1.0
    for fid in fids:
        b = archive.beliefs.get(fid)
        if b is None:
            return fid
        from aivd.invention.bandit import thompson_sample
        v = thompson_sample(b, rng)
        nov = 1.0 if b.n_tested == 0 else 1.0 / (1.0 + b.n_tested)
        # novelty alone not rewarded — weight only as exploration prior on sample
        score = v + 0.35 * nov * max(0.05, b.uncertainty)
        if score > best_v:
            best_v, best = score, fid
    return best


def hierarchical_family_select(
    archive: FamilyArchive,
    candidate_fids: list[str],
    *,
    seed: int = 0,
    allow_saturated: bool = False,
) -> str | None:
    """Two-level: pick surface class by UCB, then stem within class by Thompson."""
    fids = _unsaturated(archive, candidate_fids, allow_saturated)
    if not fids:
        return None
    # group by surface feature
    by_surface: dict[str, list[str]] = {}
    for fid in fids:
        b = archive.beliefs.get(fid)
        surf = (b.features or {}).get("surface", "unknown") if b else "unknown"
        by_surface.setdefault(str(surf), []).append(fid)
    # synthetic beliefs per surface
    surf_scores: dict[str, float] = {}
    total = sum(b.n_tested for b in archive.beliefs.values()) + 1
    for surf, members in by_surface.items():
        n = sum((archive.beliefs[m].n_tested if m in archive.beliefs else 0) for m in members)
        mean = 0.0
        if n:
            mean = sum(
                archive.beliefs[m].mean * max(1, archive.beliefs[m].n_tested)
                for m in members if m in archive.beliefs
            ) / max(1, n)
        bonus = 1.25 * math.sqrt(math.log(max(2, total)) / max(1, n)) if n else 1e6
        surf_scores[surf] = mean + bonus
    best_surf = max(surf_scores, key=surf_scores.get)
    return select_family_thompson(
        archive, by_surface[best_surf], seed=seed, allow_saturated=True
    )


def select_family(
    policy: str,
    archive: FamilyArchive,
    candidate_fids: list[str],
    *,
    seed: int = 0,
    allow_saturated: bool = False,
    epsilon: float = 0.2,
) -> str | None:
    """Dispatch exploration policy."""
    p = (policy or "thompson").lower().strip()
    if p in ("epsilon", "epsilon_greedy", "eps"):
        return epsilon_greedy_family(
            archive, candidate_fids, seed=seed, epsilon=epsilon,
            allow_saturated=allow_saturated,
        )
    if p == "ucb":
        return select_family_ucb(
            archive, candidate_fids, allow_saturated=allow_saturated
        )
    if p in ("thompson", "ts"):
        return select_family_thompson(
            archive, candidate_fids, seed=seed, allow_saturated=allow_saturated
        )
    if p in ("entropy", "entropy_allocation"):
        return entropy_allocation(
            archive, candidate_fids, seed=seed, allow_saturated=allow_saturated
        )
    if p in ("novelty", "novelty_bandit"):
        return novelty_weighted_bandit(
            archive, candidate_fids, seed=seed, allow_saturated=allow_saturated
        )
    if p in ("hierarchical", "hier"):
        return hierarchical_family_select(
            archive, candidate_fids, seed=seed, allow_saturated=allow_saturated
        )
    # default thompson
    return select_family_thompson(
        archive, candidate_fids, seed=seed, allow_saturated=allow_saturated
    )


def compare_policies_snapshot(
    archive: FamilyArchive,
    candidate_fids: list[str],
    *,
    seed: int = 0,
) -> dict[str, Any]:
    """Return which family each policy would pick (for ablation/audit)."""
    out: dict[str, Any] = {}
    for pol in EXPLORATION_POLICIES:
        out[pol] = select_family(pol, archive, candidate_fids, seed=seed)
    return out
