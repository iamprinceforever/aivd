"""AIVD 3.45 Sacred validation — locked constants (authorized envelope)."""
from __future__ import annotations

from pathlib import Path

# Implementation freeze (science must match for FIX / 3.45 condition)
IMPL_FREEZE = "52394b8"
IMPL_FREEZE_FULL = "52394b8f5f802047ffc9029910e0b0de5d110f01"
BASELINE_TIP = "72edfad"
BASELINE_TIP_FULL = "72edfadeda87c0ea6ac966487c49b9526099c613"
ADVERSARIAL_TIP = "73087ef"

SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)
EPISODE_BUDGET = 32  # B32 — authorized; NOT BH48
INVENT_CAP_EXPECTED = 48
REDISCOVERY_FLOOR_EXPECTED = 5
REPRESENTATION = "R1"
INVENTION_MODE = "full_3_39_r1"
BUDGET_LEVEL = "B32"
CONDITION_ID = "B32-R1"

CONDITIONS: tuple[str, ...] = ("BASELINE", "AIVD345")
PLANT_ID = "AIVD345-SACRED-ODDSTRIDE"

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "reports" / "aivd_3_45_sacred"
RESULTS_MD = REPO / "reports" / "aivd_3_45_sacred_results.md"
RESULTS_JSON = REPO / "reports" / "aivd_3_45_sacred_results.json"

BASELINE_WORKTREE = Path("/workspace/aivd-345-baseline-72edfad")
PRIMARY_WORKTREE = Path("/workspace/aivd-340-replication")
MODEL_PATH = "/workspace/models/tinyllama"
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

AUTHORIZATION = (
    "AIVD 3.45 SACRED VALIDATION — AUTHORIZED: B32-R1 TinyLlama Sacred; "
    "seeds[0,1,2,3,4,7,11]; invent_cap=48; REDISCOVERY_FLOOR=5; "
    "BASELINE@72edfad vs FIX science@52394b8; fresh plant "
    f"{PLANT_ID}; no retune; no 3.46; no S/ODD/MAPT injection."
)

# Measurement axes 1–9 (pipeline stages; no overall score)
AXES = (
    "1_proposal",
    "2_scoring",
    "3_ranking",
    "4_selection",
    "5_materialization",
    "6_invention",
    "7_verification",
    "8_recursive_growth",
    "9_independence",
)

__all__ = [
    "IMPL_FREEZE",
    "IMPL_FREEZE_FULL",
    "BASELINE_TIP",
    "BASELINE_TIP_FULL",
    "ADVERSARIAL_TIP",
    "SEEDS",
    "EPISODE_BUDGET",
    "INVENT_CAP_EXPECTED",
    "REDISCOVERY_FLOOR_EXPECTED",
    "REPRESENTATION",
    "INVENTION_MODE",
    "BUDGET_LEVEL",
    "CONDITION_ID",
    "CONDITIONS",
    "PLANT_ID",
    "REPO",
    "OUT_DIR",
    "RESULTS_MD",
    "RESULTS_JSON",
    "BASELINE_WORKTREE",
    "PRIMARY_WORKTREE",
    "MODEL_PATH",
    "MODEL_ID",
    "AUTHORIZATION",
    "AXES",
]
