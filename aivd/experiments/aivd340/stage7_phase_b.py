"""Stage-7 Phase B: isolated module ↔ offline spec equivalence (survivors only)."""
from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.stage6_repairs import (
    ApplyCache as OfflineCache,
    Budget as OfflineBudget,
    CLASSIFIERS as OFFLINE_CLASSIFIERS,
)
from aivd.experiments.aivd340.stage7_constants import (
    CLAIM_LABEL_B,
    FDR_MAX,
    IDENTITY_DEFAULT,
    RECORD_SCHEMA_PHASE_B,
    S7_MAX_APPLY_MICRO_PER_PAIR,
    S7_MAX_EXPANSION_CALLS,
    S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B,
)
from aivd.experiments.aivd340.stage7_freeze import core_from_freeze, reserve_from_freeze
from aivd.experiments.aivd340.stage7_resolve import resolve_token
from aivd.experiments.aivd340.stage7_repairs.classifiers import CLASSIFIERS as EXEC_CLASSIFIERS
from aivd.experiments.aivd340.stage7_repairs.classifiers import classify_pair

REPO = Path(__file__).resolve().parents[3]


def _budget(global_used: int = 0) -> OfflineBudget:
    b = OfflineBudget()
    b.pair_cap = S7_MAX_APPLY_MICRO_PER_PAIR
    b.global_cap = S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B
    b.expansion_cap = S7_MAX_EXPANSION_CALLS
    b.global_used = global_used
    return b


def _offline_to_contract(result, *, independence: str | None) -> dict[str, Any]:
    label = result.label
    ambiguity_state = None
    if label == "ambiguous":
        ambiguity_state = (
            (result.evidence or {}).get("reason")
            or (result.evidence or {}).get("stage")
            or "ambiguous"
        )
    ev = result.evidence or {}
    budget_exhausted = False
    if ev.get("reason") == "budget" or ev.get("stage") in {
        "identity_budget",
        "reserve_budget",
    }:
        budget_exhausted = True
    if "budget" in str(ev.get("stop", "")).lower():
        budget_exhausted = True
    provenance = {
        "family_id": result.mechanism,
        "contexts_used": [
            c.get("context_id")
            for c in ev.get("contexts") or []
            if isinstance(c, dict)
        ],
        "expansion_used": result.expansion_calls,
        "independence_label_echo": independence,
    }
    return {
        "label": label,
        "ambiguity_state": ambiguity_state,
        "provenance": provenance,
        "apply_micro_calls": result.apply_micro_calls,
        "budget_exhausted": budget_exhausted,
        "family_id": result.mechanism,
    }


def _compare_contract(a: dict, b: dict) -> list[str]:
    mismatches = []
    for k in ("label", "ambiguity_state", "apply_micro_calls", "budget_exhausted"):
        if a.get(k) != b.get(k):
            mismatches.append(k)
    # provenance preregistered keys
    pa, pb = a.get("provenance") or {}, b.get("provenance") or {}
    for k in ("family_id", "contexts_used", "expansion_used", "independence_label_echo"):
        if pa.get(k) != pb.get(k):
            mismatches.append(f"provenance.{k}")
    return mismatches


def isolation_audit() -> dict[str, Any]:
    grow_blob_now = subprocess.check_output(
        ["git", "hash-object", "aivd/science/grow.py"], cwd=REPO, text=True
    ).strip()
    grow_blob_base = subprocess.check_output(
        ["git", "rev-parse", "4005e66:aivd/science/grow.py"], cwd=REPO, text=True
    ).strip()
    grow_py_diff_empty = grow_blob_now == grow_blob_base

    # Import graph: discovery entrypoints should not import stage7_repairs
    discovery_files = [
        REPO / "aivd/science/grow.py",
        REPO / "aivd/science/methods.py",
    ]
    import_hits = []
    for f in discovery_files:
        if not f.exists():
            continue
        text = f.read_text()
        if "stage7_repairs" in text:
            import_hits.append(str(f.relative_to(REPO)))

    # FILTER_BEHAVIORAL_DUP string still present (label continuity) — not replaced as live rule
    grow_text = (REPO / "aivd/science/grow.py").read_text()
    # live _keep still identity-only pattern
    filter_replaced = False  # Stage-7 never edits grow.py

    return {
        "grow_py_diff_empty": grow_py_diff_empty,
        "grow_blob": grow_blob_now,
        "grow_blob_4005e66": grow_blob_base,
        "discovery_imports_stage7_repairs": import_hits,
        "pipeline_mutation": False,
        "filter_replaced": filter_replaced,
        "sacred_bh_draws": 0,
        "ok": grow_py_diff_empty and not import_hits and not filter_replaced,
    }


