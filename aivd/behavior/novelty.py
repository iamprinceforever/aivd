"""Novelty as nearest-neighbor distance in embedding space.

Supports run-local archive novelty and global (persistent memory) novelty,
plus cheap multi-level scores: probe / strategy / region.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np


def nearest_neighbor_distance(vec: np.ndarray, archive: np.ndarray) -> float:
    if archive.size == 0 or archive.shape[0] == 0:
        return 1.0
    diffs = archive - vec.reshape(1, -1)
    dists = np.linalg.norm(diffs, axis=1)
    return float(np.min(dists))


def redundancy_score(vec: np.ndarray, archive: np.ndarray, threshold: float = 0.15) -> float:
    """High when very close to an existing point."""
    if archive.size == 0 or archive.shape[0] == 0:
        return 0.0
    d = nearest_neighbor_distance(vec, archive)
    if d >= threshold:
        return 0.0
    return float(max(0.0, 1.0 - d / threshold))


def _as_matrix(archive: np.ndarray | Sequence[Sequence[float]] | None) -> np.ndarray:
    if archive is None:
        return np.zeros((0, 1))
    arr = np.asarray(archive, dtype=np.float64)
    if arr.size == 0:
        return np.zeros((0, 1))
    if arr.ndim == 1:
        return arr.reshape(1, -1)
    return arr


def run_novelty(vec: np.ndarray, run_archive: np.ndarray | Sequence[Sequence[float]] | None) -> float:
    """Novelty vs in-run (ephemeral) behavioral archive."""
    return nearest_neighbor_distance(np.asarray(vec, dtype=np.float64), _as_matrix(run_archive))


def global_novelty(
    vec: np.ndarray,
    global_archive: np.ndarray | Sequence[Sequence[float]] | None,
) -> float:
    """Novelty vs persistent cross-run memory archive."""
    return nearest_neighbor_distance(np.asarray(vec, dtype=np.float64), _as_matrix(global_archive))


def multi_level_novelty(
    *,
    probe_vec: np.ndarray | Sequence[float],
    run_archive: np.ndarray | Sequence[Sequence[float]] | None = None,
    global_archive: np.ndarray | Sequence[Sequence[float]] | None = None,
    strategy_id: str = "",
    seen_strategies: set[str] | None = None,
    region_id: str = "",
    seen_regions: set[str] | None = None,
) -> dict[str, float]:
    """Cheap multi-level novelty: probe / strategy / region (+ run vs global)."""
    pv = np.asarray(probe_vec, dtype=np.float64)
    rn = run_novelty(pv, run_archive)
    gn = global_novelty(pv, global_archive)
    seen_s = seen_strategies or set()
    seen_r = seen_regions or set()
    strategy_nov = 1.0 if strategy_id and strategy_id not in seen_s else (0.3 if strategy_id else 0.5)
    region_nov = 1.0 if region_id and str(region_id) not in seen_r else (0.3 if region_id else 0.5)
    return {
        "run_novelty": float(rn),
        "global_novelty": float(gn),
        "probe_novelty": float(rn),
        "strategy_novelty": float(strategy_nov),
        "region_novelty": float(region_nov),
        # Blend used by reward / explorers when both available
        "novelty_blend": float(0.6 * rn + 0.4 * gn),
    }
