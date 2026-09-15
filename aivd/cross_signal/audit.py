"""Cross-signal audit, leakage scan, anti-mapping helpers, controls."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _forbidden_literals() -> tuple[str, ...]:
    """Forbidden Holdout solution literals (fragment-built; no answer keys)."""
    return (
        "SECRET{" + "AIVD38_HX_BOUND}",
        "AIVD38-" + "HOLDOUT-X-" + "ERROR-BOUND",
        "ack" + "-" + "bound",
        "clear" + "ance",
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
        "HoldoutR",
        "HoldoutS",
        "SECRET{AIVD312_HQ_",
        "HOLDOUT" + "-Q",
        "SECRET{AIVD313_HR_",
        "HOLDOUT" + "-R",
        "SECRET{AIVD314_HS_",
        "HOLDOUT" + "-S",
        "holdout_x_bound_key",
        "holdout_y_phase_key",
        "holdout_z_mirror_key",
        "holdout_w_latch_key",
        "holdout_q_conduit_key",
        "holdout_q_bridge_key",
        "holdout_r_span_key",
        "holdout_s_ridge_key",
        # Q / Z / R mechanism hardcodes banned in discovery layer
        "prime-conduit",
        "arm-conduit",
        "prep-conduit",
        "seal-conduit",
        "bind-conduit",
        "couple-conduit",
        "join-conduit",
        "conduit.gap",
        "conduit.sealed",
        "flush-mirror",
        "sync-mirror",
        "drop-mirror",
        "free-mirror",
        "mirror-flush",
        "mirror.lock",
        "enable-span",
        "activate-span",
        "open-span",
        "pair-span",
        "combine-span",
        "link-span",
        "fuse-span",
        "span.split",
        # S mechanism hardcodes (post-freeze holdout) — banned in discovery
        "gauge-ridge",
        "sense-ridge",
        "trace-ridge",
        "steer-offset",
        "nudge-offset",
        "align-offset",
        "ridge.offset",
        "if holdout",
        "holdout ==",
    )


def scan_cross_signal_source(root: Path | None = None) -> list[tuple[str, str]]:
    """Scan aivd/cross_signal for forbidden Holdout solution literals."""
    root = root or Path(__file__).resolve().parents[2]
    cs = root / "aivd" / "cross_signal"
    leaks: list[tuple[str, str]] = []
    if not cs.is_dir():
        return leaks
    forbidden = _forbidden_literals()
    for f in cs.rglob("*.py"):
        if f.name == "audit.py":
            continue
        text = f.read_text(errors="ignore")
        for tok in forbidden:
            if tok and tok in text:
                leaks.append((str(f.relative_to(root)), tok))
    return leaks


def cross_signal_audit_record(
    *,
    summary: dict[str, Any],
    complexity: dict[str, Any] | None = None,
    ablation: str | None = None,
    anti_mapping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": "cross_signal_coexploration_audit",
        "summary": summary,
        "complexity": complexity or {},
        "ablation": ablation,
        "anti_mapping": anti_mapping or {},
        "note": (
            "Cross-signal co-exploration; no Holdout hardcoding; "
            "relation support required for INTERACTION_READY; "
            "multi-factor link score (not raw correlation); "
            "pruned residual↔action pairs (not brute-force Cartesian)."
        ),
    }


# Neutral anti-mapping / synthetic vocab (must NOT overlap S/R/Q tokens)
ANTI_S_RESIDUAL = "loom"
ANTI_S_ACTION_STEMS = ("tilt", "skew", "warp", "lean")
ANTI_S_RESIDUAL_STEMS = ("moor", "clamp", "dock", "pin")


def anti_mapping_benchmark_spec() -> dict[str, Any]:
    """Structurally unrelated cross-signal problem for anti-mapping test."""
    return {
        "name": "anti_s_neutral_cross_signal",
        "residual": f"{ANTI_S_RESIDUAL}.gap",
        "residual_stems": list(ANTI_S_RESIDUAL_STEMS),
        "action_stems": list(ANTI_S_ACTION_STEMS),
        "forbidden_overlap": [
            "ridge", "offset", "gauge", "sense", "trace", "steer", "nudge", "align",
            "span", "conduit", "mirror", "latch",
        ],
        "mechanism": (
            "Weak residual evidence on residual-stems guides exploration of "
            "action-stems; combination after relation SUPPORTED. Unrelated to S."
        ),
        "note": "PASS if randomized IDs still discover; hardcoded maps fail",
    }


def correlated_noncausal_spec() -> dict[str, Any]:
    """Control: correlated but noncausal residual↔action must NOT become vuln."""
    return {
        "name": "correlated_noncausal",
        "residual": "noise.hum",
        "correlated_action": "spin",
        "causal_action": None,
        "note": "High correlation alone must not yield SUPPORTED vulnerability",
    }


def false_dependency_spec() -> dict[str, Any]:
    return {
        "name": "false_cross_dependency",
        "link_score_expected_max": 0.35,
        "note": "Independent residual/action should not force combo reserve",
    }


__all__ = [
    "scan_cross_signal_source",
    "cross_signal_audit_record",
    "anti_mapping_benchmark_spec",
    "correlated_noncausal_spec",
    "false_dependency_spec",
    "ANTI_S_RESIDUAL",
    "ANTI_S_ACTION_STEMS",
    "ANTI_S_RESIDUAL_STEMS",
]
