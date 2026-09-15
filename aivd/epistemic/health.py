"""Health check for the 3.18 epistemic layer."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def health_check(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[1]
    n = sum(1 for p in (base / "epistemic").rglob("*.py") if p.name != "__pycache__")
    return {
        "package": "epistemic",
        "n_modules": n,
        "default_mode_off": True,
        "global_budget": 32,
        "greedy_eig_only": False,
        "reservations_revocable": True,
        "shadow_mode": True,
        "consolidation_note": (
            "3.18 does not add a new discovery algorithm. GlobalEpistemicArbiter "
            "allocates a single 32-slot experiment budget across proposing "
            "subsystems. Default off ≈ 3.17."
        ),
    }


__all__ = ["health_check"]
