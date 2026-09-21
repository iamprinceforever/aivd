"""AIVD 3.40 Stage-8 frozen constants (design tip 129a2e9). EXECUTION authorized."""
from __future__ import annotations

from pathlib import Path

DESIGN_TIP = "129a2e9"
DESIGN_TIP_FULL = "129a2e96bf5de6d57fb3883b0f19b9c689b329c5"
STAGE7_COMPLETE_TIP = "079d66f"
STAGE7_COMPLETE_FULL = "079d66f949991b6adbc000b85d0f01fe33bf609a"
STAGE4_GROW_TIP = "4005e66"

SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)
BH = 48
INVENT_CAP = 48
REDISCOVERY_FLOOR_EXPECTED = 5
REPRESENTATION = "R1"
INVENTION_MODE = "full_3_39_r1"

CONDITIONS: tuple[str, ...] = ("S8-BASELINE", "S8-RA", "S8-RC", "S8-RD")
CONDITION_FAMILY = {
    "S8-BASELINE": "BASELINE",
    "S8-RA": "R-A",
    "S8-RC": "R-C",
    "S8-RD": "R-D",
}
PLANT_IDS = {
    "S8-BASELINE": "AIVD340-S8-BASELINE",
    "S8-RA": "AIVD340-S8-RA",
    "S8-RC": "AIVD340-S8-RC",
    "S8-RD": "AIVD340-S8-RD",
}
EXCLUDED = ("R-B",)

# Repair evaluator ledger (separate from Sacred BH)
S8_MAX_APPLY_MICRO_PER_PAIR = 24
S8_MAX_EXPANSION_CALLS = 8
S8_MAX_TOTAL_APPLY_MICRO_EPISODE = 20000

MECHANISM_FATES = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "UNOBSERVED")
D_RATE_DELTA = 0.05  # absolute

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "reports" / "aivd_3_40_stage8"
STAGE7_FREEZE_PATH = REPO / "reports" / "aivd_3_40_stage7_execution_freeze.json"

AUTHORIZATION = (
    "STAGE-8 EXECUTION AUTHORIZATION: live _keep step-6 wiring per "
    "integration_spec for S8-RA/S8-RC/S8-RD ONLY; Sacred TinyLlama fresh-plant "
    "matrix BH48 invent_cap=48 REDISCOVERY_FLOOR=5 seeds[0,1,2,3,4,7,11]; "
    "FORBID R-B revival / retune / single-winner / combined / BH raise / floor lower / "
    "odd-atom injection / 3.38-3.39 mutation / post-hoc seeds / success:=S alone."
)

__all__ = [
    "DESIGN_TIP",
    "DESIGN_TIP_FULL",
    "STAGE7_COMPLETE_TIP",
    "SEEDS",
    "BH",
    "INVENT_CAP",
    "REDISCOVERY_FLOOR_EXPECTED",
    "REPRESENTATION",
    "INVENTION_MODE",
    "CONDITIONS",
    "CONDITION_FAMILY",
    "PLANT_IDS",
    "EXCLUDED",
    "S8_MAX_APPLY_MICRO_PER_PAIR",
    "S8_MAX_EXPANSION_CALLS",
    "S8_MAX_TOTAL_APPLY_MICRO_EPISODE",
    "MECHANISM_FATES",
    "D_RATE_DELTA",
    "REPO",
    "OUT_DIR",
    "STAGE7_FREEZE_PATH",
    "AUTHORIZATION",
]
