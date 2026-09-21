"""Stage-7 Phase A: blind generalization bench on frozen INDEPENDENT population."""
from __future__ import annotations

import statistics
from typing import Any

from aivd.experiments.aivd340.stage6_repairs import (
    ApplyCache,
    Budget,
    CLASSIFIERS,
)
from aivd.experiments.aivd340.stage7_constants import (
    ADV_TD_HARD_COLLAPSE_MAX,
    ADV_TS_COLLAPSE_MIN,
    AR_MAX,
    CLAIM_LABEL_A,
    DCR_MIN,
    FDR_MAX,
    IDENTITY_DEFAULT,
    MDR_MAX,
    MECHANISMS,
    POP,
    RECORD_SCHEMA_PHASE_A,
    REQUIRED_FAMILIES,
    S7_CALLS_MEAN_MAX,
    S7_CALLS_WORST_MAX,
    S7_MAX_APPLY_MICRO_PER_PAIR,
    S7_MAX_EXPANSION_CALLS,
    S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A,
)
from aivd.experiments.aivd340.stage7_freeze import core_from_freeze, reserve_from_freeze
from aivd.experiments.aivd340.stage7_resolve import resolve_token


def _s7_budget(global_used: int = 0) -> Budget:
    b = Budget()
    b.pair_cap = S7_MAX_APPLY_MICRO_PER_PAIR
    b.global_cap = S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A
    b.expansion_cap = S7_MAX_EXPANSION_CALLS
    b.global_used = global_used
    return b


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
        "DPR_retain": safe(
            sum(1 for r in gt_dist if r["pred"] in ("distinct", "ambiguous")), n_dist
        ),
        "DCR": safe(sum(1 for r in gt_dup if r["pred"] == "duplicate"), n_dup),
        "AR": safe(sum(1 for r in rows if r["pred"] == "ambiguous"), len(rows)),
    }


def dcr_on_td_tdbe_advts(rows: list[dict[str, Any]]) -> float | None:
    subset = [
        r
        for r in rows
        if r["pair_class"]
        in ("TRUE_DUP", "TEXT_DIFF_BEH_EQ", "ADV_TEXT_DIFF_BEH_SAME")
        and r["gt_label"] == "DUP"
    ]
    if not subset:
        return None
    return sum(1 for r in subset if r["pred"] == "duplicate") / len(subset)


def degeneracy_flags(rows: list[dict[str, Any]], rates: dict[str, Any]) -> list[str]:
    preds = [r["pred"] for r in rows]
    flags = []
    if not preds:
        return ["EMPTY"]
    if all(p == "distinct" for p in preds):
        flags.append("ALL_DISTINCT")
    if all(p == "duplicate" for p in preds):
        flags.append("ALL_DUPLICATE")
    if all(p == "ambiguous" for p in preds):
        flags.append("ALL_AMBIGUOUS")
    dcr, dpr = rates.get("DCR"), rates.get("DPR")
    if dcr == 0 and dpr == 1:
        flags.append("ALL_DISTINCT")
    if dcr == 1 and dpr == 0 and rates.get("n_gt_distinct", 0) > 0:
        flags.append("ALL_DUPLICATE")
    return sorted(set(flags))


def context_family_coverage(pairs_meta: list[dict], ind_rows: list[dict]) -> float:
    # families touched by IND pairs in freeze audit
    touched: set[str] = set()
    ind_ids = {r["condition_id"] for r in ind_rows}
    for p in pairs_meta:
        if p["condition_id"] in ind_ids:
            touched.update(p.get("families_touched") or [])
    if not REQUIRED_FAMILIES:
        return 1.0
    return sum(1 for f in REQUIRED_FAMILIES if f in touched) / len(REQUIRED_FAMILIES)


