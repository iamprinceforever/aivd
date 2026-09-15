"""AIVD 3.12 — Open Interaction Discovery (Level 3).

Discover when 2+ independently explored interventions become
security-relevant only when combined.

Config: interaction_mode / invention modes interaction|interaction_full (default off).
No Holdout-named rules; no Z/Q hardcoding; additive ≠ security interaction.
"""
from aivd.interaction.representation import InteractionCandidate, GENERATION_STRATEGIES, INTERACTION_KINDS
from aivd.interaction.pair_generator import generate_pairs, generate_triples
from aivd.interaction.composition import compose_interaction
from aivd.interaction.interaction_score import score_interaction, rank_interactions, score_terms
from aivd.interaction.counterfactual import discriminate
from aivd.interaction.screening import cheap_screen
from aivd.interaction.scheduler import InteractionScheduler, is_interaction_mode, INTERACTION_MODES
from aivd.interaction.memory import InteractionMemory
from aivd.interaction.synergy import classify_synergy, expected_additive, interaction_residual
from aivd.interaction.audit import (
    scan_interaction_source,
    interaction_audit_record,
    anti_z_benchmark_spec,
)
from aivd.interaction.controller import InteractionDiscoveryController
from aivd.interaction.traces import InteractionTrace

__all__ = [
    "InteractionCandidate",
    "GENERATION_STRATEGIES",
    "INTERACTION_KINDS",
    "generate_pairs",
    "generate_triples",
    "compose_interaction",
    "score_interaction",
    "rank_interactions",
    "score_terms",
    "discriminate",
    "cheap_screen",
    "InteractionScheduler",
    "is_interaction_mode",
    "INTERACTION_MODES",
    "InteractionMemory",
    "classify_synergy",
    "expected_additive",
    "interaction_residual",
    "scan_interaction_source",
    "interaction_audit_record",
    "anti_z_benchmark_spec",
    "InteractionDiscoveryController",
    "InteractionTrace",
]
