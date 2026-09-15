"""CrossSignalHypothesis — residual↔action relation lifecycle.

States: UNSEEN→WEAK→PLAUSIBLE→SUPPORTED→FALSIFIED→REJECTED
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import hashlib
import time

from aivd.cross_signal.signals import ActionSignal, ResidualSignal


class RelationState(str, Enum):
    UNSEEN = "UNSEEN"
    WEAK = "WEAK"
    PLAUSIBLE = "PLAUSIBLE"
    SUPPORTED = "SUPPORTED"
    FALSIFIED = "FALSIFIED"
    REJECTED = "REJECTED"


_TRANSITIONS: dict[RelationState, frozenset[RelationState]] = {
    RelationState.UNSEEN: frozenset({RelationState.WEAK, RelationState.REJECTED}),
    RelationState.WEAK: frozenset({
        RelationState.PLAUSIBLE, RelationState.FALSIFIED, RelationState.REJECTED, RelationState.UNSEEN,
    }),
    RelationState.PLAUSIBLE: frozenset({
        RelationState.SUPPORTED, RelationState.FALSIFIED, RelationState.WEAK, RelationState.REJECTED,
    }),
    RelationState.SUPPORTED: frozenset({
        RelationState.FALSIFIED, RelationState.PLAUSIBLE, RelationState.REJECTED,
    }),
    RelationState.FALSIFIED: frozenset({
        RelationState.REJECTED, RelationState.WEAK, RelationState.PLAUSIBLE,
    }),
    RelationState.REJECTED: frozenset({RelationState.UNSEEN, RelationState.WEAK}),
}


def _as_rel(x: RelationState | str) -> RelationState:
    if isinstance(x, RelationState):
        return x
    return RelationState(str(x))


def can_transition(src: RelationState | str, dst: RelationState | str) -> bool:
    s = _as_rel(src)
    d = _as_rel(dst)
    return d in _TRANSITIONS.get(s, frozenset()) or s == d


def advance_state(
    state: RelationState | str,
    *,
    link_score: float = 0.0,
    cf_pass: bool | None = None,
    n_support: int = 0,
    n_falsify: int = 0,
    force_reject: bool = False,
) -> RelationState:
    """Heuristic lifecycle advance from evidence (not holdout-tuned)."""
    s = _as_rel(state)
    if force_reject:
        return RelationState.REJECTED
    if n_falsify >= 2 and link_score < 0.25:
        if s in (RelationState.SUPPORTED, RelationState.PLAUSIBLE, RelationState.WEAK):
            return RelationState.FALSIFIED
        return RelationState.REJECTED
    if cf_pass is False and s in (RelationState.SUPPORTED, RelationState.PLAUSIBLE):
        return RelationState.FALSIFIED
    if s == RelationState.UNSEEN:
        if link_score >= 0.15 or n_support >= 1:
            return RelationState.WEAK
        return s
    if s == RelationState.WEAK:
        if link_score >= 0.35 and n_support >= 1:
            return RelationState.PLAUSIBLE
        if link_score < 0.08 and n_falsify >= 1:
            return RelationState.REJECTED
        return s
    if s == RelationState.PLAUSIBLE:
        if cf_pass is True and link_score >= 0.45 and n_support >= 2:
            return RelationState.SUPPORTED
        if link_score < 0.2:
            return RelationState.WEAK
        return s
    if s == RelationState.SUPPORTED:
        if cf_pass is False or (n_falsify >= 2 and link_score < 0.3):
            return RelationState.FALSIFIED
        return s
    if s == RelationState.FALSIFIED:
        if link_score >= 0.4 and n_support >= 2:
            return RelationState.PLAUSIBLE
        if n_falsify >= 3:
            return RelationState.REJECTED
        return s
    return s


@dataclass
class CrossSignalHypothesis:
    """Hypothesis that residual signal R relates to action/stem region A."""

    residual: ResidualSignal | None = None
    action: ActionSignal | None = None
    residual_id: str = ""
    action_id: str = ""
    state: str = RelationState.UNSEEN.value
    link_score: float = 0.0
    cross_evi: float = 0.0
    temporal_assoc: float = 0.0
    conditional_assoc: float = 0.0
    delta_similarity: float = 0.0
    information_gain: float = 0.0
    uncertainty_reduction: float = 0.0
    reproducibility: float = 0.0
    cf_consistency: float = 0.0
    causal_support: float = 0.0
    n_support: int = 0
    n_falsify: int = 0
    reserved: bool = False
    interaction_ready: bool = False
    id: str = ""
    score: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.residual is not None and not self.residual_id:
            self.residual_id = self.residual.signal_id
        if self.action is not None and not self.action_id:
            self.action_id = self.action.signal_id
        if not self.id:
            blob = f"{self.residual_id}|{self.action_id}|{time.time_ns()}"
            self.id = hashlib.sha256(blob.encode()).hexdigest()[:14]

    def refresh_scores(self) -> None:
        """Aggregate link score — NOT raw correlation alone."""
        parts = [
            ("temporal", 0.15, self.temporal_assoc),
            ("conditional", 0.18, self.conditional_assoc),
            ("delta", 0.12, self.delta_similarity),
            ("ig", 0.15, self.information_gain),
            ("u_red", 0.12, self.uncertainty_reduction),
            ("repro", 0.12, self.reproducibility),
            ("cf", 0.10, self.cf_consistency),
            ("causal", 0.06, self.causal_support),
        ]
        self.link_score = float(sum(w * max(0.0, min(1.0, v)) for _, w, v in parts))
        # CrossSignalEVI: value of co-exploring this pair
        u_r = float(self.residual.uncertainty) if self.residual else 0.8
        u_a = float(self.action.uncertainty) if self.action else 0.8
        self.cross_evi = float(
            0.40 * self.link_score
            + 0.25 * min(u_r, u_a)
            + 0.20 * self.uncertainty_reduction
            + 0.15 * (1.0 if self.reserved else 0.3)
        )
        self.score = (
            0.40 * self.cross_evi
            + 0.30 * self.link_score
            + 0.15 * (1.0 if self.state == RelationState.SUPPORTED.value else
                     0.6 if self.state == RelationState.PLAUSIBLE.value else
                     0.3 if self.state == RelationState.WEAK.value else 0.0)
            + 0.15 * (1.0 if self.interaction_ready else 0.2)
        )

    def advance(self, *, cf_pass: bool | None = None, force_reject: bool = False) -> str:
        new = advance_state(
            self.state,
            link_score=self.link_score,
            cf_pass=cf_pass,
            n_support=self.n_support,
            n_falsify=self.n_falsify,
            force_reject=force_reject,
        )
        self.state = new.value
        # INTERACTION_READY needs relation support, not mere visits
        self.interaction_ready = self.state == RelationState.SUPPORTED.value
        self.refresh_scores()
        return self.state

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "residual_id": self.residual_id,
            "action_id": self.action_id,
            "state": self.state,
            "link_score": self.link_score,
            "cross_evi": self.cross_evi,
            "temporal_assoc": self.temporal_assoc,
            "conditional_assoc": self.conditional_assoc,
            "delta_similarity": self.delta_similarity,
            "information_gain": self.information_gain,
            "uncertainty_reduction": self.uncertainty_reduction,
            "reproducibility": self.reproducibility,
            "cf_consistency": self.cf_consistency,
            "causal_support": self.causal_support,
            "n_support": self.n_support,
            "n_falsify": self.n_falsify,
            "reserved": self.reserved,
            "interaction_ready": self.interaction_ready,
            "score": self.score,
            "residual": self.residual.as_dict() if self.residual else None,
            "action": self.action.as_dict() if self.action else None,
            "meta": dict(self.meta),
        }


__all__ = [
    "RelationState",
    "CrossSignalHypothesis",
    "can_transition",
    "advance_state",
]
