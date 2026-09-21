#!/usr/bin/env python3
"""Run AIVD 3.40 Stage-2 mock validation. Does NOT run Sacred TinyLlama."""
from __future__ import annotations

from aivd.experiments.aivd340.stage2_mock import run_stage2_mock_report


def main() -> None:
    report = run_stage2_mock_report()
    print("sacred", report["sacred_tinyllama_executed"])
    print("r1_unchanged", report["r1_unchanged"])
    print("r1b_per_spec", report["r1b_per_spec"])
    print("controls_pass", report["stage1_controls_all_pass"])
    print("episodes", report["stage2"]["n_episodes"])


if __name__ == "__main__":
    main()
