"""AIVD 3.9–3.15 Open Intervention Invention (+ … + Autonomy).

Sits ABOVE 3.6 causal, BEFORE residual sweep / investigation.
Config: invention_mode = off | random | heuristic | full |
        diversity | bandit | diversity_full | diversity_heuristic |
        adaptive | adaptive_full | adaptive_heuristic |
        interaction | interaction_full | interaction_random |
        joint | joint_full | joint_only | joint_random |
        interaction_joint | full_3_13 |
        cross_signal | cross_signal_full | cross_signal_only | cross_signal_random |
        cross_joint | full_3_14 |
        autonomy | autonomy_full | autonomy_only | autonomy_random |
        autonomy_cross | full_3_15 (default off).
Optional: invention_diversity_mode, adaptive_ordering_mode, interaction_mode,
exploration, saturation/revival. Novelty alone is NOT rewarded.
No Holdout special-cases. Interaction layer distinguishes additive vs synergistic.
"""
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.candidate_generator import generate_candidates
from aivd.invention.scoring import score_intervention, rank_candidates
from aivd.invention.audit import (
    scan_invention_source,
    novelty_audit_record,
    diversity_audit_record,
    adaptive_ordering_audit_record,
    interaction_discovery_audit_record,
    joint_allocation_audit_record,
)
from aivd.invention.family import assign_family, cluster_interventions, extract_family_features
from aivd.invention.selection import diversity_score, select_diverse_batch, rank_with_diversity
from aivd.invention.archive import FamilyArchive
from aivd.invention.exploration import EXPLORATION_POLICIES, select_family
from aivd.invention.adaptive_ordering import (
    AdaptiveOrderingState,
    is_adaptive_mode,
    ADAPTIVE_MODES,
)
from aivd.invention.residual_salience import residual_salience
from aivd.invention.candidate_value import dynamic_candidate_value
from aivd.invention.dynamic_ranking import rank_dynamically
from aivd.invention.priority_history import PriorityHistory
from aivd.invention.search_scheduler import SearchScheduler

__all__ = [
    "InventionController",
    "Intervention",
    "InterventionOp",
    "generate_candidates",
    "score_intervention",
    "rank_candidates",
    "scan_invention_source",
    "novelty_audit_record",
    "diversity_audit_record",
    "adaptive_ordering_audit_record",
    "interaction_discovery_audit_record",
    "assign_family",
    "cluster_interventions",
    "extract_family_features",
    "diversity_score",
    "select_diverse_batch",
    "rank_with_diversity",
    "FamilyArchive",
    "EXPLORATION_POLICIES",
    "select_family",
    "AdaptiveOrderingState",
    "is_adaptive_mode",
    "ADAPTIVE_MODES",
    "residual_salience",
    "dynamic_candidate_value",
    "rank_dynamically",
    "PriorityHistory",
    "SearchScheduler",
]
