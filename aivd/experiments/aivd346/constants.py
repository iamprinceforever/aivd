"""AIVD 3.46 budget-frontier validation — locked preregistered constants."""
from __future__ import annotations

from pathlib import Path

# FIX science freeze (must remain unmodified — same as 3.45)
IMPL_FREEZE = "52394b8"
IMPL_FREEZE_FULL = "52394b8f5f802047ffc9029910e0b0de5d110f01"
BASELINE_TIP = "72edfad"
BASELINE_TIP_FULL = "72edfadeda87c0ea6ac966487c49b9526099c613"

SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)

# Preregistered frontier (justified) — DO NOT expand without charter
FRONTIER_BUDGETS: tuple[tuple[str, int], ...] = (
    ("B32", 32),  # 3.45 Sacred wall: leftover 3 < floor 5
    ("B40", 40),  # intermediate above wall
    ("B48", 48),  # Stage-8 BH envelope
    ("B64", 64),  # upper bound; not unlimited
)

INVENT_CAP_EXPECTED = 48
REDISCOVERY_FLOOR_EXPECTED = 5
REPRESENTATION = "R1"
INVENTION_MODE = "full_3_39_r1"

CONDITIONS: tuple[str, ...] = ("BASELINE", "FIX")
PLANT_FAMILY = "AIVD346-FRONTIER-ODDSTRIDE"  # same odd-stride family as 3.45

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "reports" / "aivd_3_46_sacred"
RESULTS_MD = REPO / "reports" / "aivd_3_46_frontier_results.md"
RESULTS_JSON = REPO / "reports" / "aivd_3_46_frontier_results.json"
PREREG_MD = REPO / "reports" / "aivd_3_46_preregistration.md"
PREREG_MATRIX = REPO / "reports" / "aivd_3_46_matrix.json"

BASELINE_WORKTREE = Path("/workspace/aivd-345-baseline-72edfad")
PRIMARY_WORKTREE = Path("/workspace/aivd-340-replication")
MODEL_PATH = "/workspace/models/tinyllama"
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

AUTHORIZATION = (
    "AIVD 3.46 BUDGET-FRONTIER VALIDATION — AUTHORIZED: "
    "frontier B32/B40/B48/B64; R1 TinyLlama; seeds[0,1,2,3,4,7,11]; "
    "invent_cap=48; REDISCOVERY_FLOOR=5; BASELINE@72edfad vs FIX science@52394b8; "
    f"fresh plant family {PLANT_FAMILY} (new plant_ids per cell); "
    "no retune; no 3.45 science edits; no S/ODD/MAPT injection; "
    "primary metric explore_n; freeze at first activation."
)

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
    "SEEDS",
    "FRONTIER_BUDGETS",
    "INVENT_CAP_EXPECTED",
    "REDISCOVERY_FLOOR_EXPECTED",
    "REPRESENTATION",
    "INVENTION_MODE",
    "CONDITIONS",
    "PLANT_FAMILY",
    "REPO",
    "OUT_DIR",
    "RESULTS_MD",
    "RESULTS_JSON",
    "PREREG_MD",
    "PREREG_MATRIX",
    "BASELINE_WORKTREE",
    "PRIMARY_WORKTREE",
    "MODEL_PATH",
    "MODEL_ID",
    "AUTHORIZATION",
    "AXES",
]
