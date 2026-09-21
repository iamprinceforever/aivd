"""Stage-4 must not mutate frozen historical artifacts."""
from __future__ import annotations

import subprocess
from pathlib import Path

FROZEN = [
    ("f4d7a2b", "reports/aivd_3_40_phase2_results.json"),
    ("f4d7a2b", "reports/aivd_3_40_phase2_results.md"),
    ("f4d7a2b", "reports/aivd_3_40_phase2_charter.md"),
    ("a2ab0cc", "reports/aivd_3_40_phase1_results.json"),
    ("146915b", "reports/aivd_3_40_stage3_charter.md"),
    ("dcae889", "reports/aivd_3_40_stage2_results.md"),
]


def test_frozen_reports_match_ancestor_blobs():
    for tip, path in FROZEN:
        if not Path(path).exists():
            continue
        tip_hash = subprocess.check_output(["git", "rev-parse", f"{tip}:{path}"], text=True).strip()
        work_hash = subprocess.check_output(["git", "hash-object", path], text=True).strip()
        assert tip_hash == work_hash, f"{path} drifted from {tip}"


def test_stage4_design_docs_still_match_27e9e88():
    for path in [
        "reports/aivd_3_40_stage4_charter.md",
        "reports/aivd_3_40_stage4_hypothesis_tree.md",
        "reports/aivd_3_40_stage4_matrix.json",
        "reports/aivd_3_40_stage4_instrumentation_spec.md",
        "reports/aivd_3_40_stage4_preregistration.md",
    ]:
        tip = subprocess.check_output(["git", "rev-parse", f"27e9e88:{path}"], text=True).strip()
        work = subprocess.check_output(["git", "hash-object", path], text=True).strip()
        assert tip == work
