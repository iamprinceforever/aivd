"""Open-world modes (3.17). Default off → ≈ 3.16."""
from __future__ import annotations

OPENWORLD_MODES = frozenset({
    "openworld", "openworld_full", "openworld_only", "openworld_random",
    "full_3_17",
})


def is_openworld_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in OPENWORLD_MODES:
        return True
    if m.startswith("openworld"):
        return True
    if m in ("full_3_17",):
        return True
    return False


def openworld_skips_legacy_invent(mode: str | None) -> bool:
    """When True, skip ACTION_STEMS invent-spam (protect experiment floor)."""
    m = (mode or "off").lower().strip()
    return is_openworld_mode(m)


def openworld_skips_duplicate_tower(mode: str | None) -> bool:
    """Skip autonomy/reasoning duplicate passes — composed into openworld."""
    return is_openworld_mode(mode)


__all__ = [
    "OPENWORLD_MODES",
    "is_openworld_mode",
    "openworld_skips_legacy_invent",
    "openworld_skips_duplicate_tower",
]
