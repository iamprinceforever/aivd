"""Health check: module / planner / generator / scorer counts (3.17).

Document duplication; do not add another planner. Openworld consolidates
experiment selection (predict+floor) instead of a new weighted scorer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _count_py(pkg: Path) -> int:
    if not pkg.exists():
        return 0
    return sum(1 for p in pkg.rglob("*.py") if p.name != "__pycache__")


def health_check(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[1]
    packages = [
        "invention", "interaction", "joint", "cross_signal", "autonomy",
        "reasoning", "openworld", "discovery", "causal", "investigation",
    ]
    counts = {name: _count_py(base / name) for name in packages}
    planners = []
    generators = []
    scorers = []
    for name in packages:
        pkg = base / name
        if not pkg.exists():
            continue
        for p in pkg.rglob("*.py"):
            n = p.name.lower()
            if "controller" in n or "planner" in n or "scheduler" in n:
                planners.append(f"{name}/{p.name}")
            if "generat" in n or "candidate" in n:
                generators.append(f"{name}/{p.name}")
            if "scor" in n:
                scorers.append(f"{name}/{p.name}")
    return {
        "module_counts": counts,
        "n_planners_schedulers_controllers": len(planners),
        "n_generators": len(generators),
        "n_scorers": len(scorers),
        "planners": planners,
        "generators": generators,
        "scorers": scorers,
        "consolidation_note": (
            "3.17 does not add a new weighted planner. OpenWorldController "
            "replaces ACTION_STEMS invent-spam with observation-harvested "
            "generative experiments + protected floor. When openworld is on, "
            "InventionController skips duplicate autonomy/reasoning passes."
        ),
    }


__all__ = ["health_check"]
