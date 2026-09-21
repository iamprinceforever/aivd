#!/usr/bin/env python3
"""Run full AIVD 3.40 Phase-1 pipeline (normalize → replay → report)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_aivd_3_40_phase1_replay.py"),
        "--repo-root",
        str(ROOT),
        "--out",
        str(ROOT / "reports" / "aivd_3_40_phase1"),
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
