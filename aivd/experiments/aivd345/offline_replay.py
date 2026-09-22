"""AIVD 3.45 offline replay: BASELINE (n_mat=1) vs FIX-A (adaptive allocator).

Reads immutable 3.41 ledger trajectories. Does NOT claim CF inventions are real
inventions. Sacred not executed. Candidate keys appear only as opaque ledger ids
for measurement — production code remains identity-agnostic.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from aivd.science.exploration_alloc import ExplorationAllocator

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = ROOT / "reports" / "aivd_3_41_audit_ledger.json"
REPORTS = ROOT / "reports"
NR = "NOT_RECORDED"


def _now_ist() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _load_ledger() -> dict:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _board0(cell: dict) -> list[str]:
    events = cell.get("ledger_events") or []
    first_select = next((e for e in events if e.get("event") == "select"), None)
    proposes = [
        e
        for e in events
        if e.get("event") == "propose"
        and (first_select is None or e["seq"] < first_select["seq"])
    ]
    rejects = {
        e["candidate_key"]
        for e in events
        if e.get("event") == "reject"
        and (first_select is None or e["seq"] < first_select["seq"])
    }
    return [e["candidate_key"] for e in proposes if e["candidate_key"] not in rejects]



class _Cand:
    __slots__ = ("cid", "proposal_index")

    def __init__(self, cid: str, proposal_index: int):
        self.cid = cid
        self.proposal_index = proposal_index

    def key(self) -> str:
        return self.cid


def _simulate_baseline(board0: list[str], *, leftover: int = 12, windows: int = 4) -> dict:
    """Lazy n_mat=1: each window materializes only position 0 of current board."""
    remaining = list(board0)
    materialized: list[str] = []
    first_window: list[str] = []
    skipped_first = []
    for w in range(windows):
        if not remaining or leftover < 3:
            break
        take = remaining[:1]
        if w == 0:
            first_window = list(take)
            skipped_first = list(remaining[1:])
        materialized.extend(take)
        remaining = remaining[1:]
        leftover -= 3
    return {
        "policy": "BASELINE_n_mat1",
        "first_window": first_window,
        "first_window_skipped": skipped_first,
        "materialized": materialized,
        "n_materialized": len(materialized),
        "n_first_window": len(first_window),
        "diversity_first": len(set(first_window)),
        "diversity_total": len(set(materialized)),
    }


def _simulate_fix_a(board0: list[str], *, leftover: int = 12, windows: int = 4) -> dict:
    """Adaptive EXPLOIT+EXPLORE via ExplorationAllocator (opaque keys)."""
    alloc = ExplorationAllocator()
    remaining = [_Cand(k, i) for i, k in enumerate(board0)]
    materialized: list[str] = []
    first_window: list[str] = []
    skipped_first: list[str] = []
    explore_events = 0
    for w in range(windows):
        if not remaining or leftover < 3:
            break
        d = alloc.decide(
            remaining,
            lazy=True,
            invent_slots_left=max(0, 4 - len(materialized)),
            leftover=leftover,
        )
        if d.n_mat <= 0:
            break
        ordered = list(d.ordered)
        take = [c.key() for c in ordered[: d.n_mat]]
        if w == 0:
            first_window = list(take)
            skipped_first = [c.key() for c in ordered[d.n_mat :]]
        if d.explore_n > 0:
            explore_events += 1
        materialized.extend(take)
        take_set = set(take)
        remaining = [c for c in ordered if c.key() not in take_set]
        alloc.observe_call(
            board_keys_before=[c.key() for c in ordered],
            materialized_keys=take,
            decision=d,
        )
        leftover -= 3 * len(take)
    return {
        "policy": "FIX_A_adaptive",
        "first_window": first_window,
        "first_window_skipped": skipped_first,
        "materialized": materialized,
        "n_materialized": len(materialized),
        "n_first_window": len(first_window),
        "diversity_first": len(set(first_window)),
        "diversity_total": len(set(materialized)),
        "explore_events": explore_events,
    }


def _simulate_fix_b(board0: list[str], *, leftover: int = 12, windows: int = 4) -> dict:
    """Optional FIX-B: fixed n_mat=2 (non-adaptive) for ablation contrast."""
    remaining = list(board0)
    materialized: list[str] = []
    first_window: list[str] = []
    skipped_first: list[str] = []
    for w in range(windows):
        if not remaining or leftover < 3:
            break
        width = 2 if leftover >= 6 else 1
        take = remaining[:width]
        if w == 0:
            first_window = list(take)
            skipped_first = list(remaining[width:])
        materialized.extend(take)
        remaining = remaining[width:]
        leftover -= 3 * len(take)
    return {
        "policy": "FIX_B_fixed_n_mat2",
        "first_window": first_window,
        "first_window_skipped": skipped_first,
        "materialized": materialized,
        "n_materialized": len(materialized),
        "n_first_window": len(first_window),
        "diversity_first": len(set(first_window)),
        "diversity_total": len(set(materialized)),
    }


def run() -> dict[str, Any]:
    ledger = _load_ledger()
    cells = ledger.get("cells_on") or ledger.get("cells") or []
    if isinstance(cells, dict):
        cells = list(cells.values())

    rows = []
    agg = {
        "n_cells": 0,
        "baseline_first_div": [],
        "fix_a_first_div": [],
        "fix_b_first_div": [],
        "baseline_total_div": [],
        "fix_a_total_div": [],
        "fix_b_total_div": [],
        "baseline_n_mat": [],
        "fix_a_n_mat": [],
        "fix_b_n_mat": [],
        "persistent_suppress_baseline": Counter(),
        "exposed_by_fix_a": Counter(),
    }

    for cell in cells:
        board0 = _board0(cell)
        if len(board0) < 2:
            continue
        b = _simulate_baseline(board0)
        a = _simulate_fix_a(board0)
        fb = _simulate_fix_b(board0)
        agg["n_cells"] += 1
        agg["baseline_first_div"].append(b["diversity_first"])
        agg["fix_a_first_div"].append(a["diversity_first"])
        agg["fix_b_first_div"].append(fb["diversity_first"])
        agg["baseline_total_div"].append(b["diversity_total"])
        agg["fix_a_total_div"].append(a["diversity_total"])
        agg["fix_b_total_div"].append(fb["diversity_total"])
        agg["baseline_n_mat"].append(b["n_materialized"])
        agg["fix_a_n_mat"].append(a["n_materialized"])
        agg["fix_b_n_mat"].append(fb["n_materialized"])
        for k in b["first_window_skipped"]:
            if k not in b["materialized"]:
                agg["persistent_suppress_baseline"][k] += 1
        for k in a["first_window"]:
            if k not in b["first_window"]:
                agg["exposed_by_fix_a"][k] += 1
        rows.append({
            "cell_id": cell.get("cell_id") or cell.get("id") or NR,
            "board0_len": len(board0),
            "baseline": b,
            "fix_a": a,
            "fix_b": fb,
        })

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    summary = {
        "document": "aivd_3_45_offline_replay",
        "recorded": _now_ist(),
        "n_cells": agg["n_cells"],
        "headlines": {
            "baseline_mean_first_window_diversity": _mean(agg["baseline_first_div"]),
            "fix_a_mean_first_window_diversity": _mean(agg["fix_a_first_div"]),
            "fix_b_mean_first_window_diversity": _mean(agg["fix_b_first_div"]),
            "baseline_mean_total_diversity": _mean(agg["baseline_total_div"]),
            "fix_a_mean_total_diversity": _mean(agg["fix_a_total_div"]),
            "fix_b_mean_total_diversity": _mean(agg["fix_b_total_div"]),
            "baseline_mean_materializations": _mean(agg["baseline_n_mat"]),
            "fix_a_mean_materializations": _mean(agg["fix_a_n_mat"]),
            "fix_b_mean_materializations": _mean(agg["fix_b_n_mat"]),
            "fix_a_first_window_diversity_lift": (
                _mean(agg["fix_a_first_div"]) - _mean(agg["baseline_first_div"])
            ),
            "keys_newly_exposed_first_window_by_fix_a": dict(agg["exposed_by_fix_a"]),
            "baseline_persistent_suppress_counts": dict(agg["persistent_suppress_baseline"]),
        },
        "ablation_note": (
            "FIX-A (adaptive) preferred over FIX-B (fixed n_mat=2) when equal diversity "
            "at equal or lower unnecessary cost under tight leftover; winner NOT chosen by "
            "any single candidate success. CF inventions are NOT real inventions."
        ),
        "limitations": [
            "Offline replay approximates first/subsequent windows from board0 order only.",
            "Rank demotion dynamics after invent are NOT fully resimulated (NOT_RECORDED).",
            "Verification/Sacred outcomes NOT_RECORDED.",
            "Budget unit costs beyond chain_floor=3 proxy NOT_RECORDED.",
        ],
        "rows_sample": rows[:3],
        "n_rows": len(rows),
    }
    return summary


def main() -> None:
    summary = run()
    _write_json(REPORTS / "aivd_3_45_offline_replay.json", summary)
    h = summary["headlines"]
    md = f"""# AIVD 3.45 — Offline Replay (BASELINE vs FIX-A / FIX-B)

