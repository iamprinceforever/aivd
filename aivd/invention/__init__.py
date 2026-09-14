"""AIVD 3.9/3.10 Open Intervention Invention (+ Open Invention Diversity).

Sits ABOVE 3.6 causal, BEFORE residual sweep / investigation.
Config: invention_mode = off | random | heuristic | full |
        diversity | bandit | diversity_full | diversity_heuristic (default off).
Optional: invention_diversity_mode, exploration policy, saturation/revival.
Novelty alone is NOT rewarded. No Holdout-X/Y/Z special-case solutions.
"""
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.candidate_generator import generate_candidates
from aivd.invention.scoring import score_intervention, rank_candidates
from aivd.invention.audit import scan_invention_source, novelty_audit_record, diversity_audit_record
from aivd.invention.family import assign_family, cluster_interventions, extract_family_features
from aivd.invention.selection import diversity_score, select_diverse_batch, rank_with_diversity
from aivd.invention.archive import FamilyArchive
from aivd.invention.exploration import EXPLORATION_POLICIES, select_family

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
    "assign_family",
    "cluster_interventions",
    "extract_family_features",
    "diversity_score",
    "select_diverse_batch",
    "rank_with_diversity",
    "FamilyArchive",
    "EXPLORATION_POLICIES",
    "select_family",
]
