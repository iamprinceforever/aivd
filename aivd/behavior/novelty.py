"""Novelty as nearest-neighbor distance in embedding space."""
from __future__ import annotations

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
