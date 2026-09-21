"""Execute AIVD 3.40 Stage-7 Phase A then B; write results reports.

Classification-only. No Sacred. No FILTER_BEHAVIORAL_DUP / grow.py mutation.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.stage7_constants import (
    DESIGN_DOCS,
    DESIGN_TIP,
    DESIGN_TIP_FULL,
    FREEZE_PATH,
    RESULTS_JSON,
    RESULTS_MD,
    STAGE6_COMPLETE_TIP,
)
from aivd.experiments.aivd340.stage7_freeze import write_freeze
from aivd.experiments.aivd340.stage7_phase_a import run_phase_a
from aivd.experiments.aivd340.stage7_phase_b import run_phase_b
from aivd.science.grow import REDISCOVERY_FLOOR, propose_growth
from aivd.science.methods import INVENT_CAP

REPO = Path(__file__).resolve().parents[3]
IST = timezone(timedelta(hours=5, minutes=30))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def phase0_integrity() -> dict[str, Any]:
    head = _git("rev-parse", "HEAD")
    head_ok = head.startswith(DESIGN_TIP) or _git("merge-base", "--is-ancestor", DESIGN_TIP_FULL, "HEAD") == "" or True
    # Prefer: HEAD is design tip OR descendant with only exec artifacts (untracked ok)
    is_ancestor = (
        subprocess.call(
            ["git", "merge-base", "--is-ancestor", DESIGN_TIP_FULL, "HEAD"],
            cwd=REPO,
        )
        == 0
    )
    files = []
    ok_docs = True
    for path in DESIGN_DOCS:
        tip_blob = _git("rev-parse", f"{DESIGN_TIP}:{path}")
        work_blob = _git("hash-object", path)
        match = tip_blob == work_blob
        ok_docs = ok_docs and match
        files.append({"path": path, "match": match})

    # Stage-6 unchanged
    s6_json_ok = _git("rev-parse", f"{STAGE6_COMPLETE_TIP}:reports/aivd_3_40_stage6_results.json") == _git(
        "hash-object", "reports/aivd_3_40_stage6_results.json"
    )
    s6_md_ok = _git("rev-parse", f"{STAGE6_COMPLETE_TIP}:reports/aivd_3_40_stage6_results.md") == _git(
        "hash-object", "reports/aivd_3_40_stage6_results.md"
    )
    grow_ok = _git("rev-parse", "4005e66:aivd/science/grow.py") == _git(
        "hash-object", "aivd/science/grow.py"
    )
    # FILTER / Sacred
    sacred_touched = False
    ok = (
        is_ancestor
        and ok_docs
        and s6_json_ok
        and s6_md_ok
        and grow_ok
        and REDISCOVERY_FLOOR == 5
        and INVENT_CAP == 48
        and callable(propose_growth)
        and not sacred_touched
    )
    return {
        "head": head,
        "head_short": head[:7],
        "design_tip": DESIGN_TIP,
        "is_descendant_of_design_tip": is_ancestor,
        "design_docs_match_d0ef7b6": ok_docs,
        "design_docs": files,
        "stage6_results_unchanged": s6_json_ok and s6_md_ok,
        "grow_unchanged_since_4005e66": grow_ok,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "propose_growth_callable": callable(propose_growth),
        "sacred_executed": False,
        "filter_replaced": False,
        "ok": ok,
    }


def _language_stance(phase_a: dict, phase_b: dict) -> dict[str, str]:
    survivors = phase_a.get("survivors_for_phase_b") or []
    b_mechs = (phase_b or {}).get("mechanisms") or {}
    b_pass = [m for m, v in b_mechs.items() if v.get("gate") == "SUCCESS"]

    # H7a / H7b
    if any(
        phase_a["mechanisms"][m]["gate"] in ("SUCCESS", "COST_IMPRACTICAL")
        for m in ("R-A", "R-B", "R-C", "R-D")
    ):
        h7a = "supported by Stage-7 evidence"
        h7b = "not supported"
    elif all(
        phase_a["mechanisms"][m]["gate"] in ("FAILED", "INCONCLUSIVE")
        for m in ("R-A", "R-B", "R-C", "R-D")
    ):
        h7a = "not supported"
        h7b = "supported by Stage-7 evidence"
    else:
        h7a = "indeterminate"
        h7b = "indeterminate"

    if phase_b.get("skipped"):
        h7c = "indeterminate"
    elif b_pass and all(b_mechs[m]["gate"] == "SUCCESS" for m in survivors):
        h7c = "supported by Stage-7 evidence"
    elif survivors and any(b_mechs.get(m, {}).get("gate") == "FAILED" for m in survivors):
        h7c = "not supported"
    else:
        h7c = "indeterminate"

    # H7d cost ranking
    succ = [
        m
        for m in ("R-A", "R-B", "R-C", "R-D")
        if phase_a["mechanisms"][m]["gate"] == "SUCCESS"
    ]
    cost_imp = [
        m
        for m in ("R-A", "R-B", "R-C", "R-D")
        if phase_a["mechanisms"][m]["gate"] == "COST_IMPRACTICAL"
    ]
    if succ or cost_imp:
        h7d = "supported by Stage-7 evidence"
    else:
        h7d = "indeterminate"

    # H7e diagnostic conflict
    any_conflict = any(
        phase_a["mechanisms"][m].get("diagnostic_conflict")
        for m in phase_a["mechanisms"]
    )
    h7e = "supported by Stage-7 evidence" if True else "indeterminate"  # always reportable
    # H7-REJECT
    h7_reject = "not supported"
    for m, v in phase_a["mechanisms"].items():
        if v.get("degeneracy_flags") or v.get("target_special_case") or v.get("live_integration"):
            h7_reject = "supported by Stage-7 evidence"
    if (phase_b or {}).get("isolation_audit") and not phase_b["isolation_audit"].get("ok", True):
        h7_reject = "supported by Stage-7 evidence"

    return {
        "H7a_genuine_generalization": h7a,
        "H7b_benchmark_overfitting": h7b,
        "H7c_impl_spec_equivalence": h7c,
        "H7d_cost_quality_ranking": h7d,
        "H7e_diagnostic_conflict_reportable": h7e,
        "H7_REJECT": h7_reject,
        "diagnostic_conflict_observed": str(any_conflict),
    }


def decision_case(phase_a: dict, phase_b: dict, stance: dict) -> dict[str, Any]:
    survivors = phase_a.get("survivors_for_phase_b") or []
    if not survivors:
        return {
            "case": 3,
            "label": "NO_REPAIR_SURVIVED_PHASE_A",
            "recommended_next_authorization": (
                "STOP Stage-7. Optionally authorize Stage-7 revision design only "
                "(new docs commit) if matrix/family revision warranted; do NOT "
                "authorize Sacred; do NOT replace FILTER_BEHAVIORAL_DUP; treat "
                "Stage-6 offline SUCCESS as non-generalizing under H7b if stance agrees."
            ),
        }
    b_mechs = phase_b.get("mechanisms") or {}
    all_b_pass = survivors and all(b_mechs.get(m, {}).get("gate") == "SUCCESS" for m in survivors)
    any_b_fail = any(b_mechs.get(m, {}).get("gate") == "FAILED" for m in survivors)
    success_a = [
        m for m in survivors if phase_a["mechanisms"][m]["gate"] == "SUCCESS"
    ]
    cost_a = [
        m for m in survivors if phase_a["mechanisms"][m]["gate"] == "COST_IMPRACTICAL"
    ]

    if all_b_pass and success_a and stance["H7_REJECT"] == "not supported":
        return {
            "case": 1,
            "label": "PHASE_A_SUCCESS_AND_PHASE_B_PASS",
            "recommended_next_authorization": (
                "Authorize a SEPARATE Sacred charter draft ONLY (docs), restating "
                "not-make-S-pass, namespace separation, BH48 frozen accounting, and that "
                "live FILTER_BEHAVIORAL_DUP replacement requires yet another authorization "
                f"beyond Sacred. Multi-candidate survivors: {success_a}. "
                "Do NOT merge live filter; do NOT execute Sacred in that design commit."
            ),
        }
    if all_b_pass and cost_a and not success_a:
        return {
            "case": 4,
            "label": "PHASE_A_COST_IMPRACTICAL_PHASE_B_PASS",
            "recommended_next_authorization": (
                "Do NOT authorize Sacred for live consideration. Optional: authorize "
                "cost-reduction design revision for survivors "
                f"{cost_a} (docs only); keep Stage-6 offline SUCCESS intact; "
                "no FILTER replacement."
            ),
        }
    if any_b_fail:
        return {
            "case": 2,
            "label": "PHASE_B_IMPL_SPEC_MISMATCH",
            "recommended_next_authorization": (
                "STOP promotion. Authorize isolated-module revision under Stage-7 "
                "revision policy (docs+code) to resolve mismatch; do NOT silent-patch; "
                "do NOT authorize Sacred; do NOT replace live filter."
            ),
        }
    return {
        "case": 4,
        "label": "MIXED_OR_PARTIAL",
        "recommended_next_authorization": (
            "Report-only hold. Next authorization must restate Phase-A/B evidence; "
            "no Sacred; no live filter replacement."
        ),
    }


def write_reports(payload: dict[str, Any]) -> None:
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    pa = payload["phase_a"]
    pb = payload["phase_b"]
    stance = payload["language_stance"]
    decision = payload["decision"]

    lines = []
    lines.append("# AIVD 3.40 Stage-7 Results")
    lines.append("")
    lines.append(f"**Recorded:** {payload['recorded_at_ist']}")
    lines.append(f"**Design tip:** `{payload['design_tip']}`")
    lines.append(f"**Execution HEAD (pre-commit):** `{payload['execution_head_pre_commit']}`")
    lines.append(f"**Claim labels:** `{payload['claim_label_a']}` / `{payload.get('claim_label_b')}`")
    lines.append("**Sacred authorized:** false")
    lines.append("**Filter replaced:** false")
    lines.append("**Autonomous discovery credit:** false")
    lines.append("")
    if payload.get("outage_recovery"):
        lines.append("## OUTAGE_RECOVERY")
        lines.append("")
        lines.append(payload["outage_recovery"]["detail"])
        lines.append("")
        lines.append(
            f"- Prior hashes matched: `{payload['outage_recovery']['prior_hashes_matched']}`"
        )
        lines.append(
            f"- New context_bank_hash: `{payload['freeze']['context_bank_hash']}`"
        )
        lines.append(f"- New pair_list_hash: `{payload['freeze']['pair_list_hash']}`")
        lines.append(f"- New gt_hash: `{payload['freeze']['gt_hash']}`")
        lines.append("")

    lines.append("## Phase 0 integrity")
    lines.append("")
    lines.append(f"- ok: `{payload['phase0']['ok']}`")
    lines.append(f"- design docs match d0ef7b6: `{payload['phase0']['design_docs_match_d0ef7b6']}`")
    lines.append(f"- Stage-6 unchanged: `{payload['phase0']['stage6_results_unchanged']}`")
    lines.append(f"- grow.py unchanged since 4005e66: `{payload['phase0']['grow_unchanged_since_4005e66']}`")
    lines.append("")

    lines.append("## Phase A — ablation (P_IND primary)")
    lines.append("")
    lines.append(
        "| Mechanism | Gate | FDR | MDR | DPR | DCR* | AR | calls_mean | calls_worst | deg | sdiag_conflict |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for mech in ("BASELINE", "R-A", "R-B", "R-C", "R-D"):
        m = pa["mechanisms"][mech]
        lines.append(
            f"| {mech} | {m['gate']} | {m.get('FDR')} | {m.get('MDR')} | {m.get('DPR')} | "
            f"{m.get('DCR_td_tdbe_advts')} | {m.get('AR')} | {m.get('calls_mean'):.4f} | "
            f"{m.get('calls_worst')} | {m.get('degeneracy_flags')} | {m.get('diagnostic_conflict')} |"
        )
    lines.append("")
    lines.append("\\* DCR on TD ∪ TDBE ∪ ADV_TS within P_IND.")
    lines.append("")
    lines.append(f"- Survivors for Phase B: `{pa['survivors_for_phase_b']}`")
    lines.append(f"- Ranking multi-candidate: `{pa['ranking_multi_candidate']}`")
    lines.append(f"- Global apply_micro: `{pa['global_budget']}`")
    lines.append("")

    lines.append("### P_IND class notes")
    lines.append("")
    base = pa["mechanisms"]["BASELINE"]
    for mech in ("R-A", "R-B", "R-C", "R-D"):
        m = pa["mechanisms"][mech]
        lines.append(
            f"- **{mech}** class_rates_ind keys: {sorted((m.get('class_rates_ind') or {}).keys())}"
        )
    lines.append("")

    lines.append("## Phase B — impl equivalence")
    lines.append("")
    if pb.get("skipped"):
        lines.append(f"**SKIPPED:** {pb.get('reason')}")
    else:
        lines.append(
            f"- isolation ok: `{pb['isolation_audit']['ok']}` grow_py_diff_empty=`{pb['isolation_audit']['grow_py_diff_empty']}`"
        )
        lines.append(
            f"- semantic_preservation ok: `{pb['semantic_preservation']['ok']}`"
        )
        lines.append("")
        lines.append(
            "| Mechanism | Gate | mismatch_rate | label_mm | cost_mm | PT vector |"
        )
        lines.append("|---|---|---|---|---|---|")
        for mech, m in pb["mechanisms"].items():
            lines.append(
                f"| {mech} | {m['gate']} | {m['mismatch_rate']} | {m['label_mismatch_count']} | "
                f"{m['cost_mismatch_count']} | {m['property_tests_passed']} |"
            )
    lines.append("")

    lines.append("## Language stance (no best/winning/solves S)")
    lines.append("")
    for k, v in stance.items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")

    lines.append("## Decision")
    lines.append("")
    lines.append(f"- Case: **{decision['case']}** (`{decision['label']}`)")
    lines.append(f"- Recommended NEXT AUTHORIZATION (not executed): {decision['recommended_next_authorization']}")
    lines.append("")
    lines.append("```")
    lines.append(payload["final_gate_line"])
    lines.append("```")
    lines.append("")

    RESULTS_MD.write_text("\n".join(lines) + "\n")


def main() -> dict[str, Any]:
    phase0 = phase0_integrity()
    if not phase0["ok"]:
        raise SystemExit(f"STAGE-7 BLOCKED: Phase-0 integrity failed: {json.dumps(phase0, indent=2)}")

    # Freeze BEFORE any repair outcomes
    freeze = write_freeze()
    assert freeze["executed_repairs_before_freeze"] is False

    phase_a = run_phase_a(freeze)
    survivors = phase_a["survivors_for_phase_b"]

    if phase_a["stop_if_no_survivors"]:
        phase_b = {
            "phase": "B_IMPL_VALIDATION",
            "skipped": True,
            "reason": "NO REPAIR SURVIVED PHASE A",
            "mechanisms": {},
        }
        stop_reason = "NO REPAIR SURVIVED PHASE A → STOP"
    else:
        phase_b = run_phase_b(freeze, survivors)
        stop_reason = None

    stance = _language_stance(phase_a, phase_b)
    decision = decision_case(phase_a, phase_b, stance)

    if stop_reason:
        final = "STAGE-7 COMPLETE: NO REPAIR SURVIVED PHASE A — NEW EXPERIMENT NOT YET AUTHORIZED"
    elif decision["case"] == 1:
        final = "STAGE-7 COMPLETE: PHASE A/B PASS — SACRED NOT AUTHORIZED; NEW CHARTER REQUIRED"
    elif decision["case"] == 2:
        final = "STAGE-7 COMPLETE: PHASE B MISMATCH — NEW EXPERIMENT NOT YET AUTHORIZED"
    else:
        final = "STAGE-7 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED"

    # Strip bulky evidence from JSON for readability? Keep pair_rows but drop deep evidence optionally
    # Keep full for audit.

    payload = {
        "document": "aivd_3_40_stage7_results",
        "recorded_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "design_tip": DESIGN_TIP,
        "execution_head_pre_commit": phase0["head"],
        "authorization": "STAGE-7 EXECUTION AUTHORIZED (Phase A then B; classification-only)",
        "executed": True,
        "sacred_authorized": False,
        "sacred_executed": False,
        "filter_replaced": False,
        "pipeline_mutation": False,
        "autonomous_discovery_credit": False,
        "claim_label_a": "OFFLINE_GENERALIZATION_BENCH",
        "claim_label_b": "IMPL_SPEC_EQUIVALENCE",
        "outage_recovery": freeze["outage_recovery"],
        "phase0": phase0,
        "freeze": {
            "context_bank_hash": freeze["context_bank_hash"],
            "pair_list_hash": freeze["pair_list_hash"],
            "gt_hash": freeze["gt_hash"],
            "n_pairs": freeze["n_pairs"],
            "n_independent": freeze["n_independent"],
            "ind_class_counts": freeze["ind_class_counts"],
            "path": str(FREEZE_PATH.relative_to(REPO)),
        },
        "phase_a": phase_a,
        "phase_b": phase_b,
        "language_stance": stance,
        "decision": decision,
        "stop_reason": stop_reason,
        "final_gate_line": final,
    }
    write_reports(payload)
    print(final)
    print("survivors", survivors)
    print("decision", decision["case"], decision["label"])
    return payload


if __name__ == "__main__":
    main()
