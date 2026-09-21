"""AIVD 3.40 Stage-2 mock validation (R1 vs R1b). No Sacred TinyLlama."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.condition import (
    CONTROL_IDS,
    STAGE2_CELLS,
    condition_from_id,
)
from aivd.experiments.aivd340.mock_matrix import (
    _run_episode,
    run_controls,
)
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.science.benchmarks import HX8OddStride, HX9Rol1
from aivd.science.representation import R1, R1B, propose_atom_candidates, r0_equals_frozen

OUT = Path("reports/aivd_3_40_stage2_mock")
MOCK_SEEDS = (0, 1, 2)


def run_stage2_mocks(seeds: tuple[int, ...] = MOCK_SEEDS) -> dict[str, Any]:
    plant_map = {"S": HX8OddStride, "U": HX9Rol1}
    prompt = "ab cd ef gh ij kl mn"
    r1 = propose_atom_candidates(prompt=prompt, question=True, policy=R1)
    r1b = propose_atom_candidates(prompt=prompt, question=True, policy=R1B)
    r1b_classes = {a.semantic_class for a in r1b}
    identity = {
        "r0_equals_frozen": r0_equals_frozen(prompt),
        "r1_n": len(r1),
        "r1b_n": len(r1b),
        "r1b_has_geo_s0": "geo_stride_s0_t2" in r1b_classes,
        "r1b_has_geo_s1": "geo_stride_s1_t2" in r1b_classes,
        "r1b_has_geo_order": "geo_order" in r1b_classes,
        "r1_no_geo_prefix": all(not a.semantic_class.startswith("geo_") for a in r1),
        "r1b_keys": [a.key() for a in r1b],
        "r1_keys_head": [a.key() for a in r1[:4]],
    }
    cells: dict[str, list] = {}
    for cid in STAGE2_CELLS:
        cond = condition_from_id(cid)
        runner = ConditionRunner(condition=cond)
        rows = []
        for seed in seeds:
            for role, cls in plant_map.items():
                def _ep(ctx, _cls=cls, _seed=seed, _cond=cond):
                    return _run_episode(
                        _cls,
                        mode=_cond.invention_mode,
                        seed=_seed,
                        episode_budget=_cond.episode_budget,
                    )

                out = runner.run_mock(
                    seed=seed,
                    plant_id=getattr(cls, "GT_ID"),
                    episode_fn=_ep,
                )
                out["role"] = role
                out["representation"] = cond.representation
                rows.append(out)
        cells[cid] = rows
    # smoke R1b mode episode
    smoke = _run_episode(HX8OddStride, mode="full_3_39_r1b", seed=0, episode_budget=48)
    return {
        "cells": cells,
        "seeds": list(seeds),
        "sacred": False,
        "representation_identity": identity,
        "r1b_smoke": {k: smoke[k] for k in smoke if k != "generation_records"},
    }


def _episode_payload(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("result") or row


def run_stage2_mock_report(out_dir: Path | None = None) -> dict[str, Any]:
    dest = out_dir or OUT
    dest.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    controls = run_controls()
    stage2 = run_stage2_mocks(seeds=MOCK_SEEDS)
    ident = stage2["representation_identity"]
    report: dict[str, Any] = {
        "document": "aivd_3_40_stage2_mock",
        "sacred_tinyllama_executed": False,
        "elapsed_s": round(time.time() - t0, 3),
        "stage1_controls_all_pass": all(controls[c]["pass"] for c in CONTROL_IDS),
        "stage2": {
            "seeds": stage2["seeds"],
            "cell_ids": list(stage2["cells"].keys()),
            "n_episodes": sum(len(v) for v in stage2["cells"].values()),
            "representation_identity": ident,
            "r1b_smoke": stage2["r1b_smoke"],
        },
        "r1_unchanged": bool(
            ident["r0_equals_frozen"] and ident["r1_no_geo_prefix"] and ident["r1_n"] >= 8
        ),
        "r1b_per_spec": bool(
            ident["r1b_has_geo_s0"]
            and ident["r1b_has_geo_s1"]
            and ident["r1b_has_geo_order"]
            and ident["r1b_n"] <= 8
        ),
    }
    summary_rows = []
    for cid, rows in stage2["cells"].items():
        for role in ("S", "U"):
            subset = [r for r in rows if r.get("role") == role]
            payloads = [_episode_payload(r) for r in subset]
            summary_rows.append({
                "condition": cid,
                "target": role,
                "seeds": len(subset),
                "firewall": sum(1 for p in payloads if int(p.get("firewall_epoch") or 0) >= 1),
                "verified": sum(1 for p in payloads if p.get("verified")),
            })
    report["summary_table"] = summary_rows
    (dest / "stage2_mock_matrix.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# AIVD 3.40 Stage-2 Mock Validation (Commit E)",
        "",
        "**Sacred TinyLlama Stage-2:** NOT RUN (Commit E mock only)",
        "",
        f"**Stage-1 controls all pass:** {report['stage1_controls_all_pass']}",
        f"**R1 unchanged:** {report['r1_unchanged']}",
        f"**R1b per spec:** {report['r1b_per_spec']}",
        f"**Stage-2 mock episodes:** {report['stage2']['n_episodes']}",
        "",
        "## Representation identity",
        "",
        "```json",
        json.dumps(ident, indent=2),
        "```",
        "",
        "## Summary (mock HX plants — not Sacred)",
        "",
        "| Condition | Target | Seeds | Firewall≥1 | Verified |",
        "|-----------|--------|-------|------------|----------|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['condition']} | {row['target']} | {row['seeds']} | {row['firewall']} | {row['verified']} |"
        )
    lines += ["", "STOP before Sacred Stage-2 until env gate + A–E green.", ""]
    (dest / "REPORT.md").write_text("\n".join(lines))
    return report


__all__ = ["run_stage2_mocks", "run_stage2_mock_report"]
