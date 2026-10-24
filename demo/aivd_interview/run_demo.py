"""DEMO – not a research result.

Interview demo runner: three small code targets (one planted path-traversal),
three local models for discovery, plus a deterministic offline scanner and
live verification. Writes JSON + markdown under demo/reports/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import LABEL, discover, harness, ollama_client, verifier

IST = ZoneInfo("Asia/Calcutta")
DEFAULT_MODELS = ("gemma3:1b", "qwen3:1.7b", "llama3.2:3b")
DEFAULT_HOST = "http://127.0.0.1:11536"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
REPORTS = HERE / "reports"
GROUND = json.loads((HERE / "ground_truth.json").read_text())


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone(IST).isoformat(timespec="seconds")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def run(
    *,
    host: str,
    models: list[str],
    mode: str,
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sandbox = harness.build_sandbox()
    started = _now_iso()
    t0 = time.time()

    det = verifier.deterministic_scan(sandbox)

    model_results: list[dict] = []
    model_mode_used = "skipped"
    available: list[str] = []
    if mode in ("models", "auto"):
        try:
            available = ollama_client.list_models(host)
        except Exception as e:
            available = []
            if mode == "models":
                raise SystemExit(f"Ollama unreachable at {host}: {e}") from e
        chosen = [m for m in models if m in available or any(a.startswith(m) for a in available)]
        # normalize tags: gemma3:1b may appear as gemma3:1b
        norm = []
        for m in models:
            hit = next((a for a in available if a == m or a.startswith(m + "-") or a == m), None)
            if hit:
                norm.append(hit)
        if norm:
            model_mode_used = "local_ollama"
            for model in norm:
                per_target = []
                for target in harness.TARGETS:
                    src = harness.source_of(target)
                    analysis = discover.analyze_with_model(host, model, target, src)
                    finding = None
                    verification = None
                    status = "NO_FINDING"
                    parsed = analysis.get("parsed") or {}
                    if analysis.get("ok") and parsed.get("vulnerable"):
                        finding = {
                            "target": target,
                            "class": parsed.get("class") or "unspecified",
                            "cwe": parsed.get("cwe"),
                            "evidence": parsed.get("evidence"),
                            "exploit_hint": parsed.get("exploit_hint"),
                            "source": f"model:{model}",
                        }
                        verification = verifier.verify_finding(finding, sandbox)
                        status = "VERIFIED" if verification.get("verified") else "UNVERIFIED"
                    elif analysis.get("ok") and parsed is not None and not parsed.get("vulnerable"):
                        status = "CLEAN_CLAIM"
                    elif not analysis.get("ok"):
                        status = "ERROR"
                    else:
                        status = "PARSE_FAIL"
                    per_target.append(
                        {
                            "target": target,
                            "status": status,
                            "analysis": analysis,
                            "finding": finding,
                            "verification": verification,
                        }
                    )
                model_results.append({"model": model, "targets": per_target})
        elif mode == "models":
            raise SystemExit(f"none of the requested models are installed: {models}; have {available}")
        else:
            model_mode_used = "deterministic_only_fallback"

    # Aggregate per-target truth table for the interview.
    per_target_summary = []
    for target in harness.TARGETS:
        gt = GROUND["targets"][target]
        det_hit = next(d for d in det if d["target"] == target)
        model_hits = []
        for mr in model_results:
            t = next(x for x in mr["targets"] if x["target"] == target)
            model_hits.append(
                {
                    "model": mr["model"],
                    "status": t["status"],
                    "verified": bool((t.get("verification") or {}).get("verified")),
                    "claimed_class": (t.get("finding") or {}).get("class"),
                }
            )
        per_target_summary.append(
            {
                "target": target,
                "planted": gt["planted"],
                "expected": gt["expected"],
                "deterministic": {
                    "status": det_hit["status"],
                    "verified": det_hit["verified"],
                    "class": det_hit.get("class"),
                },
                "models": model_hits,
            }
        )

    harness.close_sandbox(sandbox)

    doc = {
        "label": LABEL,
        "demo_id": "aivd-interview-demo-v1",
        "started_at": started,
        "finished_at": _now_iso(),
        "duration_s": round(time.time() - t0, 3),
        "mode_requested": mode,
        "mode_used": {
            "deterministic_scanner": True,
            "models": model_mode_used,
            "ollama_host": host if model_mode_used == "local_ollama" else None,
            "models_available": available,
            "models_run": [m["model"] for m in model_results],
        },
        "ground_truth": GROUND,
        "deterministic_findings": det,
        "model_results": model_results,
        "per_target_summary": per_target_summary,
        "integrity": {
            "target_sources_sha256": {
                t: _sha(HERE / "targets" / f"{t}.py") for t in harness.TARGETS
            },
            "ground_truth_sha256": _sha(HERE / "ground_truth.json"),
        },
        "honesty": (
            "Results are whatever the scanner and models actually produced. "
            "Nothing was rewritten to force a match with ground truth."
        ),
    }

    ts = datetime.now(IST).strftime("%Y%m%dT%H%M%S")
    json_path = out_dir / f"demo-report-{ts}.json"
    latest_json = out_dir / "latest.json"
    json_path.write_text(json.dumps(doc, indent=2) + "\n")
    latest_json.write_text(json.dumps(doc, indent=2) + "\n")

    md = render_markdown(doc)
    md_path = out_dir / f"demo-explainer-{ts}.md"
    latest_md = out_dir / "EXPLAINER.md"
    md_path.write_text(md)
    latest_md.write_text(md)

    doc["_paths"] = {
        "json": str(json_path),
        "md": str(md_path),
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
    }
    return doc


def render_markdown(doc: dict) -> str:
    lines = [
        f"# {LABEL}: AIVD interview demo explainer",
        "",
        f"_Generated {doc['finished_at']} (Asia/Calcutta)._ Demo id `{doc['demo_id']}`.",
        "",
        "## What AIVD is",
        "",
        "AIVD (AI Vulnerability Discovery) is a research project on whether language models can",
        "**discover** security flaws in unfamiliar code and whether those discoveries can be",
        "**verified** (and later generalized) under a sealed, preregistered protocol. Research",
        "campaigns keep the corpus sealed and the scoring blind until reveal. This",
        "page is **not** one of those campaigns.",
        "",
        f"> **{LABEL}.** The three modules below, the planted bug, the model prompts, and every",
        "> number on this page exist only so an interviewer can see the discovery → verification",
        "> loop end-to-end. They are not a research result, not a preregistered run, and not a seal.",
        "",
        "## Setup",
        "",
        "Three tiny Python “services” sit in `demo/aivd_interview/targets/`. Exactly **one** has a",
        "deliberately planted vulnerability. A local sandbox drops a secret file next to an avatars",
        "directory, a reports directory, and a small SQLite invoices database.",
        "",
        "| Target | Role | Expected |",
        "|---|---|---|",
    ]
    for t, g in doc["ground_truth"]["targets"].items():
        lines.append(
            f"| `{t}` | {g.get('class') or g.get('why', '')} | **{g['expected']}** |"
        )
    lines += [
        "",
        "### The planted bug",
        "",
        "In `avatar_store.handle`, the avatar filename is joined onto the avatars directory with",
        "`os.path.join` after only stripping a leading `/`. A `../SECRET_TOKEN.txt` probe therefore",
        "reads a file **outside** the avatars directory. The clean twin (`report_viewer`) uses",
        "`Path.resolve()` + `relative_to(base)` and rejects the same probe. `invoice_lookup` uses",
        "parameterized SQL scoped to the current user.",
        "",
        "## How discovery and verification worked",
        "",
        f"- **Deterministic offline scanner:** always on. Looks for the unsafe `os.path.join`",
        f"  pattern (and string-built SQL), then **live-verifies** by calling the target in the sandbox.",
        f"- **Models:** mode requested `{doc['mode_requested']}`; models mode used:",
        f"  `{doc['mode_used']['models']}`. Models run: `{doc['mode_used']['models_run'] or 'none'}`.",
        f"  Each model saw only the source of one target at a time and returned a JSON claim;",
        f"  claims were verified the same way (no trust in the model’s word alone).",
        "",
        "## Results",
        "",
        "| Target | Planted? | Deterministic | " + " | ".join(doc["mode_used"]["models_run"] or ["(no model)"]) + " |",
        "|---|---|---|" + "|".join(["---"] * max(1, len(doc["mode_used"]["models_run"] or [1]))) + "|",
    ]
    for row in doc["per_target_summary"]:
        cells = [
            f"`{row['target']}`",
            "yes" if row["planted"] else "no",
            f"{row['deterministic']['status']}"
            + (f" ({row['deterministic']['class']})" if row["deterministic"]["class"] else ""),
        ]
        if row["models"]:
            for m in row["models"]:
                mark = "VERIFIED" if m["verified"] else m["status"]
                cells.append(mark)
        else:
            cells.append("—")
        lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "### Reading the table",
        "",
        "- **VERIFIED** means the live probe actually returned the secret (or other user’s data).",
        "- **CLEAN / CLEAN_CLAIM / NO_FINDING** means no verified exploit.",
        "- **UNVERIFIED** means a model claimed a bug but the live probe did not confirm it",
        "  (honest miss or false positive — kept as-is).",
        "",
        "## Limitations (say these in the interview)",
        "",
        "1. This is a **toy corpus of three functions**, not the sealed AIVD research corpus.",
        "2. Small local models (≈1–3B) are used one-at-a-time under ~10–15 GiB RAM; they can miss",
        "   or hallucinate. Verification is what makes a finding count.",
        "3. The deterministic scanner is intentionally narrow (path join + string SQL) so the demo",
        "   stays understandable; research AIVD does not rely on this scanner.",
        "4. No unpublished research-campaign outcomes, seals, or preregistrations are included here.",
        "",
        "## Integrity pins",
        "",
        "```",
        json.dumps(doc["integrity"], indent=2),
        "```",
        "",
        f"_Duration: {doc['duration_s']}s. {doc['honesty']}_",
        "",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=LABEL)
    ap.add_argument("--host", default=os.environ.get("AIVD_DEMO_OLLAMA_HOST", DEFAULT_HOST))
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS),
                    help="comma-separated Ollama model tags")
    ap.add_argument("--mode", choices=("auto", "models", "deterministic"), default="auto",
                    help="auto: models if reachable else deterministic; models: require Ollama; "
                         "deterministic: scanner only")
    ap.add_argument("--out", type=Path, default=REPORTS)
    args = ap.parse_args(argv)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    mode = "deterministic" if args.mode == "deterministic" else args.mode
    if args.mode == "deterministic":
        # still record mode_used.models as skipped
        pass
    doc = run(host=args.host, models=models, mode=mode, out_dir=args.out)
    summary = {
        "label": LABEL,
        "mode_used": doc["mode_used"],
        "per_target": [
            {
                "target": r["target"],
                "planted": r["planted"],
                "deterministic_verified": r["deterministic"]["verified"],
                "any_model_verified": any(m["verified"] for m in r["models"]),
            }
            for r in doc["per_target_summary"]
        ],
        "paths": doc["_paths"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
