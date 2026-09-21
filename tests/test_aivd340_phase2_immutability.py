"""Phase-2 must not mutate frozen historical report artifacts."""
from __future__ import annotations

import subprocess
from pathlib import Path

DESIGN_TIP = "7be4124"

FROZEN_GLOBS = [
    "reports/aivd_3_40_phase2_charter.md",
    "reports/aivd_3_40_phase2_matrix.json",
    "reports/aivd_3_40_phase2_preregistration.md",
    "reports/aivd_3_40_phase2_instrumentation_spec.md",
    "reports/aivd_3_40_phase1_results.md",
    "reports/aivd_3_40_phase1_results.json",
    "reports/aivd_3_40_stage2/results.json",
    "reports/aivd_3_40_stage2/results.md",
    "reports/aivd_3_40_stage3_charter.md",
]


def test_design_docs_match_tip_blobs():
    for path in FROZEN_GLOBS[:4]:
        tip_hash = subprocess.check_output(
            ["git", "rev-parse", f"{DESIGN_TIP}:{path}"], text=True
        ).strip()
        work_hash = subprocess.check_output(["git", "hash-object", path], text=True).strip()
        assert tip_hash == work_hash, path


def test_no_diff_against_tip_for_stage2_phase1_stage3_trees():
    out = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            DESIGN_TIP,
            "--",
            "reports/aivd_3_40_stage2",
            "reports/aivd_3_40_phase1_results.md",
            "reports/aivd_3_40_phase1_results.json",
            "reports/aivd_3_40_phase1/",
            "reports/aivd_3_40_stage3_charter.md",
            "reports/aivd_3_40_stage3_counterfactual_replay_spec.md",
            "reports/aivd_3_40_stage3_experimental_matrix.json",
            "reports/aivd_3_40_stage3_experimental_matrix.md",
            "reports/aivd_3_40_stage3_hypothesis_tree.md",
            "reports/aivd_3_40_stage3_instrumentation_spec.md",
        ],
        text=True,
    ).strip()
    # Allow only if working tree has no modifications to these paths vs tip content
    # (new untracked phase2 outputs are fine). Diff vs tip should be empty for frozen files.
    assert out == "", out


def test_propose_atoms_still_has_eight_frozen_keys():
    from aivd.science.atom_synth import propose_atoms

    keys = [a.key() for a in propose_atoms(prompt="ab cd ef gh", question=True)]
    assert len(keys) == 8
    assert "MAPT(SLICE:1,2(TOK))" in keys
