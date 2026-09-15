"""AutonomousDiscoveryState — unified closed-loop belief state (3.15).

Tracks signals, regions, uncertainties, hypotheses, cross-signal links,
invention history, readiness, reserve, EIG estimates, and security relevance.
No evaluator GT; no Holdout-named fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class BehavioralRegion:
    """Abstract behavioral region derived from evidence properties (not vocabulary)."""

    region_id: str
    # Evidence-derived property bag (opaque feature hashes / stats — not token names)
    properties: dict[str, float] = field(default_factory=dict)
    visit_count: int = 0
    effect_mean: float = 0.0
    effect_var: float = 0.0
    uncertainty: float = 1.0
    characterized: bool = False
    family_ids: list[str] = field(default_factory=list)
    last_update: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def observe(self, effect: float = 0.0, *, step: int = 0) -> None:
        self.visit_count += 1
        e = float(effect)
        n = self.visit_count
        old = self.effect_mean
        self.effect_mean += (e - old) / n
        self.effect_var += (e - old) * (e - self.effect_mean)
        # Uncertainty shrinks with visits + effect magnitude
        self.uncertainty = max(0.05, 1.0 / (1.0 + 0.35 * n + abs(self.effect_mean)))
        if self.visit_count >= 2 and abs(self.effect_mean) > 0.02:
            self.characterized = True
        self.last_update = int(step)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AutonomousDiscoveryState:
    """Planner-facing state answering what-known / unexplained / EIG / readiness."""

    step: int = 0
    signals: dict[str, dict[str, Any]] = field(default_factory=dict)
    regions: dict[str, BehavioralRegion] = field(default_factory=dict)
    residual_features: dict[str, float] = field(default_factory=dict)
    region_priors: dict[str, float] = field(default_factory=dict)  # revisable cue-conditioned
    uncertainties: dict[str, float] = field(default_factory=dict)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    cross_signal: dict[str, Any] = field(default_factory=dict)
    invention_history: list[dict[str, Any]] = field(default_factory=list)
    readiness: dict[str, float] = field(default_factory=dict)
    reserve_budget: float = 0.0
    eig_estimates: dict[str, float] = field(default_factory=dict)
    security_relevance: dict[str, float] = field(default_factory=dict)
    unexplained: float = 1.0
    trajectory: list[dict[str, Any]] = field(default_factory=list)
    add_depth: int = 0
    first_broken_transition: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    # Candidate accounting (theoretical / generated / tested) — brute-force gate
    theoretical_candidates: int = 0
    generated_candidates: int = 0
    tested_candidates: int = 0

    def log(self, transition: str, **kwargs: Any) -> None:
        rec = {"step": self.step, "transition": transition, **kwargs}
        self.trajectory.append(rec)

    def mark_broken(self, transition: str) -> None:
        if self.first_broken_transition is None:
            self.first_broken_transition = transition

    def upsert_region(self, region_id: str, **props: float) -> BehavioralRegion:
        r = self.regions.get(region_id)
        if r is None:
            r = BehavioralRegion(region_id=region_id, properties=dict(props))
            self.regions[region_id] = r
        else:
            r.properties.update(props)
        return r

    def observe_region(self, region_id: str, effect: float = 0.0) -> BehavioralRegion:
        r = self.upsert_region(region_id)
        r.observe(effect, step=self.step)
        self.uncertainties[region_id] = r.uncertainty
        return r

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "signals": dict(self.signals),
            "regions": {k: v.as_dict() for k, v in self.regions.items()},
            "residual_features": dict(self.residual_features),
            "region_priors": dict(self.region_priors),
            "uncertainties": dict(self.uncertainties),
            "hypotheses": list(self.hypotheses),
            "cross_signal": dict(self.cross_signal),
            "invention_history": list(self.invention_history[-50:]),
            "readiness": dict(self.readiness),
            "reserve_budget": self.reserve_budget,
            "eig_estimates": dict(self.eig_estimates),
            "security_relevance": dict(self.security_relevance),
            "unexplained": self.unexplained,
            "add_depth": self.add_depth,
            "first_broken_transition": self.first_broken_transition,
            "trajectory_len": len(self.trajectory),
            "theoretical_candidates": self.theoretical_candidates,
            "generated_candidates": self.generated_candidates,
            "tested_candidates": self.tested_candidates,
            "meta": dict(self.meta),
        }


__all__ = ["BehavioralRegion", "AutonomousDiscoveryState"]
