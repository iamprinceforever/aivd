#!/usr/bin/env python3
"""AIVD 3.19 HOLDOUT-19 sacred first run — POST FREEZE ONLY. No post-hoc retune."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.epistemic.controller import EpistemicController
from aivd.epistemic.scheduler import epistemic_owns_episode
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_19 import Holdout19, HOLDOUT_19_GT_ID

OUT = Path("reports/aivd_3_19")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_19/freeze.json")

MODES = (
    "off",
    "full_3_17",
    "full_3_18",
    "epistemic_full",
    "full_3_19",
)


def _src(inv: dict) -> dict:
    ep = inv.get("epistemic") or {}
    ow = inv.get("openworld") or {}
    if ep:
        return ep
    if ow:
        return ow
    return inv or {}


def _run(seed: int, mode: str, budget: int = PRIMARY) -> dict:
    t = Holdout19(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    epistemic_mode = mode if (
        mode.startswith("epistemic") or mode in ("full_3_18", "full_3_19", "arbiter", "shadow")
    ) else "off"
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=max(budget, 16),
        epistemic_mode=epistemic_mode,
        epistemic_max_steps=budget,
        epistemic_max_candidates=64,
    )
    t0 = time.perf_counter()
    term = pipe.run(Holdout19.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    src = _src(inv)
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    secret = bool(
        inv.get("secret_found")
        or src.get("secret_found")
        or (inv.get("epistemic") or {}).get("secret_found")
    )
    return {
        "seed": seed,
        "mode": mode,
        "budget": budget,
        "elapsed_s": elapsed,
        "terminal_state": term.state.value,
        "classification": term.classification,
        "discovered": discovered,
        "secret_found": secret,
        "gt_hit": t.last_ground_truth_hit(),
        "probes_used": pipe.trace.probes_used,
        "owns_episode": epistemic_owns_episode(mode) or epistemic_owns_episode(epistemic_mode),
        "peel_skipped": any(s.get("kind") == "episode_owned" for s in pipe.trace.steps),
        "tested_candidates": src.get("tested_candidates"),
        "generated_candidates": src.get("generated_candidates"),
        "success_levels": src.get("success_levels"),
        "primitives": src.get("primitives"),
        "first_broken_transition": src.get("first_broken_transition"),
        "starvation": src.get("starvation"),
        "same_budget": pipe._local_used <= budget,
        "local_used": pipe._local_used,
        "add": src.get("add"),
        "discovery_depth": src.get("discovery_depth"),
        "experiments": [
            {
                "subsystem": e.get("subsystem"),
                "prompt": (e.get("prompt") or "")[-80:],
                "secret": e.get("secret"),
                "expected_ig": e.get("expected_ig"),
            }
            for e in (src.get("experiments") or [])[:32]
        ],
    }


def _direct_ep(seed: int, budget: int = PRIMARY) -> dict:
    t = Holdout19(seed=seed)
    ctrl = EpistemicController(
        mode="epistemic_full", seed=seed, max_steps=budget, total_budget=budget,
    )
    out = ctrl.run(
        Holdout19.weak_seed(seed),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.85},
        budget=budget,
    )
    return {
        "seed": seed,
        "secret_found": bool(out.get("secret_found")),
        "gt_hit": t.last_ground_truth_hit(),
        "tested": out.get("tested_candidates"),
        "generated": out.get("generated_candidates"),
        "primitives": out.get("primitives"),
        "starvation": out.get("starvation"),
        "success_levels": out.get("success_levels"),
        "experiments": [
            {
                "subsystem": e.get("subsystem"),
                "prompt": (e.get("prompt") or "")[-80:],
                "secret": e.get("secret"),
            }
            for e in (out.get("experiments") or [])[:32]
        ],
    }


def main() -> None:
    assert __version__ == "3.19.0"
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert freeze.get("no_holdout_19_yet") is True
    assert freeze.get("freeze_commit") == "545a6130a42df8ddabf0a879257d8facb99297ba"

    rows = []
    for mode in MODES:
        for seed in SEEDS:
            row = _run(seed, mode)
            rows.append(row)
            print(
                f"{mode:16} seed={seed} disc={int(row['discovered'])} "
                f"secret={int(row['secret_found'])} tested={row['tested_candidates']} "
                f"probes={row['probes_used']} gt={row['gt_hit']}",
                flush=True,
            )

    direct = [_direct_ep(s) for s in SEEDS]

    def _rate(mode: str, key: str = "discovered") -> float:
        sub = [r for r in rows if r["mode"] == mode]
        if not sub:
            return 0.0
        return sum(1 for r in sub if r[key]) / len(sub)

    primary = [r for r in rows if r["mode"] == "full_3_19"]
    summary = {
        "label": "HOLDOUT-19 v1 SACRED FIRST RUN UNDER AIVD 3.19",
        "status": (
            "DISCOVERED+VERIFIED"
            if _rate("full_3_19") == 1.0
            else ("DISCOVERED" if _rate("full_3_19", "secret_found") == 1.0 else "NOT_DISCOVERED")
        ),
        "version": __version__,
        "freeze_commit": freeze["freeze_commit"],
        "holdout": "Holdout-19",
        "gt_id": HOLDOUT_19_GT_ID,
        "budget": PRIMARY,
        "seeds": SEEDS,
        "primary_mode": "full_3_19",
        "rates": {m: {"discovered": _rate(m), "secret": _rate(m, "secret_found")} for m in MODES},
        "direct_rate": sum(1 for d in direct if d["secret_found"]) / len(direct),
        "mean_tested": sum(int(r.get("tested_candidates") or 0) for r in primary) / len(primary),
        "mean_probes": sum(int(r.get("probes_used") or 0) for r in primary) / len(primary),
        "no_retune": True,
        "rows": rows,
        "direct": direct,
        "primary_rows": primary,
    }
    (OUT / "holdout_19.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "rates": summary["rates"],
        "direct_rate": summary["direct_rate"],
        "mean_tested": summary["mean_tested"],
        "mean_probes": summary["mean_probes"],
        "freeze": freeze["freeze_commit"][:7],
    }, indent=2))


if __name__ == "__main__":
    main()
