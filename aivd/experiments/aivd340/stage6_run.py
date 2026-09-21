"""Execute Stage-6 OFFLINE equivalence-repair benchmark and write reports.

Does not modify FILTER_BEHAVIORAL_DUP, grow.py, promote sets, or historical artifacts.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from aivd.experiments.aivd340.stage6_benchmark import run_stage6_offline_benchmark
from aivd.experiments.aivd340.stage6_constants import DESIGN_DOCS, DESIGN_TIP, SEEDS
from aivd.science.grow import REDISCOVERY_FLOOR, propose_growth
from aivd.science.methods import INVENT_CAP

REPO = Path(__file__).resolve().parents[3]
IST = timezone(timedelta(hours=5, minutes=30))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def verify_freeze() -> dict:
    head = _git("rev-parse", "HEAD")
    files = []
    ok = True
    for path in DESIGN_DOCS:
        tip_blob = _git("rev-parse", f"{DESIGN_TIP}:{path}")
        work_blob = _git("hash-object", path)
        match = tip_blob == work_blob
        ok = ok and match
        files.append({"path": path, "match": match})
    matrix = json.loads((REPO / "reports/aivd_3_40_stage6_matrix.json").read_text())
    hist = []
    for tip, path in [
        ("c003e60", "reports/aivd_3_40_stage5_results.json"),
        ("c003e60", "reports/aivd_3_40_stage5_results.md"),
        ("4005e66", "reports/aivd_3_40_stage4_results.json"),
        ("146915b", "reports/aivd_3_40_stage3_charter.md"),
        ("dcae889", "reports/aivd_3_40_stage2_results.md"),
    ]:
        tip_blob = _git("rev-parse", f"{tip}:{path}")
        work_blob = _git("hash-object", path)
        match = tip_blob == work_blob
        ok = ok and match
        hist.append({"tip": tip, "path": path, "match": match})
    grow_ok = _git("rev-parse", "4005e66:aivd/science/grow.py") == _git(
        "hash-object", "aivd/science/grow.py"
    )
    ok = (
        ok
        and grow_ok
        and matrix.get("executed") is False
        and head.startswith(DESIGN_TIP)
    )
    return {
        "design_tip": DESIGN_TIP,
        "head": head,
        "head_short": head[:7],
        "head_is_design_tip": head.startswith(DESIGN_TIP),
        "files_match_tip": all(f["match"] for f in files),
        "files": files,
        "matrix_executed_at_start": bool(matrix.get("executed")),
        "historical_unchanged": all(h["match"] for h in hist),
        "historical": hist,
        "grow_unchanged_since_4005e66": grow_ok,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "propose_growth_callable": callable(propose_growth),
        "ok": ok,
    }


def main() -> dict:
    freeze = verify_freeze()
    if not freeze["ok"]:
        raise SystemExit(f"STAGE-6 BLOCKED: freeze verification failed: {freeze}")
    payload = run_stage6_offline_benchmark()
    # Reports are produced by the benchmark payload writers / prior exec.
    # Re-write stamp for this invocation.
    stamp = {
        "document": "aivd_3_40_stage6_execution_stamp",
        "design_tip": DESIGN_TIP,
        "execution_head_pre_commit": freeze["head"],
        "recorded_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "executed": True,
        "sacred_authorized": False,
        "filter_replaced": False,
        "final_gate_line": payload["final_gate_line"],
        "mechanism_gates": {
            m: payload["mechanisms"][m]["gate"] for m in payload["mechanisms"]
        },
        "context_bank_hash": payload["context_bank_hash"],
        "gt_hash": payload["gt_hash"],
        "total_apply_micro": payload["global_budget"]["total_apply_micro"],
        "seeds": list(SEEDS),
        "freeze_verification": freeze,
    }
    (REPO / "reports/aivd_3_40_stage6_execution_stamp.json").write_text(
        json.dumps(stamp, indent=2) + "\n"
    )
    print(payload["final_gate_line"])
    return payload


if __name__ == "__main__":
    main()
