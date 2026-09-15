"""AIVD 3.16 — Discovery Reasoning Reset.

Predict-before-experiment, expected vs actual IG, experiment quality,
bottleneck diagnostics, discovery-vs-activity metrics, provenance memory.

Default reasoning_mode=off → ≈ 3.15 behavior. No holdout-specific rules.
"""
from aivd.reasoning.bottleneck import (
    BottleneckCode,
    diagnose_bottleneck,
    FIRST_BOTTLENECK_AUDIT,
)
from aivd.reasoning.predict import (
    OutcomePrediction,
    predict_outcomes,
    choose_discriminating,
)
from aivd.reasoning.information_gain import (
    TransitionRecord,
    record_transition,
    predicted_vs_actual_ig,
    update_uncertainty,
)
from aivd.reasoning.experiment_quality import (
    ExperimentQuality,
    score_experiment_quality,
)
from aivd.reasoning.dead_end import (
    DeadEndDetector,
    StrategyShift,
)
from aivd.reasoning.efficiency import (
    DiscoveryEfficiency,
    compute_efficiency,
    activity_depth_vs_discovery_depth,
)
from aivd.reasoning.provenance import ProvenanceMemory, ProvenanceEdge
from aivd.reasoning.representation import (
    representation_sufficient,
    info_acquisition_candidates,
)
from aivd.reasoning.epistemic_budget import (
    EpistemicBudgetPolicy,
    reallocate_for_experiments,
)
from aivd.reasoning.controller import ReasoningController, is_reasoning_mode, REASONING_MODES
from aivd.reasoning.metrics import discovery_depth, reasoning_summary
from aivd.reasoning.audit import scan_reasoning_source, reasoning_audit_record

__all__ = [
    "BottleneckCode",
    "diagnose_bottleneck",
    "FIRST_BOTTLENECK_AUDIT",
    "OutcomePrediction",
    "predict_outcomes",
    "choose_discriminating",
    "TransitionRecord",
    "record_transition",
    "predicted_vs_actual_ig",
    "update_uncertainty",
    "ExperimentQuality",
    "score_experiment_quality",
    "DeadEndDetector",
    "StrategyShift",
    "DiscoveryEfficiency",
    "compute_efficiency",
    "activity_depth_vs_discovery_depth",
    "ProvenanceMemory",
    "ProvenanceEdge",
    "representation_sufficient",
    "info_acquisition_candidates",
    "EpistemicBudgetPolicy",
    "reallocate_for_experiments",
    "ReasoningController",
    "is_reasoning_mode",
    "REASONING_MODES",
    "discovery_depth",
    "reasoning_summary",
    "scan_reasoning_source",
    "reasoning_audit_record",
]
