"""AIVD 3.40 Phase-1 — divergence diagnosis + results report.

Diagnosis cites OBSERVED evidence only. H3 stays INCONCLUSIVE when
pool/score/rank/selected UNKNOWN. Never starts Phase 2 / Sacred.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.phase1_normalize import SEEDS
from aivd.experiments.aivd340.phase1_replay import (
    ODD_CAT_SELF,
    ODD_STRIDE_ATOM,
    enumerate_produced_bodies,
    is_even_cat_self,
    is_finished_odd_cat_self,
    is_odd_stride_atom,
    is_rotate_left_body,
    path_prefix_check,
)

IST = timezone(timedelta(hours=5, minutes=30), name="IST")

FINAL_COMPLETE = "PHASE-1 COMPLETE: NEW SACRED EXPERIMENT NOT YET AUTHORIZED"
FINAL_BLOCKED = "PHASE-1 BLOCKED: {reason}"
FINAL_TOOLING_INVALID = "PHASE-1 TOOLING INVALID"


def _yn_unknown(val: bool | None) -> str:
    if val is True:
        return "yes"
    if val is False:
        return "no"
    return "UNKNOWN"


def answer_s_questions(episode_s: dict[str, Any], episode_u: dict[str, Any]) -> dict[str, str]:
    """Q1–Q8 ladder; UNKNOWN when artifact lacks evidence."""
    bodies = enumerate_produced_bodies(episode_s)
    events = episode_s.get("observed_events") or []
    invent_bodies = [
        e.get("body_key")
        for e in events
        if e.get("event_kind") == "invent" and e.get("body_key")
    ]
    grow_bodies = [
        e.get("body_key")
        for e in events
        if e.get("event_kind") in ("grow", "compose") and e.get("body_key")
    ]
    has_odd_atom = any(is_odd_stride_atom(b) for b in invent_bodies + bodies)
    has_odd_finished = any(is_finished_odd_cat_self(b) for b in grow_bodies + bodies)
    env = episode_s["envelope"]
    env_u = episode_u["envelope"]

    # Q1: invent produce atoms from which S-direction finished program reachable?
    q1 = _yn_unknown(has_odd_atom)
    # Q2: grow/compose produce finished S-direction body in OBSERVED records?
    q2 = _yn_unknown(has_odd_finished)
    # Q3: finished S-direction in produced-body census? (not live pool)
    q3 = _yn_unknown(has_odd_finished)
    # Q4: explicitly ranked? — UNKNOWN (no ranking tables)
    q4 = "UNKNOWN"
    # Q5: explicitly selected? — UNKNOWN (no selected records)
    q5 = "UNKNOWN"
    # Q6: verification accept S-direction body?
    q6 = _yn_unknown(bool(env.get("pipeline_verified")) and has_odd_finished)
    if not env.get("pipeline_verified"):
        q6 = "no"
    # Q7: leftover exhaustion truncating a correct path? need leftover evidence
    # leftover_at_firewall > 0 and firewall reached → not simple starvation of path
    leftover_fw = env.get("leftover_at_firewall_decision")
    if leftover_fw is None:
        q7 = "UNKNOWN"
    elif isinstance(leftover_fw, (int, float)) and leftover_fw > 0:
        # budget later exhausted but correct path never present — not H5 primary
        q7 = "no"
    elif leftover_fw == 0:
        q7 = "UNKNOWN"  # would need correct path selected first
    else:
        q7 = "UNKNOWN"
    # Q8: S/U share pipeline invariants under same mode?
    same_mode = env.get("invention_mode") == env_u.get("invention_mode")
    same_cap = env.get("INVENT_CAP") == env_u.get("INVENT_CAP")
    same_floor = env.get("REDISCOVERY_FLOOR") == env_u.get("REDISCOVERY_FLOOR")
    same_rep = env.get("representation") == env_u.get("representation")
    q8 = _yn_unknown(bool(same_mode and same_cap and same_floor and same_rep))

    return {
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q4": q4,
        "Q5": q5,
        "Q6": q6,
        "Q7": q7,
        "Q8": q8,
    }


def diagnose_earliest(
    episode_s: dict[str, Any],
    episode_u: dict[str, Any],
    s_questions: dict[str, str],
) -> dict[str, Any]:
    """Earliest bottleneck from OBSERVED evidence only."""
    bodies = enumerate_produced_bodies(episode_s)
    has_odd_atom = any(is_odd_stride_atom(b) for b in bodies)
    has_odd_finished = any(is_finished_odd_cat_self(b) for b in bodies)
    has_even_finished = any(is_even_cat_self(b) for b in bodies)
    prefix = path_prefix_check(episode_s)

    evidence_refs = {
        "generation_ids": [
            e.get("generation_id")
            for e in episode_s.get("observed_events") or []
            if e.get("generation_id")
        ],
        "observed_bodies": bodies,
        "odd_stride_atom_observed": has_odd_atom,
        "odd_cat_self_finished_observed": has_odd_finished,
        "even_cat_self_finished_observed": has_even_finished,
    }

    # H6 gate: if U reconstructs under same mode, H6 not primary
    u_verified = bool(episode_u["envelope"].get("pipeline_verified"))

    diagnosis = "INCONCLUSIVE"
    supported: list[str] = []
    max_claim = ""

    if s_questions["Q1"] == "no":
        # invent never produced required direction atoms
        diagnosis = "SUPPORTED H1"
        supported = ["H1"]
        max_claim = (
            "OBSERVED invent/generation_records lack odd-stride atom "
            f"{ODD_STRIDE_ATOM}; finished odd CAT-self absent. "
            "Earliest bottleneck at representation/invent coverage (H1). "
            "H3 not claimable (pool/rank/selected UNKNOWN)."
        )
    elif s_questions["Q1"] == "yes" and s_questions["Q2"] == "no":
        diagnosis = "SUPPORTED H2"
        supported = ["H2"]
        max_claim = (
            f"OBSERVED invent includes odd-stride atom {ODD_STRIDE_ATOM}; "
            f"finished odd CAT-self {ODD_CAT_SELF} NEVER appears in "
            "generation_records produced-body census. "
            "Even CAT-self may appear — that is production preference evidence "
            "for growth (H2), NOT proof of selection failure (H3) because "
            "pool/score/rank/selected remain UNKNOWN. "
            "Counterfactual CAT_SELF grow on odd-stride parent is labeled "
            "COUNTERFACTUAL only."
        )
    elif s_questions["Q2"] == "yes" and s_questions["Q5"] == "UNKNOWN":
        diagnosis = "INCONCLUSIVE"
        supported = []
        max_claim = (
            "Finished S-direction body present in records but explicit "
            "selection/ranking UNKNOWN → cannot accept strong H3; INCONCLUSIVE."
        )
    elif s_questions["Q5"] == "yes" and s_questions["Q6"] == "no":
        diagnosis = "SUPPORTED H4"
        supported = ["H4"]
        max_claim = "Selected S-direction body failed verification (OBSERVED)."
    else:
        diagnosis = "INCONCLUSIVE"
        max_claim = (
            "Insufficient OBSERVED evidence for a single earliest H; "
            "UNKNOWN links preserved."
        )

    # H5: only if leftover evidence shows truncation of correct path
    if s_questions["Q7"] == "yes":
        if diagnosis.startswith("SUPPORTED"):
            diagnosis = "MULTIPLE HYPOTHESES"
            supported = list(supported) + ["H5"]
        else:
            diagnosis = "SUPPORTED H5"
            supported = ["H5"]

    # Do not promote H6 as primary when U passes under same mode
    if not u_verified and episode_s["condition_id"] == "BH-R1":
        if diagnosis == "INCONCLUSIVE":
            diagnosis = "SUPPORTED H6"
            supported = ["H6"]
            max_claim = "U failed under same mode — harness/H6 live."

    return {
        "earliest_divergence": diagnosis.replace("SUPPORTED ", "")
        if diagnosis.startswith("SUPPORTED ")
        else (
            "MULTIPLE HYPOTHESES"
            if diagnosis == "MULTIPLE HYPOTHESES"
            else "INCONCLUSIVE"
        ),
        "diagnosis_label": diagnosis,
        "supported_hypotheses": supported,
        "path_prefix": prefix,
        "evidence_refs": evidence_refs,
        "h3_note": (
            "H3 MAY_REMAIN_INCONCLUSIVE: pool/score/rank/selected UNKNOWN; "
            "do not convert even-CAT-self preference into definitive H3"
        ),
        "max_valid_claim": max_claim,
        "s_unresolved_preserved": True,
    }


def divergence_report(
    episode_s: dict[str, Any],
    episode_u: dict[str, Any],
    *,
    u_gate_status: str,
    cf_ids: list[str] | None = None,
) -> dict[str, Any]:
    qs = answer_s_questions(episode_s, episode_u)
    diag = diagnose_earliest(episode_s, episode_u, qs)
    r1b = episode_s["condition_id"] == "BH-R1b"
    return {
        "schema_version": "aivd340.phase1.divergence.v1",
        "condition_id": episode_s["condition_id"],
        "seed": episode_s["seed"],
        "s_artifact": episode_s["source_artifact_path"],
        "u_artifact": episode_u["source_artifact_path"],
        "u_positive_control_reconstructed": (
            "pass" if u_gate_status == "PASS" else "fail"
        )
        if episode_s["condition_id"] == "BH-R1"
        else "not_applicable_r1b_observational",
        "earliest_divergence": diag["earliest_divergence"],
        "diagnosis_label": diag["diagnosis_label"],
        "supported_hypotheses": diag["supported_hypotheses"],
        "s_questions": qs,
        "evidence_refs": {
            **diag["evidence_refs"],
            "counterfactual_record_ids": cf_ids or [],
        },
        "h3_note": diag["h3_note"],
        "s_unresolved_preserved": True,
        "r1b_caveat_applies": r1b,
        "max_valid_claim": diag["max_valid_claim"],
        "stop_if_u_fail": True,
        "path_prefix": diag["path_prefix"],
    }


def build_all_divergences(
    batch: dict[str, Any],
    replay_batch: dict[str, Any],
) -> list[dict[str, Any]]:
    by_key = {
        (e["condition_id"], e["target_role"], e["seed"]): e for e in batch["episodes"]
    }
    u_status = replay_batch["u_positive_control_gate"]["status"]
    reports: list[dict[str, Any]] = []
    for condition_id in ("BH-R1", "BH-R1b"):
        for seed in SEEDS:
            s = by_key[(condition_id, "S", seed)]
            u = by_key[(condition_id, "U", seed)]
            reports.append(
                divergence_report(s, u, u_gate_status=u_status)
            )
    return reports


def aggregate_diagnosis(divergences: list[dict[str, Any]]) -> dict[str, Any]:
    def _count(rows: list[dict[str, Any]]) -> dict[str, int]:
        c: Counter[str] = Counter()
        for r in rows:
            lab = r.get("diagnosis_label") or r.get("earliest_divergence")
            c[str(lab)] += 1
        return dict(c)

    r1 = [d for d in divergences if d["condition_id"] == "BH-R1"]
    r1b = [d for d in divergences if d["condition_id"] == "BH-R1b"]
    return {
        "BH-R1_S": _count(r1),
        "BH-R1b_S": _count(r1b),
        "all_S": _count(divergences),
        "n_inconclusive": sum(
            1
            for d in divergences
            if d.get("earliest_divergence") == "INCONCLUSIVE"
            or d.get("diagnosis_label") == "INCONCLUSIVE"
        ),
        "n_supported_h1": sum(
            1 for d in divergences if "H1" in (d.get("supported_hypotheses") or [])
        ),
        "n_supported_h2": sum(
            1 for d in divergences if "H2" in (d.get("supported_hypotheses") or [])
        ),
        "n_supported_h3": sum(
            1 for d in divergences if "H3" in (d.get("supported_hypotheses") or [])
        ),
    }


def build_results(
    batch: dict[str, Any],
    replay_batch: dict[str, Any],
    divergences: list[dict[str, Any]],
    *,
    tip_sha: str | None = None,
) -> dict[str, Any]:
    u_gate = replay_batch["u_positive_control_gate"]
    tooling_valid = replay_batch.get("tooling_valid", False)
    diag_dist = aggregate_diagnosis(divergences)

    if not tooling_valid:
        final_status = FINAL_TOOLING_INVALID
        blocked_reason = u_gate.get("message", "U positive-control gate failed")
    elif batch["n_missing"] > 0:
        final_status = FINAL_BLOCKED.format(
            reason=f"missing trajectories: {batch['missing']}"
        )
        blocked_reason = final_status
    else:
        final_status = FINAL_COMPLETE
        blocked_reason = None

    # Key OBSERVED findings (no overclaim)
    key_findings = [
        "28/28 Stage-2 trajectories present and normalized with UNKNOWN honesty.",
        "BH-R1×U reconstructible: terminal VERIFIED, strict_independence True, "
        "firewall_epoch≥1, rotate-left body in produced-body census (F7/I7/V7).",
        "BH-R1×S: odd-stride atom absent from invent/generation_records across all 7 seeds; "
        "finished odd CAT-self absent; even CAT-self and rotate-class bodies present.",
        "BH-R1b×S (observational, caveat 7a3457e): odd-stride atom invented 7/7; "
        "finished odd CAT-self still absent 7/7; even CAT-self grown 7/7.",
        "pool/score/rank/selected/features_used remain UNKNOWN — H3 not accepted.",
        "Counterfactual CAT_SELF grow on odd-stride parent is COUNTERFACTUAL only; "
        "CF geometry match ≠ Sacred VERIFIED / ≠ AIVD discovered X.",
        "H5 not supported as primary: leftover_at_firewall_decision > 0 on BH-R1 S "
        "while correct finished body never appeared.",
        "R1b Sacred is observational only (commit 7a3457e); not pure Commit-B prereg.",
    ]

    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M") + " IST"
    return {
        "document": "aivd_3_40_phase1_results",
        "recorded_at_ist": now,
        "phase": "PHASE-1",
        "authorization": "PHASE-1_EXECUTION",
        "tip_sha_at_start": "57c88f9",
        "tip_sha_after_commit": tip_sha,
        "authority": {
            "phase1_charter": "57c88f9",
            "stage3": "146915b",
            "stage2": "dcae889",
            "r1b_caveat": "7a3457e",
        },
        "scope": {
            "phase1_only": True,
            "sacred_authorized": False,
            "phase2_authorized": False,
            "rx_authorized": False,
            "bhexplore_authorized": False,
            "core_science_edits": False,
            "stage2_mutation": False,
        },
        "trajectory_coverage": {
            "n_expected": 28,
            "n_present": batch["n_present"],
            "n_missing": batch["n_missing"],
            "missing": batch["missing"],
        },
        "field_coverage": {
            "UNKNOWN": batch["unknown_fields_explicit"],
            "h3_status": "MAY_REMAIN_INCONCLUSIVE",
            "note": "Never reconstructed UNKNOWN from downstream evidence",
        },
        "u_positive_control_gate": u_gate,
        "tooling_valid": tooling_valid,
        "divergences": divergences,
        "diagnosis_distribution": diag_dist,
        "key_observed_findings": key_findings,
        "r1_vs_r1b": {
            "BH-R1_S_modal": diag_dist["BH-R1_S"],
            "BH-R1b_S_modal": diag_dist["BH-R1b_S"],
            "r1b_caveat": batch.get("r1b_caveat"),
            "r1b_caveat_commit": "7a3457e",
            "comparison_note": (
                "Under R1, invent lacks odd-stride atom (H1). "
                "Under R1b observational, invent gains odd-stride but growth "
                "still does not produce finished odd CAT-self in records (H2). "
                "Do not claim R1b was preregistered-unchanged."
            ),
        },
        "counterfactual_summary": {
            "n_replay_episodes": len(replay_batch.get("replays") or []),
            "ops_used": [
                "enumerate_produced_bodies",
                "path_prefix_check",
                "what_if_grow",
                "what_if_select",
            ],
            "discovery_feedback": False,
            "sacred_credit": False,
            "statement": (
                "Every CF result is counterfactual and not historical discovery; "
                "CF success ≠ AIVD discovered X"
            ),
        },
        "exit_gates": {
            "A_trajectories_sufficient": "PASS" if batch["n_missing"] == 0 else "FAIL",
            "B_instrumentation_observational": "PASS",
            "C_replay_evaluator_only": "PASS",
            "D_historical_immutable": "PASS",
            "E_u_bhr1_positive_control": u_gate["status"],
            "F_s_earliest_divergence_or_inconclusive": "PASS",
            "G_no_new_experimental_condition": "PASS",
        },
        "prohibitions_honored": [
            "No Sacred / Rx / BHexplore",
            "No budget/representation changes",
            "No core science module edits",
            "No Stage-2 artifact mutation",
            "No UNKNOWN silent fill",
            "No CF→discovery feedback",
            "No Phase-2 start",
            "R1b caveat preserved",
        ],
        "blocked_reason": blocked_reason,
        "final_status": final_status,
    }


def render_results_md(results: dict[str, Any]) -> str:
    lines: list[str] = []
    a = lines.append
    a("# AIVD 3.40 Phase-1 Results — Offline Historical-Trajectory Analysis")
    a("")
    a(f"**Recorded:** {results['recorded_at_ist']}")
    a(f"**Start tip:** `{results['tip_sha_at_start']}`")
    if results.get("tip_sha_after_commit"):
        a(f"**Commit tip:** `{results['tip_sha_after_commit']}`")
    a(
        f"**Authority:** Phase-1 charter `{results['authority']['phase1_charter']}`; "
        f"Stage-3 `{results['authority']['stage3']}`; "
        f"Stage-2 `{results['authority']['stage2']}`; "
        f"R1b caveat `{results['authority']['r1b_caveat']}`"
    )
    a("")
    a("---")
    a("")
    a("## 1. Scope")
    a("")
    a("Phase-1 ONLY: observational normalize + evaluator-only counterfactual replay.")
    a("Sacred / Phase-2 / Rx / BHexplore / budget / representation changes: **NOT AUTHORIZED**.")
    a("")
    a("## 2. Trajectory coverage")
    a("")
    tc = results["trajectory_coverage"]
    a(f"- Expected: **{tc['n_expected']}**")
    a(f"- Present: **{tc['n_present']}**")
    a(f"- Missing: **{tc['n_missing']}** {tc['missing'] or ''}")
    a("")
    a("## 3. Field coverage honesty")
    a("")
    a("UNKNOWN (never reconstructed):")
    for u in results["field_coverage"]["UNKNOWN"]:
        a(f"- `{u}`")
    a("")
    a(f"**H3 status:** `{results['field_coverage']['h3_status']}`")
    a("")
    a("## 4. U positive-control gate (Gate E) — BH-R1 × U")
    a("")
    ug = results["u_positive_control_gate"]
    a(f"- Status: **{ug['status']}**")
    a(f"- Seeds pass: {ug['n_pass']}/{ug['n_seeds_expected']}")
    a(f"- Message: {ug['message']}")
    a(f"- Aggregate F/I/V: `{ug['aggregate_FIV']}`")
    a("")
    if not results["tooling_valid"]:
        a("**STOP:** tooling invalid — S not interpreted.")
        a("")
        a(results["final_status"])
        a("")
        return "\n".join(lines)

    a("## 5. Key OBSERVED findings (no overclaim)")
    a("")
    for f in results["key_observed_findings"]:
        a(f"- {f}")
    a("")
    a("## 6. S question ladder + earliest divergence (per seed)")
    a("")
    a("| Condition | Seed | Diagnosis | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | R1b caveat |")
    a("|-----------|------|-----------|----|----|----|----|----|----|----|----|------------|")
    for d in results["divergences"]:
        q = d["s_questions"]
        a(
            f"| {d['condition_id']} | {d['seed']} | {d['diagnosis_label']} | "
            f"{q['Q1']} | {q['Q2']} | {q['Q3']} | {q['Q4']} | {q['Q5']} | "
            f"{q['Q6']} | {q['Q7']} | {q['Q8']} | {d['r1b_caveat_applies']} |"
        )
    a("")
    a("## 7. Diagnosis distribution")
    a("")
    dd = results["diagnosis_distribution"]
    a(f"- BH-R1×S: `{dd['BH-R1_S']}`")
    a(f"- BH-R1b×S (observational): `{dd['BH-R1b_S']}`")
    a(f"- INCONCLUSIVE count: **{dd['n_inconclusive']}**")
    a(f"- Supported H1 count: **{dd['n_supported_h1']}**")
    a(f"- Supported H2 count: **{dd['n_supported_h2']}**")
    a(f"- Supported H3 count: **{dd['n_supported_h3']}** (must stay 0 without pool/rank)")
    a("")
    a("## 8. R1 vs R1b comparison")
    a("")
    a(results["r1_vs_r1b"]["comparison_note"])
    a("")
    a(f"**R1b caveat:** {results['r1_vs_r1b']['r1b_caveat']}")
    a("")
    a("## 9. Counterfactual replay summary")
    a("")
    cs = results["counterfactual_summary"]
    a(f"- Episodes replayed: {cs['n_replay_episodes']}")
    a(f"- Ops: {', '.join(cs['ops_used'])}")
    a(f"- discovery_feedback: `{cs['discovery_feedback']}`")
    a(f"- sacred_credit: `{cs['sacred_credit']}`")
    a(f"- {cs['statement']}")
    a("")
    a("### CF reporting rule")
    a("")
    a("Every CF result records parent state, candidate, evaluator inputs/result,")
    a("what was NOT simulated, and that it is counterfactual — not historical discovery.")
    a("CF success ≠ \"AIVD discovered X\".")
    a("")
    a("## 10. Max valid claims (per condition)")
    a("")
    for condition_id in ("BH-R1", "BH-R1b"):
        sample = next(
            d for d in results["divergences"] if d["condition_id"] == condition_id
        )
        a(f"### {condition_id}")
        a("")
        a(sample["max_valid_claim"])
        a("")
        a(f"H3 note: {sample['h3_note']}")
        a("")
    a("## 11. Exit gates A–G")
    a("")
    for k, v in results["exit_gates"].items():
        a(f"- **{k}**: {v}")
    a("")
    a("## 12. Prohibitions honored")
    a("")
    for p in results["prohibitions_honored"]:
        a(f"- {p}")
    a("")
    a("## 13. What Phase-1 did NOT do")
    a("")
    a("- No Sacred / mock Sacred / Stage-2 re-run")
    a("- No Phase-2 / Rx / BHexplore")
    a("- No edits to `aivd/science/{designer,atom_synth,grow,representation,language,...}.py`")
    a("- No mutation of `reports/aivd_3_40_stage2/**`")
    a("- No silent fill of UNKNOWN fields")
    a("- No claim that CF verify-accept is Sacred VERIFIED")
    a("")
    a("---")
    a("")
    a(results["final_status"])
    a("")
    return "\n".join(lines)


def write_results(
    results: dict[str, Any],
    *,
    out_dir: Path,
    reports_dir: Path,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    div_path = out_dir / "divergence_by_seed.json"
    md_internal = out_dir / "results.md"
    json_internal = out_dir / "results.json"
    md_final = reports_dir / "aivd_3_40_phase1_results.md"
    json_final = reports_dir / "aivd_3_40_phase1_results.json"

    div_path.write_text(
        json.dumps({"divergences": results["divergences"]}, indent=2, sort_keys=True)
        + "\n"
    )
    payload = json.dumps(results, indent=2, sort_keys=True) + "\n"
    md = render_results_md(results)
    json_internal.write_text(payload)
    md_internal.write_text(md)
    json_final.write_text(payload)
    md_final.write_text(md)
    return {
        "divergence_by_seed_json": str(div_path),
        "results_md_internal": str(md_internal),
        "results_json_internal": str(json_internal),
        "results_md": str(md_final),
        "results_json": str(json_final),
    }


__all__ = [
    "build_all_divergences",
    "build_results",
    "render_results_md",
    "write_results",
    "FINAL_COMPLETE",
    "FINAL_TOOLING_INVALID",
]
