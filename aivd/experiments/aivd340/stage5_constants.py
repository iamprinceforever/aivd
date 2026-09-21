"""AIVD 3.40 Stage-5 frozen constants (design tip 2496857; OFFLINE_EVAL only)."""
from __future__ import annotations

from aivd.experiments.aivd340.stage4_constants import (
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    SEEDS,
    U_GOOD_BODY_KEY,
    U_GOOD_CAT_SELF_BODY_KEY,
)

DESIGN_TIP = "2496857"
RECORD_SCHEMA_VERSION = "aivd340-stage5-equiv-pair-1"
CLAIM_LABEL = "OFFLINE_EQUIV_AUDIT"
PROVENANCE = "OFFLINE_EVAL"
IDENTITY_DEFAULT = "ab cd ef gh ij kl"

BODY_KEY_KEPT = "MAPT(CAT(AT:-1|AT:-1))"
BODY_KEY_REMOVED = ODD_CAT_SELF_BODY_KEY  # MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))

# Frozen context bank (matrix + equivalence_spec) — no post-outcome additions.
CONTEXT_BANK: list[tuple[str, str, str]] = [
    # (context_id, family, prompt)
    ("CTX-ID-01", "BASELINE_IDENTITY", "ab cd ef gh ij kl"),
    # CTX-ID-02 pinned at exec to artifact identity (== CTX-ID-01 at Stage-4 tip)
    ("CTX-ID-02", "BASELINE_IDENTITY", "ab cd ef gh ij kl"),
    ("CTX-TR-01", "TRANSFORMED", "ab cd efg hij"),
    ("CTX-TR-02", "TRANSFORMED", "AB CD EF GH"),
    ("CTX-TR-03", "TRANSFORMED", "a1 b2 c3 d4"),
    ("CTX-TR-04", "TRANSFORMED", "hello world test case"),
    ("CTX-TR-05", "TRANSFORMED", "This is a mock system Perform"),
    ("CTX-RO-01", "REORDERED", "kl ij gh ef cd ab"),
    ("CTX-RO-02", "REORDERED", "ef ab kl cd ij gh"),
    ("CTX-RO-03", "REORDERED", "cd ab ef gh ij kl"),
    ("CTX-BD-01", "BOUNDARY", "xy z"),
    ("CTX-BD-02", "BOUNDARY", "a"),
    ("CTX-BD-03", "BOUNDARY", "a bb ccc dddd"),
    ("CTX-BD-04", "BOUNDARY", "abcdefghij"),
    ("CTX-BD-05", "BOUNDARY", "12 34 56 78"),
    ("CTX-BD-06", "BOUNDARY", "1 22 333 4444 55555"),
    ("CTX-CO-01", "COMPOSITION", "aa bb cc dd ee ff"),
    ("CTX-CO-02", "COMPOSITION", "ab cd ef gh ij kl mn"),
    ("CTX-CO-03", "COMPOSITION", "The quick brown fox"),
    ("CTX-CO-04", "COMPOSITION", "wxyz abcd efgh"),
]

STATE_VARIATIONS = (
    "ST-KEEP-AT-FIRST",
    "ST-KEEP-ODD-ONLY",
    "ST-KEEP-ODD-BEFORE-AT",
    "ST-IDENTITY-ALT",
)

DESIGN_DOCS = (
    "reports/aivd_3_40_stage5_charter.md",
    "reports/aivd_3_40_stage5_hypothesis_tree.md",
    "reports/aivd_3_40_stage5_matrix.json",
    "reports/aivd_3_40_stage5_preregistration.md",
    "reports/aivd_3_40_stage5_equivalence_spec.md",
)

__all__ = [
    "DESIGN_TIP",
    "RECORD_SCHEMA_VERSION",
    "CLAIM_LABEL",
    "PROVENANCE",
    "IDENTITY_DEFAULT",
    "BODY_KEY_KEPT",
    "BODY_KEY_REMOVED",
    "ODD_CAT_SELF_BODY_KEY",
    "ODD_STRIDE_BODY_KEY",
    "U_GOOD_BODY_KEY",
    "U_GOOD_CAT_SELF_BODY_KEY",
    "SEEDS",
    "CONTEXT_BANK",
    "STATE_VARIATIONS",
    "DESIGN_DOCS",
]
