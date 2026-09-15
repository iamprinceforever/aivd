"""Autonomy audit, leakage scan, anti-mapping / noncausal specs (3.15)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _forbidden_literals() -> tuple[str, ...]:
    return (
        "SECRET{" + "AIVD38_HX_BOUND}",
        "AIVD38-" + "HOLDOUT-X-" + "ERROR-BOUND",
        "ack" + "-" + "bound",
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
        "HoldoutT",
        "SECRET{AIVD312_HQ_",
        "HOLDOUT" + "-Q",
        "SECRET{AIVD313_HR_",
        "HOLDOUT" + "-R",
        "SECRET{AIVD314_HS_",
        "HOLDOUT" + "-S",
        "SECRET{AIVD315_HT_",
        "HOLDOUT" + "-T",
        "holdout_x_bound_key",
        "holdout_y_phase_key",
        "holdout_z_mirror_key",
        "holdout_w_latch_key",
        "holdout_q_conduit_key",
        "holdout_q_bridge_key",
        "holdout_r_span_key",
        "holdout_s_ridge_key",
        "holdout_t_prism_key",
        "prime-conduit",
        "seal-conduit",
        "conduit.gap",
        "flush-mirror",
        "mirror-flush",
        "enable-span",
        "pair-span",
        "fuse-span",
        "gauge-ridge",
        "steer-offset",
        "ridge.offset",
        "prism.drift",
        "facet-prism",
        "tilt-drift",
        "if holdout",
        "holdout ==",
    )


def scan_autonomy_source(root: Path | None = None) -> list[tuple[str, str]]:
    root = root or Path(__file__).resolve().parents[2]
    pkg = root / "aivd" / "autonomy"
    leaks: list[tuple[str, str]] = []
    if not pkg.is_dir():
        return leaks
    forbidden = _forbidden_literals()
    for f in pkg.rglob("*.py"):
        if f.name == "audit.py":
            continue
        text = f.read_text(errors="ignore")
        for tok in forbidden:
            if tok and tok in text:
                leaks.append((str(f.relative_to(root)), tok))
    return leaks


def autonomy_audit_record(
    *,
    summary: dict[str, Any],
    add: int | None = None,
    ablation: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "autonomous_signal_to_intervention_audit",
        "summary": summary,
        "add": add,
        "ablation": ablation,
        "note": (
            "Unified closed-loop OBSERVE→…→VERIFY; no Holdout hardcoding; "
            "cue-conditioned revisable priors; EVI planner; pruned candidates "
            "(not residual×stem Cartesian brute-force)."
        ),
    }


def anti_mapping_benchmark_spec() -> dict[str, Any]:
    return {
        "name": "autonomy_anti_mapping",
        "residual_vocab": ["loom", "haze", "drift"],
        "action_vocab": ["tilt", "warp", "fold"],
        "note": "Randomized opaque IDs must not change planner ranking structure",
    }


def correlated_noncausal_spec() -> dict[str, Any]:
    return {
        "name": "autonomy_correlated_noncausal",
        "note": "Correlated residual/action must not auto-verify without CF + relation support",
    }


def false_transfer_spec() -> dict[str, Any]:
    return {
        "name": "false_residual_region_transfer",
        "transfer_expected_max": 0.55,
        "note": "Independent residual features should not force high region prior",
    }


__all__ = [
    "scan_autonomy_source",
    "autonomy_audit_record",
    "anti_mapping_benchmark_spec",
    "correlated_noncausal_spec",
    "false_transfer_spec",
]
