"""Commit E — Stage-2 mock validation gates."""
from __future__ import annotations

from pathlib import Path

from aivd.experiments.aivd340.stage2_mock import run_stage2_mock_report


def test_stage2_mock_report_green():
    report = run_stage2_mock_report(out_dir=Path("reports/aivd_3_40_stage2_mock"))
    assert report["sacred_tinyllama_executed"] is False
    assert report["stage1_controls_all_pass"] is True
    assert report["r1_unchanged"] is True
    assert report["r1b_per_spec"] is True
    assert report["stage2"]["n_episodes"] == 12  # 2 cells × 3 seeds × 2 roles
    assert Path("reports/aivd_3_40_stage2_mock/REPORT.md").is_file()
    assert Path("reports/aivd_3_40_stage2_mock/stage2_mock_matrix.json").is_file()
