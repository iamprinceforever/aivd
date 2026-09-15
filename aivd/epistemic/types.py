"""Shared types for global epistemic budget arbitration (3.18)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class BranchState(str, Enum):
    FORMING = "FORMING"
    PROMISING = "PROMISING"
    ACTIVE = "ACTIVE"
    HIGH_VALUE = "HIGH_VALUE"
    INTERACTION_READY = "INTERACTION_READY"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FALSIFIED = "FALSIFIED"
    STARVED = "STARVED"
    ABANDONED = "ABANDONED"


TERMINAL_BRANCH_STATES = frozenset({
    BranchState.COMPLETED,
    BranchState.FALSIFIED,
    BranchState.STARVED,
    BranchState.ABANDONED,
})

VIABLE_BRANCH_STATES = frozenset({
    BranchState.FORMING,
    BranchState.PROMISING,
    BranchState.ACTIVE,
    BranchState.HIGH_VALUE,
    BranchState.INTERACTION_READY,
    BranchState.VERIFYING,
})


class ArbiterMode(str, Enum):
    OFF = "off"
    SHADOW = "shadow"
    ARBITER = "arbiter"


@dataclass
class ScoreBreakdown:
    """Normalized components of expected_experiment_value (not greedy EIG)."""
    immediate_information: float = 0.0
    uncertainty_reduction: float = 0.0
    hypothesis_discrimination: float = 0.0
    security_relevance: float = 0.0
    verification: float = 0.0
    expected_completion: float = 0.0
    unlock: float = 0.0
    experiment_cost: float = 0.0
    redundancy_penalty: float = 0.0
    repetition_penalty: float = 0.0
    opportunity_cost: float = 0.0
    total: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class ExperimentProposal:
    """Generic experiment proposal. Not OpenWorld-specific."""
    proposal_id: str
    branch_id: str
    subsystem: str
    hypothesis_id: str = ""
    action: str = ""
    prompt: str = ""
    expected_information_gain: float = 0.0
    uncertainty_reduction: float = 0.0
    security_relevance: float = 0.0
    hypothesis_discrimination_value: float = 0.0
    verification_value: float = 0.0
    causal_value: float = 0.0
    novelty_value: float = 0.0
    experiment_cost: float = 1.0
    estimated_remaining_steps: int = 1
    estimated_completion_probability: float = 0.0
    expected_terminal_value: float = 0.0
    repetition_penalty: float = 0.0
    redundancy_penalty: float = 0.0
    opportunity_cost: float = 0.0
    branch_starvation_risk: float = 0.0
    prerequisites: list[str] = field(default_factory=list)
    unlocks_hypothesis_class: bool = False
    provenance: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    score: ScoreBreakdown = field(default_factory=ScoreBreakdown)

    def as_dict(self) -> dict[str, Any]:
        d = {
            "proposal_id": self.proposal_id,
            "branch_id": self.branch_id,
            "subsystem": self.subsystem,
            "hypothesis_id": self.hypothesis_id,
            "action": self.action,
            "prompt": self.prompt,
            "expected_information_gain": self.expected_information_gain,
            "uncertainty_reduction": self.uncertainty_reduction,
            "security_relevance": self.security_relevance,
            "hypothesis_discrimination_value": self.hypothesis_discrimination_value,
            "verification_value": self.verification_value,
            "causal_value": self.causal_value,
            "novelty_value": self.novelty_value,
            "experiment_cost": self.experiment_cost,
            "estimated_remaining_steps": self.estimated_remaining_steps,
            "estimated_completion_probability": self.estimated_completion_probability,
            "expected_terminal_value": self.expected_terminal_value,
            "repetition_penalty": self.repetition_penalty,
            "redundancy_penalty": self.redundancy_penalty,
            "opportunity_cost": self.opportunity_cost,
            "branch_starvation_risk": self.branch_starvation_risk,
            "prerequisites": list(self.prerequisites),
            "unlocks_hypothesis_class": self.unlocks_hypothesis_class,
            "provenance": self.provenance,
            "score": self.score.as_dict(),
        }
        return d


@dataclass
class AllocationDecision:
    step: int
    selected: ExperimentProposal | None
    legacy_selected: ExperimentProposal | None
    proposals: list[ExperimentProposal]
    remaining_budget: int
    reason: str = ""
    shadow: bool = False
    agreement: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "selected_id": self.selected.proposal_id if self.selected else None,
            "selected_branch": self.selected.branch_id if self.selected else None,
            "selected_subsystem": self.selected.subsystem if self.selected else None,
            "selected_score": self.selected.score.total if self.selected else None,
            "legacy_id": self.legacy_selected.proposal_id if self.legacy_selected else None,
            "legacy_branch": self.legacy_selected.branch_id if self.legacy_selected else None,
            "n_proposals": len(self.proposals),
            "remaining_budget": self.remaining_budget,
            "reason": self.reason,
            "shadow": self.shadow,
            "agreement": self.agreement,
        }


@dataclass
class ExperimentTraceRecord:
    """Machine-readable per-experiment budget trace (3.17 audit + 3.18)."""
    global_index: int
    subsystem: str
    branch_id: str
    hypothesis_id: str
    candidate_id: str
    expected_ig: float
    actual_ig: float
    uncertainty_before: float
    uncertainty_after: float
    security_relevance: float
    verification_relevance: float
    experiment_cost: float
    branch_state: str
    remaining_global_budget: int
    locally_reserved: bool
    later_redundant: bool = False
    branch_completed: bool = False
    starved_other: bool = False
    proposal_id: str = ""
    action: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "BranchState",
    "TERMINAL_BRANCH_STATES",
    "VIABLE_BRANCH_STATES",
    "ArbiterMode",
    "ScoreBreakdown",
    "ExperimentProposal",
    "AllocationDecision",
    "ExperimentTraceRecord",
]
