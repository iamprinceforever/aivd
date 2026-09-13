"""Behavior map: archive of embeddings + coverage / novelty / density / trajectories."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from aivd.behavior.clustering import assign_region, fit_regions, unique_region_count
from aivd.behavior.novelty import nearest_neighbor_distance, redundancy_score
from aivd.behavior.state import BehavioralState
from aivd.behavior.uncertainty import cluster_entropy


@dataclass
class BehaviorMap:
    """Behavioral archive. ``add()`` return dict keys stay Controller-compatible."""

    encoder: Any  # BehaviorEncoder | TorchBehaviorEncoder | LearnedBehaviorEncoder
    n_clusters: int = 8
    estimated_reachable: int = 12
    seed: int = 42
    embeddings: list[np.ndarray] = field(default_factory=list)
    labels: list[int] = field(default_factory=list)
    trajectories: list[list[int]] = field(default_factory=list)
    _current_traj: list[int] = field(default_factory=list)
    _region_visits: dict[int, int] = field(default_factory=dict)
    _model: object | None = None

    def archive_matrix(self) -> np.ndarray:
        if not self.embeddings:
            return np.zeros((0, self.encoder.dim))
        return np.vstack(self.embeddings)

    def local_density(self, vec: np.ndarray, k: int = 5) -> float:
        """Fraction of archive within median NN distance scale (0..1-ish)."""
        mat = self.archive_matrix()
        if mat.size == 0 or mat.shape[0] == 0:
            return 0.0
        diffs = mat - vec.reshape(1, -1)
        dists = np.linalg.norm(diffs, axis=1)
        kk = min(k, len(dists))
        near = np.partition(dists, kk - 1)[:kk]
        # high density when neighbors are close
        mean_d = float(np.mean(near))
        return float(1.0 / (1.0 + mean_d))

    def unexplored_regions(self) -> list[int]:
        """Region ids with zero or below-median visits (heuristic)."""
        if self._model is None:
            return list(range(self.n_clusters))
        n_fit = int(getattr(self._model, "n_clusters", self.n_clusters))
        visits = [self._region_visits.get(i, 0) for i in range(n_fit)]
        if not visits:
            return list(range(n_fit))
        med = float(np.median(visits))
        return [i for i, v in enumerate(visits) if v <= med]

    def unexplored_hint_vector(self, dim: int = 8) -> list[float]:
        """Soft hint: under-visited region one-hot / counts normalized (fixed dim)."""
        under = self.unexplored_regions()
        out = [0.0] * dim
        for i, rid in enumerate(under[:dim]):
            out[i] = 1.0 / (1.0 + self._region_visits.get(rid, 0))
        return out

    def add(self, text: str) -> dict:
        vec = self.encoder.encode(text)
        novelty = nearest_neighbor_distance(vec, self.archive_matrix())
        red = redundancy_score(vec, self.archive_matrix())
        dens = self.local_density(vec)
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
        region = self.labels[-1] if self.labels else 0
        self._region_visits[region] = self._region_visits.get(region, 0) + 1
        self._current_traj.append(region)
        if len(self._current_traj) >= 32:
            self.trajectories.append(list(self._current_traj))
            self._current_traj = []
        entropy_after = cluster_entropy(self.labels, self.n_clusters)
        coverage = unique_region_count(self._model, mat) / max(1, self.estimated_reachable)
        return {
            "embedding": vec.tolist(),
            "novelty": novelty,
            "redundancy": red,
            "delta_uncertainty": max(0.0, entropy_before - entropy_after),
            "coverage": min(1.0, coverage),
            "region": region,
            # extended (optional consumers)
            "density": dens,
            "visit_count_region": self._region_visits.get(region, 0),
            "uncertainty": entropy_after,
            "unexplored_regions": self.unexplored_regions(),
            "trajectory_length": len(self._current_traj) + sum(len(t) for t in self.trajectories),
        }

    def coverage(self) -> float:
        mat = self.archive_matrix()
        return min(1.0, unique_region_count(self._model, mat) / max(1, self.estimated_reachable))

    def to_behavioral_state(
        self,
        beh: dict[str, Any],
        *,
        security_relevance: float = 0.0,
    ) -> BehavioralState:
        return BehavioralState.from_map_result(
            beh,
            security_relevance=security_relevance,
            density=float(beh.get("density") or 0.0),
            visit_count_region=int(beh.get("visit_count_region") or 0),
            uncertainty=float(beh.get("uncertainty") or 0.0),
            trajectory_length=int(beh.get("trajectory_length") or 0),
            unexplored_hint=self.unexplored_hint_vector(),
        )
