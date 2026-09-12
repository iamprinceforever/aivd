"""Compare explorers under modest budgets; write honest research-results.md."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.metrics.discovery import compute_metrics
from aivd.viz.report import metrics_to_html_table, write_json, write_markdown_report


METHODS = ["random", "corpus", "novelty", "evolutionary", "rl", "hybrid"]


def run_comparison(budget_per_method: int = 80, seed: int = 42, out_dir: str | Path = "reports") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    all_metrics: dict[str, dict] = {}

    for method in METHODS:
        data_dir = Path("aivd_data") / f"cmp_{method}_{seed}"
        if data_dir.exists():
            for p in data_dir.glob("*"):
                if p.is_file():
                    p.unlink()
        cfg = AIVDConfig(
            seed=seed,
            data_dir=data_dir,
            db_path=data_dir / "aivd.db",
            audit_path=data_dir / "audit.jsonl",
            reports_dir=out,
            budget=BudgetConfig(
                max_experiments=budget_per_method,
                max_concurrency=1,
                wall_clock_s=600.0,
            ),
        )
        ctrl = Controller(config=cfg, explorer_name=method)
        results = ctrl.run(n=budget_per_method)
        metrics = compute_metrics(results, estimated_regions=cfg.estimated_reachable_regions)
        all_metrics[method] = metrics
        write_json(out / f"comparison_{method}_metrics.json", metrics)
        print(
            f"[compare] {method}: confirmed={metrics['ConfirmedCount']} "
            f"eff={metrics['DiscoveryEfficiency']:.4f} "
            f"escape={metrics['CorpusEscapeRate']:.4f} "
            f"gt_hits={metrics['gt_hits']}"
        )

    write_json(out / "comparison_all_metrics.json", all_metrics)

    ranked = sorted(
        all_metrics.items(),
        key=lambda kv: (kv[1].get("ConfirmedCount", 0), kv[1].get("CorpusEscapeRate", 0.0)),
        reverse=True,
    )
    lines = []
    lines.append(f"Comparison seed={seed}, budget_per_method={budget_per_method}.")
    lines.append("")
    lines.append(
        "| Method | Experiments | Confirmed | DiscoveryEfficiency | CorpusEscapeRate | GT hits |"
    )
    lines.append(
        "|--------|-------------|-----------|---------------------|------------------|---------|"
    )
    for method, m in all_metrics.items():
        lines.append(
            f"| {method} | {m['experiments']} | {m['ConfirmedCount']} | "
            f"{m['DiscoveryEfficiency']:.4f} | {m['CorpusEscapeRate']:.4f} | `{m['gt_hits']}` |"
        )
    lines.append("")
    lines.append("### Observations (honest)")
    if ranked:
        best, bm = ranked[0]
        lines.append(
            f"- Highest confirmed count under this budget: **{best}** "
            f"({bm['ConfirmedCount']} confirmed, unique GT={bm.get('ConfirmedUniqueGT')})."
        )
    corpus_m = all_metrics.get("corpus", {})
    lines.append(
        f"- Corpus explorer GT hits: `{corpus_m.get('gt_hits', {})}` "
        "(expected to rediscover in-corpus vulns; escape should be low unless accidental)."
    )
    escape_methods = [m for m, met in all_metrics.items() if met.get("CorpusEscapeRate", 0) > 0]
    if escape_methods:
        lines.append(
            f"- Methods with corpus escape (confirmed out-of-corpus GT): {escape_methods}."
        )
    else:
        lines.append(
            "- No method achieved confirmed corpus-escape under this modest budget "
            "(or escapes were not confirmed through the full pipeline)."
        )
    zero_conf = [m for m, met in all_metrics.items() if met.get("ConfirmedCount", 0) == 0]
    if zero_conf:
        lines.append(f"- Methods with zero confirmed findings: {zero_conf}.")

    # Research-question note
    novel_ids = ["HV-NOVEL-ENCODING", "HV-NOVEL-INDIRECT", "HV-NOVEL-DELIMITER"]
    for method, m in all_metrics.items():
        hits = m.get("gt_hits") or {}
        novel_hits = {k: v for k, v in hits.items() if k in novel_ids}
        if novel_hits:
            lines.append(f"- `{method}` triggered out-of-corpus GT (raw hits): `{novel_hits}`.")

    lines.append(
        "- DiscoveryEfficiency counts **unique confirmed ground-truth IDs** / experiments "
        "(not raw confirmation events), so it stays small when the mock has few hidden vulns."
    )
    lines.append(
        "- These results are from actual local mock runs; they do not claim zero-days "
        "or production vulnerability discovery."
    )
    lines.append(
        "- Limitations: small budget, hashing embeddings, mock-only target, verification "
        "variations are shallow; mock vulns are relatively easy to re-trigger once a strategy hits."
    )

    body = "\n".join(lines)
    write_markdown_report(
        out / "research-results.md",
        "AIVD Research Results (Actual Runs)",
        {
            "Protocol": (
                f"Six explorers × {budget_per_method} experiments on `mock://default`, "
                f"seed={seed}. Ground truth used only for offline metrics."
            ),
            "Results": body,
            "HTML table": metrics_to_html_table(all_metrics),
        },
    )
    (out / "comparison_summary.html").write_text(
        "<html><body><h1>AIVD Comparison</h1>"
        + metrics_to_html_table(all_metrics)
        + "<p>See research-results.md for narrative.</p></body></html>"
    )
    print(f"Wrote {out / 'research-results.md'}")
    return all_metrics


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="AIVD explorer comparison")
    p.add_argument("--budget", type=int, default=80)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", type=str, default="reports")
    args = p.parse_args(argv)
    run_comparison(budget_per_method=args.budget, seed=args.seed, out_dir=args.out_dir)


if __name__ == "__main__":
    main()
