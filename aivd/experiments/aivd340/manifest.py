"""Condition manifest I/O for AIVD 3.40."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.condition import (
    BH_BUDGET,
    B32_BUDGET,
    CONTROL_IDS,
    FACTORIAL_CELLS,
    LOCKED_SEEDS,
    PLANT_CANARY,
    PLANT_S,
    PLANT_U,
    all_control_conditions,
    all_factorial_conditions,
)

DEFAULT_MANIFEST = Path("reports/aivd_3_40_condition_manifest.json")


def build_manifest() -> dict[str, Any]:
    factorial = [c.to_dict() for c in all_factorial_conditions()]
    controls = [c.to_dict() for c in all_control_conditions()]
    return {
        "document": "aivd_3_40_condition_manifest",
        "sacred_tinyllama_matrix_executed": False,
        "B32": B32_BUDGET,
        "BH": BH_BUDGET,
        "REDISCOVERY_FLOOR": 5,
        "INVENT_CAP": 48,
        "seeds": list(LOCKED_SEEDS),
        "plants": {"S": PLANT_S, "U": PLANT_U, "canary": PLANT_CANARY},
        "factorial_cell_ids": list(FACTORIAL_CELLS),
        "control_ids": list(CONTROL_IDS),
        "factorial": factorial,
        "controls": controls,
        "runner_invariant": "one ExperimentCondition per episode; mix raises ConditionMixError",
        "absolute": {
            "propose_atoms_immutable": True,
            "no_force_firewall": True,
            "no_lower_floor": True,
            "no_sacred_run_step1plus": True,
        },
    }


def write_manifest(path: Path | str | None = None) -> Path:
    out = Path(path) if path else DEFAULT_MANIFEST
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build_manifest()
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return out


def load_manifest(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_MANIFEST
    return json.loads(p.read_text(encoding="utf-8"))


__all__ = ["DEFAULT_MANIFEST", "build_manifest", "write_manifest", "load_manifest"]
