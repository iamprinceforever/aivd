"""Health check for the 3.21 science layer."""
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
        "consolidation_note": (
            "3.21 owns the episode like 3.19/3.20, but when a method collapses "
            "it invents a new experimental method from the live informative "
            "state and keeps spending remaining budget. Default off ≈ 3.19."
        ),
    }


__all__ = ["health_check"]
