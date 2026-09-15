"""AIVD 3.13 — Joint Residual Budget Allocation (Level 4).

Recognize joint residual dependency → allocate across underexplored
component families → characterize both → reserve for combination →
test interaction when ready.

Config: joint_mode / invention modes joint|joint_full|... (default off).
No Holdout-named rules; no Q/Z hardcoding; readiness ≠ vulnerability.
"""
from aivd.joint.dependency import (
    JointResidualHypothesis,
    estimate_linkage,
    hypothesize_joint_residuals,
)
from aivd.joint.joint_uncertainty import (
    component_uncertainty,
    joint_uncertainty,
    joint_evi,
)
from aivd.joint.readiness import (
    ComponentState,
    advance_from_evidence,
    pair_interaction_ready,
    readiness_score,
    readiness_record,
)
from aivd.joint.residual_graph import ResidualGraph
from aivd.joint.budget_allocator import allocate_budget, ALLOC_POLICIES
from aivd.joint.reserve import BudgetReserve
from aivd.joint.coexploration import (
    coexplore_families,
    compose_ordered_prompts,
    ORDERINGS,
)
from aivd.joint.scheduler import (
    JointScheduler,
    is_joint_mode,
    joint_enables_interaction,
    JOINT_MODES,
)
from aivd.joint.controller import JointResidualController
from aivd.joint.traces import JointTrace
from aivd.joint.audit import (
    scan_joint_source,
    joint_audit_record,
    anti_q_benchmark_spec,
    false_joint_dependency_spec,
    complexity_metrics,
)

__all__ = [
    "JointResidualHypothesis",
    "estimate_linkage",
    "hypothesize_joint_residuals",
    "component_uncertainty",
    "joint_uncertainty",
    "joint_evi",
    "ComponentState",
    "advance_from_evidence",
    "pair_interaction_ready",
    "readiness_score",
    "readiness_record",
    "ResidualGraph",
    "allocate_budget",
    "ALLOC_POLICIES",
    "BudgetReserve",
    "coexplore_families",
    "compose_ordered_prompts",
    "ORDERINGS",
    "JointScheduler",
    "is_joint_mode",
    "joint_enables_interaction",
    "JOINT_MODES",
    "JointResidualController",
    "JointTrace",
    "scan_joint_source",
    "joint_audit_record",
    "anti_q_benchmark_spec",
    "false_joint_dependency_spec",
    "complexity_metrics",
]
