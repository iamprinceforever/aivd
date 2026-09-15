"""AIVD 3.15 — Autonomous Signal-to-Intervention Discovery.

Unified closed-loop:
OBSERVE → ABSTRACT → HYPOTHESIZE → ROUTE → INVENT → EXPERIMENT → UPDATE → COMPOSE → VERIFY

Config: autonomy_mode / invention modes autonomy|... (default off).
When disabled ≈ 3.14 behavior. No Holdout-named rules.
"""
from aivd.autonomy.state import AutonomousDiscoveryState, BehavioralRegion
from aivd.autonomy.hypotheses import HypState, DiscoveryHypothesis, HypothesisTree
from aivd.autonomy.region_transfer import (
    extract_residual_features,
    rank_regions_given_residual,
    update_cue_conditioned_priors,
    seed_regions_from_individuals,
)
from aivd.autonomy.candidate_generation import route_weak_signals, generate_routed_candidates
from aivd.autonomy.intervention_invention import invent_from_evidence, ABSTRACT_OPERATORS
from aivd.autonomy.experiment_planner import plan_experiments, score_candidate, PlanItem
from aivd.autonomy.decision import next_transition, should_reserve_for_composition
from aivd.autonomy.composition import (
    assess_composition_readiness,
    compose_via_joint,
    compose_via_cross_signal,
)
from aivd.autonomy.budget import AutonomyBudget
from aivd.autonomy.metrics import compute_add, trajectory_summary, ADD_LABELS
from aivd.autonomy.memory import AutonomyMemory
from aivd.autonomy.scheduler import (
    AUTONOMY_MODES,
    is_autonomy_mode,
    autonomy_enables_cross_signal,
    autonomy_enables_joint,
    autonomy_enables_interaction,
)
from aivd.autonomy.controller import AutonomousDiscoveryController
from aivd.autonomy.validation import brute_force_fail, correlated_noncausal_should_not_verify
from aivd.autonomy.audit import (
    scan_autonomy_source,
    autonomy_audit_record,
    anti_mapping_benchmark_spec,
    correlated_noncausal_spec,
    false_transfer_spec,
)

__all__ = [
    "AutonomousDiscoveryState",
    "BehavioralRegion",
    "HypState",
    "DiscoveryHypothesis",
    "HypothesisTree",
    "extract_residual_features",
    "rank_regions_given_residual",
    "update_cue_conditioned_priors",
    "seed_regions_from_individuals",
    "route_weak_signals",
    "generate_routed_candidates",
    "invent_from_evidence",
    "ABSTRACT_OPERATORS",
    "plan_experiments",
    "score_candidate",
    "PlanItem",
    "next_transition",
    "should_reserve_for_composition",
    "assess_composition_readiness",
    "compose_via_joint",
    "compose_via_cross_signal",
    "AutonomyBudget",
    "compute_add",
    "trajectory_summary",
    "ADD_LABELS",
    "AutonomyMemory",
    "AUTONOMY_MODES",
    "is_autonomy_mode",
    "autonomy_enables_cross_signal",
    "autonomy_enables_joint",
    "autonomy_enables_interaction",
    "AutonomousDiscoveryController",
    "brute_force_fail",
    "correlated_noncausal_should_not_verify",
    "scan_autonomy_source",
    "autonomy_audit_record",
    "anti_mapping_benchmark_spec",
    "correlated_noncausal_spec",
    "false_transfer_spec",
]
