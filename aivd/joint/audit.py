"""Joint-layer audit, leakage scan, anti-Q overfitting helpers, budget audit."""
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
        "SECRET{AIVD312_HQ_",
        "HOLDOUT" + "-Q",
        "SECRET{AIVD313_HR_",
        "HOLDOUT" + "-R",
        "holdout_x_bound_key",
        "holdout_y_phase_key",
        "holdout_z_mirror_key",
        "holdout_w_latch_key",
        "holdout_q_conduit_key",
        "holdout_q_bridge_key",
        "holdout_r_span_key",
        # Q mechanism hardcodes banned in joint/discovery layer
        "prime-conduit",
        "arm-conduit",
        "prep-conduit",
        "seal-conduit",
        "bind-conduit",
        "couple-conduit",
        "join-conduit",
        "conduit.gap",
        "conduit.sealed",
        # Z hardcodes
        "flush-mirror",
        "sync-mirror",
        "drop-mirror",
        "free-mirror",
        "mirror-flush",
        "mirror.lock",
    )


def scan_joint_source(root: Path | None = None) -> list[tuple[str, str]]:
    """Scan aivd/joint for forbidden Holdout / Q / Z solution literals."""
    root = root or Path(__file__).resolve().parents[2]
    joint = root / "aivd" / "joint"
    leaks: list[tuple[str, str]] = []
    if not joint.is_dir():
        return leaks
    forbidden = _forbidden_literals()
    for f in joint.rglob("*.py"):
        if f.name == "audit.py":
            continue
        text = f.read_text(errors="ignore")
        for tok in forbidden:
            if tok and tok in text:
                leaks.append((str(f.relative_to(root)), tok))
    return leaks


def joint_audit_record(
    *,
    summary: dict[str, Any],
    allocation: dict[str, Any] | None = None,
    readiness: list[dict[str, Any]] | None = None,
    complexity: dict[str, Any] | None = None,
    anti_q: dict[str, Any] | None = None,
    ablation: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "joint_residual_budget_allocation_audit",
        "summary": summary,
        "allocation": allocation or {},
        "readiness": readiness or [],
        "complexity": complexity or {},
        "anti_q": anti_q or {},
        "ablation": ablation,
        "note": (
            "Joint residual budget allocation; no Holdout/Q/Z hardcoding; "
            "readiness ≠ vulnerability; asymmetric allocation; "
            "revisable reserve; hierarchical multi-way (not brute force)."
        ),
    }


# Neutral anti-Q vocabulary (must NOT overlap Q conduit/prime/arm/prep/seal/bind/couple/join)
ANTI_Q_STEMS_A = ("tilt", "skew", "warp", "lean")
ANTI_Q_STEMS_B = ("moor", "clamp", "dock", "pin")
ANTI_Q_RESIDUAL = "loom"


def anti_q_benchmark_spec() -> dict[str, Any]:
    """Structurally unrelated joint problem for anti-Q overfitting test."""
    return {
        "name": "anti_q_neutral_joint",
        "residual": f"{ANTI_Q_RESIDUAL}.gap",
        "group_a": list(ANTI_Q_STEMS_A),
        "group_b": list(ANTI_Q_STEMS_B),
        "forbidden_overlap": [
            "conduit", "prime", "arm", "prep", "seal", "bind", "couple", "join",
        ],
        "mechanism": (
            "Characterize A then B under joint residual; combination only after "
            "both PARTIALLY_CHARACTERIZED; unrelated to Q conduit co-presence."
        ),
        "note": "PASS if joint layer allocates + reaches readiness without Q stems",
    }


def false_joint_dependency_spec() -> dict[str, Any]:
    """FP control: independent residuals should NOT force joint allocation."""
    return {
        "name": "false_joint_dependency",
        "family_a": "enable",
        "family_b": "dismiss",
        "linkage_expected_max": 0.35,
        "note": "Low linkage → allocator should not over-reserve combination slots",
    }


def complexity_metrics(
    *,
    n_families: int,
    n_hypotheses_possible: int,
    n_hypotheses_generated: int,
    n_orders_possible: int,
    n_orders_tested: int,
    n_triples_possible: int = 0,
    n_triples_tested: int = 0,
) -> dict[str, Any]:
    possible_pairs = n_families * (n_families - 1) // 2 if n_families >= 2 else 0
    prune = 1.0 - (
        n_hypotheses_generated / max(1, max(possible_pairs, n_hypotheses_possible))
    )
    return {
        "n_families": n_families,
        "possible_unordered_pairs": possible_pairs,
        "hypotheses_possible": n_hypotheses_possible,
        "hypotheses_generated": n_hypotheses_generated,
        "orders_possible": n_orders_possible,
        "orders_tested": n_orders_tested,
        "triples_possible": n_triples_possible,
        "triples_tested": n_triples_tested,
        "pruning_ratio": round(max(0.0, prune), 4),
        "brute_force": bool(prune < 0.3 and n_families >= 4),
    }


__all__ = [
    "scan_joint_source",
    "joint_audit_record",
    "anti_q_benchmark_spec",
    "false_joint_dependency_spec",
    "complexity_metrics",
    "ANTI_Q_STEMS_A",
    "ANTI_Q_STEMS_B",
    "ANTI_Q_RESIDUAL",
]
