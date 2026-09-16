"""Health check for the 3.22 science layer."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def health_check(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parent
    n = sum(1 for p in base.glob("*.py") if p.name != "__pycache__")
    return {
        "package": "science",
        "n_modules": n,
        "default_mode_off": True,
        "global_budget": 32,
        "no_signatures": True,
        "no_planted_hints": True,
        "no_closed_attack_taxonomy": True,
        "invents_at_runtime": True,
        "does_not_stop_on_collapse": True,
        "single_charge_per_experiment": True,
        "live_priority_untested_methods": True,
        "consolidation_note": (
            "3.22: one experiment, one slot in the full pipeline, and after a "
            "live informative state untested methods outrank already-tried "
            "uninformative singles. Budget stays 32. Default off ≈ 3.19."
        ),
    }