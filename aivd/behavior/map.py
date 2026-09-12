"""Behavior map: archive of embeddings + coverage / novelty queries."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from aivd.behavior.clustering import assign_region, fit_regions, unique_region_count
from aivd.behavior.encoder import BehaviorEncoder
from aivd.behavior.novelty import nearest_neighbor_distance, redundancy_score
from aivd.behavior.uncertainty import cluster_entropy


@dataclass
class BehaviorMap:
    encoder: BehaviorEncoder
    n_clusters: int = 8
    estimated_reachable: int = 12
    seed: int = 42
    embeddings: list[np.ndarray] = field(default_factory=list)
    labels: list[int] = field(default_factory=list)
    _model: object | None = None

    def archive_matrix(self) -> np.ndarray:
        if not self.embeddings:
            return np.zeros((0, self.encoder.dim))
        return np.vstack(self.embeddings)

    def add(self, text: str) -> dict:
        vec = self.encoder.encode(text)
        novelty = nearest_neighbor_distance(vec, self.archive_matrix())
        red = redundancy_score(vec, self.archive_matrix())
        entropy_before = cluster_entropy(self.labels, self.n_clusters)
        self.embeddings.append(vec)
        # refit periodically
        mat = self.archive_matrix()
        if len(self.embeddings) % 5 == 0 or self._model is None:
            self._model = fit_regions(mat, n_clusters=self.n_clusters, seed=self.seed)
            if self._model is not None:
                self.labels = [assign_region(self._model, e) for e in self.embeddings]
            else:
                self.labels = [0] * len(self.embeddings)
        else:
            self.labels.append(assign_region(self._model, vec))
        entropy_after = cluster_entropy(self.labels, self.n_clusters)
        coverage = unique_region_count(self._model, mat) / max(1, self.estimated_reachable)
        return {
            "embedding": vec.tolist(),
            "novelty": novelty,
            "redundancy": red,
            "delta_uncertainty": max(0.0, entropy_before - entropy_after),
            "coverage": min(1.0, coverage),
            "region": self.labels[-1] if self.labels else 0,
        }

    def coverage(self) -> float:
        mat = self.archive_matrix()
        return min(1.0, unique_region_count(self._model, mat) / max(1, self.estimated_reachable))
