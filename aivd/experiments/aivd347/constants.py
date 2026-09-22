"""AIVD 3.47 exploration-value validation — locked preregistered constants."""
from __future__ import annotations

from pathlib import Path

# FIX science freeze (must remain unmodified — same as 3.45/3.46)
IMPL_FREEZE = "52394b8"
IMPL_FREEZE_FULL = "52394b8f5f802047ffc9029910e0b0de5d110f01"
BASELINE_TIP = "72edfad"
BASELINE_TIP_FULL = "72edfadeda87c0ea6ac966487c49b9526099c613"

SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)

# Sacred TinyLlama matched B48 only (no B64, no retune)
BUDGET_LEVEL = "B48"
EPISODE_BUDGET = 48
INVENT_CAP_EXPECTED = 48
REDISCOVERY_FLOOR_EXPECTED = 5
REPRESENTATION = "R1"
INVENTION_MODE = "full_3_39_r1"
CONDITION_ID = "B48-R1"

CONDITIONS: tuple[str, ...] = ("BASELINE", "FIX")
PLANT_FAMILY = "AIVD347-EXPLVAL-ODDSTRIDE"  # same odd-stride family; new plant_ids

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "reports" / "aivd_3_47_sacred"
RESULTS_MD = REPO / "reports" / "aivd_3_47_exploration_value.md"
RESULTS_JSON = REPO / "reports" / "aivd_3_47_exploration_value.json"
PREREG_MD = REPO / "reports" / "aivd_3_47_preregistration.md"
PREREG_MATRIX = REPO / "reports" / "aivd_3_47_matrix.json"

BASELINE_WORKTREE = Path("/workspace/aivd-345-baseline-72edfad")
PRIMARY_WORKTREE = Path("/workspace/aivd-340-replication")
MODEL_PATH = "/workspace/models/tinyllama"
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

AUTHORIZATION = (
    "AIVD 3.47 EXPLORATION-VALUE VALIDATION — AUTHORIZED: "
    "Sacred TinyLlama matched B48 only; invent_cap=48; REDISCOVERY_FLOOR=5; R1; "
    "seeds[0,1,2,3,4,7,11]; BASELINE@72edfad vs FIX science@52394b8; "
    f"fresh plant family {PLANT_FAMILY} (new plant_ids per cell); "
    "no retune; no B64; no 3.45/3.46 science edits; no S/ODD/MAPT injection; "
    "primary question: useful behavioral coverage vs number of constructions; "
    "separate A/B/C/D (never collapse)."
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

# A/B/C/D — never collapse
ABCD = (
    "A_NEW_LANGUAGE_CONSTRUCTION",
    "B_NEW_BEHAVIORAL_DIMENSION",
    "C_SECURITY_RELEVANT_BEHAVIOR",
    "D_VERIFIED_SECURITY_FINDING",
)

SECURITY_LABELS = (
    "NOVEL_LANGUAGE_ONLY",
    "NOVEL_BEHAVIOR",
    "NOVEL_SECURITY_BEHAVIOR",
    "VERIFIED_SECURITY_FINDING",
    "NOT_SECURITY_RELEVANT",
)

__all__ = [
    "IMPL_FREEZE",
    "IMPL_FREEZE_FULL",
    "BASELINE_TIP",
    "BASELINE_TIP_FULL",
    "SEEDS",
    "BUDGET_LEVEL",
    "EPISODE_BUDGET",
    "INVENT_CAP_EXPECTED",
    "REDISCOVERY_FLOOR_EXPECTED",
    "REPRESENTATION",
    "INVENTION_MODE",
    "CONDITION_ID",
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
    "ABCD",
    "SECURITY_LABELS",
]
