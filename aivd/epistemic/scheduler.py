"""Epistemic arbiter modes (3.18). Default off → ≈ 3.17."""
from __future__ import annotations

EPISTEMIC_MODES = frozenset({
    "epistemic", "epistemic_full", "epistemic_only", "epistemic_shadow",
    "arbiter", "shadow", "full_3_18",
})

AUTHORITATIVE_MODES = frozenset({
    "epistemic", "epistemic_full", "epistemic_only", "arbiter", "full_3_18",
})

SHADOW_MODES = frozenset({
    "epistemic_shadow", "shadow",
})


def is_epistemic_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in EPISTEMIC_MODES:
        return True
    if m.startswith("epistemic"):
        return True
    if m in ("full_3_18", "arbiter", "shadow"):
        return True
    return False


def is_authoritative(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in SHADOW_MODES:
        return False
    return is_epistemic_mode(m) and m in AUTHORITATIVE_MODES or (
        is_epistemic_mode(m) and m not in SHADOW_MODES
    )


def is_shadow_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    return m in SHADOW_MODES or m.endswith("_shadow")


def epistemic_skips_legacy_tower(mode: str | None) -> bool:
    """When True, skip sequential local-reserve tower; arbiter owns allocation."""
    return is_authoritative(mode)


__all__ = [
    "EPISTEMIC_MODES",
    "AUTHORITATIVE_MODES",
    "SHADOW_MODES",
    "is_epistemic_mode",
    "is_authoritative",
    "is_shadow_mode",
    "epistemic_skips_legacy_tower",
]
