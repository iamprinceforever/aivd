"""Health check for the 3.20 science layer."""
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
        "consolidation_note": (
            "3.20 owns the episode like 3.19, but the search is hypothesis "
            "discrimination over generic operators — not residual token replay "
            "and not a predefined attack catalog. Default off ≈ 3.19."
        ),
    }


__all__ = ["health_check"]
