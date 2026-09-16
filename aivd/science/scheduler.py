"""Science-loop modes. Default off. full_3_19 leftover protocol preserved."""
from __future__ import annotations

SCIENCE_MODES = frozenset({
    "science", "science_full", "science_only", "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27",
})


def is_science_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in SCIENCE_MODES:
        return True
    if m.startswith("science"):
        return True
    return False


__all__ = ["SCIENCE_MODES", "is_science_mode"]
