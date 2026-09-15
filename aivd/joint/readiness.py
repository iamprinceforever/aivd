"""Interaction readiness states — readiness ≠ vulnerability."""
from __future__ import annotations

from enum import Enum
from typing import Any


class ComponentState(str, Enum):
    """Missing-component / characterization lifecycle."""

    UNEXAMINED = "UNEXAMINED"
    PARTIALLY_CHARACTERIZED = "PARTIALLY_CHARACTERIZED"
    CHARACTERIZED = "CHARACTERIZED"
    INTERACTION_READY = "INTERACTION_READY"
    DISQUALIFIED = "DISQUALIFIED"
    REOPENED = "REOPENED"


# Valid transitions (scientific lifecycle; not vuln claims)
_TRANSITIONS: dict[ComponentState, frozenset[ComponentState]] = {
    ComponentState.UNEXAMINED: frozenset({
        ComponentState.PARTIALLY_CHARACTERIZED,
        ComponentState.DISQUALIFIED,
    }),
    ComponentState.PARTIALLY_CHARACTERIZED: frozenset({
        ComponentState.CHARACTERIZED,
        ComponentState.DISQUALIFIED,
        ComponentState.UNEXAMINED,  # revise down
    }),
    ComponentState.CHARACTERIZED: frozenset({
        ComponentState.INTERACTION_READY,
        ComponentState.DISQUALIFIED,
        ComponentState.REOPENED,
        ComponentState.PARTIALLY_CHARACTERIZED,
    }),
    ComponentState.INTERACTION_READY: frozenset({
        ComponentState.DISQUALIFIED,
        ComponentState.REOPENED,
        ComponentState.CHARACTERIZED,
    }),
    ComponentState.DISQUALIFIED: frozenset({
        ComponentState.REOPENED,
    }),
    ComponentState.REOPENED: frozenset({
        ComponentState.PARTIALLY_CHARACTERIZED,
        ComponentState.UNEXAMINED,
        ComponentState.DISQUALIFIED,
    }),
}


def _as_state(x: ComponentState | str) -> ComponentState:
    if isinstance(x, ComponentState):
        return x
    return ComponentState(str(x))


def can_transition(src: ComponentState | str, dst: ComponentState | str) -> bool:
    s = _as_state(src)
    d = _as_state(dst)
    return d in _TRANSITIONS.get(s, frozenset())


def transition(
    state: ComponentState | str,
    dst: ComponentState | str,
    *,
    force: bool = False,
) -> ComponentState:
    s = _as_state(state)
    d = _as_state(dst)
    if force or can_transition(s, d) or s == d:
        return d
    raise ValueError(f"illegal readiness transition {s.value} → {d.value}")


def advance_from_evidence(
    state: ComponentState | str,
    *,
    n_probes: int = 0,
    n_variants: int = 0,
    effect_mean: float = 0.0,
    negative_evidence: bool = False,
    peer_characterized: bool = False,
    reopen: bool = False,
) -> ComponentState:
    """Heuristic state advance from characterization evidence.

    INTERACTION_READY requires this component characterized AND a peer characterized.
    Never equates readiness with vulnerability.
    """
    s = _as_state(state)
    if reopen and s == ComponentState.DISQUALIFIED:
        return ComponentState.REOPENED
    if negative_evidence and n_probes >= 3 and effect_mean < 0.02:
        if s not in (ComponentState.DISQUALIFIED,):
            return ComponentState.DISQUALIFIED
        return s
    if s in (ComponentState.DISQUALIFIED,):
        return s
    if s == ComponentState.REOPENED:
        s = ComponentState.UNEXAMINED
    if n_probes <= 0:
        return ComponentState.UNEXAMINED
    if n_probes == 1 or (n_variants < 2 and n_probes < 3):
        return ComponentState.PARTIALLY_CHARACTERIZED
    # Characterized: enough probes/variants
    characterized = n_probes >= 2 and (n_variants >= 2 or n_probes >= 3 or effect_mean > 0.05)
    if not characterized:
        return ComponentState.PARTIALLY_CHARACTERIZED
    if peer_characterized:
        return ComponentState.INTERACTION_READY
    return ComponentState.CHARACTERIZED


def pair_interaction_ready(state_a: ComponentState | str, state_b: ComponentState | str) -> bool:
    """Both sides at least CHARACTERIZED; ideally INTERACTION_READY."""
    ok = {
        ComponentState.CHARACTERIZED,
        ComponentState.INTERACTION_READY,
    }
    return _as_state(state_a) in ok and _as_state(state_b) in ok


def readiness_score(state: ComponentState | str) -> float:
    order = [
        ComponentState.UNEXAMINED,
        ComponentState.REOPENED,
        ComponentState.PARTIALLY_CHARACTERIZED,
        ComponentState.CHARACTERIZED,
        ComponentState.INTERACTION_READY,
        ComponentState.DISQUALIFIED,
    ]
    s = _as_state(state)
    if s == ComponentState.DISQUALIFIED:
        return 0.0
    try:
        idx = order.index(s)
    except ValueError:
        return 0.0
    # INTERACTION_READY is index 4 → 1.0
    return min(1.0, idx / 4.0)


def readiness_record(
    family_id: str,
    state: ComponentState | str,
    **evidence: Any,
) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "state": _as_state(state).value,
        "readiness_score": readiness_score(state),
        "is_vulnerability": False,  # explicit: readiness ≠ vuln
        **evidence,
    }


__all__ = [
    "ComponentState",
    "can_transition",
    "transition",
    "advance_from_evidence",
    "pair_interaction_ready",
    "readiness_score",
    "readiness_record",
]