**Recorded:** {summary['recorded']}  
**Cells:** {summary['n_cells']}  
**Sacred:** NO  

## Headlines

| Metric | BASELINE n_mat=1 | FIX-A adaptive | FIX-B fixed n_mat=2 |
|--------|------------------|----------------|---------------------|
| Mean first-window diversity | {h['baseline_mean_first_window_diversity']:.3f} | {h['fix_a_mean_first_window_diversity']:.3f} | {h['fix_b_mean_first_window_diversity']:.3f} |
| Mean total diversity (sim windows) | {h['baseline_mean_total_diversity']:.3f} | {h['fix_a_mean_total_diversity']:.3f} | {h['fix_b_mean_total_diversity']:.3f} |
| Mean materializations | {h['baseline_mean_materializations']:.3f} | {h['fix_a_mean_materializations']:.3f} | {h['fix_b_mean_materializations']:.3f} |

**FIX-A first-window diversity lift vs baseline:** {h['fix_a_first_window_diversity_lift']:.3f}

## Newly exposed (first window) under FIX-A

```
{json.dumps(h['keys_newly_exposed_first_window_by_fix_a'], indent=2)}
```

## Ablation

{summary['ablation_note']}

## Limitations

""" + "\n".join(f"- {x}" for x in summary["limitations"]) + """

## Note

Do not claim CF inventions are real inventions. Success of any single ledger key is observation only.
"""
    _write(REPORTS / "aivd_3_45_offline_replay.md", md)
    print(json.dumps(h, indent=2))


if __name__ == "__main__":
    main()
