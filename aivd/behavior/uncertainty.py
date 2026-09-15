"""Simple uncertainty / entropy helpers over cluster assignments."""
from __future__ import annotations

import numpy as np


def cluster_entropy(labels: list[int], n_clusters: int) -> float:
    if not labels or n_clusters <= 0:
        return 0.0
    counts = np.bincount(np.array(labels, dtype=int), minlength=n_clusters).astype(float)
    p = counts / counts.sum()
    p = p[p > 0]
    return float(-(p * np.log(p + 1e-12)).sum() / (np.log(n_clusters) + 1e-12))


def uncertainty_reduction(before: float, after: float) -> float:
    return float(max(0.0, before - after))
