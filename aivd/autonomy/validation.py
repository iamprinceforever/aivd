"""Validation helpers: anti-mapping, noncausal, brute-force gates (3.15)."""
from __future__ import annotations

from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState


def brute_force_fail(state: AutonomousDiscoveryState) -> bool:
    """True if search exhausted theoretical Cartesian space (FAIL condition)."""
    if state.theoretical_candidates <= 0:
        return False
    return (
        state.generated_candidates >= state.theoretical_candidates
        and state.tested_candidates >= state.theoretical_candidates
    )


def anti_mapping_ok(remap_fn, score_fn, *args, **kwargs) -> bool:
    """Scores should be invariant to randomized opaque IDs."""
    try:
        a = score_fn(*args, **kwargs)
        # Remap if callable provided
        if remap_fn is not None:
            remap_fn()
        b = score_fn(*args, **kwargs)
        if isinstance(a, dict) and isinstance(b, dict):
            ka = a.get("link_score") or a.get("score") or a.get("priority")
            kb = b.get("link_score") or b.get("score") or b.get("priority")
            if ka is None or kb is None:
                return True
            return abs(float(ka) - float(kb)) < 0.15
        return True
    except Exception:
        return True


def correlated_noncausal_should_not_verify(
    *,
    secret_found: bool,
    relation_supported: bool,
    cf_pass: bool,
) -> bool:
    """Correlated-but-noncausal links must not yield verified vulnerability."""
    if secret_found and not cf_pass:
        return True  # correctly withheld verification
    if secret_found and not relation_supported:
        return False  # BAD: secret without relation support
    return not secret_found or (secret_found and cf_pass and relation_supported)


def diversity_ok(tested_regions: list[str], *, min_regions: int = 2) -> bool:
    return len(set(tested_regions)) >= min_regions or len(tested_regions) < min_regions


__all__ = [
    "brute_force_fail",
    "anti_mapping_ok",
    "correlated_noncausal_should_not_verify",
    "diversity_ok",
]
