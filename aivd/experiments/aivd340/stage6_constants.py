"""AIVD 3.40 Stage-6 frozen constants (design tip ac152c6). OFFLINE only."""
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

DESIGN_TIP = "ac152c6"
STAGE5_COMPLETE_TIP = "c003e60"
STAGE5_DESIGN_TIP = "2496857"
STAGE4_COMPLETE_TIP = "4005e66"
STAGE3_TIP = "146915b"
STAGE2_TIP = "dcae889"

RECORD_SCHEMA_VERSION = "aivd340-stage6-ablation-1"
CLAIM_LABEL = "OFFLINE_REPAIR_BENCH"
PROVENANCE = "OFFLINE_EVAL"
IDENTITY_DEFAULT = "ab cd ef gh ij kl"

BODY_KEY_KEPT = "MAPT(CAT(AT:-1|AT:-1))"
BODY_KEY_REMOVED = ODD_CAT_SELF_BODY_KEY

S6_MAX_APPLY_MICRO_PER_PAIR = 24
S6_MAX_EXPANSION_CALLS = 8
S6_MAX_TOTAL_APPLY_MICRO_RUN = 5000
S6_AMBIGUOUS_AT_BUDGET_EXHAUSTION = True
S6_CORE_CONTEXT_COUNT = 20
S6_RESERVE_CONTEXT_COUNT = 8

DCR_MIN = 0.95
FDR_MAX = 0.05
MDR_MAX = 0.05
AR_MAX = 0.20
CRITICAL_HARD_COLLAPSE_MAX = 0
ADV_TS_COLLAPSE_MIN = 0.95
ADV_TD_HARD_COLLAPSE_MAX = 0.05

RB_MIN_AGREE_FAMILIES = 3
RB_AGREE_FAMILIES = ("TRANSFORMED", "ORDERING", "BOUNDARY", "COMPOSITION")
RD_SEMANTIC_FAMILIES = ("TRANSFORMED", "BOUNDARY", "COMPOSITION", "ORDERING")
RC_PROBE_P0 = ("CTX-TR-01", "CTX-BD-01", "CTX-CO-01", "CTX-OR-01")
IDENTITY_FAMILY = "BASELINE_IDENTITY"

MECHANISMS = ("BASELINE", "R-A", "R-B", "R-C", "R-D")

DESIGN_DOCS = (
    "reports/aivd_3_40_stage6_charter.md",
    "reports/aivd_3_40_stage6_hypothesis_tree.md",
    "reports/aivd_3_40_stage6_matrix.json",
    "reports/aivd_3_40_stage6_preregistration.md",
    "reports/aivd_3_40_stage6_equivalence_repair_spec.md",
    "reports/aivd_3_40_stage6_metrics.md",
)

REPO = Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO / "reports/aivd_3_40_stage6_matrix.json"


def load_matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text())


def _families(m: dict) -> dict:
    return m.get("context_families") or m["context_families"]


def pinned_core_bank(matrix: dict | None = None) -> list[tuple[str, str, str]]:
    m = matrix or load_matrix()
    fams = _families(m)
    out: list[tuple[str, str, str]] = []
    for fam in ("BASELINE_IDENTITY", "TRANSFORMED", "ORDERING", "BOUNDARY", "COMPOSITION"):
        for c in fams[fam]["contexts"]:
            prompt = c["prompt"]
            if c["context_id"] == "CTX-ID-02" and "ARTIFACT" in str(prompt):
                prompt = IDENTITY_DEFAULT
            out.append((c["context_id"], fam, prompt))
    if len(out) != S6_CORE_CONTEXT_COUNT:
        raise RuntimeError(f"core bank size {len(out)} != {S6_CORE_CONTEXT_COUNT}")
    return out


def reserve_bank(matrix: dict | None = None) -> list[tuple[str, str, str]]:
    m = matrix or load_matrix()
    fams = _families(m)
    out = [(c["context_id"], "RESERVE", c["prompt"]) for c in fams["RESERVE"]["contexts"]]
    if len(out) != S6_RESERVE_CONTEXT_COUNT:
        raise RuntimeError(f"reserve bank size {len(out)} != {S6_RESERVE_CONTEXT_COUNT}")
    return out


def context_bank_hash(core, reserve) -> str:
    blob = json.dumps(
        {
            "core": [{"id": a, "family": b, "prompt": c} for a, b, c in core],
            "reserve": [{"id": a, "family": b, "prompt": c} for a, b, c in reserve],
        },
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()
