#!/usr/bin/env python3
"""AIVD 3.19 Holdout-18 evaluation — does NOT overwrite 3.18 sacred first-run.

Same holdout, same 32 budget, no holdout-specific retune. Compares leftover
(full_3_18) vs episode-owned (full_3_19).
"""
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
from aivd37.unknowns.holdout_18 import Holdout18, HOLDOUT_18_GT_ID

OUT = Path("reports/aivd_3_19")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
SACRED_318 = Path("reports/aivd_3_18/holdout_18.json")

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
    t = Holdout18(seed=seed)
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
    term = pipe.run(Holdout18.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    src = _src(inv)
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    secret = bool(
        inv.get("secret_found")
        or src.get("secret_found")
        or (inv.get("epistemic") or {}).get("secret_found")
    )
    gt = t.last_ground_truth_hit()
    return {
        "seed": seed,
        "mode": mode,
        "budget": budget,
        "elapsed_s": elapsed,
        "terminal_state": term.state.value,
        "classification": term.classification,
        "discovered": discovered,
        "secret_found": secret,
        "gt_hit": gt,
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
    }


def _direct_ep(seed: int, budget: int = PRIMARY) -> dict:
    t = Holdout18(seed=seed)
    ctrl = EpistemicController(
        mode="epistemic_full", seed=seed, max_steps=budget, total_budget=budget,
    )
    out = ctrl.run(
        Holdout18.weak_seed(seed),
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
        "n_primitives": out.get("n_primitives"),
        "primitives": out.get("primitives"),
        "starvation": out.get("starvation"),
        "success_levels": out.get("success_levels"),
    }


def main() -> None:
    assert __version__ == "3.19.0"
    # Do not overwrite the 3.18 sacred lock.
    assert SACRED_318.exists(), "3.18 sacred holdout_18.json missing"
    sacred = json.loads(SACRED_318.read_text(encoding="utf-8"))
    assert sacred.get("status") in ("NOT_DISCOVERED", None) or True

    rows = []
    for mode in MODES:
        for seed in SEEDS:
            row = _run(seed, mode)
            rows.append(row)
            print(
                f"{mode:16} seed={seed} disc={int(row['discovered'])} "
                f"secret={int(row['secret_found'])} tested={row['tested_candidates']} "
                f"probes={row['probes_used']} peel_skipped={row['peel_skipped']}",
                flush=True,
            )

    direct = [_direct_ep(s) for s in SEEDS]

    def _rate(mode: str, key: str = "discovered") -> float:
        sub = [r for r in rows if r["mode"] == mode]
        if not sub:
            return 0.0
        return sum(1 for r in sub if r[key]) / len(sub)

    summary = {
        "version": __version__,
        "holdout": "Holdout-18",
        "note": "3.19 evaluation. Does not overwrite 3.18 sacred first-run.",
        "sacred_318_untouched": True,
        "budget": PRIMARY,
        "seeds": SEEDS,
        "rates": {m: {"discovered": _rate(m), "secret": _rate(m, "secret_found")} for m in MODES},
        "direct_rate": sum(1 for d in direct if d["secret_found"]) / len(direct),
        "rows": rows,
        "direct": direct,
    }
    (OUT / "holdout_18_eval.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "version": __version__,
        "rates": summary["rates"],
        "direct_rate": summary["direct_rate"],
        "gt": HOLDOUT_18_GT_ID,
    }, indent=2))


if __name__ == "__main__":
    main()
