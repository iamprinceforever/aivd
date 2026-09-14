"""AIVD 3.9 Open Intervention Invention.

Sits ABOVE 3.6 causal, BEFORE residual sweep / investigation.
Config: invention_mode = off | random | heuristic | full (default off).
Novelty alone is NOT rewarded. No Holdout-X/Y special-case solutions.
"""
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.candidate_generator import generate_candidates
from aivd.invention.scoring import score_intervention, rank_candidates
from aivd.invention.audit import scan_invention_source, novelty_audit_record

__all__ = [
    "InventionController",
    "Intervention",
    "InterventionOp",
    "generate_candidates",
    "score_intervention",
    "rank_candidates",
    "scan_invention_source",
    "novelty_audit_record",
]