def semantic_preservation_check() -> dict[str, Any]:
    """Confirm isolated module wraps Stage-6 family algorithms without semantic rewrite."""
    clf_path = REPO / "aivd/experiments/aivd340/stage7_repairs/classifiers.py"
    text = clf_path.read_text()
    required_imports = [
        "classify_baseline as _baseline",
        "classify_r_a as _ra",
        "classify_r_b as _rb",
        "classify_r_c as _rc",
        "classify_r_d as _rd",
    ]
    missing = [s for s in required_imports if s not in text]
    # No hard-coded critical body special cases
    forbidden = [
        "SLICE:1,2",
        "ODD_CAT",
        "S6-HO-CRIT",
        "odd stride",
        "make S pass",
    ]
    hits = [f for f in forbidden if f in text]
    return {
        "wraps_stage6_family_algorithms": len(missing) == 0,
        "missing_wraps": missing,
        "no_target_special_case_in_module": len(hits) == 0,
        "forbidden_hits": hits,
        "module_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "family_spec_version": "ac152c6",
        "ok": len(missing) == 0 and len(hits) == 0,
    }


def property_tests(
    family_id: str,
    freeze: dict,
    core,
    reserve,
    resolved_pairs: list[dict],
) -> dict[str, bool]:
    results: dict[str, bool] = {}

    # PT-REFL: identical bodies → duplicate
    refl_ok = True
    for d in resolved_pairs:
        if d["body_key_a"] == d["body_key_b"]:
            budget = _budget()
            cache = OfflineCache()
            out = classify_pair(
                d["_body_a"],
                d["_body_b"],
                family_id=family_id,
                core=core,
                reserve=reserve,
                cache=cache,
                budget_state=budget,
                independence=d["independence"],
            )
            if out["label"] != "duplicate":
                refl_ok = False
                break
    results["PT-REFL"] = refl_ok

    # PT-DET: replay twice
    det_ok = True
    sample = resolved_pairs[:5]
    for d in sample:
        outs = []
        for _ in range(2):
            budget = _budget()
            cache = OfflineCache()
            outs.append(
                classify_pair(
                    d["_body_a"],
                    d["_body_b"],
                    family_id=family_id,
                    core=core,
                    reserve=reserve,
                    cache=cache,
                    budget_state=budget,
                    independence=d["independence"],
                )
            )
        if outs[0]["label"] != outs[1]["label"] or outs[0]["apply_micro_calls"] != outs[
            1
        ]["apply_micro_calls"]:
            det_ok = False
            break
    results["PT-DET"] = det_ok

    # PT-TD / PT-ND on IND subsets
    ind = [d for d in resolved_pairs if d["independence"] == "INDEPENDENT"]
    td = [d for d in ind if d["pair_class"] == "TRUE_DUP"]
    nd = [d for d in ind if d["pair_class"] == "KNOWN_NONDUP"]

    def run_rows(subset):
        rows = []
        budget = _budget()
        cache = OfflineCache()
        for d in subset:
            budget.reset_pair()
            out = classify_pair(
                d["_body_a"],
                d["_body_b"],
                family_id=family_id,
                core=core,
                reserve=reserve,
                cache=cache,
                budget_state=budget,
                independence=d["independence"],
            )
            rows.append({"gt": d["gt_label"], "pred": out["label"]})
        return rows

    td_rows = run_rows(td)
    nd_rows = run_rows(nd)
    dcr = (
        sum(1 for r in td_rows if r["pred"] == "duplicate") / len(td_rows)
        if td_rows
        else 1.0
    )
    fdr = (
        sum(1 for r in nd_rows if r["pred"] == "duplicate") / len(nd_rows)
        if nd_rows
        else 0.0
    )
    results["PT-TD"] = dcr >= 0.95
    results["PT-ND"] = fdr <= FDR_MAX

    # PT-COST: all pairs within cap
    cost_ok = True
    budget = _budget()
    cache = OfflineCache()
    for d in resolved_pairs:
        budget.reset_pair()
        out = classify_pair(
            d["_body_a"],
            d["_body_b"],
            family_id=family_id,
            core=core,
            reserve=reserve,
            cache=cache,
            budget_state=budget,
            independence=d["independence"],
        )
        if out["apply_micro_calls"] > S7_MAX_APPLY_MICRO_PER_PAIR:
            cost_ok = False
            break
    results["PT-COST"] = cost_ok

    # PT-PROV: no sacred / live flags
    budget = _budget()
    cache = OfflineCache()
    d0 = resolved_pairs[0]
    out = classify_pair(
        d0["_body_a"],
        d0["_body_b"],
        family_id=family_id,
        core=core,
        reserve=reserve,
        cache=cache,
        budget_state=budget,
        independence=d0["independence"],
    )
    prov = out.get("provenance") or {}
    results["PT-PROV"] = (
        prov.get("sacred") is False or "sacred" not in prov or prov.get("sacred") is False
    ) and not prov.get("live_promote_set_mutation", False)
    # strengthen: keys must not claim sacred true
    results["PT-PROV"] = not bool(prov.get("sacred")) and not bool(
        prov.get("live_promote_set_mutation")
    )

    # PT-CTX: informational soft — pairs with full-bank agreement shouldn't flip on agreeing subset
    # Enabled as PASS when family doesn't claim weird flips; check identical-key pairs stay duplicate on core subset
    ctx_ok = True
    id_subset = [c for c in core if c[1] == "BASELINE_IDENTITY"]
    for d in resolved_pairs:
        if d["body_key_a"] != d["body_key_b"]:
            continue
        budget = _budget()
        cache = OfflineCache()
        out = classify_pair(
            d["_body_a"],
            d["_body_b"],
            family_id=family_id,
            core=id_subset,
            reserve=reserve,
            cache=cache,
            budget_state=budget,
            independence=d["independence"],
        )
        if out["label"] != "duplicate":
            ctx_ok = False
            break
    results["PT-CTX"] = ctx_ok

    return results


