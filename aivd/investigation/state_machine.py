"""Investigation episode state machine (AIVD 3.4).

Adaptive (not forced-linear): transitions depend on evidence, budget, and policy.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class InvestigationState(str, Enum):
    SIGNAL_DETECTED = "signal_detected"
    TRIAGE = "triage"
    HYPOTHESIS_FORMED = "hypothesis_formed"
    BASELINE_CHECK = "baseline_check"
    PROBING = "probing"
    LOCALIZING = "localizing"
    VARIANT_TESTING = "variant_testing"
    BOUNDARY_SEARCH = "boundary_search"
    COUNTERFACTUAL_TEST = "counterfactual_test"
    STOCHASTICITY_CHECK = "stochasticity_check"
    SECURITY_ASSESSMENT = "security_assessment"
    VERIFICATION = "verification"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"
    RETURN_TO_EXPLORATION = "return_to_exploration"


# Terminal states — episode should stop and hand control back to exploration.
TERMINAL_STATES = frozenset(
    {
        InvestigationState.CONFIRMED,
        InvestigationState.REJECTED,
        InvestigationState.UNRESOLVED,
        InvestigationState.RETURN_TO_EXPLORATION,
    }
)

# Allowed adaptive transitions (from → frozenset of to). Not a forced chain.
_ALLOWED: dict[InvestigationState, frozenset[InvestigationState]] = {
    InvestigationState.SIGNAL_DETECTED: frozenset(
        {
            InvestigationState.TRIAGE,
            InvestigationState.RETURN_TO_EXPLORATION,
            InvestigationState.REJECTED,
        }
    ),
    InvestigationState.TRIAGE: frozenset(
        {
            InvestigationState.HYPOTHESIS_FORMED,
            InvestigationState.RETURN_TO_EXPLORATION,
            InvestigationState.REJECTED,
            InvestigationState.ABANDON if False else InvestigationState.UNRESOLVED,  # noqa: placeholder
        }
    ),
    InvestigationState.HYPOTHESIS_FORMED: frozenset(
        {
            InvestigationState.BASELINE_CHECK,
            InvestigationState.PROBING,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.BASELINE_CHECK: frozenset(
        {
            InvestigationState.PROBING,
            InvestigationState.LOCALIZING,
            InvestigationState.REJECTED,
            InvestigationState.UNRESOLVED,
        }
    ),
    InvestigationState.PROBING: frozenset(
        {
            InvestigationState.LOCALIZING,
            InvestigationState.VARIANT_TESTING,
            InvestigationState.COUNTERFACTUAL_TEST,
            InvestigationState.BOUNDARY_SEARCH,
            InvestigationState.STOCHASTICITY_CHECK,
            InvestigationState.SECURITY_ASSESSMENT,
            InvestigationState.REJECTED,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.LOCALIZING: frozenset(
        {
            InvestigationState.VARIANT_TESTING,
            InvestigationState.COUNTERFACTUAL_TEST,
            InvestigationState.BOUNDARY_SEARCH,
            InvestigationState.SECURITY_ASSESSMENT,
            InvestigationState.VERIFICATION,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.VARIANT_TESTING: frozenset(
        {
            InvestigationState.LOCALIZING,
            InvestigationState.COUNTERFACTUAL_TEST,
            InvestigationState.BOUNDARY_SEARCH,
            InvestigationState.STOCHASTICITY_CHECK,
            InvestigationState.SECURITY_ASSESSMENT,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.BOUNDARY_SEARCH: frozenset(
        {
            InvestigationState.COUNTERFACTUAL_TEST,
            InvestigationState.SECURITY_ASSESSMENT,
            InvestigationState.VERIFICATION,
            InvestigationState.CONFIRMED,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.COUNTERFACTUAL_TEST: frozenset(
        {
            InvestigationState.LOCALIZING,
            InvestigationState.VARIANT_TESTING,
            InvestigationState.SECURITY_ASSESSMENT,
            InvestigationState.REJECTED,
            InvestigationState.VERIFICATION,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.STOCHASTICITY_CHECK: frozenset(
        {
            InvestigationState.SECURITY_ASSESSMENT,
            InvestigationState.VERIFICATION,
            InvestigationState.CONFIRMED,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.SECURITY_ASSESSMENT: frozenset(
        {
            InvestigationState.VERIFICATION,
            InvestigationState.CONFIRMED,
            InvestigationState.REJECTED,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.VERIFICATION: frozenset(
        {
            InvestigationState.CONFIRMED,
            InvestigationState.REJECTED,
            InvestigationState.UNRESOLVED,
            InvestigationState.RETURN_TO_EXPLORATION,
        }
    ),
    InvestigationState.CONFIRMED: frozenset({InvestigationState.RETURN_TO_EXPLORATION}),
    InvestigationState.REJECTED: frozenset({InvestigationState.RETURN_TO_EXPLORATION}),
    InvestigationState.UNRESOLVED: frozenset({InvestigationState.RETURN_TO_EXPLORATION}),
    InvestigationState.RETURN_TO_EXPLORATION: frozenset(),
}

# Fix TRIAGE allowed set cleanly (no placeholder)
_ALLOWED[InvestigationState.TRIAGE] = frozenset(
    {
        InvestigationState.HYPOTHESIS_FORMED,
        InvestigationState.RETURN_TO_EXPLORATION,
        InvestigationState.REJECTED,
        InvestigationState.UNRESOLVED,
    }
)


def is_terminal(state: InvestigationState | str) -> bool:
    s = InvestigationState(state) if not isinstance(state, InvestigationState) else state
    return s in TERMINAL_STATES


def can_transition(src: InvestigationState | str, dst: InvestigationState | str) -> bool:
    s = InvestigationState(src) if not isinstance(src, InvestigationState) else src
    d = InvestigationState(dst) if not isinstance(dst, InvestigationState) else dst
    if s == d:
        return True
    return d in _ALLOWED.get(s, frozenset())


def transition(
    src: InvestigationState | str,
    dst: InvestigationState | str,
    *,
    force: bool = False,
) -> InvestigationState:
    """Return destination if allowed (or force=True); else keep src."""
    s = InvestigationState(src) if not isinstance(src, InvestigationState) else src
    d = InvestigationState(dst) if not isinstance(dst, InvestigationState) else dst
    if force or can_transition(s, d):
        return d
    return s


def next_candidates(state: InvestigationState | str) -> list[InvestigationState]:
    s = InvestigationState(state) if not isinstance(state, InvestigationState) else state
    return sorted(_ALLOWED.get(s, frozenset()), key=lambda x: x.value)


def infer_state_from_flags(
    *,
    has_signal: bool,
    triaged: bool,
    hypothesis_formed: bool,
    baseline_done: bool,
    has_meaningful_delta: bool,
    localized: bool,
    variants_tested: bool,
    boundary_found: bool,
    counterfactual_done: bool,
    stochastic_done: bool,
    security_gated: bool,
    verified: bool,
    falsified: bool,
    abandoned: bool,
    budget_exhausted: bool,
    confidence: float,
    confirm_threshold: float = 0.75,
) -> InvestigationState:
    """Heuristic state inference for adaptive controllers (not forced linear)."""
    if abandoned or (budget_exhausted and not localized and not verified):
        return InvestigationState.RETURN_TO_EXPLORATION
    if falsified:
        return InvestigationState.REJECTED
    if verified or confidence >= confirm_threshold:
        return InvestigationState.CONFIRMED
    if not has_signal:
        return InvestigationState.SIGNAL_DETECTED
    if not triaged:
        return InvestigationState.TRIAGE
    if not hypothesis_formed:
        return InvestigationState.HYPOTHESIS_FORMED
    if not baseline_done:
        return InvestigationState.BASELINE_CHECK
    if security_gated and not verified:
        return InvestigationState.VERIFICATION
    if stochastic_done and not security_gated:
        return InvestigationState.SECURITY_ASSESSMENT
    if counterfactual_done and not stochastic_done:
        return InvestigationState.STOCHASTICITY_CHECK
    if boundary_found and not counterfactual_done:
        return InvestigationState.COUNTERFACTUAL_TEST
    if variants_tested and not boundary_found:
        return InvestigationState.BOUNDARY_SEARCH
    if localized and not variants_tested:
        return InvestigationState.VARIANT_TESTING
    if has_meaningful_delta and not localized:
        return InvestigationState.LOCALIZING
    if baseline_done:
        return InvestigationState.PROBING
    return InvestigationState.UNRESOLVED


__all__ = [
    "InvestigationState",
    "TERMINAL_STATES",
    "is_terminal",
    "can_transition",
    "transition",
    "next_candidates",
    "infer_state_from_flags",
]
