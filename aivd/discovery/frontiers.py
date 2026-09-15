"""Behavioral frontier detection and prioritization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aivd.discovery.cartography import BehavioralMapView, RegionStats


@dataclass
class Frontier:
    region_id: str
    score: float
    reason: str
    residual_uncertainty: float
    visit_count: int
    mean_security: float


def detect_frontiers(view: BehavioralMapView, *, min_score: float = 0.25, top_k: int = 8) -> list[Frontier]:
    out: list[Frontier] = []
    for rid, st in view.region_stats.items():
        score = float(st.frontier_score)
        if score < min_score and st.visit_count > 0:
            continue
        reason_parts = []
        if st.residual_uncertainty > 0.4:
            reason_parts.append("high_uncertainty")
        if st.explored_frac < 0.5:
            reason_parts.append("under_explored")
        if st.mean_novelty > 0.3:
            reason_parts.append("novelty")
        if st.mean_security > 0.1:
            reason_parts.append("security_density")
        if not reason_parts and st.visit_count == 0:
            reason_parts.append("unvisited")
            score = max(score, 0.3)
        out.append(Frontier(
            region_id=str(rid),
            score=score,
            reason="+".join(reason_parts) or "frontier",
            residual_uncertainty=st.residual_uncertainty,
            visit_count=st.visit_count,
            mean_security=st.mean_security,
        ))
    # Unvisited cluster slots
    seen = set(view.region_stats.keys())
    for i in range(view.n_clusters):
        if str(i) not in seen:
            out.append(Frontier(
                region_id=str(i), score=0.35, reason="unvisited",
                residual_uncertainty=1.0, visit_count=0, mean_security=0.0,
            ))
    out.sort(key=lambda f: f.score, reverse=True)
    return out[:top_k]


def prioritize_frontiers(
    frontiers: list[Frontier],
    *,
    prefer_security: bool = True,
    avoid_saturated: list[str] | None = None,
) -> list[Frontier]:
    avoid = set(avoid_saturated or [])
    ranked = [f for f in frontiers if f.region_id not in avoid]
    if prefer_security:
        ranked.sort(key=lambda f: (f.score + 0.2 * f.mean_security, f.residual_uncertainty), reverse=True)
    return ranked


def boundary_walk_candidates(seed_prompt: str, *, pads: list[int] | None = None) -> list[str]:
    """Generate length-cliff style probes for boundary frontiers."""
    pads = pads or [2, 4, 6, 8, 10, 12, 16]
    return [f"{seed_prompt} lencliff:{'y' * n}" for n in pads]
