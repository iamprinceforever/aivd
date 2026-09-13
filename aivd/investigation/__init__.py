"""Active Behavioral Investigation (AIVD 3.3.0).

Optional scientific layer between exploration and verification.
Does not replace Explorer, Verifier, Memory, or Reward — extends them.
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
from aivd.investigation.localizer import localize_minimal_trigger
from aivd.investigation.metrics import summarize_investigation

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
    "summarize_investigation",
]
