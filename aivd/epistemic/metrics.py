"""Aggregate metrics helpers for 3.18 eval rows."""
from __future__ import annotations

from typing import Any


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = max(1, len(rows))
    return {
        "n": len(rows),
        "discovery_rate": sum(1 for r in rows if r.get("secret_found") or r.get("discovered")) / n,
        "mean_tested": sum(int(r.get("tested_candidates") or 0) for r in rows) / n,
        "mean_starvation": sum(1 for r in rows if r.get("starvation")) / n,
        "mean_slot_efficiency": sum(float(
            (r.get("diagnostics") or {}).get("pipeline_experiment_slot_efficiency")
            or r.get("pipeline_experiment_slot_efficiency")
            or 0.0
        ) for r in rows) / n,
        "mean_agreement": sum(float(
            (r.get("diagnostics") or {}).get("legacy_vs_arbiter_choice_agreement")
            or r.get("agreement_rate")
            or 0.0
        ) for r in rows) / n,
        "mean_probes": sum(int(r.get("probes_used") or 0) for r in rows) / n,
        "false_positive_rate": sum(1 for r in rows if r.get("false_positive")) / n,
    }


__all__ = ["summarize_rows"]
