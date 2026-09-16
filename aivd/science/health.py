"""Health check for the 3.24 science layer."""
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
        "intra_token_invention": True,
        "invents_only_after_slot_residual": True,
        "consolidation_note": (
            "3.24: when a token-slot residual is unexplained, compile "
            "identity-preserving intra-token mutations from that index. "
            "The 3.23 wrap/omit/insert grammar stays. Default off ≈ 3.19."
        ),
    }
