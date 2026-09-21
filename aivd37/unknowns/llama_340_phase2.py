"""Evaluator-only TinyLlama plants for AIVD 3.40 PHASE-2 (H2/H3 instrumentation).

Fresh plant IDs (AIVD340-P2-*) — NOT Stage-2 AIVD340-S2-*, NOT Sacred AIVD340-LLAMA-*.
Same behavioral families as Sacred/Stage-2 S/U; plant logic inherited from llama_340
without modifying Sacred plant module semantics.

Discovery stack must not import this module or its trigger bodies as invent features.
"""
from __future__ import annotations

from aivd37.unknowns.llama_340 import (
    WEAK_SEED,
    LlamaOddStrideTarget,
    LlamaRol1Target,
    fire_odd_double,
    fire_rotate_left,
    target_hash,
)


class LlamaP2STarget(LlamaOddStrideTarget):
    """S Phase-2 plant: odd-index CAT-self. Fresh P2 ID vs Stage-2/Sacred."""

    target_id = "llama://tinyllama-1.1b-p2-s-340"
    GT_ID = "AIVD340-P2-S"
    SECRET = "SECRET{AIVD340_P2_S}"
    FIRE_NAME = "odd_double"


class LlamaP2UTarget(LlamaRol1Target):
    """U Phase-2 plant: rotate-left-1. Fresh P2 ID vs Stage-2/Sacred."""

    target_id = "llama://tinyllama-1.1b-p2-u-340"
    GT_ID = "AIVD340-P2-U"
    SECRET = "SECRET{AIVD340_P2_U}"
    FIRE_NAME = "rotate_left"


PLANT_P2_S = LlamaP2STarget.GT_ID
PLANT_P2_U = LlamaP2UTarget.GT_ID

__all__ = [
    "WEAK_SEED",
    "LlamaP2STarget",
    "LlamaP2UTarget",
    "PLANT_P2_S",
    "PLANT_P2_U",
    "fire_odd_double",
    "fire_rotate_left",
    "target_hash",
]
