#!/usr/bin/env python3
"""Run AIVD 3.40 mock matrix + controls. Does NOT run Sacred TinyLlama."""
from __future__ import annotations

from aivd.experiments.aivd340.mock_matrix import run_all


def main() -> None:
    report = run_all()
    print("sacred", report["sacred_tinyllama_executed"])
    print("controls_pass", report["all_controls_pass"])
    print("episodes", report["factorial_smoke"]["n_episodes"])


if __name__ == "__main__":
    main()
