"""PCA helpers for visualization only (not for discovery decisions)."""
from __future__ import annotations

from typing import Any

import numpy as np


def pca_2d(embeddings: np.ndarray, seed: int = 42) -> np.ndarray:
    """Project to 2D via SVD PCA. For plots only."""
    if embeddings.size == 0:
        return np.zeros((0, 2))
    x = np.asarray(embeddings, dtype=np.float64)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    x = x - x.mean(axis=0, keepdims=True)
    # skinny SVD
    try:
        _, _, vt = np.linalg.svd(x, full_matrices=False)
        comps = vt[:2].T
        return x @ comps
    except np.linalg.LinAlgError:
        return np.zeros((x.shape[0], 2))


def embedding_scatter_payload(embeddings: list[list[float]] | np.ndarray) -> dict[str, Any]:
    mat = np.asarray(embeddings, dtype=np.float64)
    pts = pca_2d(mat)
    return {"x": pts[:, 0].tolist(), "y": pts[:, 1].tolist(), "n": int(pts.shape[0])}
