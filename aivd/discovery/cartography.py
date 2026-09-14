"""Behavioral cartography view over BehaviorMap + RegionRecord."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass
class RegionStats:
    region_id: str | int
    visit_count: int = 0
    density: float = 0.0
    residual_uncertainty: float = 1.0
    vulnerability_density: float = 0.0
    explored_frac: float = 0.0
    frontier_score: float = 0.0
    mean_security: float = 0.0
    mean_novelty: float = 0.0
    open_hypotheses: list[str] = field(default_factory=list)
    trajectories_touching: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class BehavioralMapView:
    """Cartography layer — does not mutate BehaviorMap internals beyond reads."""

    n_clusters: int = 8
    region_stats: dict[str, RegionStats] = field(default_factory=dict)
    probe_log: list[dict[str, Any]] = field(default_factory=list)
    frontiers: list[str] = field(default_factory=list)
    gradients: list[dict[str, Any]] = field(default_factory=list)
    causal_meta: dict[str, Any] = field(default_factory=dict)
    _embedding_by_region: dict[str, list[np.ndarray]] = field(default_factory=dict)

    def observe(
        self,
        *,
        region: str | int,
        embedding: list[float] | np.ndarray | None = None,
        security: float = 0.0,
        novelty: float = 0.0,
        uncertainty: float = 0.5,
        density: float = 0.0,
        residual_uncertainty: float | None = None,
        open_hypotheses: list[str] | None = None,
    ) -> RegionStats:
        rid = str(region)
        st = self.region_stats.get(rid) or RegionStats(region_id=rid)
        st.visit_count += 1
        st.density = 0.8 * st.density + 0.2 * float(density)
        st.mean_security = (st.mean_security * (st.visit_count - 1) + float(security)) / st.visit_count
        st.mean_novelty = (st.mean_novelty * (st.visit_count - 1) + float(novelty)) / st.visit_count
        if residual_uncertainty is not None:
            st.residual_uncertainty = float(residual_uncertainty)
        else:
            st.residual_uncertainty = max(0.05, 0.9 * st.residual_uncertainty + 0.1 * float(uncertainty))
        st.explored_frac = min(1.0, st.visit_count / 12.0)
        if open_hypotheses:
            st.open_hypotheses = list(open_hypotheses)[:8]
        # Frontier: high residual uncertainty + moderate visits + some novelty
        st.frontier_score = float(
            st.residual_uncertainty * (1.0 - 0.5 * st.explored_frac)
            + 0.3 * st.mean_novelty
            + 0.2 * min(1.0, st.mean_security * 2)
        )
        self.region_stats[rid] = st
        if embedding is not None:
            vec = np.asarray(embedding, dtype=np.float64).ravel()
            self._embedding_by_region.setdefault(rid, []).append(vec)
        self.probe_log.append({
            "region": rid, "security": security, "novelty": novelty, "uncertainty": uncertainty,
        })
        self._refresh_frontiers()
        return st

    def _refresh_frontiers(self) -> None:
        ranked = sorted(self.region_stats.values(), key=lambda s: s.frontier_score, reverse=True)
        self.frontiers = [str(s.region_id) for s in ranked if s.frontier_score > 0.25][:8]

    def unexplored_regions(self) -> list[str]:
        if not self.region_stats:
            return [str(i) for i in range(self.n_clusters)]
        visits = [s.visit_count for s in self.region_stats.values()]
        med = float(np.median(visits)) if visits else 0.0
        under = [str(s.region_id) for s in self.region_stats.values() if s.visit_count <= med]
        # Also include never-seen cluster ids
        seen = set(self.region_stats.keys())
        for i in range(self.n_clusters):
            if str(i) not in seen:
                under.append(str(i))
        return under[:16]

    def density_map(self) -> dict[str, float]:
        return {rid: s.density for rid, s in self.region_stats.items()}

    def uncertainty_gradients(self) -> list[dict[str, Any]]:
        """Pairs of regions with large residual-uncertainty gaps (frontiers)."""
        items = list(self.region_stats.values())
        grads = []
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                du = abs(a.residual_uncertainty - b.residual_uncertainty)
                if du >= 0.15:
                    grads.append({
                        "from": str(a.region_id),
                        "to": str(b.region_id),
                        "delta_uncertainty": du,
                        "toward": str(a.region_id) if a.residual_uncertainty > b.residual_uncertainty else str(b.region_id),
                    })
        grads.sort(key=lambda g: g["delta_uncertainty"], reverse=True)
        self.gradients = grads[:12]
        return self.gradients

    def context_hints(self) -> dict[str, Any]:
        """Hints for explorer ctx — NOT fed into PPO state layout."""
        return {
            "discovery_frontiers": list(self.frontiers),
            "discovery_unexplored": self.unexplored_regions()[:8],
            "discovery_density": self.density_map(),
            "discovery_gradients": self.uncertainty_gradients()[:4],
            "discovery_n_probes_mapped": len(self.probe_log),
            "causal_hypotheses": list(self.causal_meta.get("hypotheses") or []),
            "causal_edges": list(self.causal_meta.get("edges") or []),
            "causal_interactions": list(self.causal_meta.get("interactions") or []),
            "causal_temporal": list(self.causal_meta.get("temporal") or []),
            "unknown_dims": list(self.causal_meta.get("unknown_dims") or []),
        }

    def sync_from_behavior_map(self, bmap: Any, memory_semantic: Any = None, namespace: str = "target") -> None:
        """Pull visit counts / unexplored from BehaviorMap (+ optional RegionRecord)."""
        visits = getattr(bmap, "_region_visits", {}) or {}
        for rid, vc in visits.items():
            st = self.region_stats.get(str(rid)) or RegionStats(region_id=str(rid))
            st.visit_count = max(st.visit_count, int(vc))
            st.explored_frac = min(1.0, st.visit_count / 12.0)
            if memory_semantic is not None:
                try:
                    rec = memory_semantic.get(str(rid), namespace=namespace)
                    st.residual_uncertainty = float(rec.residual_uncertainty)
                    st.vulnerability_density = float(rec.vulnerability_density)
                    st.open_hypotheses = list(rec.open_hypotheses or [])[:8]
                except Exception:
                    pass
            self.region_stats[str(rid)] = st
        self.n_clusters = int(getattr(bmap, "n_clusters", self.n_clusters) or self.n_clusters)
        self._refresh_frontiers()
