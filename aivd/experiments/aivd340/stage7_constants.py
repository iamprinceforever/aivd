"""AIVD 3.40 Stage-7 frozen constants. OFFLINE_GENERALIZATION_BENCH / IMPL_VALIDATION only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aivd.experiments.aivd340.stage4_constants import (
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    SEEDS,
    U_GOOD_BODY_KEY,
    U_GOOD_CAT_SELF_BODY_KEY,
)

DESIGN_TIP = "d0ef7b6"
DESIGN_TIP_FULL = "d0ef7b64c7981ab900b9e5049fc65fd47211ca29"
STAGE6_COMPLETE_TIP = "000a4d8"
STAGE6_DESIGN_TIP = "ac152c6"
STAGE5_COMPLETE_TIP = "c003e60"
STAGE4_COMPLETE_TIP = "4005e66"

RECORD_SCHEMA_PHASE_A = "aivd340-stage7-phaseA-ablation-1"
RECORD_SCHEMA_PHASE_B = "aivd340-stage7-phaseB-equivalence-1"
CLAIM_LABEL_A = "OFFLINE_GENERALIZATION_BENCH"
CLAIM_LABEL_B = "IMPL_SPEC_EQUIVALENCE"
PROVENANCE = "OFFLINE_EVAL"
IDENTITY_DEFAULT = "ab cd ef gh ij kl"

# Critical-class keys (RELATED / S_DIAGNOSTIC only — never INDEPENDENT)
CRITICAL_BODY_KEYS = frozenset(
    {
        ODD_STRIDE_BODY_KEY,
        ODD_CAT_SELF_BODY_KEY,
        U_GOOD_CAT_SELF_BODY_KEY,
    }
)

S7_MAX_APPLY_MICRO_PER_PAIR = 24
S7_MAX_EXPANSION_CALLS = 8
S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A = 5000
S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B = 5000
S7_AMBIGUOUS_AT_BUDGET_EXHAUSTION = True
S7_RESERVE_CONTEXT_COUNT_MAX = 8
S7_CALLS_MEAN_MAX = 4.0
S7_CALLS_WORST_MAX = 24

DCR_MIN = 0.95
FDR_MAX = 0.05
MDR_MAX = 0.05
AR_MAX = 0.20
ADV_TS_COLLAPSE_MIN = 0.95
ADV_TD_HARD_COLLAPSE_MAX = 0.05

# Continuity with Stage-6 family algorithms (ac152c6) — no semantic change
RB_MIN_AGREE_FAMILIES = 3
RB_AGREE_FAMILIES = ("TRANSFORMED", "ORDERING", "BOUNDARY", "COMPOSITION")
RD_SEMANTIC_FAMILIES = ("TRANSFORMED", "BOUNDARY", "COMPOSITION", "ORDERING")
RC_PROBE_P0 = ("CTX-TR-01", "CTX-BD-01", "CTX-CO-01", "CTX-OR-01")
IDENTITY_FAMILY = "BASELINE_IDENTITY"

MECHANISMS = ("BASELINE", "R-A", "R-B", "R-C", "R-D")
STAGE6_BANK_HASH_REF = "bd8cf523e5723d371dec85526199287648a290fc3abde1477ac350b01329c862"

REQUIRED_FAMILIES = (
    "BASELINE_IDENTITY",
    "TRANSFORMED",
    "BOUNDARY",
    "COMPOSITION",
    "ORDERING",
    "STATE_CONTEXT",
)

DESIGN_DOCS = (
    "reports/aivd_3_40_stage7_charter.md",
    "reports/aivd_3_40_stage7_hypothesis_tree.md",
    "reports/aivd_3_40_stage7_matrix.json",
    "reports/aivd_3_40_stage7_preregistration.md",
    "reports/aivd_3_40_stage7_generalization_spec.md",
    "reports/aivd_3_40_stage7_implementation_validation_spec.md",
    "reports/aivd_3_40_stage7_metrics.md",
)

REPO = Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO / "reports/aivd_3_40_stage7_matrix.json"
FREEZE_PATH = REPO / "reports/aivd_3_40_stage7_execution_freeze.json"
RESULTS_JSON = REPO / "reports/aivd_3_40_stage7_results.json"
RESULTS_MD = REPO / "reports/aivd_3_40_stage7_results.md"

POP = {
    "TRUE_DUP": "P_TD",
    "KNOWN_NONDUP": "P_ND",
    "CONTEXT_DEPENDENT": "P_CD",
    "TEXT_EQ_BEH_DIFF": "P_TEBD",
    "TEXT_DIFF_BEH_EQ": "P_TDBE",
    "STATE_CONTEXT_SENSITIVE": "P_ST",
    "COMPOSITION_SENSITIVE": "P_CO",
    "U_GOOD": "P_UG",
    "ADV_TEXT_DIFF_BEH_SAME": "P_ADV_TS",
    "ADV_TEXT_SIM_BEH_DIFF": "P_ADV_TD",
    "S6_REPLAY": "P_REPLAY",
    "RELATED": "P_REL",
    "S_DIAGNOSTIC": "P_SDIAG",
}


def sha256_json(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
