"""Decision / routing layer for the autonomous loop (3.15)."""
from __future__ import annotations

from typing import Any, Literal

from aivd.autonomy.state import AutonomousDiscoveryState


Transition = Literal[
    "OBSERVE", "ABSTRACT", "HYPOTHESIZE", "ROUTE", "INVENT",
    "EXPERIMENT", "UPDATE", "COMPOSE", "VERIFY", "STOP",
]


def next_transition(
    state: AutonomousDiscoveryState,
    *,
    secret_found: bool = False,
    budget_remaining: int = 0,
    observation_limit: bool = False,
    verified: bool = False,
) -> Transition:
    """Choose next closed-loop transition from state."""
    if secret_found or verified:
        return "VERIFY" if not verified else "STOP"
    if observation_limit or budget_remaining <= 0:
        state.mark_broken("EXPERIMENT" if budget_remaining <= 0 else "OBSERVE")
        return "STOP"
    # Bootstrap
    if state.step == 0:
        return "OBSERVE"
    if not state.regions:
        return "ABSTRACT"
    if not state.hypotheses and not state.meta.get("hypothesized"):
        return "HYPOTHESIZE"
    if not state.meta.get("routed"):
        return "ROUTE"
    if state.generated_candidates < 4 and budget_remaining > 2:
        return "INVENT"
    # Composition when readiness high or enough experiments done
    ready_vals = list(state.readiness.values())
    chars = sum(1 for r in state.regions.values() if r.characterized)
    if (not state.meta.get("composed")) and (
        (ready_vals and max(ready_vals) >= 0.55) or (state.tested_candidates >= 4 and chars >= 1)
    ):
        return "COMPOSE"
    if budget_remaining > 0:
        return "EXPERIMENT"
    return "STOP"


def should_reserve_for_composition(state: AutonomousDiscoveryState) -> bool:
    """Reserve budget when cross-signal / dual-region readiness emerging."""
    if state.cross_signal.get("n_hypotheses", 0) >= 1:
        return True
    chars = sum(1 for r in state.regions.values() if r.characterized)
    return chars >= 2 and state.unexplained > 0.3


def record_decision(state: AutonomousDiscoveryState, transition: Transition, **kwargs: Any) -> None:
    state.meta["last_decision"] = transition
    state.log("DECISION", next=transition, **kwargs)


__all__ = [
    "Transition",
    "next_transition",
    "should_reserve_for_composition",
    "record_decision",
]