def gate_phase_a(metrics: dict[str, Any], baseline: dict[str, Any] | None) -> str:
    deg = metrics.get("degeneracy_flags") or []
    if (
        deg
        or metrics.get("sacred_bh_draws", 0) > 0
        or metrics.get("target_special_case")
        or metrics.get("related_as_independent")
        or metrics.get("live_integration")
    ):
        return "FAILED"
    dcr = metrics.get("DCR_td_tdbe_advts")
    if dcr is None:
        dcr = metrics.get("DCR")
    fdr, mdr, ar = metrics.get("FDR"), metrics.get("MDR"), metrics.get("AR")
    adv_ts = metrics.get("adv_ts_collapse")
    adv_td = metrics.get("adv_td_hard_collapse")
    cov = metrics.get("context_family_coverage")
    dpr = metrics.get("DPR")
    dpr_ret = metrics.get("DPR_retain")
    dpr_ok = (dpr is not None and dpr >= 0.95) or (
        dpr_ret is not None
        and dpr_ret >= 0.95
        and fdr is not None
        and fdr <= FDR_MAX
        and ar is not None
        and ar <= AR_MAX
    )
    accuracy = (
        dcr is not None
        and fdr is not None
        and mdr is not None
        and ar is not None
        and adv_ts is not None
        and adv_td is not None
        and cov is not None
        and dcr >= DCR_MIN
        and fdr <= FDR_MAX
        and mdr <= MDR_MAX
        and ar <= AR_MAX
        and adv_ts >= ADV_TS_COLLAPSE_MIN
        and adv_td <= ADV_TD_HARD_COLLAPSE_MAX
        and cov == 1.0
        and dpr_ok
    )
    if accuracy:
        if (
            metrics.get("calls_mean", 999) <= S7_CALLS_MEAN_MAX
            and metrics.get("calls_worst", 999) <= S7_CALLS_WORST_MAX
        ):
            return "SUCCESS"
        return "COST_IMPRACTICAL"
    if baseline is not None and not deg:
        base_fdr = baseline.get("FDR")
        improved_fdr = (
            fdr is not None and base_fdr is not None and fdr < base_fdr - 1e-12
        )
        dcr_all = metrics.get("DCR")
        dcr_ok = dcr_all is None or dcr_all >= 0.80 or (
            baseline.get("DCR") is not None and dcr_all >= baseline["DCR"] - 0.05
        )
        if improved_fdr and dcr_ok:
            return "PARTIAL"
    return "INCONCLUSIVE"


