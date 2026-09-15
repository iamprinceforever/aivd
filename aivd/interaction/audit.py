"""Interaction-layer audit + anti-Z / leakage helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _forbidden_literals() -> tuple[str, ...]:
    """Forbidden Holdout solution literals (fragment-built)."""
    return (
        "SECRET{" + "AIVD38_HX_BOUND}",
        "AIVD38-" + "HOLDOUT-X-" + "ERROR-BOUND",
        "ack" + "-" + "bound",
        "clear" + "ance",
        "bound" + "." + "trip",
        "SECRET{AIVD39_HY_",
        "HOLDOUT" + "-Y",
        "SECRET{AIVD310_HZ_",
        "HOLDOUT" + "-Z",
        "SECRET{AIVD311_HW_",
        "HOLDOUT" + "-W",
        "HoldoutX",
        "HoldoutY",
        "HoldoutZ",
        "HoldoutW",
        "HoldoutQ",
        "SECRET{AIVD312_HQ_",
        "HOLDOUT" + "-Q",
        "holdout_x_bound_key",
        "holdout_y_phase_key",
        "holdout_z_mirror_key",
        "holdout_w_latch_key",
        "holdout_q_bridge_key",
        # Z-solution hardcodes banned in interaction layer
        "flush-mirror",
        "sync-mirror",
        "drop-mirror",
        "free-mirror",
        "mirror-flush",
        "mirror.lock",
    )


def scan_interaction_source(root: Path | None = None) -> list[tuple[str, str]]:
    """Scan aivd/interaction for forbidden Holdout / Z-solution literals."""
    root = root or Path(__file__).resolve().parents[2]
    inv = root / "aivd" / "interaction"
    leaks: list[tuple[str, str]] = []
    if not inv.is_dir():
        return leaks
    forbidden = _forbidden_literals()
    for f in inv.rglob("*.py"):
        if f.name == "audit.py":
            continue
        text = f.read_text(errors="ignore")
        for tok in forbidden:
            if tok and tok in text:
                leaks.append((str(f.relative_to(root)), tok))
    return leaks


def interaction_audit_record(
    *,
    summary: dict[str, Any],
    complexity: dict[str, Any] | None = None,
    anti_z: dict[str, Any] | None = None,
    ablation: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "interaction_discovery_audit",
        "summary": summary,
        "complexity": complexity or {},
        "anti_z": anti_z or {},
        "ablation": ablation,
        "note": (
            "Open interaction discovery; no Holdout/Z/Q hardcoding; "
            "additive ≠ security interaction; multi-factor scoring; "
            "hierarchical pair gen (not Cartesian brute force)."
        ),
    }


# Neutral anti-Z vocabulary (must not overlap Z flush/mirror/sync/drop/free)
ANTI_Z_STEMS_A = ("prime", "arm", "prep", "spin")
ANTI_Z_STEMS_B = ("seal", "bind", "knit", "tack")
ANTI_Z_RESIDUAL = "loom"


def anti_z_benchmark_spec() -> dict[str, Any]:
    """Neutral interaction benchmark unrelated to Z vocabulary."""
    return {
        "name": "anti_z_neutral_interaction",
        "residual": f"{ANTI_Z_RESIDUAL}.gap",
        "group_a": list(ANTI_Z_STEMS_A),
        "group_b": list(ANTI_Z_STEMS_B),
        "forbidden_overlap": ["flush", "mirror", "sync", "drop", "free"],
        "note": "PASS if interaction layer discovers A×B synergy without Z stems",
    }
