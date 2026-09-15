"""AIVD 3.20 — Autonomous Hypothesis Science.

Default off ≈ 3.19. No holdout-specific rules. No vulnerability signatures.
No planted cue following. Generic operators + hypothesis discrimination
under the same 32-experiment budget.
"""
from aivd.science.scheduler import SCIENCE_MODES, is_science_mode
from aivd.science.operators import OPERATORS, BATTERY, apply_operator, apply_sequence
from aivd.science.hypotheses import HypState, ScienceHypothesis, HypothesisBoard
from aivd.science.contrast import Contrast, contrast
from aivd.science.designer import ScienceDesigner
from aivd.science.proposers import ScienceProposer
from aivd.science.controller import ScienceController
from aivd.science.report import VulnerabilityReport, build_report
from aivd.science.audit import scan_science_source
from aivd.science.health import health_check

__all__ = [
    "SCIENCE_MODES",
    "is_science_mode",
    "OPERATORS",
    "BATTERY",
    "apply_operator",
    "apply_sequence",
    "HypState",
    "ScienceHypothesis",
    "HypothesisBoard",
    "Contrast",
    "contrast",
    "ScienceDesigner",
    "ScienceProposer",
    "ScienceController",
    "VulnerabilityReport",
    "build_report",
    "scan_science_source",
    "health_check",
]
