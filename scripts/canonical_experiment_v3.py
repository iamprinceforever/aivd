#!/usr/bin/env python3
"""Canonical offline mock experiment for AIVD v3 research platform."""
from __future__ import annotations

import json
from pathlib import Path

from aivd.core.config import AIVDConfig
from aivd.agents.controller import Controller
from aivd.metrics.discovery import compute_metrics


def run(budget: int = 25, seed: int = 42) -> dict:
    explorers = ["random", "corpus", "rl", "rl_v2", "ppo", "hybrid"]
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    summary = {"budget": budget, "seed": seed, "methods": {}}
    for name in explorers:
        cfg = AIVDConfig(seed=seed)
        cfg.budget.max_experiments = budget
        cfg.data_dir = Path(f"aivd_data/canon_{name}_{seed}")
        cfg.db_path = cfg.data_dir / "aivd.db"
        cfg.audit_path = cfg.data_dir / "audit.jsonl"
        # Enable WM only for ppo variant demo (optional)
        if name == "ppo":
            cfg.world_model = True
            cfg.use_critic = True
        cfg.ensure_dirs()
        ctrl = Controller(config=cfg, explorer_name=name)
        results = ctrl.run(n=budget)
        metrics = compute_metrics(results, estimated_regions=cfg.estimated_reachable_regions)
        summary["methods"][name] = metrics
        print(name, metrics.get("ConfirmedCount"), metrics.get("DiscoveryEfficiency"))
    out = reports / "canonical_v3_metrics.json"
    out.write_text(json.dumps(summary, indent=2))
    print("wrote", out)
    return summary


if __name__ == "__main__":
    run()
