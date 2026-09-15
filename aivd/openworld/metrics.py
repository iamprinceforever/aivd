"""Open-world metrics (3.17).

OPEN-WORLD DISCOVERY RATE; REPRESENTATION→EXPERIMENT SUCCESS;
EXPERIMENT STARVATION RATE; DISCOVERY-CAUSALITY GAP.
Activity vs discovery split is mandatory.
"""
from __future__ import annotations

from typing import Any


def open_world_discovery_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(1 for r in rows if r.get("secret_found") or r.get("discovered")) / len(rows)


def representation_to_experiment_success(rows: list[dict[str, Any]]) -> float:
    """Among representable runs, fraction that generated+executed+informative."""
    reps = [r for r in rows if r.get("representable") or (r.get("n_primitives") or 0) > 0]
    if not reps:
        return 0.0
    ok = 0
    for r in reps:
        gen = (r.get("generated_candidates") or 0) > 0
        exe = (r.get("tested_candidates") or 0) > 0
        inf = bool(r.get("informative") or (r.get("mean_actual_ig") or 0) > 0.01)
        if gen and exe and inf:
            ok += 1
    return ok / len(reps)


def experiment_starvation_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(1 for r in rows if int(r.get("tested_candidates") or 0) == 0) / len(rows)


def discovery_causality_gap(rows: list[dict[str, Any]]) -> float:
    """Mean (activity_depth - discovery_depth). High gap = activity without discovery."""
    if not rows:
        return 0.0
    gaps = []
    for r in rows:
        a = float(r.get("activity_depth") or r.get("add") or 0)
        d = float(r.get("discovery_depth") or 0)
        gaps.append(a - d)
    return sum(gaps) / len(gaps)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = max(1, len(rows))
    return {
        "n": len(rows),
        "open_world_discovery_rate": open_world_discovery_rate(rows),
        "representation_to_experiment_success": representation_to_experiment_success(rows),
        "experiment_starvation_rate": experiment_starvation_rate(rows),
        "discovery_causality_gap": discovery_causality_gap(rows),
        "mean_tested": sum(int(r.get("tested_candidates") or 0) for r in rows) / n,
        "mean_generated": sum(int(r.get("generated_candidates") or 0) for r in rows) / n,
        "mean_activity_depth": sum(float(r.get("activity_depth") or 0) for r in rows) / n,
        "mean_discovery_depth": sum(float(r.get("discovery_depth") or 0) for r in rows) / n,
        "mean_ig": sum(float(r.get("mean_actual_ig") or 0) for r in rows) / n,
    }


__all__ = [
    "open_world_discovery_rate",
    "representation_to_experiment_success",
    "experiment_starvation_rate",
    "discovery_causality_gap",
    "summarize_rows",
]
