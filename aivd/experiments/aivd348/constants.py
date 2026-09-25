"""Locked constants for AIVD 3.48 sacred invent-cap validation. Evaluator only."""
from __future__ import annotations

from pathlib import Path

IMPL = "b1b7106"
IMPL_FULL = "b1b71068a79944341fb23540c4f1f19386eb4d50"
GATE = "da0ce85"
GATE_FULL = "da0ce8555a8fe1ba2b281ff7f00f8c1f814f2a35"
INTEGRITY = "0da689e"
INTEGRITY_FULL = "0da689e78691302f8ef922a307cf6aa0b879f114"
SCIENCE_FREEZE = "52394b8"
SCIENCE_FREEZE_FULL = "52394b8f5f802047ffc9029910e0b0de5d110f01"

SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)
EPISODE_BUDGET = 48
INVENT_CAP_EXPECTED = 48
REDISCOVERY_FLOOR_EXPECTED = 5
INVENTION_MODE = "full_3_39_r1"
CONDITIONS: tuple[str, ...] = ("BASELINE", "FIX")
PLANT_FAMILY = "AIVD348-ANTISTARVE-ODDSTRIDE"
ODD_KEY = "MAPT(SLICE:1,2(TOK))"
ALLOWED_RELEASE_KINDS = (
    "rediscovery_redundant",
    "independent_rediscovery",
    "class_redundant",
    "final_nonlease_fallback",
)

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "reports" / "aivd_3_48_sacred"
RESULTS_MD = REPO / "reports" / "aivd_3_48_sacred_results.md"
RESULTS_JSON = REPO / "reports" / "aivd_3_48_sacred_results.json"
BASELINE_WORKTREE = Path("/tmp/aivd-348-baseline")
MODEL_PATH = "/workspace/models/tinyllama"
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
SCIENCE_FILES = (
    "aivd/science/designer.py",
    "aivd/science/exploration_alloc.py",
    "aivd/science/grow.py",
    "aivd/science/methods.py",
    "aivd/science/atom_synth.py",
)
