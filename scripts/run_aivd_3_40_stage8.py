#!/usr/bin/env python3
"""AIVD 3.40 STAGE-8 EXECUTION — Live equivalence integration + fresh-plant Sacred.

Authorize: live _keep step-6 for S8-RA/RC/RD; Sacred BH48 × 7 seeds × 4 plants.
FORBID: R-B; retune; winner merge; BH/floor cheat; odd-atom injection; Stage-9 auto.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))


def _ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def main() -> int:
    from aivd.experiments.aivd340.stage8_constants import (
        AUTHORIZATION,
        DESIGN_TIP_FULL,
        OUT_DIR,
        STAGE7_COMPLETE_TIP,
    )
    from aivd.experiments.aivd340.stage8_controls import run_controls
    from aivd.experiments.aivd340.stage8_integration_replay import run_integration_replay
    from aivd.experiments.aivd340.stage8_analyze import analyze, write_results_md
    from aivd.experiments.aivd340.stage8_run import run_matrix, write_progress

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print("STAGE-8 EXECUTION", _ist(), flush=True)
    print("HEAD", head, flush=True)
    print("AUTH", AUTHORIZATION[:120], "...", flush=True)

    # P0 integrity already stamped; refresh progress
    write_progress({"phase": "P0_DONE", "head": head, "design_tip": DESIGN_TIP_FULL})

    # P1
    print("P1 integration fixture replay ...", flush=True)
    replay = run_integration_replay()
    print("  axis1_pass", replay.get("axis1_pass"), "families", {k: v.get("pass") for k, v in replay.get("families", {}).items()}, flush=True)
    if not replay.get("axis1_pass"):
        write_progress({"phase": "P1_FAIL", "replay": replay})
        print("P1 FAIL — stopping before Sacred", flush=True)
        return 2
    write_progress({"phase": "P1_DONE"})

    # P2
    print("P2 controls battery ...", flush=True)
    controls = run_controls(integration_replay=replay)
    print("  controls overall_pass", controls.get("overall_pass"), flush=True)
    if not controls.get("overall_pass"):
        write_progress({"phase": "P2_FAIL", "controls": {k: v.get("pass") for k, v in controls.get("checks", {}).items()}})
        print("P2 FAIL — stopping before Sacred", flush=True)
        # Still allow BASELINE-only? Spec: FAIL → STOP
        return 3
    write_progress({"phase": "P2_DONE"})

    # P3
    print("P3 Sacred matrix (4×7) ...", flush=True)
    matrix = run_matrix(resume=True)
    if matrix.get("blocked"):
        print("P3 BLOCKED", matrix.get("gate"), flush=True)
        return 4
    write_progress({"phase": "P3_DONE", "n_runs": matrix.get("n_runs")})

    # P4
    print("P4 analysis ...", flush=True)
    results = analyze(
        matrix=matrix,
        integration_replay=replay,
        controls=controls,
        execution_head=head,
    )
    Path("reports/aivd_3_40_stage8_results.json").write_text(
        json.dumps(results, indent=2, default=str) + "\n"
    )
    write_results_md(results, Path("reports/aivd_3_40_stage8_results.md"))
    # also copy key artifacts under stage8 dir
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str) + "\n")
    write_results_md(results, OUT_DIR / "results.md")
    write_progress({"phase": "P4_DONE", "gate": results.get("gate"), "gate_line": results.get("gate_line")})

    print(results["gate_line"], flush=True)
    print(results["final_gate"], flush=True)
    print("surviving", results.get("surviving_condition_set"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
