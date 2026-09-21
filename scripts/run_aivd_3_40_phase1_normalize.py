#!/usr/bin/env python3
"""Run AIVD 3.40 Phase-1 normalize (observational only)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aivd.experiments.aivd340.phase1_normalize import (  # noqa: E402
    normalize_all,
    write_normalized_artifacts,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "aivd_3_40_phase1",
    )
    p.add_argument("--repo-root", type=Path, default=ROOT)
    args = p.parse_args()
    batch = normalize_all(repo_root=args.repo_root)
    paths = write_normalized_artifacts(batch, args.out)
    print(f"normalized {batch['n_present']}/{batch['n_expected']} episodes")
    if batch["n_missing"]:
        print("MISSING:", batch["missing"])
        return 2
    for k, v in paths.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
