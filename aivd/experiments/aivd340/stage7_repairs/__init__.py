"""Isolated Stage-7 repair modules — NOT live FILTER_BEHAVIORAL_DUP / grow.py.

Faithful re-export of Stage-6 family algorithms (ac152c6) for Phase-B
offline↔executable equivalence. Discovery entrypoints must not import this package.
"""
from aivd.experiments.aivd340.stage7_repairs.classifiers import (
    CLASSIFIERS,
    classify_baseline,
    classify_r_a,
    classify_r_b,
    classify_r_c,
    classify_r_d,
    classify_pair,
)

__all__ = [
    "CLASSIFIERS",
    "classify_baseline",
    "classify_r_a",
    "classify_r_b",
    "classify_r_c",
    "classify_r_d",
    "classify_pair",
]
