"""Epistemic arbiter modes (3.18/3.19). Default off → ≈ 3.17.

3.18: arbiter owns leftover after sequential peel.
3.19: arbiter owns the episode after a single infra smoke.
"""
from __future__ import annotations

EPISTEMIC_MODES = frozenset({
    "epistemic", "epistemic_full", "epistemic_only", "epistemic_shadow",
    "arbiter", "shadow", "full_3_18", "full_3_19", "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31",
    "science", "science_full", "science_only",
})

AUTHORITATIVE_MODES = frozenset({
    "epistemic", "epistemic_full", "epistemic_only", "arbiter",
    "full_3_18", "full_3_19", "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31", "science", "science_full", "science_only",
})

SHADOW_MODES = frozenset({
    "epistemic_shadow", "shadow",
})

# 3.19: skip smoke/sweep/gate sequential ownership. full_3_18 keeps leftover
# so the 3.18 first-run protocol remains reproducible.
EPISODE_OWNED_MODES = frozenset({
    "epistemic", "epistemic_full", "epistemic_only", "arbiter", "full_3_19",
    "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31", "science", "science_full", "science_only",
})


def is_epistemic_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in EPISTEMIC_MODES:
        return True
    if m.startswith("epistemic"):
        return True
    if m in ("full_3_18", "full_3_19", "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31", "arbiter", "shadow"):
        return True
    if m.startswith("full_3_31"):
        return True
    if m.startswith("science"):
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


def epistemic_owns_episode(mode: str | None) -> bool:
    """True when the arbiter owns remaining slots after infra smoke.

    Sequential residual-sweep peel and pre-discovery gate locks are skipped.
    Verification still runs after a positive candidate, on leftover slots.
    `full_3_18` is False so the 3.18 leftover protocol stays intact.
    """
    m = (mode or "off").lower().strip()
    if m in EPISODE_OWNED_MODES:
        return True
    if m.startswith("full_3_31"):
        return True
    if m == "full_3_18" or m in SHADOW_MODES or "shadow" in m:
        return False
    if m.startswith("epistemic"):
        return is_authoritative(m)
    return False


__all__ = [
    "EPISTEMIC_MODES",
    "AUTHORITATIVE_MODES",
    "SHADOW_MODES",
    "EPISODE_OWNED_MODES",
    "is_epistemic_mode",
    "is_authoritative",
    "is_shadow_mode",
    "epistemic_skips_legacy_tower",
    "epistemic_owns_episode",
]
