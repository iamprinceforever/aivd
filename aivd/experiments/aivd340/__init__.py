"""AIVD 3.40 budget × representation experiment framework (Step 1+).

Sacred TinyLlama factorial is NOT executed from this package at Step 1+.
Absolute 3.38/3.39 sacred semantics remain immutable.
"""
from __future__ import annotations

from aivd.experiments.aivd340.condition import (
    BH_BUDGET,
    B32_BUDGET,
    CONTROL_IDS,
    FACTORIAL_CELLS,
    ExperimentCondition,
    condition_from_id,
    locked_seeds,
)
from aivd.experiments.aivd340.manifest import load_manifest, write_manifest
from aivd.experiments.aivd340.runner import ConditionRunner, ConditionMixError

__all__ = [
    "BH_BUDGET",
    "B32_BUDGET",
    "CONTROL_IDS",
    "FACTORIAL_CELLS",
    "ExperimentCondition",
    "condition_from_id",
    "locked_seeds",
    "load_manifest",
    "write_manifest",
    "ConditionRunner",
    "ConditionMixError",
]
