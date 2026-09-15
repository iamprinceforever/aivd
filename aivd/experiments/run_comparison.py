"""Compare explorers under modest budgets; write honest research-results.md."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.metrics.discovery import compute_metrics
from aivd.viz.report import metrics_to_html_table, write_json, write_markdown_report


METHODS = ["random", "corpus", "novelty", "evolutionary", "rl", "rl_v2", "hybrid"]


def _run_one(method: str, seed: int, budget: int, out: Path) -> dict:
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
            max_experiments=budget,
            max_concurrency=1,
            wall_clock_s=600.0,
        ),
    )
    ctrl = Controller(config=cfg, explorer_name=method)
    results = ctrl.run(n=budget)
    metrics = compute_metrics(results, estimated_regions=cfg.estimated_reachable_regions)
    metrics["seed"] = seed
    return metrics


def _aggregate(seed_metrics: list[dict]) -> dict:
    """Mean±std over numeric fields; keep last gt_hits as example."""
    if len(seed_metrics) == 1:
        return seed_metrics[0]
    keys = [
        "experiments",
        "ConfirmedCount",
        "DiscoveryEfficiency",
        "CorpusEscapeRate",
        "ExplorationCoverage",
        "FalsePositiveRate",
        "ReproRate",
        "mean_reward",
    ]
    agg: dict = {"seeds": [m.get("seed") for m in seed_metrics], "per_seed": seed_metrics}
    for k in keys:
        vals = []
        for m in seed_metrics:
            v = m.get(k, 0)
            if isinstance(v, (int, float)):
                vals.append(float(v))
            else:
                vals.append(0.0)
        mean = statistics.fmean(vals) if vals else 0.0
        std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        agg[k] = mean
        agg[f"{k}_std"] = std
        agg[f"{k}_mean_std"] = f"{mean:.4f}±{std:.4f}"
    # Union of unique confirmed GT ids across seeds
    uniq: set[str] = set()
    for m in seed_metrics:
        for g in m.get("ConfirmedUniqueGT") or []:
            uniq.add(g)
    agg["ConfirmedUniqueGT"] = sorted(uniq)
    # merge gt hit counts
    merged: dict[str, int] = {}
    for m in seed_metrics:
        for hid, c in (m.get("gt_hits") or {}).items():
            merged[hid] = merged.get(hid, 0) + int(c)
    agg["gt_hits"] = merged
    return agg


def run_comparison(
    budget_per_method: int = 80,
    seed: int = 42,
    out_dir: str | Path = "reports",
    seeds: list[int] | None = None,
) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seed_list = seeds if seeds else [seed]
    all_metrics: dict[str, dict] = {}

    for method in METHODS:
        per_seed = []
        for s in seed_list:
            metrics = _run_one(method, s, budget_per_method, out)
            per_seed.append(metrics)
            print(
                f"[compare] {method} seed={s}: confirmed={metrics['ConfirmedCount']} "
                f"eff={metrics['DiscoveryEfficiency']:.4f} "
                f"escape={metrics['CorpusEscapeRate']:.4f} "
                f"gt_hits={metrics['gt_hits']}"
            )
        agg = _aggregate(per_seed)
        all_metrics[method] = agg
        write_json(out / f"comparison_{method}_metrics.json", agg)

    write_json(out / "comparison_all_metrics.json", all_metrics)

    ranked = sorted(
        all_metrics.items(),
        key=lambda kv: (kv[1].get("ConfirmedCount", 0), kv[1].get("CorpusEscapeRate", 0.0)),
        reverse=True,
    )
    lines = []
    seeds_s = ",".join(str(s) for s in seed_list)
    lines.append(
        f"Comparison seeds=[{seeds_s}], budget_per_method={budget_per_method}, "
        f"explorers={METHODS}."
    )
    lines.append("")
    if len(seed_list) > 1:
        lines.append(
            "| Method | Experiments | Confirmed (mean±std) | DiscoveryEfficiency | "
            "CorpusEscapeRate | GT hits |"
        )
        lines.append(
            "|--------|-------------|----------------------|---------------------|"
            "------------------|---------|"
        )
        for method, m in all_metrics.items():
            conf = m.get("ConfirmedCount_mean_std") or f"{m.get('ConfirmedCount', 0)}"
            eff = m.get("DiscoveryEfficiency_mean_std") or f"{m.get('DiscoveryEfficiency', 0):.4f}"
            esc = m.get("CorpusEscapeRate_mean_std") or f"{m.get('CorpusEscapeRate', 0):.4f}"
            lines.append(
                f"| {method} | {m.get('experiments', budget_per_method)} | {conf} | "
                f"{eff} | {esc} | `{m.get('gt_hits', {})}` |"
            )
    else:
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
            f"({bm.get('ConfirmedCount')} confirmed, unique GT={bm.get('ConfirmedUniqueGT')})."
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

    novel_ids = [
        "HV-NOVEL-ENCODING",
        "HV-NOVEL-INDIRECT",
        "HV-NOVEL-DELIMITER",
        "HV-LATENT-COMPOSE",
        "HV-LATENT-CHAIN",
    ]
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
        "- Latent compositional vulns (`HV-LATENT-*`, `human_hard=True`) require obscure "
        "multi-part triggers; finding them is framed as latent/compositional strategy search "
        "with confirmation — not as magical superhuman zero-day discovery."
    )
    lines.append(
        "- `rl_v2` uses the **same** multi-term `compute_reward` total (continuous MLP policy + "
        "baseline); it does not switch to success-only reward."
    )
    lines.append(
        "- These results are from actual local mock runs; they do not claim zero-days "
        "or production vulnerability discovery."
    )
    lines.append(
        "- Limitations: modest budget, hashing embeddings by default, mock-only target, "
        "stricter v2 verifier; latent vulns are intentionally hard."
    )

    body = "\n".join(lines)
    write_markdown_report(
        out / "research-results.md",
        "AIVD Research Results (Actual Runs)",
        {
            "Protocol": (
                f"Explorers {METHODS} × {budget_per_method} experiments on `mock://default`, "
                f"seeds=[{seeds_s}]. Ground truth used only for offline metrics. AIVD v2."
            ),
            "Results": body,
            "HTML table": metrics_to_html_table(
                {k: {kk: vv for kk, vv in v.items() if not isinstance(vv, (list, dict)) or kk == "gt_hits"}
                 for k, v in all_metrics.items()}
            ),
        },
    )
    (out / "comparison_summary.html").write_text(
        "<html><body><h1>AIVD Comparison</h1>"
        + metrics_to_html_table(
            {k: {kk: vv for kk, vv in v.items() if isinstance(vv, (int, float, str))}
             for k, v in all_metrics.items()}
        )
        + "<p>See research-results.md for narrative.</p></body></html>"
    )
    print(f"Wrote {out / 'research-results.md'}")
    return all_metrics


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="AIVD explorer comparison")
    p.add_argument("--budget", type=int, default=80)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--seeds",
        type=str,
        default="",
        help="Comma-separated seeds for mean±std reporting, e.g. 42,43,44",
    )
    p.add_argument("--out-dir", type=str, default="reports")
    args = p.parse_args(argv)
    seeds = None
    if args.seeds.strip():
        seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    run_comparison(
        budget_per_method=args.budget,
        seed=args.seed,
        out_dir=args.out_dir,
        seeds=seeds,
    )


if __name__ == "__main__":
    main()
