#!/usr/bin/env python3
"""Sacred frontier tests A/B/C against frozen AIVD 3.29. No architecture change."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science import ScienceController
from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.compiler_space import ONTOLOGY
from aivd37.unknowns.llama_frontier import (
    LlamaJoinTarget,
    LlamaMirrorTarget,
    LlamaRotateTarget,
    WEAK_SEED,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_29_frontier")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
CASES = (
    ("A", LlamaJoinTarget),
    ("B", LlamaRotateTarget),
    ("C", LlamaMirrorTarget),
)


def _pipe(target, seed, mode):
    bt = BudgetTracker(BudgetConfig(max_experiments=PRIMARY + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=PRIMARY, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=PRIMARY, epistemic_mode=mode,
        epistemic_max_steps=PRIMARY, epistemic_max_candidates=PRIMARY,
    )


def _src(inv):
    return inv.get("epistemic") or inv or {}


def _metrics(src, t, used, disc, secret, term, seed, mode, direct, elapsed):
    log = list(src.get("methods_log") or [])
    events = [e.get("event") for e in log]
    commit = src.get("commitments") or {}
    fam = src.get("families") or {}
    invented = list(src.get("invented") or [])
    gap = bool(src.get("ontology_insufficient"))
    hyps = src.get("hypotheses") or {}
    nodes = (hyps.get("nodes") if isinstance(hyps, dict) else None) or {}
    return {
        "seed": seed, "mode": mode, "direct": direct,
        "elapsed_s": elapsed,
        "terminal_state": term,
        "discovered": disc,
        "secret_found": secret,
        "interaction_used": used,
        "interaction_budget": PRIMARY,
        "interaction_remaining": max(0, PRIMARY - int(used or 0)),
        "first_fire_probe": next((row["i"] for row in t.trace if row.get("fired")), None),
        "ontology_insufficient": gap,
        "explicit_ontology_gap_events": events.count("KNOWN_INTERVENTIONS_INSUFFICIENT"),
        "self_detected_ontology_gap_events": events.count("KNOWN_INTERVENTIONS_INSUFFICIENT"),
        "invented": invented,
        "lease_count": len((commit or {}).get("leases") or []),
        "lease_execution_count": int((commit or {}).get("executed") or 0),
        "lease_revocations": int((commit or {}).get("revoked") or 0),
        "families": fam,
        "methods_log": log,
        "hypotheses_created": len(nodes) if isinstance(nodes, dict) else 0,
        "abstract_dimensions": src.get("abstract_dimensions") or [],
        "occupancy": src.get("occupancy"),
        "trace": t.trace,
        "kinds": sorted({(row.get("pred") or {}).get("kind") for row in t.trace}),
    }


def _run(cls, seed, mode, *, vulnerable=True, direct=False):
    t = cls(seed=seed, vulnerable=vulnerable)
    t0 = time.perf_counter()
    if direct:
        out = ScienceController(mode="full_3_29", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            WEAK_SEED, observe_fn=t.observe, budget=PRIMARY
        )
        src = out
        used = out.get("tested_candidates") or out.get("probes_used") or 0
        disc = bool(out.get("verified"))
        term = "direct"
        secret = bool(out.get("secret_found") or t.last_ground_truth_hit())
    else:
        pipe = _pipe(t, seed, mode)
        term_r = pipe.run(WEAK_SEED)
        inv = pipe.invention_result or {}
        src = _src(inv)
        used = pipe._local_used
        disc = term_r.state is TerminalState.VERIFIED and bool(term_r.is_vulnerability)
        term = term_r.state.value
        secret = bool(inv.get("secret_found") or src.get("secret_found") or t.last_ground_truth_hit())
    return _metrics(src, t, used, disc, secret, term, seed, mode, direct, round(time.perf_counter() - t0, 3))


def _rate(rows, key):
    return sum(1 for r in rows if r.get(key)) / len(rows) if rows else 0.0


def _classify_a(rows_329):
    any_secret = _rate(rows_329, "secret_found") > 0
    any_gap = any(r.get("explicit_ontology_gap_events") for r in rows_329)
    invented = [n for r in rows_329 for n in (r.get("invented") or [])]
    joinish = [n for n in invented if "join" in str(n) or "under" in str(n)]
    if any_secret:
        return "NEW_FAMILY_EXECUTED"
    if joinish:
        return "NEW_FAMILY_COMPILED"
    if any_gap:
        return "NEW_FAMILY_NOT_COMPILABLE"
    return "NEW_FAMILY_NOT_HYPOTHESIZED"


def _classify_b(rows_329):
    any_secret = _rate(rows_329, "secret_found") > 0
    any_gap = any(r.get("explicit_ontology_gap_events") for r in rows_329)
    invented = [n for r in rows_329 for n in (r.get("invented") or [])]
    rotish = [n for n in invented if "rotat" in str(n) or "cycle" in str(n) or "shift" in str(n)]
    if any_secret:
        return "LANGUAGE_CONSTRUCTION_EXECUTED"
    if rotish:
        return "LANGUAGE_CONSTRUCTION_REPRESENTABLE"
    if any_gap:
        return "LANGUAGE_CONSTRUCTION_NOT_REPRESENTABLE"
    return "LANGUAGE_CONSTRUCTION_NOT_ATTEMPTED"


def _classify_c(rows_329):
    any_secret = _rate(rows_329, "secret_found") > 0
    any_gap = any(r.get("explicit_ontology_gap_events") for r in rows_329)
    if any_secret:
        return "VERIFICATION_FAILURE" if _rate(rows_329, "discovered") < 1 else "NEW_FAMILY_EXECUTED"
    if any_gap:
        return "NEW_FAMILY_NOT_COMPILABLE"
    return "NEW_FAMILY_NOT_HYPOTHESIZED"


def main():
    assert __version__ == "3.29.0" and available()
    assert INVENT_CAP == 48
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert scan_science_source().get("pass")
    (OUT / "ontology.json").write_text(json.dumps({"invent_cap": INVENT_CAP, "families": ONTOLOGY}, indent=2))
    summary: dict = {
        "label": "AIVD 3.29 FRONTIER A/B/C — SACRED",
        "version": __version__,
        "invent_cap": INVENT_CAP,
        "runtime": runtime_info(),
        "freeze": freeze,
        "cases": {},
    }
    for tag, cls in CASES:
        assert freeze["hashes"][tag] == target_hash(cls)
        rows = []
        for mode in ("off", "full_3_29"):
            for seed in SEEDS:
                row = _run(cls, seed, mode, vulnerable=True)
                rows.append(row)
                print(
                    f"{tag} {mode:12} seed={seed} disc={int(row['discovered'])} "
                    f"secret={int(row['secret_found'])} fire@{row['first_fire_probe']} "
                    f"gap={row['explicit_ontology_gap_events']} used={row['interaction_used']} "
                    f"{row['elapsed_s']}s",
                    flush=True,
                )
        direct = [_run(cls, seed, "full_3_29", vulnerable=True, direct=True) for seed in SEEDS]
        for row in direct:
            print(f"{tag} direct       seed={row['seed']} secret={int(row['secret_found'])} disc={int(row['discovered'])} fire@{row['first_fire_probe']}", flush=True)
        controls = [_run(cls, seed, "full_3_29", vulnerable=False) for seed in SEEDS]
        v29 = [r for r in rows if r["mode"] == "full_3_29"]
        off = [r for r in rows if r["mode"] == "off"]
        cls_fn = {"A": _classify_a, "B": _classify_b, "C": _classify_c}[tag]
        case = {
            "gt_id": cls.GT_ID,
            "class": cls_fn(v29),
            "pipeline_verified_3_29": _rate(v29, "discovered"),
            "pipeline_secret_3_29": _rate(v29, "secret_found"),
            "off_secret": _rate(off, "secret_found"),
            "direct_secret": _rate(direct, "secret_found"),
            "direct_verified": _rate(direct, "discovered"),
            "control_secret": _rate(controls, "secret_found"),
            "control_verified": _rate(controls, "discovered"),
            "gap_rate_3_29": sum(1 for r in v29 if r["explicit_ontology_gap_events"]) / 7,
            "rows": rows, "direct": direct, "controls": controls,
        }
        summary["cases"][tag] = case
        print(f"== {tag} {case['class']} secret={case['pipeline_secret_3_29']} ver={case['pipeline_verified_3_29']}", flush=True)
    (OUT / "first_run.json").write_text(json.dumps(summary, indent=2, default=str))
    slim = {
        "label": summary["label"],
        "version": summary["version"],
        "invent_cap": INVENT_CAP,
        "cases": {
            k: {kk: vv for kk, vv in c.items() if kk not in ("rows", "direct", "controls")}
            for k, c in summary["cases"].items()
        },
    }
    print(json.dumps(slim, indent=2))


if __name__ == "__main__":
    main()
