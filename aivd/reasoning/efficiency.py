"""Discovery vs activity efficiency metrics (3.16)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DiscoveryEfficiency:
    discovery_efficiency: float  # useful IG / probes
    hypothesis_efficiency: float  # hyps falsified_or_supported / hyps
    information_efficiency: float  # actual IG / predicted IG mass
    search_reduction: float  # 1 - tested/theoretical
    activity_depth: int
    discovery_depth: int
    activity_without_discovery: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "discovery_efficiency": self.discovery_efficiency,
            "hypothesis_efficiency": self.hypothesis_efficiency,
            "information_efficiency": self.information_efficiency,
            "search_reduction": self.search_reduction,
            "activity_depth": self.activity_depth,
            "discovery_depth": self.discovery_depth,
            "activity_without_discovery": self.activity_without_discovery,
        }


def activity_depth_vs_discovery_depth(
    *,
    add: int,
    tested: int,
    mean_actual_ig: float,
    secret_found: bool,
    u_drop: float,
) -> tuple[int, int]:
    """Activity depth ≈ ADD (process milestones). Discovery depth requires info."""
    activity = int(add)
    discovery = 0
    if tested > 0:
        discovery = max(discovery, 1)
    if mean_actual_ig > 0.02 or u_drop > 0.05:
        discovery = max(discovery, min(activity, 3 + int(3 * min(1.0, mean_actual_ig * 5))))
    if secret_found:
        discovery = max(discovery, activity)
    # Cap discovery by activity (can't discover past what you did)
    discovery = min(discovery, activity)
    return activity, int(discovery)


def compute_efficiency(
    *,
    probes: int,
    tested: int,
    theoretical: int,
    generated: int,
    total_actual_ig: float,
    total_predicted_ig: float,
    n_hypotheses: int,
    n_hyp_resolved: int,
    add: int,
    secret_found: bool,
    u_before: float,
    u_after: float,
) -> DiscoveryEfficiency:
    probes = max(0, int(probes))
    tested = max(0, int(tested))
    de = float(total_actual_ig / probes) if probes else 0.0
    he = float(n_hyp_resolved / n_hypotheses) if n_hypotheses else 0.0
    ie = (
        float(total_actual_ig / total_predicted_ig)
        if total_predicted_ig > 1e-6
        else (1.0 if total_actual_ig > 0 else 0.0)
    )
    ie = float(min(2.0, max(0.0, ie)))
    theo = max(1, int(theoretical) or int(generated) or 1)
    sr = float(1.0 - (tested / theo))
    sr = float(min(1.0, max(0.0, sr)))
    mean_ig = float(total_actual_ig / tested) if tested else 0.0
    u_drop = float(u_before - u_after)
    act, disc = activity_depth_vs_discovery_depth(
        add=add,
        tested=tested,
        mean_actual_ig=mean_ig,
        secret_found=secret_found,
        u_drop=u_drop,
    )
    return DiscoveryEfficiency(
        discovery_efficiency=float(de),
        hypothesis_efficiency=float(he),
        information_efficiency=float(ie),
        search_reduction=sr,
        activity_depth=act,
        discovery_depth=disc,
        activity_without_discovery=bool(act >= 4 and disc <= 1 and not secret_found),
    )


__all__ = [
    "DiscoveryEfficiency",
    "compute_efficiency",
    "activity_depth_vs_discovery_depth",
]
