#!/usr/bin/env python3
"""Run AIVD 3.40 Phase-1 evaluator-only replay + report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aivd.experiments.aivd340.phase1_normalize import (  # noqa: E402
    normalize_all,
    write_normalized_artifacts,
)
from aivd.experiments.aivd340.phase1_replay import (  # noqa: E402
    replay_all,
    write_replay_artifacts,
)
from aivd.experiments.aivd340.phase1_report import (  # noqa: E402
    build_all_divergences,
    build_results,
    write_results,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "aivd_3_40_phase1",
    )
    p.add_argument("--repo-root", type=Path, default=ROOT)
    p.add_argument("--tip-sha", type=str, default=None)
    args = p.parse_args()

    batch = normalize_all(repo_root=args.repo_root)
    write_normalized_artifacts(batch, args.out)
    if batch["n_missing"]:
        print("PHASE-1 BLOCKED: missing trajectories", batch["missing"])
        return 2

    replay_batch = replay_all(batch)
    write_replay_artifacts(replay_batch, args.out)

    if not replay_batch["tooling_valid"]:
        # Still write a blocked results artifact
        divergences = []
        results = build_results(batch, replay_batch, divergences, tip_sha=args.tip_sha)
        write_results(
            results,
            out_dir=args.out,
            reports_dir=args.repo_root / "reports",
        )
        print(results["final_status"])
        return 3

    divergences = build_all_divergences(batch, replay_batch)
    results = build_results(batch, replay_batch, divergences, tip_sha=args.tip_sha)
    paths = write_results(
        results,
        out_dir=args.out,
        reports_dir=args.repo_root / "reports",
    )
    print(json.dumps({
        "u_gate": replay_batch["u_positive_control_gate"]["status"],
        "diagnosis_distribution": results["diagnosis_distribution"],
        "final_status": results["final_status"],
        "artifacts": paths,
    }, indent=2))
    print(results["final_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
