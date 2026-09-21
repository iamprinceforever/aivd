"""AIVD 3.40 budget/leftover transition documentation helpers.

READ-ONLY instrumentation of existing designer/grow/lifecycle semantics.
Does NOT change accounting, floors, or invent_cap.
"""
from __future__ import annotations

from typing import Any

from aivd.science.grow import REDISCOVERY_FLOOR

# Documented floors from existing code (designer.py / grow.py) — not retuned.
CHAIN_FLOOR = 3  # invent / grow / compose skip if leftover < 3
# REDISCOVERY_FLOOR = 5 imported

TRANSITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "probe_consume",
        "trigger": "successful probe / step charge",
        "effect": "remaining_steps := max(0, remaining_steps - 1)",
        "source": "aivd/science/designer.py",
    },
    {
        "id": "invent_skip_leftover_lt_3",
        "trigger": "leftover < 3 and atom invention attempted",
        "effect": "skip invent; emit ATOM_INVENTION_SKIPPED_BY_PLANNING / planning skip",
        "source": "ScienceDesigner._maybe_invent_atom",
    },
    {
        "id": "grow_skip_leftover_lt_3",
        "trigger": "leftover < 3 and growth attempted",
        "effect": "skip growth; LANGUAGE_GROWTH_BUDGET_EXHAUSTION / RECURSIVE path",
        "source": "ScienceDesigner._maybe_grow / propose_growth",
    },
    {
        "id": "compose_skip_leftover_lt_3",
        "trigger": "leftover < 3 and compose attempted",
        "effect": "skip compose",
        "source": "ScienceDesigner._maybe_compose",
    },
    {
        "id": "firewall_skip_leftover_lt_floor",
        "trigger": f"leftover < REDISCOVERY_FLOOR ({REDISCOVERY_FLOOR})",
        "effect": "skip firewall; emit REDISCOVERY_BUDGET_FAILURE; epoch stays 0",
        "source": "ScienceDesigner._maybe_firewall",
    },
    {
        "id": "firewall_arm_leftover_ge_floor",
        "trigger": f"leftover >= REDISCOVERY_FLOOR ({REDISCOVERY_FLOOR}) and other gates",
        "effect": "language.firewall(); firewall_epoch += 1",
        "source": "ScienceDesigner._maybe_firewall",
    },
    {
        "id": "bh_headroom",
        "trigger": "episode_budget=BH(48) vs B32(32) under same invent schedule",
        "effect": "expected leftover_at_firewall ≈ sacred_339_leftover(3) + 16 = 19",
        "source": "reports/aivd_3_40_experiment_design.md (preregistered)",
    },
)


def documented_floors() -> dict[str, int]:
    return {
        "CHAIN_FLOOR": CHAIN_FLOOR,
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "B32": 32,
        "BH": 48,
        "INVENT_CAP": 48,
    }


def predict_leftover_at_firewall(*, episode_budget: int, sacred_b32_leftover: int = 3) -> int:
    """Linear headroom model used in BH justification (documentation only)."""
    return int(sacred_b32_leftover) + (int(episode_budget) - 32)


def classify_firewall_gate(leftover: int) -> str:
    if int(leftover) < REDISCOVERY_FLOOR:
        return "SKIP_REDISCOVERY_BUDGET_FAILURE"
    return "ARM_ELIGIBLE"


__all__ = [
    "CHAIN_FLOOR",
    "TRANSITIONS",
    "documented_floors",
    "predict_leftover_at_firewall",
    "classify_firewall_gate",
]
