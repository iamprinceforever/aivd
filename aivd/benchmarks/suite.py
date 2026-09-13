"""Offline hidden benchmark suite runner. GT used only for scoring."""
from __future__ import annotations

from typing import Any

from aivd.core.config import AIVDConfig
from aivd.agents.controller import Controller
from aivd.metrics.discovery import compute_metrics
from aivd.targets.profiles import PROFILE_GROUND_TRUTH, get_profile_target

SUITE_PROFILES = ["A", "B", "C", "D", "E", "F"]


def run_hidden_suite(
    explorer: str = "random",
    budget: int = 20,
    seed: int = 42,
    profiles: list[str] | None = None,
) -> dict[str, Any]:
    """Run explorer on each profile; return offline metrics. GT not passed to explorer."""
    profiles = profiles or list(SUITE_PROFILES)
    out: dict[str, Any] = {"explorer": explorer, "budget": budget, "seed": seed, "profiles": {}}
    for p in profiles:
        cfg = AIVDConfig(seed=seed)
        cfg.budget.max_experiments = budget
        cfg.data_dir = cfg.data_dir / f"suite_{p}_{explorer}_{seed}"
        cfg.db_path = cfg.data_dir / "aivd.db"
        cfg.audit_path = cfg.data_dir / "audit.jsonl"
        cfg.ensure_dirs()
        ctrl = Controller(config=cfg, explorer_name=explorer)
        ctrl.target = get_profile_target(p, seed=seed)
        results = ctrl.run(n=budget)
        metrics = compute_metrics(results, estimated_regions=cfg.estimated_reachable_regions)
        gt_expected = PROFILE_GROUND_TRUTH.get(p.upper(), {}).get("vulns", [])
        hits = [r.finding.ground_truth_hit for r in results if r.finding.ground_truth_hit]
        out["profiles"][p] = {
            "label": PROFILE_GROUND_TRUTH.get(p.upper(), {}).get("label"),
            "metrics": metrics,
            "gt_expected": gt_expected,
            "gt_hits_observed": hits,
            "hit_any_expected": any(h in gt_expected for h in hits),
        }
    return out
