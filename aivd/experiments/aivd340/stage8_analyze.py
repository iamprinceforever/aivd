"""Phase P4 — Stage-8 analysis, axes, H8* stances, results.md/.json."""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.stage8_constants import (
    CONDITIONS,
    CONDITION_FAMILY,
    D_RATE_DELTA,
    DESIGN_TIP_FULL,
    PLANT_IDS,
    SEEDS,
    STAGE7_COMPLETE_TIP,
)

IST = timezone(timedelta(hours=5, minutes=30))


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _agg(rows: list[dict], cid: str) -> list[dict]:
    return [r for r in rows if r.get("condition_id") == cid and not r.get("error")]


def analyze(
    *,
    matrix: dict[str, Any],
    integration_replay: dict[str, Any],
    controls: dict[str, Any],
    execution_head: str,
) -> dict[str, Any]:
    rows = matrix.get("rows") or []
    per_condition: dict[str, Any] = {}
    per_seed: dict[str, Any] = {}

    for cid in CONDITIONS:
        subset = _agg(rows, cid)
        d_rates = [float((r.get("mechanism") or {}).get("D_rate") or 0) for r in subset]
        surv = [float((r.get("mechanism") or {}).get("surv_rate") or 0) for r in subset]
        repair = [int((r.get("mechanism") or {}).get("repair_calls_total") or 0) for r in subset]
        n_ver = sum(1 for r in subset if r.get("pipeline_verified"))
        n_ind = sum(1 for r in subset if int(r.get("n_independent") or 0) > 0)
        n_strict = sum(1 for r in subset if r.get("strict_independence"))
        n_fw = sum(1 for r in subset if int(r.get("firewall_epoch") or 0) >= 1)
        n_leak = sum(1 for r in subset if r.get("provenance_leak"))
        fate_sum: dict[str, int] = defaultdict(int)
        for r in subset:
            for k, v in ((r.get("mechanism") or {}).get("fate_counts") or {}).items():
                fate_sum[k] += int(v)
        n_pool = sum(int((r.get("mechanism") or {}).get("n_pool_entered") or 0) for r in subset)
        n_d = sum(int((r.get("mechanism") or {}).get("n_pool_removed_D") or 0) for r in subset)
        n_rec = sum(int((r.get("mechanism") or {}).get("n_recursive") or 0) for r in subset)
        n_h = sum(int((r.get("mechanism") or {}).get("n_rediscovered") or 0) for r in subset)
        mean_d = sum(d_rates) / len(d_rates) if d_rates else 0.0
        mean_s = sum(surv) / len(surv) if surv else 0.0
        per_condition[cid] = {
            "family": CONDITION_FAMILY[cid],
            "plant": PLANT_IDS[cid],
            "n_seeds_ok": len(subset),
            "n_errors": sum(1 for r in rows if r.get("condition_id") == cid and r.get("error")),
            "mean_D_rate": round(mean_d, 4),
            "mean_surv_rate": round(mean_s, 4),
            "mean_repair_calls": round(sum(repair) / len(repair), 3) if repair else 0.0,
            "sum_pool_entered": n_pool,
            "sum_D": n_d,
            "n_verified": n_ver,
            "n_independent": n_ind,
            "n_strict_independence": n_strict,
            "n_firewall_epoch_ge1": n_fw,
            "n_leak": n_leak,
            "n_recursive_bodies": n_rec,
            "n_rediscovered_bodies": n_h,
            "fate_counts_sum": dict(fate_sum),
            "per_seed_D_rate": {str(r["seed"]): (r.get("mechanism") or {}).get("D_rate") for r in subset},
            "per_seed_verified": {str(r["seed"]): bool(r.get("pipeline_verified")) for r in subset},
            "budgets_used": [r.get("budget_used") for r in subset],
            "terminal_states": sorted({str(r.get("terminal_state")) for r in subset}),
        }

    for r in rows:
        key = f"{r.get('condition_id')}:seed{r.get('seed')}"
        mech = r.get("mechanism") or {}
        per_seed[key] = {
            "condition_id": r.get("condition_id"),
            "seed": r.get("seed"),
            "family": r.get("family"),
            "terminal_state": r.get("terminal_state"),
            "pipeline_verified": r.get("pipeline_verified"),
            "firewall_epoch": r.get("firewall_epoch"),
            "n_independent": r.get("n_independent"),
            "strict_independence": r.get("strict_independence"),
            "provenance_leak": r.get("provenance_leak"),
            "budget_used": r.get("budget_used"),
            "D_rate": mech.get("D_rate"),
            "surv_rate": mech.get("surv_rate"),
            "n_pool_entered": mech.get("n_pool_entered"),
            "n_pool_removed_D": mech.get("n_pool_removed_D"),
            "repair_calls_total": mech.get("repair_calls_total"),
            "fate_counts": mech.get("fate_counts"),
            "s_diagnostic": r.get("s_diagnostic"),
            "error": r.get("error"),
            "elapsed_s": r.get("elapsed_s"),
        }

    # Axes
    axis1 = bool(integration_replay.get("axis1_pass")) and bool(controls.get("overall_pass"))
    # semantic preservation: floor/BH/invent_cap/no grow.py mutation
    c2 = (controls.get("checks") or {}).get("C2_baseline", {})
    c6 = (controls.get("checks") or {}).get("C6_budget", {})
    c7 = (controls.get("checks") or {}).get("C7_firewall", {})
    axis2 = bool(c2.get("pass")) and bool(c6.get("pass")) and bool(c7.get("pass"))
    # invent parity: compare invent-related occupancy across conditions holding seed
    invent_parity_issues = []
    for seed in SEEDS:
        base = next((r for r in rows if r.get("condition_id") == "S8-BASELINE" and r.get("seed") == seed), None)
        if not base or base.get("error"):
            continue
        b_occ = base.get("occupancy")
        for cid in ("S8-RA", "S8-RC", "S8-RD"):
            rr = next((r for r in rows if r.get("condition_id") == cid and r.get("seed") == seed), None)
            if not rr or rr.get("error"):
                continue
            # occupancy may legitimately differ post-equiv; only flag if invent_cap/floor drifted
            if int(rr.get("REDISCOVERY_FLOOR") or 0) != 5 or int(rr.get("INVENT_CAP") or 0) != 48:
                invent_parity_issues.append({"seed": seed, "cid": cid, "reason": "lock_drift"})
            if int(rr.get("BH") or 0) != 48:
                invent_parity_issues.append({"seed": seed, "cid": cid, "reason": "bh_drift"})
    if invent_parity_issues:
        axis2 = False

    baseline_d = per_condition["S8-BASELINE"]["mean_D_rate"]
    mechanism_pass: dict[str, Any] = {}
    for cid in ("S8-RA", "S8-RC", "S8-RD"):
        d = per_condition[cid]["mean_D_rate"]
        delta = baseline_d - d  # positive if repair reduces D
        # paired seed direction
        base_seeds = per_condition["S8-BASELINE"]["per_seed_D_rate"]
        rep_seeds = per_condition[cid]["per_seed_D_rate"]
        directions = []
        for s in SEEDS:
            bd = base_seeds.get(str(s))
            rd = rep_seeds.get(str(s))
            if bd is None or rd is None:
                continue
            directions.append(float(rd) < float(bd))
        n_dir = sum(1 for x in directions if x)
        # attribution: any equiv label flip evidence
        flips = 0
        for r in _agg(rows, cid):
            for ed in (r.get("mechanism") or {}).get("equiv_decisions") or []:
                if ed.get("label") in ("distinct", "ambiguous", "retain") and ed.get("action") == "keep":
                    flips += 1
        unobs_rates = []
        for r in _agg(rows, cid):
            mech = r.get("mechanism") or {}
            fates = mech.get("fates") or {}
            n = len(fates) or 1
            u = sum(1 for v in fates.values() if v == "UNOBSERVED")
            unobs_rates.append(u / n)
        mean_unobs = sum(unobs_rates) / len(unobs_rates) if unobs_rates else 1.0
        pass3 = (
            axis1
            and axis2
            and (delta >= D_RATE_DELTA or n_dir >= 5)
            and flips >= 1
            and mean_unobs <= 0.05
        )
        # null if no shift
        null = delta < D_RATE_DELTA and n_dir < 5
        mechanism_pass[cid] = {
            "axis3_pass": bool(pass3) and not null,
            "axis3_null": bool(null),
            "baseline_mean_D": baseline_d,
            "family_mean_D": d,
            "delta": round(delta, 4),
            "seeds_D_decreased": n_dir,
            "seeds_compared": len(directions),
            "attribution_keep_events": flips,
            "mean_unobserved_rate": round(mean_unobs, 4),
        }

    axis3_any = any(v["axis3_pass"] for v in mechanism_pass.values())

    # Axis 4 — report only; H8c support
    h8c = {}
    for cid in ("S8-RA", "S8-RC", "S8-RD"):
        base_v = per_condition["S8-BASELINE"]["per_seed_verified"]
        rep_v = per_condition[cid]["per_seed_verified"]
        uplift = sum(
            1
            for s in SEEDS
            if rep_v.get(str(s)) and not base_v.get(str(s))
        )
        same_dir = sum(
            1
            for s in SEEDS
            if bool(rep_v.get(str(s))) >= bool(base_v.get(str(s)))
        )
        h8c[cid] = {
            "verify_uplift_seeds": uplift,
            "verify_base": per_condition["S8-BASELINE"]["n_verified"],
            "verify_repair": per_condition[cid]["n_verified"],
            "support_h8c": bool(mechanism_pass[cid]["axis3_pass"]) and (uplift >= 1 or same_dir >= 5),
        }

    # Axis 5
    leak_ok = all(int(per_condition[c]["n_leak"]) == 0 for c in CONDITIONS)
    axis5 = leak_ok and bool((controls.get("checks") or {}).get("C3_leakage", {}).get("pass"))

    # Axis 6 — report
    axis6_report = {
        cid: {
            "I_related_recursive_bodies": per_condition[cid]["n_recursive_bodies"],
            "H_rediscovered": per_condition[cid]["n_rediscovered_bodies"],
        }
        for cid in CONDITIONS
    }

    # H8 stances
    h8 = {
        "H8a": "supported" if (axis1 and axis2) else "not_supported",
        "H8b": "supported" if axis3_any else "not_supported",
        "H8c": "supported"
        if any(v.get("support_h8c") for v in h8c.values())
        else "not_supported",
        "H8d": "supported" if axis5 else "not_supported",
        "H8e": "supported"
        if any(per_condition[c]["n_recursive_bodies"] > per_condition["S8-BASELINE"]["n_recursive_bodies"] for c in ("S8-RA", "S8-RC", "S8-RD"))
        else "report_only_null_ok",
        "H8f": "applicable",  # S-null with mechanism change
        "H8-REJECT": "not_supported",
    }
    # Reject checks
    reject_reasons = []
    if not bool((controls.get("checks") or {}).get("C9_multi_candidate", {}).get("pass")):
        reject_reasons.append("C9")
        h8["H8-REJECT"] = "supported"
    if not bool((controls.get("checks") or {}).get("C10_s_non_injection", {}).get("pass")):
        reject_reasons.append("C10")
        h8["H8-REJECT"] = "supported"
    if any(int(r.get("BH") or 48) > 48 or int(r.get("INVENT_CAP") or 48) > 48 or int(r.get("REDISCOVERY_FLOOR") or 5) < 5 for r in rows if not r.get("error")):
        reject_reasons.append("budget_cheat")
        h8["H8-REJECT"] = "supported"

    # Overall gate
    if h8["H8-REJECT"] == "supported" or not axis1 or not axis2:
        gate = "FAILED"
        reading = "protocol/integration/semantics failure or H8-REJECT"
    elif axis1 and axis2 and axis3_any:
        # SUCCESS if axes 1+2+3; 4-6 reported
        gate = "SUCCESS"
        reading = "integration+semantics PASS; mechanism change for >=1 survivor; discovery/rediscovery/recursion reported"
    elif axis1 and axis2 and not axis3_any:
        gate = "PARTIAL"
        reading = "integration+semantics PASS; no threshold-meeting mechanism change (null axis 3)"
    else:
        gate = "INCONCLUSIVE"
        reading = "instrumentation or separation insufficient"

    surviving = []
    if gate in ("SUCCESS", "PARTIAL"):
        for cid in ("S8-RA", "S8-RC", "S8-RD"):
            if mechanism_pass[cid]["axis3_pass"] or (axis1 and axis2):
                # retain ties among practical survivors that remain valid
                surviving.append(cid)
        # On SUCCESS, retain those with axis3_pass; if none but PARTIAL, retain all three as still-valid integrations
        if gate == "SUCCESS":
            surviving = [c for c in ("S8-RA", "S8-RC", "S8-RD") if mechanism_pass[c]["axis3_pass"]]
            if not surviving:
                surviving = ["S8-RA", "S8-RC", "S8-RD"]  # should not happen
        else:
            surviving = ["S8-RA", "S8-RC", "S8-RD"]

    # S diagnostic aggregate
    s_diag = {
        "n_verified_by_condition": {c: per_condition[c]["n_verified"] for c in CONDITIONS},
        "note": "S VERIFIED neither necessary nor sufficient",
    }

    unexpected = []
    for r in rows:
        if r.get("error"):
            unexpected.append({"run": f"{r.get('condition_id')}:seed{r.get('seed')}", "error": r.get("error")})
    if invent_parity_issues:
        unexpected.append({"invent_parity_issues": invent_parity_issues})

    results = {
        "document": "aivd_3_40_stage8_results",
        "recorded_at_ist": _ist_now(),
        "design_tip": DESIGN_TIP_FULL,
        "stage7_complete_tip": STAGE7_COMPLETE_TIP,
        "execution_head": execution_head,
        "authorization": "STAGE-8 EXECUTION AUTHORIZED",
        "gate": gate,
        "gate_line": f"STAGE-8 COMPLETE: {gate} — {reading}",
        "reading": reading,
        "axes": {
            "1_INTEGRATION_VALIDITY": {"pass": axis1, "integration_replay": integration_replay.get("axis1_pass"), "controls": controls.get("overall_pass")},
            "2_DISCOVERY_SEMANTICS_PRESERVATION": {"pass": axis2, "invent_parity_issues": invent_parity_issues},
            "3_MECHANISM_CHANGE": {"any_pass": axis3_any, "by_family": mechanism_pass},
            "4_REAL_MODEL_DISCOVERY_OUTCOME": {"report": True, "h8c": h8c, "per_condition_verified": {c: per_condition[c]["n_verified"] for c in CONDITIONS}},
            "5_INDEPENDENT_REDISCOVERY": {"pass": axis5, "leak_ok": leak_ok},
            "6_RECURSIVE_GENERATION": {"report": axis6_report},
        },
        "hypotheses": h8,
        "reject_reasons": reject_reasons,
        "surviving_condition_set": surviving,
        "single_winner": None,
        "ranking": None,
        "per_condition": per_condition,
        "per_seed": per_seed,
        "s_diagnostic": s_diag,
        "budget_firewall_accounting": {
            "BH": 48,
            "INVENT_CAP": 48,
            "REDISCOVERY_FLOOR": 5,
            "repair_calls_mean_by_condition": {c: per_condition[c]["mean_repair_calls"] for c in CONDITIONS},
            "budget_cheat_flag": h8["H8-REJECT"] == "supported" and "budget_cheat" in reject_reasons,
        },
        "provenance_leakage": {
            "n_leak_by_condition": {c: per_condition[c]["n_leak"] for c in CONDITIONS},
            "fresh_plant_ids": dict(PLANT_IDS),
        },
        "mechanism_localization": {
            "change_surface": "_keep step 6 only",
            "baseline_rule": "got in behaviors.values()",
            "families": ["R-A", "R-C", "R-D"],
            "excluded": ["R-B"],
        },
        "evidence_separated": {
            "mechanism": mechanism_pass,
            "discovery": {c: {"n_verified": per_condition[c]["n_verified"], "terminals": per_condition[c]["terminal_states"]} for c in CONDITIONS},
            "rediscovery": {c: {"n_independent": per_condition[c]["n_independent"], "n_strict": per_condition[c]["n_strict_independence"], "H_bodies": per_condition[c]["n_rediscovered_bodies"]} for c in CONDITIONS},
            "recursion": axis6_report,
        },
        "unexpected_observations": unexpected,
        "next_authorization_required": (
            "STAGE-9 DESIGN AUTHORIZATION REQUIRED (do not auto-start). "
            "Also: any production merge of a surviving repair into default grow.py "
            "requires SEPARATE authorization beyond Stage-8 COMPLETE. "
            "Do not modify 3.38/3.39; do not rewrite Stage-7 conclusions; "
            "do not retune R-A/R-C/R-D; do not revive R-B without design revision."
        ),
        "final_gate": f"STAGE-8 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED",
    }
    return results


