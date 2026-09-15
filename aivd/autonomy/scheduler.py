"""Autonomy modes + enablement helpers (3.15)."""
from __future__ import annotations

AUTONOMY_MODES = frozenset({
    "autonomy", "autonomy_full", "autonomy_only", "autonomy_random",
    "autonomy_cross", "full_3_15",
})


def is_autonomy_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in AUTONOMY_MODES:
        return True
    if m.startswith("autonomy"):
        return True
    if m in ("full_3_15",):
        return True
    return False


def autonomy_enables_cross_signal(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in ("autonomy_only",):
        return False
    if m in ("autonomy", "autonomy_full", "autonomy_cross", "full_3_15"):
        return True
    return False


def autonomy_enables_joint(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in ("autonomy_only",):
        return False
    if m in ("autonomy", "autonomy_full", "autonomy_cross", "full_3_15"):
        return True
    return False


def autonomy_enables_interaction(mode: str | None) -> bool:
    return autonomy_enables_joint(mode)


__all__ = [
    "AUTONOMY_MODES",
    "is_autonomy_mode",
    "autonomy_enables_cross_signal",
    "autonomy_enables_joint",
    "autonomy_enables_interaction",
]
