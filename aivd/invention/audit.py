"""Intervention novelty / diversity audit helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def _forbidden_holdout_literals() -> tuple[str, ...]:
    """Construct forbidden Holdout solution literals (not stored as answers in source)."""
    # Built from fragments so invention source does not embed Holdout GT strings.
    hx_secret = "SECRET{" + "AIVD38_HX_BOUND}"
    hx_gt = "AIVD38-" + "HOLDOUT-X-" + "ERROR-BOUND"
    # Hyphenated ack + bound and clear + ance are Holdout-X triggers — ban as literals
    ack_bound = "ack" + "-" + "bound"
    clearance = "clear" + "ance"
    bound_trip = "bound" + "." + "trip"
    hy_secret_prefix = "SECRET{AIVD39_HY_"
    hy_label = "HOLDOUT" + "-Y"
    # Holdout-Z fragments (post-3.10; ban if present as hard-coded solutions)
    hz_secret_prefix = "SECRET{AIVD310_HZ_"
    hz_label = "HOLDOUT" + "-Z"
    hw_secret_prefix = "SECRET{AIVD311_HW_"
    hw_label = "HOLDOUT" + "-W"
    hq_secret_prefix = "SECRET{AIVD312_HQ_"
    hq_label = "HOLDOUT" + "-Q"
    hr_secret_prefix = "SECRET{AIVD313_HR_"
    hr_label = "HOLDOUT" + "-R"
    return (
        ack_bound,
        clearance,
        bound_trip,
        hx_secret,
        hx_gt,
        "holdout_x_bound_key",
        "HoldoutX",
        "HoldoutY",
        "HoldoutZ",
        hy_label,
        hz_label,
        hy_secret_prefix,
        hz_secret_prefix,
        hw_label,
        hw_secret_prefix,
        "HoldoutW",
        "HoldoutQ",
        hq_label,
        hq_secret_prefix,
        "holdout_y_phase_key",
        "holdout_z_lease_key",
        "holdout_w_latch_key",
        "holdout_q_conduit_key",
        "HoldoutR",
        hr_label,
        hr_secret_prefix,
        "holdout_r_span_key",
        "prime-conduit",
        "seal-conduit",
        "flush-mirror",
        "free-mirror",
        "sync-mirror",
        "drop-mirror",
    )


FORBIDDEN_HOLDOUT_LITERALS = _forbidden_holdout_literals()


def scan_invention_source(root: Path | None = None) -> list[tuple[str, str]]:
    """Scan aivd/invention and aivd/interaction for forbidden Holdout solution literals."""
    root = root or Path(__file__).resolve().parents[2]
    leaks: list[tuple[str, str]] = []
    forbidden = _forbidden_holdout_literals()
    for sub in ("invention", "interaction", "joint"):
        inv = root / "aivd" / sub
        if not inv.is_dir():
            continue
        for f in inv.rglob("*.py"):
            if f.name == "audit.py":
                continue  # checker documents forbidden tokens via fragments
            text = f.read_text(errors="ignore")
            for tok in forbidden:
                if tok and tok in text:
                    leaks.append((str(f.relative_to(root)), tok))
    return leaks


def novelty_audit_record(
    *,
    intervention: dict[str, Any],
    derived_via: str,
    residual_tokens: list[str] | None = None,
    success: bool = False,
) -> dict[str, Any]:
    return {
        "intervention_id": intervention.get("id"),
        "sequence": intervention.get("sequence"),
        "strategy": intervention.get("strategy"),
        "provenance": intervention.get("provenance"),
        "derived_via": derived_via,
        "residual_tokens": list(residual_tokens or []),
        "novelty": intervention.get("novelty"),
        "eig": intervention.get("eig"),
        "family_id": (intervention.get("meta") or {}).get("family_id")
        if isinstance(intervention.get("meta"), dict)
        else intervention.get("family_id"),
        "success": success,
        "note": "Novelty alone is not rewarded; success requires security-shaped effect.",
    }


def diversity_audit_record(
    *,
    archive_summary: dict[str, Any],
    scheduler_summary: dict[str, Any] | None = None,
    exploration: str = "",
    anti_bias: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": "diversity_audit",
        "exploration": exploration,
        "archive": archive_summary,
        "scheduler": scheduler_summary or {},
        "anti_bias": anti_bias or {},
        "note": (
            "Family diversity from intervention structure; "
            "no Holdout-named boosts/penalties; novelty not sole reward."
        ),
    }



def adaptive_ordering_audit_record(
    *,
    search_summary: dict[str, Any],
    salience_summary: dict[str, Any] | None = None,
    anti_lock_in: dict[str, Any] | None = None,
    ablation: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "adaptive_ordering_audit",
        "search": search_summary,
        "salience": salience_summary or {},
        "anti_lock_in": anti_lock_in or {},
        "ablation": ablation,
        "note": (
            "Adaptive reorder from evidence; priority decay ≠ blacklist; "
            "no Holdout-named boosts; salience ≠ vulnerability; "
            "no single score dominates."
        ),
    }


def write_audit_json(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"records": records, "n": len(records)}, indent=2))



def interaction_discovery_audit_record(
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
            "additive ≠ security interaction; not Cartesian brute force."
        ),
    }


def joint_allocation_audit_record(**kwargs: Any) -> dict[str, Any]:
    """Audit record for 3.13 joint residual budget allocation."""
    return {
        "kind": "joint_residual_budget_allocation",
        "note": (
            "Joint residual budget allocation; no Holdout/Q/Z hardcoding; "
            "readiness ≠ vulnerability; asymmetric allocation."
        ),
        **kwargs,
    }
