"""Behavioral region clustering."""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans


def fit_regions(embeddings: np.ndarray, n_clusters: int = 8, seed: int = 42) -> KMeans | None:
    if embeddings.size == 0 or len(embeddings) < 2:
        return None
    # Cap k by unique rows to avoid ConvergenceWarning on duplicates
    uniq = np.unique(np.round(embeddings, 6), axis=0)
    k = min(n_clusters, len(embeddings), len(uniq))
    if k < 2:
        return None
    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    km.fit(embeddings)
    return km


def assign_region(model: KMeans | None, vec: np.ndarray) -> int:
    if model is None:
        return 0
    return int(model.predict(vec.reshape(1, -1))[0])


def unique_region_count(model: KMeans | None, embeddings: np.ndarray) -> int:
    if embeddings.size == 0:
        return 0
    if model is None:
        return min(1, len(embeddings))
    labels = model.predict(embeddings)
    return int(len(set(labels.tolist())))