def write_results_md(results: dict[str, Any], path: Path) -> None:
    pc = results["per_condition"]
    lines = [
        "# AIVD 3.40 Stage-8 RESULTS — Live Equivalence Integration + Fresh-Plant Discovery",
        "",
        f"**Recorded:** {results['recorded_at_ist']}  ",
        f"**Design tip:** `{results['design_tip']}`  ",
        f"**Stage-7 COMPLETE tip:** `{results['stage7_complete_tip']}`  ",
        f"**Execution head:** `{results['execution_head']}`  ",
        f"**Authorization:** Stage-8 EXECUTION  ",
        "",
        f"## Gate",
        "",
        f"```",
        results["gate_line"],
        results["final_gate"],
        f"```",
        "",
        f"**Reading:** {results['reading']}",
        "",
        f"**Surviving condition set (no single winner):** `{results['surviving_condition_set']}`",
        "",
        "## Axes",
        "",
    ]
    for k, v in results["axes"].items():
        lines.append(f"- **{k}**: `{json.dumps(v, default=str)[:500]}`")
    lines += ["", "## Hypotheses", ""]
    for k, v in results["hypotheses"].items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Per-condition aggregates", "", "| Condition | Family | D_rate | surv | verified | independent | strict | repair_calls |", "|---|---|---|---|---|---|---|---|"]
    for cid in CONDITIONS:
        a = pc[cid]
        lines.append(
            f"| {cid} | {a['family']} | {a['mean_D_rate']} | {a['mean_surv_rate']} | {a['n_verified']}/7 | {a['n_independent']}/7 | {a['n_strict_independence']}/7 | {a['mean_repair_calls']} |"
        )
    lines += ["", "## Evidence (separated)", ""]
    for k, v in results["evidence_separated"].items():
        lines.append(f"### {k}")
        lines.append("```json")
        lines.append(json.dumps(v, indent=2, default=str)[:4000])
        lines.append("```")
        lines.append("")
    lines += [
        "## Semantic preservation",
        "",
        f"Axis-2 pass: `{results['axes']['2_DISCOVERY_SEMANTICS_PRESERVATION']['pass']}`",
        "",
        "## Provenance / leakage",
        "",
        f"`{results['provenance_leakage']}`",
        "",
        "## Budget / firewall",
        "",
        f"`{results['budget_firewall_accounting']}`",
        "",
        "## Unexpected",
        "",
        f"`{results['unexpected_observations']}`",
        "",
        "## Next authorization (DO NOT EXECUTE)",
        "",
        results["next_authorization_required"],
        "",
        "## Stopping",
        "",
        "Stage-8 COMPLETE. Do not auto-start Stage-9. Do not modify 3.38/3.39. Do not rewrite Stage-7.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")
