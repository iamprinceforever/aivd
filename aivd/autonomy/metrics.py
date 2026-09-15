"""ADD (Autonomous Discovery Depth 0–9) + trajectory metrics (3.15)."""
from __future__ import annotations

from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState


# Depth ladder (conservative):
# 0 observe only
# 1 abstract regions
# 2 hypothesize
# 3 route weak signals
# 4 invent interventions
# 5 experiment / update beliefs
# 6 cross-signal integration
# 7 composition readiness
# 8 composition tested
# 9 verified secret / CF pass
ADD_LABELS = {
    0: "observe",
    1: "abstract",
    2: "hypothesize",
    3: "route",
    4: "invent",
    5: "experiment_update",
    6: "cross_signal",
    7: "composition_ready",
    8: "composition_tested",
    9: "verified",
}


def compute_add(
    state: AutonomousDiscoveryState,
    *,
    secret_found: bool = False,
    composition_tested: bool = False,
    cross_signal_integrated: bool = False,
    cf_pass: bool = False,
) -> int:
    depth = 0
    transitions = {t.get("transition") for t in state.trajectory}
    if "OBSERVE" in transitions or state.step > 0:
        depth = max(depth, 0)
    if state.regions:
        depth = max(depth, 1)
    if state.hypotheses or state.meta.get("hypothesized"):
        depth = max(depth, 2)
    if state.meta.get("routed"):
        depth = max(depth, 3)
    if state.invention_history or state.generated_candidates > 0:
        depth = max(depth, 4)
    if state.tested_candidates > 0:
        depth = max(depth, 5)
    if cross_signal_integrated or state.cross_signal.get("n_hypotheses"):
        depth = max(depth, 6)
    ready = list(state.readiness.values())
    if ready and max(ready) >= 0.5:
        depth = max(depth, 7)
    if composition_tested or state.meta.get("composed"):
        depth = max(depth, 8)
    if secret_found and cf_pass:
        depth = max(depth, 9)
    elif secret_found:
        depth = max(depth, 8)  # found but not fully CF-verified → cap 8 conservatively
    state.add_depth = int(depth)
    return int(depth)


def trajectory_summary(state: AutonomousDiscoveryState) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for t in state.trajectory:
        k = str(t.get("transition") or "?")
        counts[k] = counts.get(k, 0) + 1
    return {
        "add": state.add_depth,
        "add_label": ADD_LABELS.get(state.add_depth, "unknown"),
        "n_steps": state.step,
        "transition_counts": counts,
        "first_broken_transition": state.first_broken_transition,
        "n_hypotheses": len(state.hypotheses),
        "n_regions": len(state.regions),
        "theoretical_candidates": state.theoretical_candidates,
        "generated_candidates": state.generated_candidates,
        "tested_candidates": state.tested_candidates,
        "brute_force": (
            state.theoretical_candidates > 0
            and state.generated_candidates >= state.theoretical_candidates
            and state.tested_candidates >= state.theoretical_candidates
        ),
    }


__all__ = ["ADD_LABELS", "compute_add", "trajectory_summary"]
