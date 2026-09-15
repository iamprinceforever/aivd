"""AIVD 3.14 — Cross-Signal Co-Exploration (Level 5).

Weak residual evidence informs where to explore on the action/stem side
(and vice versa), so multi-region components get characterized early enough
to test combinations — without holdout knowledge.

Config: cross_signal_mode / invention modes cross_signal|... (default off).
No Holdout-named rules; INTERACTION_READY needs relation support, not mere visits.
"""
from aivd.cross_signal.signals import ResidualSignal, ActionSignal, remap_signal_id
from aivd.cross_signal.relation import (
    RelationState,
    CrossSignalHypothesis,
    can_transition,
    advance_state,
)
from aivd.cross_signal.scoring import (
    score_pair,
    cross_signal_evi,
    temporal_association,
    conditional_association,
    delta_similarity,
    information_gain_estimate,
    cf_consistency_score,
)
from aivd.cross_signal.graph import RelationGraph
from aivd.cross_signal.coexplore import (
    hypothesize_cross_signals,
    coexplore_bidirectional,
    compose_cross_prompts,
)
from aivd.cross_signal.scheduler import (
    CrossSignalScheduler,
    is_cross_signal_mode,
    cross_enables_joint,
    cross_enables_interaction,
    CROSS_SIGNAL_MODES,
)
from aivd.cross_signal.reserve import CrossSignalReserve
from aivd.cross_signal.validation import validate_counterfactuals, falsify_hypothesis
from aivd.cross_signal.memory import CrossSignalMemory
from aivd.cross_signal.controller import CrossSignalController
from aivd.cross_signal.traces import CrossSignalTrace
from aivd.cross_signal.audit import (
    scan_cross_signal_source,
    cross_signal_audit_record,
    anti_mapping_benchmark_spec,
    correlated_noncausal_spec,
    false_dependency_spec,
)

__all__ = [
    "ResidualSignal",
    "ActionSignal",
    "remap_signal_id",
    "RelationState",
    "CrossSignalHypothesis",
    "can_transition",
    "advance_state",
    "score_pair",
    "cross_signal_evi",
    "temporal_association",
    "conditional_association",
    "delta_similarity",
    "information_gain_estimate",
    "cf_consistency_score",
    "RelationGraph",
    "hypothesize_cross_signals",
    "coexplore_bidirectional",
    "compose_cross_prompts",
    "CrossSignalScheduler",
    "is_cross_signal_mode",
    "cross_enables_joint",
    "cross_enables_interaction",
    "CROSS_SIGNAL_MODES",
    "CrossSignalReserve",
    "validate_counterfactuals",
    "falsify_hypothesis",
    "CrossSignalMemory",
    "CrossSignalController",
    "CrossSignalTrace",
    "scan_cross_signal_source",
    "cross_signal_audit_record",
    "anti_mapping_benchmark_spec",
    "correlated_noncausal_spec",
    "false_dependency_spec",
]