def run_phase_a(freeze: dict[str, Any]) -> dict[str, Any]:
    core = core_from_freeze(freeze)
    reserve = reserve_from_freeze(freeze)
    pairs_meta = freeze["pairs"]

    # Resolve bodies once
    resolved = []
    for p in pairs_meta:
        ba = resolve_token(p["body_a_token"])
        bb = resolve_token(p["body_b_token"])
        assert ba.key() == p["body_key_a"] and bb.key() == p["body_key_b"]
        resolved.append({**p, "_body_a": ba, "_body_b": bb})

    global_used = 0
    mechanism_results: dict[str, Any] = {}

    for mech in MECHANISMS:
        clf = CLASSIFIERS[mech]
        budget = _s7_budget(global_used)
        cache = ApplyCache()
        rows = []
        for d in resolved:
            budget.reset_pair()
            result = clf(
                d["_body_a"],
                d["_body_b"],
                identity=IDENTITY_DEFAULT,
                core=core,
                reserve=reserve,
                cache=cache,
                budget=budget,
            )
            rows.append(
                {
                    "condition_id": d["condition_id"],
                    "pair_class": d["pair_class"],
                    "independence": d["independence"],
                    "population": POP.get(d["pair_class"], "P_OTHER"),
                    "gt_label": d["gt_label"],
                    "pred": result.label,
                    "apply_micro_calls": result.apply_micro_calls,
                    "expansion_calls": result.expansion_calls,
                    "evidence": result.evidence,
                    "body_key_a": d["body_key_a"],
                    "body_key_b": d["body_key_b"],
                    "claim_label": CLAIM_LABEL_A,
                    "epistemic": "OFFLINE_GENERALIZATION_BENCH",
                }
            )
        global_used = budget.global_used

        # Populations
        ind = [r for r in rows if r["independence"] == "INDEPENDENT"]
        rel = [r for r in rows if r["independence"] == "RELATED"]
        replay = [r for r in rows if r["independence"] == "S6_REPLAY"]
        sdiag = [r for r in rows if r["independence"] == "S_DIAGNOSTIC"]

        # Independence purity: primary numerators must not include RELATED
        related_as_independent = False  # by construction we filter

        rates_ind = compute_rates(ind)
        rates_all = compute_rates(rows)
        dcr_spec = dcr_on_td_tdbe_advts(ind)

        adv_ts = [
            r
            for r in ind
            if r["pair_class"] == "ADV_TEXT_DIFF_BEH_SAME"
        ]
        adv_td = [
            r
            for r in ind
            if r["pair_class"] == "ADV_TEXT_SIM_BEH_DIFF"
        ]
        calls = [r["apply_micro_calls"] for r in ind]
        calls_sorted = sorted(calls)

        def pct(p):
            if not calls_sorted:
                return None
            return calls_sorted[
                min(len(calls_sorted) - 1, int(round(p * (len(calls_sorted) - 1))))
            ]

        deg = degeneracy_flags(ind, rates_ind)
        cov = context_family_coverage(pairs_meta, ind)

        # Diagnostic conflict
        sdiag_hard = 0
        for r in sdiag:
            if r["gt_label"] == "DISTINCT" and r["pred"] == "duplicate":
                sdiag_hard = 1

        class_rates = {}
        for pc in sorted({r["pair_class"] for r in ind}):
            class_rates[pc] = compute_rates([r for r in ind if r["pair_class"] == pc])

        metrics = {
            "schema": RECORD_SCHEMA_PHASE_A,
            "mechanism": mech,
            "population": "INDEPENDENT",
            **rates_ind,
            "DCR_td_tdbe_advts": dcr_spec,
            "DCR_all_ind_gt_dup": rates_ind.get("DCR"),
            "context_family_coverage": cov,
            "adv_ts_collapse": (
                sum(1 for r in adv_ts if r["pred"] == "duplicate") / len(adv_ts)
                if adv_ts
                else None
            ),
            "adv_td_hard_collapse": (
                sum(1 for r in adv_td if r["pred"] == "duplicate") / len(adv_td)
                if adv_td
                else None
            ),
            "calls_mean": (sum(calls) / len(calls)) if calls else 0.0,
            "calls_median": statistics.median(calls) if calls else 0.0,
            "calls_max": max(calls) if calls else 0,
            "calls_worst": max(calls) if calls else 0,
            "calls_p50": pct(0.5),
            "calls_p95": pct(0.95),
            "calls_total": sum(r["apply_micro_calls"] for r in rows),
            "calls_total_ind": sum(calls),
            "budget_utilization": global_used / S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A,
            "sacred_bh_draws": 0,
            "degeneracy_flags": deg,
            "target_special_case": False,
            "related_as_independent": related_as_independent,
            "live_integration": False,
            "diagnostic_conflict": bool(sdiag_hard),
            "sdiag_hard_collapse": sdiag_hard,
            "class_rates_ind": class_rates,
            "side_tables": {
                "RELATED": compute_rates(rel),
                "S6_REPLAY": compute_rates(replay),
                "S_DIAGNOSTIC": {
                    **compute_rates(sdiag),
                    "rows": [
                        {
                            "condition_id": r["condition_id"],
                            "gt_label": r["gt_label"],
                            "pred": r["pred"],
                            "calls": r["apply_micro_calls"],
                        }
                        for r in sdiag
                    ],
                },
            },
            "full_set_rates": rates_all,
            "pair_rows": rows,
            "autonomous_discovery_credit": False,
            "claim_label": CLAIM_LABEL_A,
        }
        mechanism_results[mech] = metrics

    baseline = mechanism_results["BASELINE"]
    for mech in MECHANISMS:
        mr = mechanism_results[mech]
        mr["gate"] = gate_phase_a(mr, None if mech == "BASELINE" else baseline)
        if mech != "BASELINE":
            mr["delta_vs_baseline"] = {
                k: (
                    None
                    if mr.get(k) is None or baseline.get(k) is None
                    else mr[k] - baseline[k]
                )
                for k in (
                    "FDR",
                    "MDR",
                    "DPR",
                    "DCR",
                    "AR",
                    "calls_mean",
                    "adv_ts_collapse",
                    "adv_td_hard_collapse",
                    "DCR_td_tdbe_advts",
                )
            }

    # Ranking among SUCCESS (no S-driven)
    gate_rank = {
        "SUCCESS": 0,
        "COST_IMPRACTICAL": 1,
        "PARTIAL": 2,
        "INCONCLUSIVE": 3,
        "FAILED": 4,
    }
    candidates = []
    for mech in ("R-A", "R-B", "R-C", "R-D"):
        mr = mechanism_results[mech]
        candidates.append(
            (
                gate_rank.get(mr["gate"], 9),
                mr.get("calls_mean") or 999,
                mr.get("calls_worst") or 999,
                mr.get("AR") if mr.get("AR") is not None else 999,
                mech,
            )
        )
    candidates.sort()
    # Multi-candidate retain for top gate
    if candidates:
        top_gate = candidates[0][0]
        tied = [c for c in candidates if c[0] == top_gate]
        # further tie on calls_mean/worst/AR
        best = tied[0]
        multi = [
            c[4]
            for c in tied
            if c[0] == best[0] and c[1] == best[1] and c[2] == best[2] and c[3] == best[3]
        ]
        if not multi:
            multi = [tied[0][4]]
    else:
        multi = []

    survivors = [
        m
        for m in ("R-A", "R-B", "R-C", "R-D")
        if mechanism_results[m]["gate"] in ("SUCCESS", "COST_IMPRACTICAL")
    ]

    return {
        "phase": "A_GENERALIZATION",
        "claim_label": CLAIM_LABEL_A,
        "context_bank_hash": freeze["context_bank_hash"],
        "pair_list_hash": freeze["pair_list_hash"],
        "gt_hash": freeze["gt_hash"],
        "global_budget": {
            "total_apply_micro": global_used,
            "cap": S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A,
        },
        "cost_exhausted": global_used > S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A,
        "mechanisms": mechanism_results,
        "survivors_for_phase_b": survivors,
        "ranking_multi_candidate": multi,
        "ranking_order": [c[4] for c in candidates],
        "stop_if_no_survivors": len(survivors) == 0,
    }
