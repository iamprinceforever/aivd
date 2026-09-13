"""Active Behavioral Investigation (AIVD 3.3–3.4).

Optional scientific layer between exploration and verification.
3.4 adds autonomous multi-step episode control — does not replace
Explorer, Verifier, Memory, or Reward.
"""
from aivd.investigation.types import (
    BehavioralDelta,
    BoundaryRecord,
    Hypothesis,
    HypothesisStatus,
    InvestigationHypothesis,
    InvestigationResult,
    ProbEstimate,
    SensitivityClass,
    StressLevel,
    TriadExperiment,
    TriggerSensitivity,
)
from aivd.investigation.behavioral_investigator import BehavioralInvestigator
from aivd.investigation.delta import BehavioralDeltaComputer, compute_delta
from aivd.investigation.localizer import localize_minimal_trigger, localize_with_transforms
from aivd.investigation.metrics import summarize_investigation
from aivd.investigation.episode import InvestigationEpisode
from aivd.investigation.state_machine import InvestigationState, is_terminal, can_transition
from aivd.investigation.episode_controller import MultiStepInvestigationController
from aivd.investigation.triage import expected_value_of_investigation, TriageFeatures
from aivd.investigation.policies import HeuristicController, LearnedController, PolicyAction

__all__ = [
    "BehavioralDelta",
    "BoundaryRecord",
    "Hypothesis",
    "HypothesisStatus",
    "InvestigationHypothesis",
    "InvestigationResult",
    "ProbEstimate",
    "SensitivityClass",
    "StressLevel",
    "TriadExperiment",
    "TriggerSensitivity",
    "BehavioralInvestigator",
    "BehavioralDeltaComputer",
    "compute_delta",
    "localize_minimal_trigger",
    "localize_with_transforms",
    "summarize_investigation",
    "InvestigationEpisode",
    "InvestigationState",
    "is_terminal",
    "can_transition",
    "MultiStepInvestigationController",
    "expected_value_of_investigation",
    "TriageFeatures",
    "HeuristicController",
    "LearnedController",
    "PolicyAction",
]
