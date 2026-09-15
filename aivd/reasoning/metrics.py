"""Discovery-depth and reasoning summary metrics (3.16)."""
from __future__ import annotations

from typing import Any

from aivd.reasoning.efficiency import compute_efficiency, activity_depth_vs_discovery_depth


def discovery_depth(
    *,
    add: int,
    tested: int,
    mean_actual_ig: float,
    secret_found: bool,
    u_drop: float,
) -> int:
    _, d = activity_depth_vs_discovery_depth(
        add=add,
        tested=tested,
        mean_actual_ig=mean_actual_ig,
        secret_found=secret_found,
        u_drop=u_drop,
    )
    return d


def reasoning_summary(state: dict[str, Any]) -> dict[str, Any]:
    """Compact summary for reports."""
    eff = state.get("efficiency") or {}
    bn = state.get("bottleneck") or {}
    return {
        "reasoning_enabled": bool(state.get("reasoning_enabled")),
        "bottleneck_earliest": bn.get("earliest"),
        "bottleneck_codes": bn.get("codes"),
        "activity_depth": eff.get("activity_depth"),
        "discovery_depth": eff.get("discovery_depth"),
        "activity_without_discovery": eff.get("activity_without_discovery"),
        "discovery_efficiency": eff.get("discovery_efficiency"),
        "information_efficiency": eff.get("information_efficiency"),
        "search_reduction": eff.get("search_reduction"),
        "n_transitions_instrumented": state.get("n_transitions_instrumented"),
        "mean_actual_ig": state.get("mean_actual_ig"),
        "mean_prediction_error": state.get("mean_prediction_error"),
        "strategy_shifts": state.get("strategy_shifts"),
    }


__all__ = ["discovery_depth", "reasoning_summary", "compute_efficiency"]
