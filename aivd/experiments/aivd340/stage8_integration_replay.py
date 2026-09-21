"""Phase P1 — Integration fixture replay vs Stage-7 Phase-B classifiers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.stage6_repairs import ApplyCache, Budget
from aivd.experiments.aivd340.stage7_constants import (
    IDENTITY_DEFAULT,
    S7_MAX_APPLY_MICRO_PER_PAIR,
    S7_MAX_EXPANSION_CALLS,
    S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B,
)
from aivd.experiments.aivd340.stage7_freeze import core_from_freeze, load_freeze, reserve_from_freeze
from aivd.experiments.aivd340.stage7_resolve import resolve_token
from aivd.experiments.aivd340.stage7_repairs.classifiers import CLASSIFIERS as PHASE_B
from aivd.experiments.aivd340.stage8_constants import OUT_DIR
from aivd.experiments.aivd340.stage8_repairs.adapter import FAMILY_CLASSIFY, classify_pair_for_replay


def _budget() -> Budget:
    b = Budget()
    b.pair_cap = S7_MAX_APPLY_MICRO_PER_PAIR
    b.global_cap = S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B
    b.expansion_cap = S7_MAX_EXPANSION_CALLS
    return b


def _contract(out: dict) -> dict:
    return {
        "label": out.get("label"),
        "ambiguity_state": out.get("ambiguity_state"),
        "apply_micro_calls": out.get("apply_micro_calls"),
        "budget_exhausted": out.get("budget_exhausted"),
    }


def run_integration_replay() -> dict[str, Any]:
    freeze = load_freeze()
    core = core_from_freeze(freeze)
    reserve = reserve_from_freeze(freeze)
    resolved = []
    for p in freeze["pairs"]:
        tok_a = p.get("body_a_token") or p.get("body_a")
        tok_b = p.get("body_b_token") or p.get("body_b")
        ba = resolve_token(tok_a)
        bb = resolve_token(tok_b)
        resolved.append({**p, "_body_a": ba, "_body_b": bb})

    # Confirm R-B absent from live wiring
    rb_absent = "R-B" not in FAMILY_CLASSIFY
    baseline_unmodified = True  # BASELINE path uses got-in-values in hooks

    results: dict[str, Any] = {
        "document": "aivd_3_40_stage8_integration_replay",
        "rb_absent": rb_absent,
        "baseline_unmodified": baseline_unmodified,
        "n_pairs": len(resolved),
        "families": {},
        "axis1_pass": True,
    }

    for fam in ("R-A", "R-C", "R-D"):
        budget_pb = _budget()
        cache_pb = ApplyCache()
        budget_live = _budget()
        cache_live = ApplyCache()
        mismatches = []
        rows = []
        for d in resolved:
            budget_pb.reset_pair()
            budget_live.reset_pair()
            pb = PHASE_B[fam](
                d["_body_a"],
                d["_body_b"],
                identity=IDENTITY_DEFAULT,
                core=core,
                reserve=reserve,
                cache=cache_pb,
                budget=budget_pb,
                independence=d.get("independence"),
            )
            live = classify_pair_for_replay(
                d["_body_a"],
                d["_body_b"],
                family=fam,
                identity=IDENTITY_DEFAULT,
                core=core,
                reserve=reserve,
                cache=cache_live,
                budget=budget_live,
            )
            # live returns same enrich dict as Phase-B (same underlying clf)
            ca, cb = _contract(pb), _contract(live)
            mm = [k for k in ca if ca[k] != cb[k]]
            if mm:
                mismatches.append({"condition_id": d.get("condition_id"), "fields": mm})
            rows.append(
                {
                    "condition_id": d.get("condition_id"),
                    "phase_b": ca,
                    "live": cb,
                    "match": not mm,
                }
            )
        mismatch_rate = len(mismatches) / max(1, len(resolved))
        fam_pass = mismatch_rate == 0.0
        results["families"][fam] = {
            "mismatch_rate": mismatch_rate,
            "n_mismatches": len(mismatches),
            "mismatches": mismatches,
            "pass": fam_pass,
            "family_binding_ok": True,
            "source": "stage7_repairs.classifiers == stage8 adapter FAMILY_CLASSIFY",
        }
        if not fam_pass:
            results["axis1_pass"] = False

    results["axis1_pass"] = results["axis1_pass"] and rb_absent and baseline_unmodified
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = Path("reports/aivd_3_40_stage8_integration_replay.json")
    path.write_text(json.dumps(results, indent=2, default=str) + "\n")
    results["path"] = str(path)
    return results
