"""Run a single explorer baseline on the mock target."""
from __future__ import annotations

import json
from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.metrics.discovery import compute_metrics
from aivd.viz.report import write_json, write_markdown_report


def run_baseline(explorer_name: str = "random", budget: int = 50, seed: int = 42, out_dir: str | Path = "reports") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data_dir = Path("aivd_data") / f"baseline_{explorer_name}_{seed}"
    cfg = AIVDConfig(
        seed=seed,
        data_dir=data_dir,
        db_path=data_dir / "aivd.db",
        audit_path=data_dir / "audit.jsonl",
        reports_dir=out,
        budget=BudgetConfig(max_experiments=budget, max_concurrency=1, wall_clock_s=300.0),
    )
    ctrl = Controller(config=cfg, explorer_name=explorer_name)
    results = ctrl.run(n=budget)
    metrics = compute_metrics(results, estimated_regions=cfg.estimated_reachable_regions)
    write_json(out / f"baseline_{explorer_name}_metrics.json", metrics)
    write_markdown_report(
        out / f"baseline_{explorer_name}.md",
        f"Baseline: {explorer_name}",
        {
            "Summary": (
                f"Explorer `{explorer_name}` ran `{metrics['experiments']}` experiments "
                f"(seed={seed}). ConfirmedCount={metrics['ConfirmedCount']}, "
                f"DiscoveryEfficiency={metrics['DiscoveryEfficiency']:.4f}, "
                f"CorpusEscapeRate={metrics['CorpusEscapeRate']:.4f}."
            ),
            "Metrics": "```json\n" + json.dumps(metrics, indent=2) + "\n```",
            "Language note": (
                "Statuses use research vocabulary (candidate / confirmed novel finding / "
                "unresolved anomaly). Unusualness alone is never claimed as a zero-day."
            ),
        },
    )
    print(json.dumps({"explorer": explorer_name, **metrics}, indent=2, default=str))
    return metrics


if __name__ == "__main__":
    run_baseline()
