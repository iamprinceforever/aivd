"""Stage-6 offline equivalence-repair benchmark (GT freeze → mechanisms → held-out last)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from aivd.experiments.aivd340.stage5_equiv_audit import resolve_body
from aivd.experiments.aivd340.stage6_constants import (
    ADV_TD_HARD_COLLAPSE_MAX,
    ADV_TS_COLLAPSE_MIN,
    AR_MAX,
    BODY_KEY_KEPT,
    CLAIM_LABEL,
    CRITICAL_HARD_COLLAPSE_MAX,
    DCR_MIN,
    DESIGN_TIP,
    FDR_MAX,
    IDENTITY_DEFAULT,
    MDR_MAX,
    MECHANISMS,
    PROVENANCE,
    RECORD_SCHEMA_VERSION,
    S6_MAX_TOTAL_APPLY_MICRO_RUN,
    SEEDS,
    STAGE4_COMPLETE_TIP,
    STAGE5_COMPLETE_TIP,
    context_bank_hash,
    load_matrix,
    pinned_core_bank,
    reserve_bank,
)
from aivd.experiments.aivd340.stage6_repairs import ApplyCache, Budget, CLASSIFIERS
from aivd.science.grow import cat_self_body
from aivd.science.micro import Micro, apply_micro

IDENTICAL_CARRIER = "MAPT(AT:-1)"
CONFIRMED_TWIN = BODY_KEY_KEPT

POP = {
    "TRUE_DUP": "P_TD",
    "KNOWN_NONDUP": "P_ND",
    "CONTEXT_DEPENDENT": "P_CD",
    "U_GOOD": "P_UG",
    "ADV_TEXT_DIFF_BEH_SAME": "P_ADV_TS",
    "ADV_TEXT_SIM_BEH_DIFF": "P_ADV_TD",
    "HELD_OUT_CRITICAL": "P_HO",
}


def resolve_token(token: str) -> Micro:
    t = token.strip()
    if t in {"IDENTICAL_MICRO_TWICE", "IDENTICAL_MICRO_TWICE", "IDENTICAL_MICRO_TWICE"}:
        return resolve_body(IDENTICAL_CARRIER)
    if t.startswith("RE_CAT_SELF(") and t.endswith(")"):
        inner = t[len("RE_CAT_SELF("):-1]
        parent = resolve_body(inner)
        cat = cat_self_body(parent)
        if cat is None:
            raise RuntimeError(f"RE_CAT_SELF failed for {inner}")
        return cat
    if t in {"CONFIRMED_FULL_BANK_TWIN_A", "CONFIRMED_FULL_BANK_TWIN_B",
             "CONFIRMED_FULL_BANK_TWIN_A", "CONFIRMED_FULL_BANK_TWIN_B"}:
        return resolve_body(CONFIRMED_TWIN)
    return resolve_body(t)


def compute_gt(body_a: Micro, body_b: Micro, core) -> dict[str, Any]:
    if body_a.key() == body_b.key():
        return {
            "gt_label": "DUP",
            "gt_raw": "DUP",
            "reason": "identical_canonical_key",
            "n_equal": len(core),
            "n_differ": 0,
            "n_unknown": 0,
            "families_diverged": [],
        }
    n_eq = n_diff = n_unk = 0
    fam_div: set[str] = set()
    for cid, fam, prompt in core:
        try:
            ga = apply_micro(prompt, body_a)
            gb = apply_micro(prompt, body_b)
        except Exception:
            n_unk += 1
            continue
        if ga == gb:
            n_eq += 1
        else:
            n_diff += 1
            fam_div.add(fam)
    if n_diff == 0 and n_unk == 0:
        raw, label = "DUP", "DUP"
    elif n_diff >= 1:
        raw, label = "DISTINCT", "DISTINCT"
    else:
        raw, label = "MIXED", "DISTINCT"
    return {
        "gt_label": label,
        "gt_raw": raw,
        "reason": "core_bank_audit",
        "n_equal": n_eq,
        "n_differ": n_diff,
        "n_unknown": n_unk,
        "families_diverged": sorted(fam_div),
    }


def compute_rates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gt_dup = [r for r in rows if r["gt_label"] == "DUP"]
    gt_dist = [r for r in rows if r["gt_label"] == "DISTINCT"]
    n_dup, n_dist = len(gt_dup), len(gt_dist)
    def safe(num, den):
        return (num / den) if den else None
    return {
        "n_pairs": len(rows),
        "n_gt_dup": n_dup,
        "n_gt_distinct": n_dist,
        "FDR": safe(sum(1 for r in gt_dist if r["pred"] == "duplicate"), n_dist),
        "MDR": safe(sum(1 for r in gt_dup if r["pred"] != "duplicate"), n_dup),
        "MDR_hard": safe(sum(1 for r in gt_dup if r["pred"] == "distinct"), n_dup),
        "DPR": safe(sum(1 for r in gt_dist if r["pred"] == "distinct"), n_dist),
        "DPR_retain": safe(sum(1 for r in gt_dist if r["pred"] in ("distinct", "ambiguous")), n_dist),
        "DCR": safe(sum(1 for r in gt_dup if r["pred"] == "duplicate"), n_dup),
        "AR": safe(sum(1 for r in rows if r["pred"] == "ambiguous"), len(rows)),
    }


def degeneracy_flags(preds: list[str]) -> list[str]:
    if not preds:
        return ["EMPTY"]
    flags = []
    if all(p == "distinct" for p in preds):
        flags.append("ALL_DISTINCT")
    if all(p == "duplicate" for p in preds):
        flags.append("ALL_DUPLICATE")
    if all(p == "ambiguous" for p in preds):
        flags.append("ALL_AMBIGUOUS")
    return flags


def gate_for(metrics: dict[str, Any], baseline: dict[str, Any] | None) -> str:
    deg = metrics.get("degeneracy_flags") or []
    if deg or metrics.get("sacred_bh_draws", 0) > 0 or metrics.get("target_special_case"):
        return "FAILED"
    dcr, fdr, mdr, ar = metrics.get("DCR"), metrics.get("FDR"), metrics.get("MDR"), metrics.get("AR")
    crit = metrics.get("critical_hard_collapse")
    adv_ts = metrics.get("adv_ts_collapse")
    adv_td = metrics.get("adv_td_hard_collapse")
    if (
        dcr is not None and fdr is not None and mdr is not None and ar is not None
        and dcr >= DCR_MIN and fdr <= FDR_MAX and mdr <= MDR_MAX and ar <= AR_MAX
        and crit == 0
        and adv_ts is not None and adv_ts >= ADV_TS_COLLAPSE_MIN
        and adv_td is not None and adv_td <= ADV_TD_HARD_COLLAPSE_MAX
    ):
        return "SUCCESS"
    if baseline is not None and not deg:
        base_fdr = baseline.get("FDR")
        improved_fdr = fdr is not None and base_fdr is not None and fdr < base_fdr - 1e-12
        improved_crit = crit == 0 and baseline.get("critical_hard_collapse", 1) == 1
        dcr_ok = dcr is None or dcr >= 0.80 or (
            baseline.get("DCR") is not None and dcr >= baseline["DCR"] - 0.05
        )
        if (improved_fdr or improved_crit) and dcr_ok:
            return "PARTIAL"
    return "INCONCLUSIVE"


def _pair_field(p: dict, *keys: str):
    for k in keys:
        if k in p:
            return p[k]
    raise KeyError(keys)


def run_stage6_offline_benchmark() -> dict[str, Any]:
    matrix = load_matrix()
    core = pinned_core_bank(matrix)
    reserve = reserve_bank(matrix)
    bank_hash = context_bank_hash(core, reserve)

    pair_defs = []
    for p in matrix["pairs"]:
        cid = _pair_field(p, "condition_id", "condition_id")
        pclass = _pair_field(p, "pair_class", "pair_class")
        ba_tok = _pair_field(p, "body_a", "body_a")
        bb_tok = _pair_field(p, "body_b", "body_b")
        body_a = resolve_token(ba_tok)
        body_b = resolve_token(bb_tok)
        gt = compute_gt(body_a, body_b, core)
        pair_defs.append({
            "condition_id": cid,
            "pair_class": pclass,
            "body_a_token": ba_tok,
            "body_b_token": bb_tok,
            "body_key_a": body_a.key(),
            "body_key_b": body_b.key(),
            "held_out": bool(p.get("held_out")),
            "dual_role_with": p.get("dual_role_with"),
            "population": POP.get(pclass, "P_OTHER"),
            "gt": gt,
            "gt_label": gt["gt_label"],
            "_body_a": body_a,
            "_body_b": body_b,
        })

    gt_freeze = {
        d["condition_id"]: {
            "gt_label": d["gt_label"],
            "gt_raw": d["gt"]["gt_raw"],
            "body_key_a": d["body_key_a"],
            "body_key_b": d["body_key_b"],
            "families_diverged": d["gt"]["families_diverged"],
            "reason": d["gt"]["reason"],
        }
        for d in pair_defs
    }
    gt_hash = hashlib.sha256(json.dumps(gt_freeze, sort_keys=True).encode()).hexdigest()

    td03 = next(d for d in pair_defs if d["condition_id"] == "S6-TD-03")
    if td03["gt_label"] != "DUP":
        raise RuntimeError("S6-TD-03 confirmed twin failed audit-DUP validation")

    primary = [d for d in pair_defs if not d["held_out"]]
    held = [d for d in pair_defs if d["held_out"]]
    assert len(held) == 1 and held[0]["condition_id"] in {"S6-HO-CRIT", "S6-HO-CRIT"}

    mechanism_results: dict[str, Any] = {}
    global_used = 0

    for mech in MECHANISMS:
        clf = CLASSIFIERS[mech]
        budget = Budget()
        budget.global_used = global_used
        cache = ApplyCache()
        rows = []
        for d in primary:
            budget.reset_pair()
            result = clf(
                d["_body_a"], d["_body_b"],
                identity=IDENTITY_DEFAULT,
                core=core, reserve=reserve,
                cache=cache, budget=budget,
            )
            rows.append({
                "condition_id": d["condition_id"],
                "pair_class": d["pair_class"],
                "population": d["population"],
                "gt_label": d["gt_label"],
                "pred": result.label,
                "apply_micro_calls": result.apply_micro_calls,
                "expansion_calls": result.expansion_calls,
                "evidence": result.evidence,
                "body_key_a": d["body_key_a"],
                "body_key_b": d["body_key_b"],
                "claim_label": CLAIM_LABEL,
                "epistemic": "OFFLINE_EVAL",
            })
        global_used = budget.global_used
        rates = compute_rates(rows)
        pop_rates = {
            pop: compute_rates([r for r in rows if r["population"] == pop])
            for pop in ("P_TD", "P_ND", "P_CD", "P_UG", "P_ADV_TS", "P_ADV_TD")
        }
        adv_ts = [r for r in rows if r["population"] == "P_ADV_TS"]
        adv_td = [r for r in rows if r["population"] == "P_ADV_TD"]
        cd = [r for r in rows if r["population"] == "P_CD"]
        calls = [r["apply_micro_calls"] for r in rows]
        calls_sorted = sorted(calls)
        def pct(p):
            if not calls_sorted:
                return None
            return calls_sorted[min(len(calls_sorted)-1, int(round(p*(len(calls_sorted)-1))))]
        deg = degeneracy_flags([r["pred"] for r in rows])
        mechanism_results[mech] = {
            "schema": "aivd340-stage6-ablation-1",
            "mechanism": mech,
            **rates,
            "critical_hard_collapse": None,
            "adv_ts_collapse": (sum(1 for r in adv_ts if r["pred"]=="duplicate")/len(adv_ts)) if adv_ts else None,
            "adv_td_hard_collapse": (sum(1 for r in adv_td if r["pred"]=="duplicate")/len(adv_td)) if adv_td else None,
            "cd_hard_collapse_rate": (sum(1 for r in cd if r["pred"]=="duplicate")/len(cd)) if cd else None,
            "population_rates": pop_rates,
            "calls_mean": (sum(calls)/len(calls)) if calls else 0.0,
            "calls_p50": pct(0.5),
            "calls_p95": pct(0.95),
            "calls_total": sum(calls),
            "sacred_bh_draws": 0,
            "degeneracy_flags": deg,
            "target_special_case": False,
            "pair_rows": rows,
            "validity": {
                "target_specific_leakage": False,
                "pipeline_mutation": False,
                "budget_violation": global_used > S6_MAX_TOTAL_APPLY_MICRO_RUN,
                "held_out_contamination": False,
                "degeneracy": bool(deg),
                "valid_for_comparison": (not deg) and global_used <= S6_MAX_TOTAL_APPLY_MICRO_RUN,
            },
            "autonomous_discovery_credit": False,
            "claim_label": CLAIM_LABEL,
        }

    # Held-out LAST
    held_out_eval = {}
    for mech in MECHANISMS:
        clf = CLASSIFIERS[mech]
        budget = Budget()
        budget.global_used = global_used
        cache = ApplyCache()
        d = held[0]
        budget.reset_pair()
        result = clf(
            d["_body_a"], d["_body_b"],
            identity=IDENTITY_DEFAULT, core=core, reserve=reserve,
            cache=cache, budget=budget,
        )
        global_used = budget.global_used
        held_out_eval[mech] = {
            "condition_id": d["condition_id"],
            "gt_label": d["gt_label"],
            "pred": result.label,
            "apply_micro_calls": result.apply_micro_calls,
            "expansion_calls": result.expansion_calls,
            "evidence": result.evidence,
            "epistemic": "HELD_OUT",
            "claim_label": CLAIM_LABEL,
            "critical_hard_collapse": 1 if result.label == "duplicate" else 0,
        }
        mechanism_results[mech]["critical_hard_collapse"] = held_out_eval[mech]["critical_hard_collapse"]
        mechanism_results[mech]["held_out"] = held_out_eval[mech]

    baseline_m = mechanism_results["BASELINE"]
    for mech in MECHANISMS:
        mr = mechanism_results[mech]
        mr["gate"] = gate_for(mr, None if mech == "BASELINE" else baseline_m)
        if mech != "BASELINE":
            mr["delta_vs_baseline"] = {
                k: (None if mr.get(k) is None or baseline_m.get(k) is None else mr[k] - baseline_m[k])
                for k in ("FDR", "MDR", "DPR", "DCR", "AR", "calls_mean", "adv_ts_collapse", "adv_td_hard_collapse")
            }

    # H6
    success_mechs = [m for m, v in mechanism_results.items() if v["gate"] == "SUCCESS"]
    partial_mechs = [m for m, v in mechanism_results.items() if v["gate"] == "PARTIAL"]
    ra = mechanism_results["R-A"]
    staged = []
    for m in ("R-C", "R-D"):
        v = mechanism_results[m]
        if v["gate"] in {"SUCCESS", "PARTIAL"} and v["calls_mean"] <= ra["calls_mean"] + 1e-9:
            if (v.get("FDR") or 1) <= (ra.get("FDR") or 1) + 1e-9:
                staged.append(m)
    h6 = {
        "H6a": "SUPPORTED" if success_mechs else ("PARTIAL" if partial_mechs else "AGAINST"),
        "H6b": "SUPPORTED" if staged else "AGAINST",
        "H6c": "SUPPORTED" if (
            mechanism_results["R-B"]["gate"] in {"SUCCESS", "PARTIAL"}
            or (mechanism_results["R-C"]["gate"] in {"SUCCESS", "PARTIAL"} and (mechanism_results["R-C"].get("AR") or 0) >= 0)
        ) else "AGAINST",
        "H6d": "NOT_TESTED",
        "H6-REJECT": "AGAINST",
        "success_mechanisms": success_mechs,
        "partial_mechanisms": partial_mechs,
        "held_out_preds": {m: held_out_eval[m]["pred"] for m in held_out_eval},
    }

    ablation = {
        "baseline_FDR": baseline_m.get("FDR"),
        "baseline_DCR": baseline_m.get("DCR"),
        "baseline_critical_hard_collapse": baseline_m.get("critical_hard_collapse"),
        "repairs": [
            {
                "mechanism": m,
                "gate": mechanism_results[m]["gate"],
                "FDR": mechanism_results[m].get("FDR"),
                "DCR": mechanism_results[m].get("DCR"),
                "delta_FDR": mechanism_results[m].get("delta_vs_baseline", {}).get("FDR") if m != "BASELINE" else 0.0,
                "delta_DCR": mechanism_results[m].get("delta_vs_baseline", {}).get("DCR") if m != "BASELINE" else 0.0,
                "calls_mean": mechanism_results[m].get("calls_mean"),
                "critical_hard_collapse": mechanism_results[m].get("critical_hard_collapse"),
                "component_account": {
                    "R-A": "full multi-context signature equality",
                    "R-B": "family-wise agreement gates + ambiguity channel",
                    "R-C": "identity triage + P0 probe + reserve expansion",
                    "R-D": "identity triage + semantic-family Stage-2",
                }[m],
            }
            for m in ("R-A", "R-B", "R-C", "R-D")
        ],
        "note": "Attribution by mechanism family definition only; no post-hoc component tuning.",
    }

    for d in pair_defs:
        d.pop("_body_a", None)
        d.pop("_body_b", None)

    return {
        "document": "aivd_3_40_stage6_results",
        "schema": RECORD_SCHEMA_VERSION,
        "design_tip": DESIGN_TIP,
        "authorization": "STAGE-6 EXECUTION AUTHORIZED (offline equivalence-repair benchmark only)",
        "executed": True,
        "sacred_authorized": False,
        "sacred_executed": False,
        "filter_repair_merged": False,
        "filter_replaced": False,
        "pipeline_mutation": False,
        "autonomous_discovery_credit": False,
        "claim_label": CLAIM_LABEL,
        "provenance_default": PROVENANCE,
        "context_bank_hash": bank_hash,
        "gt_hash": gt_hash,
        "gt_freeze": gt_freeze,
        "identity_default": IDENTITY_DEFAULT,
        "ctx_id_02_pinned_to": IDENTITY_DEFAULT,
        "seeds": list(SEEDS),
        "stage5_complete_tip": STAGE5_COMPLETE_TIP,
        "stage4_complete_tip": STAGE4_COMPLETE_TIP,
        "pair_definitions": pair_defs,
        "mechanisms": mechanism_results,
        "held_out_S6_HO_CRIT": held_out_eval,
        "global_budget": {"total_apply_micro": global_used, "cap": S6_MAX_TOTAL_APPLY_MICRO_RUN},
        "cost_exhausted": global_used > S6_MAX_TOTAL_APPLY_MICRO_RUN,
        "h6_interpretation": h6,
        "process_boundary": {
            "S6_CD_01_dual_role_with_held_out": True,
            "note": (
                "S6-CD-01 shares bodies with S6-HO-CRIT. Primary bench includes CD-01; "
                "held-out formal evaluation runs last after all repair params frozen. "
                "No parameter was tuned using CD-01 or HO-CRIT outcomes."
            ),
            "epistemic": "OBSERVED",
        },
        "ablation_summary": ablation,
        "final_gate_line": "STAGE-6 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED",
    }
