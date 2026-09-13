#!/usr/bin/env python3
"""Authorized local scan of three open-source Llama-family models via Ollama.

Stores JSON + markdown under reports/llama_opensource/.
Does NOT claim zero-days; mock ground-truth metrics do not apply to real models.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.config import AIVDConfig
from aivd.metrics.discovery import compute_metrics

MODELS = [
    {"id": "tinyllama:latest", "label": "TinyLlama 1.1B", "family": "TinyLlama"},
    {"id": "llama3.2:1b", "label": "Llama 3.2 1B", "family": "Llama 3.2"},
    {"id": "llama3.2:3b", "label": "Llama 3.2 3B", "family": "Llama 3.2"},
]

BASE_URL = "http://127.0.0.1:11434/v1"
OUT_DIR = Path("reports/llama_opensource")
BUDGET = 8
SEED = 42
EXPLORER = "hybrid"
TIMEOUT_S = 120.0


def ollama_stop(model: str) -> None:
    try:
        subprocess.run(["ollama", "stop", model], check=False, capture_output=True, text=True)
    except Exception:
        pass


def summarize_results(model_meta: dict, results, latency_ms: float) -> dict:
    samples = []
    status_counts: dict[str, int] = {}
    errors = 0
    for r in results:
        st = r.finding.status.value if r.finding else "unknown"
        status_counts[st] = status_counts.get(st, 0) + 1
        if r.observation.error:
            errors += 1
        if len(samples) < 5:
            f = r.finding
            samples.append(
                {
                    "strategy": r.experiment.strategy,
                    "prompt": (r.experiment.prompt or "")[:400],
                    "response": (r.observation.response_text or "")[:600],
                    "error": r.observation.error,
                    "novelty": getattr(f, "novelty", None),
                    "security_score": getattr(f, "security_relevance", None),
                    "reward": r.reward.total if r.reward else None,
                    "status": st,
                }
            )
    metrics = compute_metrics(results)
    # Strip mock-GT-centric interpretation for real targets
    return {
        "model": model_meta,
        "protocol": {
            "explorer": EXPLORER,
            "budget": BUDGET,
            "seed": SEED,
            "base_url": BASE_URL,
            "request_timeout_s": TIMEOUT_S,
            "authorized": True,
            "runtime": "Ollama OpenAI-compatible API on localhost",
        },
        "wall_clock_s": latency_ms / 1000.0,
        "n_results": len(results),
        "n_errors": errors,
        "status_counts": status_counts,
        "metrics_raw": metrics,
        "notes": [
            "Mock hidden-vuln ground truth does NOT apply to these open-weight models.",
            "Security scores come from AIVD's heuristic SecurityEvaluator (mock-oriented signals).",
            "Treat outputs as previously observed behaviors under this probe budget, not verified vulnerabilities or zero-days.",
            "High novelty without security evidence remains unresolved / exploratory.",
        ],
        "samples": samples,
    }


def run_one(model_meta: dict) -> dict:
    model_id = model_meta["id"]
    print(f"\n=== Scanning {model_id} ===", flush=True)
    ollama_stop(model_id)  # ensure clean load
    time.sleep(1)

    cfg = AIVDConfig(seed=SEED)
    cfg.budget.max_experiments = BUDGET
    cfg.budget.request_timeout_s = TIMEOUT_S
    cfg.budget.wall_clock_s = max(900.0, BUDGET * TIMEOUT_S)
    cfg.data_dir = Path(f"aivd_data/llama_{model_id.replace(':', '_').replace('/', '_')}")
    cfg.db_path = cfg.data_dir / "aivd.db"
    cfg.audit_path = cfg.data_dir / "audit.jsonl"
    cfg.ensure_dirs()

    ctrl = Controller(config=cfg, explorer_name=EXPLORER)
    ctrl.set_target(
        "local://model",
        base_url=BASE_URL,
        model=model_id,
        allow_network=True,
    )

    t0 = time.perf_counter()
    results = ctrl.run(n=BUDGET)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    summary = summarize_results(model_meta, results, elapsed_ms)

    safe_name = model_id.replace(":", "_").replace("/", "_")
    out_json = OUT_DIR / f"scan_{safe_name}.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out_json} n={len(results)} errors={summary['n_errors']}", flush=True)

    ollama_stop(model_id)
    time.sleep(2)
    return summary


def write_markdown(all_summaries: list[dict]) -> Path:
    lines = [
        "# AIVD open-source Llama scan report",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        f"**Runtime:** Ollama at `{BASE_URL}` (authorized localhost)",
        f"**Explorer:** `{EXPLORER}` · **Budget:** {BUDGET} probes/model · **Seed:** {SEED}",
        "",
        "## Important scientific caveats",
        "",
        "- These are **authorized local open-weight** models, not production SaaS APIs.",
        "- AIVD mock ground-truth vulnerabilities **do not apply** here.",
        "- Heuristic security scores may stay low unless responses match mock-oriented signals.",
        "- Do **not** interpret unusual replies as zero-days; use candidate / unresolved language only.",
        "",
        "## Models tested",
        "",
        "| Model | Family | Results | Errors | Status mix | Wall clock |",
        "|-------|--------|---------|--------|------------|------------|",
    ]
    for s in all_summaries:
        m = s["model"]
        sc = ", ".join(f"{k}:{v}" for k, v in sorted(s["status_counts"].items())) or "(none)"
        lines.append(
            f"| `{m['id']}` | {m['family']} | {s['n_results']} | {s['n_errors']} | {sc} | {s['wall_clock_s']:.1f}s |"
        )

    lines += ["", "## Per-model notes", ""]
    for s in all_summaries:
        m = s["model"]
        lines.append(f"### {m['label']} (`{m['id']}`)")
        lines.append("")
        lines.append(f"- JSON: `reports/llama_opensource/scan_{m['id'].replace(':', '_')}.json`")
        lines.append(f"- Mean reward (raw metrics): {s['metrics_raw'].get('mean_reward')}")
        lines.append(f"- ConfirmedCount (heuristic pipeline): {s['metrics_raw'].get('ConfirmedCount')}")
        lines.append("")
        if s["samples"]:
            lines.append("Sample interactions (truncated):")
            lines.append("")
            for i, sample in enumerate(s["samples"][:3], 1):
                lines.append(f"{i}. **strategy=`{sample['strategy']}`** status=`{sample['status']}` "
                             f"sec={sample['security_score']} nov={sample['novelty']}")
                lines.append(f"   - prompt: {sample['prompt'][:180]!r}")
                resp = sample['response'] or f"<error {sample['error']}>"
                lines.append(f"   - response: {resp[:220]!r}")
                lines.append("")
        lines.append("")

    lines += [
        "## Reproduction",
        "",
        "```bash",
        "# requires Ollama running with: tinyllama, llama3.2:1b, llama3.2:3b",
        "ollama serve &",
        "python scripts/run_llama_open_source_scan.py",
        "```",
        "",
        "## Conclusion",
        "",
        "Scans completed against three Llama-family open-weight models via local Ollama. "
        "Findings remain exploratory observations under AIVD's heuristic evaluator; "
        "no independently verified vulnerability claims are made for these models in this report.",
        "",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines))
    # also top-level pointer
    pointer = Path("reports/llama_opensource_summary.md")
    pointer.write_text(
        "# Llama open-source scan\n\nSee [`llama_opensource/README.md`](llama_opensource/README.md) "
        "for the full report and per-model JSON.\n"
    )
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # health check
    import httpx

    r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=10.0)
    r.raise_for_status()
    available = {m["name"] for m in r.json().get("models", [])}
    missing = [m["id"] for m in MODELS if m["id"] not in available]
    if missing:
        raise SystemExit(f"Missing Ollama models: {missing}. Available: {sorted(available)}")

    summaries = []
    for meta in MODELS:
        summaries.append(run_one(meta))

    md = write_markdown(summaries)
    aggregate = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "models": summaries,
    }
    agg_path = OUT_DIR / "aggregate.json"
    agg_path.write_text(json.dumps(aggregate, indent=2))
    print("aggregate", agg_path)
    print("markdown", md)


if __name__ == "__main__":
    main()
