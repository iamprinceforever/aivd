"""AIVD 3.45 pre-Sacred audit harness (observational; no production edits).

Covers charter scenarios 1–10, determinism twin runs, and summary metrics
against offline replay. Does NOT execute Sacred.
"""
from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from aivd.science.exploration_alloc import (
    DEFAULT_CHAIN_FLOOR,
    DEFAULT_MAX_EXPLORE_SLOTS,
    DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE,
    ExplorationAllocator,
)
from aivd.science.methods import INVENT_CAP

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "reports"
NR = "NOT_RECORDED"


def _now_ist() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")


@dataclass
class FakeCand:
    cid: str
    proposal_index: int = 0

    def key(self) -> str:
        return self.cid


def _board(labels: list[str]) -> list[FakeCand]:
    return [FakeCand(cid=lab, proposal_index=i) for i, lab in enumerate(labels)]


@dataclass
class Check:
    scenario: str
    name: str
    status: str
    detail: str = ""


def _traj(alloc: ExplorationAllocator, boards: list[list[str]], *, leftover: int, invent_left: int) -> list[tuple]:
    outs = []
    left = leftover
    inv = invent_left
    for labs in boards:
        d = alloc.decide(_board(labs), lazy=True, invent_slots_left=inv, leftover=left)
        keys = [c.key() for c in d.ordered]
        mats = keys[: d.n_mat]
        outs.append((d.n_mat, d.exploit_n, d.explore_n, tuple(d.explore_keys), tuple(keys), d.reason))
        alloc.observe_call(board_keys_before=labs, materialized_keys=mats, decision=d)
        left = max(0, left - DEFAULT_CHAIN_FLOOR * max(1, d.n_mat))
        inv = max(0, inv - d.n_mat)
    return outs


def scenario_checks() -> list[Check]:
    out: list[Check] = []

    # 1 high-ranked — exploit preserves rank-0
    a = ExplorationAllocator()
    d = a.decide(_board(["H0", "H1", "H2"]), lazy=True, invent_slots_left=4, leftover=12)
    ok = d.ordered[0].key() == "H0" and d.exploit_n == 1
    out.append(Check("1", "high_ranked_exploit_preserved", "PASS" if ok else "FAIL",
                     f"ordered0={d.ordered[0].key()} exploit={d.exploit_n}"))

    # 2 lower-ranked novel — first-window explore surfaces next
    a = ExplorationAllocator()
    d = a.decide(_board(["L0", "L1", "L2", "L3"]), lazy=True, invent_slots_left=4, leftover=12)
    ok = d.explore_n == 1 and d.n_mat == 2 and d.ordered[1].key() == "L1"
    out.append(Check("2", "lower_ranked_novel_bounded_explore", "PASS" if ok else "FAIL",
                     f"n_mat={d.n_mat} explore={d.explore_keys}"))

    # 3 permanently demoted — one opportunity then saturated
    a = ExplorationAllocator()
    d0 = a.decide(_board(["D0", "D1"]), lazy=True, invent_slots_left=2, leftover=3)
    a.observe_call(board_keys_before=["D0", "D1"], materialized_keys=["D0"], decision=d0)
    d1 = a.decide(_board(["D0b", "D1"]), lazy=True, invent_slots_left=2, leftover=12)
    a.observe_call(board_keys_before=["D0b", "D1"], materialized_keys=["D0b"], decision=d1)
    d2 = a.decide(_board(["D0c", "D1"]), lazy=True, invent_slots_left=2, leftover=12)
    ok = d1.explore_keys == ["D1"] and "D1" not in d2.explore_keys
    out.append(Check("3", "permanently_demoted_one_opportunity", "PASS" if ok else "FAIL",
                     f"d1={d1.explore_keys} d2={d2.explore_keys}"))

    # 4 duplicate — terminal suppresses
    a = ExplorationAllocator()
    a.state_of("DUP").skip_count = 5
    a.note_terminal("DUP", reason="duplicate")
    d = a.decide(_board(["T0", "DUP", "T2"]), lazy=True, invent_slots_left=3, leftover=12)
    ok = "DUP" not in d.explore_keys
    out.append(Check("4", "duplicate_terminal_suppressed", "PASS" if ok else "FAIL",
                     f"explore={d.explore_keys}"))

    # 5 rejected
    a = ExplorationAllocator()
    a.state_of("RJ").skip_count = 9
    d = a.decide(_board(["R0", "RJ", "R2"]), lazy=True, invent_slots_left=3, leftover=12,
                 rejected_keys={"RJ"})
    ok = "RJ" not in d.explore_keys
    out.append(Check("5", "rejected_excluded", "PASS" if ok else "FAIL", f"explore={d.explore_keys}"))

    # 6 null / empty board
    a = ExplorationAllocator()
    d = a.decide([], lazy=True, invent_slots_left=4, leftover=12)
    ok = d.n_mat == 0 and d.reason == "empty_or_no_cap"
    out.append(Check("6", "null_empty_board", "PASS" if ok else "FAIL", f"reason={d.reason}"))

    # 7 multiple families — bounded +1
    a = ExplorationAllocator()
    d = a.decide(_board([f"F{i}" for i in range(12)]), lazy=True, invent_slots_left=8, leftover=30)
    ok = d.explore_n == DEFAULT_MAX_EXPLORE_SLOTS and d.n_mat == 2
    out.append(Check("7", "multiple_families_bounded", "PASS" if ok else "FAIL",
                     f"n_mat={d.n_mat} explore_n={d.explore_n}"))

    # 8 budget-near-exhaustion (leftover == chain_floor → afford 1, no explore)
    a = ExplorationAllocator()
    d = a.decide(_board(["B0", "B1", "B2"]), lazy=True, invent_slots_left=4,
                 leftover=DEFAULT_CHAIN_FLOOR)
    ok = d.n_mat == 1 and d.explore_n == 0
    out.append(Check("8", "budget_near_exhaustion", "PASS" if ok else "FAIL",
                     f"n_mat={d.n_mat} explore_n={d.explore_n} leftover={DEFAULT_CHAIN_FLOOR}"))

    # 9 firewall-near-floor — leftover just above floor still budget-gated; allocator
    # does not bypass firewall (no firewall API). Proxy: leftover=chain_floor+1 → still 1.
    a = ExplorationAllocator()
    d = a.decide(_board(["W0", "W1", "W2"]), lazy=True, invent_slots_left=4,
                 leftover=DEFAULT_CHAIN_FLOOR + 1)
    ok = d.n_mat == 1 and d.explore_n == 0
    # Also confirm allocator source has no firewall mutation
    import inspect
    src = inspect.getsource(ExplorationAllocator).lower()
    ok = ok and ("firewall" not in src)
    out.append(Check("9", "firewall_near_floor_budget_proxy", "PASS" if ok else "FAIL",
                     f"n_mat={d.n_mat}; allocator_has_firewall_api=False"))

    # 10 invent_cap-near-limit — invent_slots_left=1 → n_mat<=1; =0 → 0
    a = ExplorationAllocator()
    d1 = a.decide(_board(["C0", "C1", "C2"]), lazy=True, invent_slots_left=1, leftover=99)
    d0 = a.decide(_board(["C0", "C1", "C2"]), lazy=True, invent_slots_left=0, leftover=99)
    # Near INVENT_CAP occupancy simulation: slots_left = 2 → may explore if leftover enough
    d2 = a.decide(_board(["C0", "C1", "C2"]), lazy=True, invent_slots_left=2, leftover=99)
    ok = d1.n_mat <= 1 and d0.n_mat == 0 and d2.n_mat <= 2 and d2.n_mat <= 2
    out.append(Check("10", "invent_cap_near_limit", "PASS" if ok else "FAIL",
                     f"slots1={d1.n_mat} slots0={d0.n_mat} slots2={d2.n_mat} INVENT_CAP={INVENT_CAP}"))

    return out


