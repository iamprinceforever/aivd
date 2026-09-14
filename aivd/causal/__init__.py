"""AIVD 3.6 Unknown Dimension / Active Causal Discovery.

Sits ABOVE 3.5 Active Behavioral Discovery. Does not replace explorers,
memory, PPO, verifier, 3.4 investigation, or 3.5 discovery.
"""
from aivd.causal.hypotheses import Hypothesis, HypothesisSpace, HypothesisStatus
from aivd.causal.unknown_dimension import (
    UNKNOWN_DIMENSION,
    KNOWN_DIMENSION_CANDIDATES,
    candidate_space,
    generate_dimension_experiments,
)
from aivd.causal.causal_graph import CausalGraph
from aivd.causal.discrimination import NWayDiscriminator
from aivd.causal.causal_controller import CausalController, CausalMode
from aivd.causal.metrics import summarize_causal

__all__ = [
    "Hypothesis",
    "HypothesisSpace",
    "HypothesisStatus",
    "UNKNOWN_DIMENSION",
    "KNOWN_DIMENSION_CANDIDATES",
    "candidate_space",
    "generate_dimension_experiments",
    "CausalGraph",
    "NWayDiscriminator",
    "CausalController",
    "CausalMode",
    "summarize_causal",
]