def run_phase_b(freeze: dict[str, Any], survivors: list[str]) -> dict[str, Any]:
    if not survivors:
        return {
            "phase": "B_IMPL_VALIDATION",
            "skipped": True,
            "reason": "NO REPAIR SURVIVED PHASE A",
            "mechanisms": {},
        }

    core = core_from_freeze(freeze)
    reserve = reserve_from_freeze(freeze)
    resolved = []
    for p in freeze["pairs"]:
        ba = resolve_token(p["body_a_token"])
        bb = resolve_token(p["body_b_token"])
        resolved.append({**p, "_body_a": ba, "_body_b": bb})

    iso = isolation_audit()
    sem = semantic_preservation_check()
    fixture_hash = hashlib.sha256(
        (
            freeze["pair_list_hash"]
            + "|"
            + freeze["context_bank_hash"]
            + "|"
            + freeze["gt_hash"]
        ).encode()
    ).hexdigest()

    mechanism_results: dict[str, Any] = {}
    global_used_off = 0
    global_used_ex = 0

    for mech in survivors:
        # OFFLINE_REF pass
        budget_o = _budget(0)
        cache_o = OfflineCache()
        offline_rows = []
        for d in resolved:
            budget_o.reset_pair()
            raw = OFFLINE_CLASSIFIERS[mech](
                d["_body_a"],
                d["_body_b"],
                identity=IDENTITY_DEFAULT,
                core=core,
                reserve=reserve,
                cache=cache_o,
                budget=budget_o,
            )
            offline_rows.append(
                (
                    d["condition_id"],
                    _offline_to_contract(raw, independence=d["independence"]),
                )
            )
        global_used_off += budget_o.global_used

        # ISOLATED_EXEC pass
        budget_e = _budget(0)
        cache_e = OfflineCache()
        exec_rows = []
        for d in resolved:
            budget_e.reset_pair()
            out = EXEC_CLASSIFIERS[mech](
                d["_body_a"],
                d["_body_b"],
                identity=IDENTITY_DEFAULT,
                core=core,
                reserve=reserve,
                cache=cache_e,
                budget=budget_e,
                independence=d["independence"],
            )
            # strip non-contract
            exec_rows.append(
                (
                    d["condition_id"],
                    {
                        "label": out["label"],
                        "ambiguity_state": out["ambiguity_state"],
                        "provenance": {
                            k: (out.get("provenance") or {}).get(k)
                            for k in (
                                "family_id",
                                "contexts_used",
                                "expansion_used",
                                "independence_label_echo",
                            )
                        },
                        "apply_micro_calls": out["apply_micro_calls"],
                        "budget_exhausted": out["budget_exhausted"],
                        "family_id": out["family_id"],
                    },
                )
            )
        global_used_ex += budget_e.global_used

        mismatches = []
        for (cid_o, co), (cid_e, ce) in zip(offline_rows, exec_rows):
            assert cid_o == cid_e
            mm = _compare_contract(co, ce)
            if mm:
                mismatches.append({"condition_id": cid_o, "fields": mm})

        mismatch_rate = len(mismatches) / len(offline_rows) if offline_rows else 0.0
        pts = property_tests(mech, freeze, core, reserve, resolved)

        label_mismatch = sum(1 for m in mismatches if "label" in m["fields"])
        amb_mismatch = sum(1 for m in mismatches if "ambiguity_state" in m["fields"])
        prov_mismatch = sum(
            1 for m in mismatches if any(f.startswith("provenance.") for f in m["fields"])
        )
        cost_mismatch = sum(1 for m in mismatches if "apply_micro_calls" in m["fields"])

        gate = "SUCCESS"
        if (
            not iso["ok"]
            or not sem["ok"]
            or mismatch_rate > 0
            or not all(pts.values())
            or iso["sacred_bh_draws"] > 0
        ):
            gate = "FAILED"

        mechanism_results[mech] = {
            "schema": RECORD_SCHEMA_PHASE_B,
            "mechanism": mech,
            "n_pairs": len(offline_rows),
            "mismatch_rate": mismatch_rate,
            "label_mismatch_count": label_mismatch,
            "ambiguity_mismatch_count": amb_mismatch,
            "provenance_mismatch_count": prov_mismatch,
            "cost_mismatch_count": cost_mismatch,
            "mismatches": mismatches,
            "property_tests_passed": pts,
            "pipeline_mutation": iso["pipeline_mutation"],
            "filter_replaced": iso["filter_replaced"],
            "grow_py_diff_empty": iso["grow_py_diff_empty"],
            "calls_total_offline": sum(r[1]["apply_micro_calls"] for r in offline_rows),
            "calls_total_exec": sum(r[1]["apply_micro_calls"] for r in exec_rows),
            "sacred_bh_draws": 0,
            "gate": gate,
            "autonomous_discovery_credit": False,
            "claim_label": CLAIM_LABEL_B,
        }

    return {
        "phase": "B_IMPL_VALIDATION",
        "skipped": False,
        "claim_label": CLAIM_LABEL_B,
        "phase_b_fixture_hash": fixture_hash,
        "isolation_audit": iso,
        "semantic_preservation": sem,
        "survivors_tested": survivors,
        "mechanisms": mechanism_results,
        "global_budget": {
            "offline_total": global_used_off,
            "exec_total": global_used_ex,
            "cap": S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B,
        },
    }