def determinism_twin() -> Check:
    def once():
        a = ExplorationAllocator()
        return _traj(
            a,
            [["T0", "T1", "T2", "T3", "T4"], ["T0", "T4", "T3", "T2"], ["T5", "T4", "T1"]],
            leftover=18,
            invent_left=6,
        )

    a_run, b_run = once(), once()
    ok = a_run == b_run
    return Check("DET", "identical_seed_config_trajectory", "PASS" if ok else "FAIL",
                 f"len={len(a_run)}")


def identity_rename() -> Check:
    def traj(labels: list[str]):
        a = ExplorationAllocator()
        outs = []
        d = a.decide(_board(labels), lazy=True, invent_slots_left=4, leftover=12)
        outs.append((d.n_mat, d.exploit_n, d.explore_n, [labels.index(k) for k in d.explore_keys]))
        mats = [c.key() for c in d.ordered[: d.n_mat]]
        a.observe_call(board_keys_before=labels, materialized_keys=mats, decision=d)
        rel = [labels[0], labels[2], labels[3], labels[1]]
        d2 = a.decide(_board(rel), lazy=True, invent_slots_left=3, leftover=12)
        outs.append((d2.n_mat, d2.exploit_n, d2.explore_n, [labels.index(k) for k in d2.explore_keys]))
        return outs

    ok = traj(["X0", "X1", "X2", "X3"]) == traj(["Y0", "Y1", "Y2", "Y3"])
    return Check("ID", "identity_rename_invariant", "PASS" if ok else "FAIL")


def load_offline_metrics() -> dict[str, Any]:
    path = REPORTS / "aivd_3_45_offline_replay.json"
    if not path.exists():
        return {"status": "NOT_RECORDED", "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"status": "OK", "headlines": data.get("headlines", {}), "n_cells": data.get("n_cells"),
            "limitations": data.get("limitations", [])}


def run() -> dict[str, Any]:
    checks = scenario_checks()
    checks.append(determinism_twin())
    checks.append(identity_rename())
    fails = [c for c in checks if c.status != "PASS"]
    offline = load_offline_metrics()
    return {
        "document": "aivd_3_45_pre_sacred_audit_harness",
        "recorded": _now_ist(),
        "sacred": "NO",
        "scenario_checks": [c.__dict__ for c in checks],
        "n_pass": sum(1 for c in checks if c.status == "PASS"),
        "n_fail": len(fails),
        "harness_status": "PASS" if not fails else "FAIL",
        "offline_metrics": offline,
        "constants": {
            "DEFAULT_MAX_EXPLORE_SLOTS": DEFAULT_MAX_EXPLORE_SLOTS,
            "DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE": DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE,
            "DEFAULT_CHAIN_FLOOR": DEFAULT_CHAIN_FLOOR,
            "INVENT_CAP": INVENT_CAP,
        },
    }


if __name__ == "__main__":
    try:
        result = run()
    except Exception as e:
        result = {
            "document": "aivd_3_45_pre_sacred_audit_harness",
            "recorded": _now_ist(),
            "harness_status": "FAIL",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    out = REPORTS / "aivd_3_45_pre_sacred_audit_harness.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"harness_status": result.get("harness_status"),
                      "n_pass": result.get("n_pass"),
                      "n_fail": result.get("n_fail"),
                      "wrote": str(out)}, indent=2))
