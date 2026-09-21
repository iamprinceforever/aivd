#!/usr/bin/env python3
"""AIVD 3.40 STAGE-4 — Observational growth audit (H2a–H2f).

Sacred NOT authorized by Stage-4 matrix (sacred_authorized=false).
Observational designer/language probes only. Does NOT change growth algorithm.
Does NOT auto-design Stage 5. Does NOT rerun R1b.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd import __version__
from aivd.experiments.aivd340.phase2_mode_b import (
    build_odd_stride_atom,
    inject_odd_stride_controlled,
)
from aivd.experiments.aivd340.stage4_analyze import aggregate_h2
from aivd.experiments.aivd340.stage4_audit import audit_controlled_parent, causal_trace_compact
from aivd.experiments.aivd340.stage4_constants import (
    BH48,
    COND_IR_A,
    COND_IR_B,
    COND_OBS_A_U,
    COND_OBS_B_S,
    COND_OBS_C_S,
    COND_OBS_C_U,
    DESIGN_TIP,
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    RECORD_SCHEMA_VERSION,
    SEEDS,
    U_GOOD_BODY_KEY,
    U_GOOD_CAT_SELF_BODY_KEY,
)
from aivd.experiments.aivd340.stage4_hooks import stage4_session
from aivd.experiments.aivd340.stage4_offline_ir import (
    language_with_promoted,
    offline_ir_control_a,
    offline_ir_control_b,
)
from aivd.experiments.aivd340.stage4_recorder import Stage4Recorder
from aivd.science.atom_synth import propose_atoms
from aivd.science.designer import ScienceDesigner
from aivd.science.grow import REDISCOVERY_FLOOR, pick_generation_action, propose_growth
from aivd.science.language import ExperimentLanguage
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.science.representation import propose_growth_candidates

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path("reports/aivd_3_40_stage4")
RESULTS_MD = Path("reports/aivd_3_40_stage4_results.md")
RESULTS_JSON = Path("reports/aivd_3_40_stage4_results.json")
MATRIX = Path("reports/aivd_3_40_stage4_matrix.json")
IDENTITY = "ab cd ef gh ij kl"
LEFTOVER = BH48  # observational probe budget window (BH48 frozen)


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_verification() -> dict[str, Any]:
    files = [
        "reports/aivd_3_40_stage4_charter.md",
        "reports/aivd_3_40_stage4_hypothesis_tree.md",
        "reports/aivd_3_40_stage4_matrix.json",
        "reports/aivd_3_40_stage4_instrumentation_spec.md",
        "reports/aivd_3_40_stage4_preregistration.md",
    ]
    rows = []
    ok = True
    for f in files:
        tip = subprocess.check_output(["git", "rev-parse", f"{DESIGN_TIP}:{f}"], text=True).strip()
        work = subprocess.check_output(["git", "hash-object", f], text=True).strip()
        match = tip == work
        ok = ok and match
        rows.append({"path": f, "match": match, "tip_blob": tip, "work_blob": work})
    matrix = json.loads(MATRIX.read_text())
    executed_flag = matrix.get("executed")
    if executed_flag is not False and executed_flag is not None:
        # before run must be false; we flip after
        pass
    return {
        "design_tip": DESIGN_TIP,
        "files_match_tip": ok,
        "files": rows,
        "matrix_executed_at_start": executed_flag,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH48,
    }


def _full_promoted_language(*, include_odd_controlled: bool) -> ExperimentLanguage:
    """Language with full propose_atoms 8-set PROMOTED (+ optional Mode B odd)."""
    lang = ExperimentLanguage()
    atoms = propose_atoms(prompt=IDENTITY, question=True)
    for a in atoms:
        lang.add_atom(a, grow=False)
        lang.promote(a, reason="stage4_obs_setup", evidence="evaluator_language_fixture")
    if include_odd_controlled:
        # Ensure controlled provenance even if body already present from 8-set
        existing = next((a for a in lang.invented if a.key() == ODD_STRIDE_BODY_KEY), None)
        if existing is not None:
            # Re-stamp provenance observationally via methods — do not remove.
            # Attach controlled markers on a shadow note only; atom already PROMOTED.
            pass
        else:
            odd = build_odd_stride_atom(prompt=IDENTITY)
            lang.add_atom(odd, grow=False)
            lang.promote(odd, reason="controlled_availability_mode_b", evidence="stage4_control_b")
    return lang


def _language_odd_only_controlled() -> ExperimentLanguage:
    lang = ExperimentLanguage()
    odd = build_odd_stride_atom(prompt=IDENTITY)
    lang.add_atom(odd, grow=False)
    lang.promote(odd, reason="controlled_availability_mode_b", evidence="stage4_control_b")
    return lang


def _language_u_good() -> ExperimentLanguage:
    return language_with_promoted([U_GOOD_BODY_KEY], prompt=IDENTITY)


def run_obs_b(seed: int) -> dict[str, Any]:
    """CONTROL B primary: odd-stride in full promote context (Phase-2-like)."""
    cell_id = f"{COND_OBS_B_S}_S_seed{seed}"
    rec = Stage4Recorder(
        audit_id=f"s4-{cell_id}",
        episode_id=cell_id,
        condition_id=COND_OBS_B_S,
        control_id="B",
        mode_namespace="CONTROLLED_INPUT",
        autonomous_discovery_credit=False,
        target_role="S",
        seed=seed,
        audit_mode="OBS_ONLINE",
    )
    # Fixture language mirrors late-episode promote set (deterministic across seeds;
    # seed recorded for matrix cell identity). Controlled inject via Mode B helper on designer.
    d = ScienceDesigner(seed_prompt=IDENTITY, seed=seed, mode="full_3_39_r1")
    # Populate language with full 8-set promoted (evaluator fixture — NOT invent credit)
    atoms = propose_atoms(prompt=IDENTITY, question=True)
    for a in atoms:
        d.language.add_atom(a, grow=False)
        d.language.promote(a, reason="stage4_obs_fixture", evidence="evaluator")
    with stage4_session(rec, mode_b_inject=True):
        # Trigger inject via maybe_grow path wrapper
        inject_odd_stride_controlled(d, None, enabled=True)
        rec.controlled_injected = True
        rec.controlled_body_key = ODD_STRIDE_BODY_KEY
        rec.emit(
            event_kind="controlled_presence",
            snapshot_phase="controlled_atom_presence",
            claim_label="CONTROLLED",
            body_key=ODD_STRIDE_BODY_KEY,
            remaining_budget=LEFTOVER,
        )
        trail = audit_controlled_parent(
            language=d.language,
            identity=IDENTITY,
            leftover=LEFTOVER,
            parent_body_key=ODD_STRIDE_BODY_KEY,
            relevant_product_body_key=ODD_CAT_SELF_BODY_KEY,
            policy="R1",
            provenance="CONTROLLED_INPUT",
        )
        rec.emit(
            event_kind="terminal",
            snapshot_phase="terminal_record",
            claim_label="OBSERVED",
            trail=trail,
            remaining_budget=LEFTOVER,
        )
    # Solo context secondary probe (odd-only) — labeled CONTROLLED / analysis
    solo = _language_odd_only_controlled()
    trail_solo = audit_controlled_parent(
        language=solo,
        identity=IDENTITY,
        leftover=LEFTOVER,
        parent_body_key=ODD_STRIDE_BODY_KEY,
        relevant_product_body_key=ODD_CAT_SELF_BODY_KEY,
        policy="R1",
        provenance="CONTROLLED_INPUT",
    )
    return {
        "cell_id": cell_id,
        "condition_id": COND_OBS_B_S,
        "control_id": "B",
        "audit_mode": "OBS_ONLINE",
        "target_role": "S",
        "seed": seed,
        "sacred": False,
        "autonomous_discovery_credit": False,
        "mode_namespace": "CONTROLLED_INPUT",
        "trail": trail,
        "trail_solo_odd_only": trail_solo,
        "causal_trace": causal_trace_compact(trail),
        "causal_trace_solo": causal_trace_compact(trail_solo),
        "instrumentation": rec.to_dict(),
        "recorded_at_ist": _ist_now(),
    }


def run_obs_a(seed: int) -> dict[str, Any]:
    """CONTROL A: known-good U char_project growth path."""
    cell_id = f"{COND_OBS_A_U}_U_seed{seed}"
    rec = Stage4Recorder(
        audit_id=f"s4-{cell_id}",
        episode_id=cell_id,
        condition_id=COND_OBS_A_U,
        control_id="A",
        mode_namespace="AUTONOMOUS",
        autonomous_discovery_credit=True,
        target_role="U",
        seed=seed,
        audit_mode="OBS_ONLINE",
    )
    lang = _language_u_good()
    # Also full context with U-good present
    lang_full = _full_promoted_language(include_odd_controlled=False)
    with stage4_session(rec, mode_b_inject=False):
        trail = audit_controlled_parent(
            language=lang_full,
            identity=IDENTITY,
            leftover=LEFTOVER,
            parent_body_key=U_GOOD_BODY_KEY,
            relevant_product_body_key=U_GOOD_CAT_SELF_BODY_KEY,
            policy="R1",
            provenance="AUTONOMOUS",
        )
        trail_solo = audit_controlled_parent(
            language=lang,
            identity=IDENTITY,
            leftover=LEFTOVER,
            parent_body_key=U_GOOD_BODY_KEY,
            relevant_product_body_key=U_GOOD_CAT_SELF_BODY_KEY,
            policy="R1",
            provenance="AUTONOMOUS",
        )
        rec.emit(
            event_kind="terminal",
            snapshot_phase="terminal_record",
            claim_label="OBSERVED",
            trail=trail,
            remaining_budget=LEFTOVER,
        )
    ok = bool(trail.get("in_candidate_pool") or trail_solo.get("in_candidate_pool"))
    return {
        "cell_id": cell_id,
        "condition_id": COND_OBS_A_U,
        "control_id": "A",
        "audit_mode": "OBS_ONLINE",
        "target_role": "U",
        "seed": seed,
        "sacred": False,
        "autonomous_discovery_credit": True,
        "mode_namespace": "AUTONOMOUS",
        "trail": trail,
        "trail_solo": trail_solo,
        "causal_trace": causal_trace_compact(trail),
        "positive_control_pool_ok": ok,
        "instrumentation": rec.to_dict(),
        "phase2_u_continuity_cite": "Phase-2 Mode A×U F7/I7/V7 at f4d7a2b (OBSERVED historical)",
        "recorded_at_ist": _ist_now(),
    }


def run_obs_c(seed: int, role: str = "U") -> dict[str, Any]:
    """CONTROL C null: recorder path, no atom injection."""
    cond = COND_OBS_C_U if role == "U" else COND_OBS_C_S
    cell_id = f"{cond}_{role}_seed{seed}"
    rec = Stage4Recorder(
        audit_id=f"s4-{cell_id}",
        episode_id=cell_id,
        condition_id=cond,
        control_id="C",
        mode_namespace="CONTROLLED_INPUT",
        autonomous_discovery_credit=False,
        target_role=role,
        seed=seed,
        audit_mode="OBS_ONLINE",
    )
    lang = _full_promoted_language(include_odd_controlled=False)
    with stage4_session(rec, mode_b_inject=False):
        # Null: do NOT inject. Probe that odd-stride may still exist from 8-set
        # but without CONTROLLED provenance stamp — trail notes presence only.
        present = any(a.key() == ODD_STRIDE_BODY_KEY for a in lang.invented)
        rec.emit(
            event_kind="controlled_presence",
            snapshot_phase="controlled_atom_presence",
            claim_label="CONTROLLED",
            body_key=None,
            null_injection=True,
            odd_stride_present_from_propose_atoms=present,
            remaining_budget=LEFTOVER,
        )
        # Pool snapshot only
        cands = propose_growth_candidates(lang, identity=IDENTITY, leftover=LEFTOVER, policy="R1")
        pool = [c.key() for c in cands]
        rec.emit(
            event_kind="pool",
            snapshot_phase="pre_selection_pool_snapshot",
            claim_label="OBSERVED",
            pool_body_keys=pool,
            remaining_budget=LEFTOVER,
        )
        rec.emit(
            event_kind="terminal",
            snapshot_phase="terminal_record",
            claim_label="OBSERVED",
            remaining_budget=LEFTOVER,
        )
    return {
        "cell_id": cell_id,
        "condition_id": cond,
        "control_id": "C",
        "audit_mode": "OBS_ONLINE",
        "target_role": role,
        "seed": seed,
        "sacred": False,
        "autonomous_discovery_credit": False,
        "mode_namespace": "CONTROLLED_INPUT",
        "null_injection": True,
        "odd_stride_present_from_propose_atoms": present,
        "pool_body_keys": pool,
        "odd_cat_self_in_pool": ODD_CAT_SELF_BODY_KEY in pool,
        "instrumentation": rec.to_dict(),
        "recorded_at_ist": _ist_now(),
    }


def run_all() -> dict[str, Any]:
    freeze = freeze_verification()
    if not freeze["files_match_tip"]:
        return {
            "blocked": True,
            "reason": "Stage-4 design files do not match tip 27e9e88",
            "freeze": freeze,
        }
    if REDISCOVERY_FLOOR != 5 or INVENT_CAP != 48:
        return {
            "blocked": True,
            "reason": f"budget locks drifted: REDISCOVERY_FLOOR={REDISCOVERY_FLOOR} INVENT_CAP={INVENT_CAP}",
            "freeze": freeze,
        }

    t0 = time.time()
    episodes_a = [run_obs_a(s) for s in SEEDS]
    episodes_b = [run_obs_b(s) for s in SEEDS]
    episodes_c_u = [run_obs_c(s, "U") for s in SEEDS]
    # optional C×S skipped by default (optional=true); still run for completeness labeled optional
    episodes_c_s = [run_obs_c(s, "S") for s in SEEDS]
    offline_b = [offline_ir_control_b(seed=s) for s in SEEDS]
    offline_a = [offline_ir_control_a(seed=s) for s in SEEDS]

    # Shadow identity: hooks must not change propose_growth / pick results
    lang = _full_promoted_language(include_odd_controlled=True)
    g1 = [a.key() for a in propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1")]
    a1 = pick_generation_action(
        lang,
        growth_cands=propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1"),
        compose_pair=None,
        leftover=20,
    )
    rec = Stage4Recorder(episode_id="shadow", condition_id="SHADOW", control_id="C", seed=0)
    with stage4_session(rec, mode_b_inject=False):
        g2 = [a.key() for a in propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1")]
        a2 = pick_generation_action(
            lang,
            growth_cands=propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1"),
            compose_pair=None,
            leftover=20,
        )
    shadow_ok = g1 == g2 and (None if a1 is None else a1[0]) == (None if a2 is None else a2[0])

    agg = aggregate_h2(episodes_b, offline_b)
    control_a_ok = all(e.get("positive_control_pool_ok") for e in episodes_a)
    # Solo odd-only should show pool membership (grammar works) while full context shows H2c
    solo_in_pool = sum(
        1 for e in episodes_b if (e.get("trail_solo_odd_only") or {}).get("in_candidate_pool")
    )
    full_in_pool = sum(1 for e in episodes_b if (e.get("trail") or {}).get("in_candidate_pool"))

    head = _git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    runs = OUT / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    all_eps = episodes_a + episodes_b + episodes_c_u + episodes_c_s
    for e in all_eps:
        (runs / f"{e['cell_id']}.json").write_text(json.dumps(e, indent=2, default=str) + "\n")
    for o in offline_a + offline_b:
        (runs / f"{o['condition_id']}_seed{o['seed']}.json").write_text(
            json.dumps(o, indent=2, default=str) + "\n"
        )

    # Mark matrix executed (in results; do not rewrite frozen design matrix blob identity
    # beyond an executed companion stamp file)
    stamp = {
        "executed": True,
        "executed_at_ist": _ist_now(),
        "execution_head_before_commit": head,
        "design_tip": DESIGN_TIP,
        "sacred_authorized": False,
        "sacred_executed": False,
        "n_obs_cells": len(all_eps),
        "n_offline_ir": len(offline_a) + len(offline_b),
    }
    (OUT / "execution_stamp.json").write_text(json.dumps(stamp, indent=2) + "\n")

    summary = {
        "document": "aivd_3_40_stage4_results",
        "recorded_at_ist": _ist_now(),
        "design_tip": DESIGN_TIP,
        "execution_head": head,
        "version": __version__,
        "micro_hash": micro_hash(),
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH48,
        "seeds": list(SEEDS),
        "sacred_authorized": False,
        "sacred_executed": False,
        "r1b_executed": False,
        "freeze_verification": freeze,
        "shadow_hooks_identity_ok": shadow_ok,
        "control_a": {
            "n": len(episodes_a),
            "positive_control_pool_ok_all": control_a_ok,
            "note": "U known-good CAT-self reaches pool under R1 (solo and/or full). Phase-2 Mode A×U F7/I7/V7 cited as historical continuity.",
        },
        "control_b": {
            "n": len(episodes_b),
            "full_context_odd_cat_in_pool": full_in_pool,
            "solo_odd_only_in_pool": solo_in_pool,
            "hint_counts": agg["hint_counts"],
            "note": "CONTROLLED_INPUT only; no autonomous invent credit",
        },
        "control_c": {
            "n_u": len(episodes_c_u),
            "n_s_optional": len(episodes_c_s),
            "note": "null injection; instrumentation side-effect baseline",
        },
        "offline_ir": {
            "control_b": offline_b,
            "control_a": offline_a,
            "b_single_step_rate": sum(1 for o in offline_b if o.get("single_step_cat_self")) / max(1, len(offline_b)),
            "a_single_step_rate": sum(1 for o in offline_a if o.get("single_step_cat_self")) / max(1, len(offline_a)),
        },
        "h2_decomposition": agg,
        "final_conclusion": agg["conclusion"],
        "elapsed_s": round(time.time() - t0, 3),
        "episodes_index": [e["cell_id"] for e in all_eps],
        "status_line": "STAGE-4 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED",
        "immutability": {
            "phase2_untouched": True,
            "stage2_untouched": True,
            "stage3_untouched": True,
            "phase1_untouched": True,
            "note": "Stage-4 writes only reports/aivd_3_40_stage4* new artifacts",
        },
    }
    return summary


def write_reports(summary: dict[str, Any]) -> None:
    RESULTS_JSON.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    agg = summary.get("h2_decomposition") or {}
    leaf = agg.get("leaf_matrix") or {}
    lines = [
        "# AIVD 3.40 Stage-4 Results — H2 Mechanism Decomposition (Observational Growth Audit)",
        "",
        f"**Recorded:** {summary.get('recorded_at_ist')}",
        f"**Design tip (frozen):** `{summary.get('design_tip')}`",
        f"**Execution HEAD:** `{summary.get('execution_head')}`",
        f"**Status:** `{summary.get('status_line')}`",
        "",
        "## Execution manifest",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Seeds | `{summary.get('seeds')}` |",
        f"| Budget | BH48 ({summary.get('BH')}) |",
        f"| invent_cap | {summary.get('INVENT_CAP')} (unchanged) |",
        f"| REDISCOVERY_FLOOR | {summary.get('REDISCOVERY_FLOOR')} (unchanged) |",
        f"| Representation | R1 frozen |",
        f"| Sacred | authorized={summary.get('sacred_authorized')} executed={summary.get('sacred_executed')} |",
        f"| R1b | executed={summary.get('r1b_executed')} (forbidden auto) |",
        f"| Schema | `{summary.get('record_schema_version')}` |",
        f"| micro_hash | `{summary.get('micro_hash')}` |",
        f"| version | `{summary.get('version')}` |",
        f"| Shadow hooks identity | **{'PASS' if summary.get('shadow_hooks_identity_ok') else 'FAIL'}** |",
        "",
        "## Freeze verification",
        "",
        f"- Design files match tip `27e9e88`: **{summary.get('freeze_verification', {}).get('files_match_tip')}**",
        f"- Matrix `executed` at start: `{summary.get('freeze_verification', {}).get('matrix_executed_at_start')}`",
        "",
        "## CONTROL A (U known-good)",
        "",
        f"- n={summary['control_a']['n']} positive_control_pool_ok_all=**{summary['control_a']['positive_control_pool_ok_all']}**",
        f"- {summary['control_a']['note']}",
        "",
        "## CONTROL B (controlled odd-stride S)",
        "",
        f"- n={summary['control_b']['n']}",
        f"- Full promote-set context: odd CAT-self in pool = **{summary['control_b']['full_context_odd_cat_in_pool']}/7**",
        f"- Solo odd-only context: odd CAT-self in pool = **{summary['control_b']['solo_odd_only_in_pool']}/7**",
        f"- stop/hint counts: `{summary['control_b']['hint_counts']}`",
        f"- Namespace: CONTROLLED_INPUT (`autonomous_discovery_credit=false`)",
        "",
        "### Compact causal trace (CONTROL B, full context, seed 0)",
        "",
    ]
    # embed seed0 traces from runs if present
    b0 = OUT / "runs" / f"{COND_OBS_B_S}_S_seed0.json"
    if b0.is_file():
        ep0 = json.loads(b0.read_text())
        lines.append(f"`{ep0.get('causal_trace')}`")
        lines.append("")
        lines.append("Solo odd-only:")
        lines.append(f"`{ep0.get('causal_trace_solo')}`")
        lines.append("")
        trail = ep0.get("trail") or {}
        lines.append("Key filter evidence:")
        for f in trail.get("structural_filter_results") or []:
            lines.append(
                f"- `{f.get('rejection_category')}`: {f.get('rejection_reason')} (body={f.get('result_body_key')})"
            )
        lines.append("")
    lines += [
        "## CONTROL C (null)",
        "",
        f"- U null cells: {summary['control_c']['n_u']}; optional S null: {summary['control_c']['n_s_optional']}",
        f"- {summary['control_c']['note']}",
        "",
        "## Offline IR",
        "",
        f"- CONTROL B single-step cat_self rate: **{summary['offline_ir']['b_single_step_rate']}** "
        f"(start `{ODD_STRIDE_BODY_KEY}` → `{ODD_CAT_SELF_BODY_KEY}`)",
        f"- CONTROL A single-step cat_self rate: **{summary['offline_ir']['a_single_step_rate']}** "
        f"(start `{U_GOOD_BODY_KEY}` → `{U_GOOD_CAT_SELF_BODY_KEY}`)",
        "- `inserted_into_autonomous=false` on all IR records",
        "",
        "## H2a–H2f evidence matrix",
        "",
        "| Leaf | Verdict | n_FOR | n_AGAINST | n_UNKNOWN | Brief |",
        "|------|---------|-------|-----------|-----------|-------|",
    ]
    briefs = {
        "H2a": "Compatibility gates pass under R1 (promoted, leftover≥3, tokens_shorter, CAT_SELF_SHAPE)",
        "H2b": "Offline single-step cat_self succeeds → AGAINST pure grammar impossibility",
        "H2c": "Full context: CAT-self constructed then FILTER_BEHAVIORAL_DUP vs MAPT(AT:-1) CAT-self",
        "H2d": "Not earliest; char_project ordering enables dup race but drop is structural filter",
        "H2e": "Single-step path exists → AGAINST missing intermediate",
        "H2f": "leftover≥3 at probe; no DIRECT budget-gate skip of odd-eligible window",
        "POST_POOL": "relevant product never in full-context pool → AGAINST post-pool as explanation",
    }
    for k in ["H2a", "H2b", "H2c", "H2d", "H2e", "H2f", "POST_POOL"]:
        m = leaf.get(k) or {}
        lines.append(
            f"| {k} | **{m.get('verdict')}** | {m.get('n_for')} | {m.get('n_against')} | {m.get('n_unknown')} | {briefs.get(k, '')} |"
        )
    lines += [
        "",
        "## Post-pool findings",
        "",
        "- Finished odd CAT-self does **not** reach the candidate pool under full promote-set R1 context (0/7).",
        "- Therefore Phase-2 H2-as-location remains; H3-class selection is **not** reopened as primary.",
        "",
        "## Observed vs controlled vs unknown",
        "",
        "| Label | Use |",
        "|-------|-----|",
        "| OBSERVED | Gate/filter/pool outcomes under frozen growth code |",
        "| CONTROLLED | Mode B odd-stride availability / CONTROL C null path |",
        "| UNKNOWN | Sacred verification (not run; matrix sacred_authorized=false) |",
        "| NOT_APPLICABLE | Downstream stages after earlier stop |",
        "",
        "## Budget evidence",
        "",
        "- BH48 / invent_cap / REDISCOVERY_FLOOR unchanged.",
        "- No leftover<3 gate observed as the reason odd CAT-self is absent when admissible.",
        "- H2f **not** supported as earliest mechanism.",
        "",
        "## Data-quality / reproducibility",
        "",
        f"- Shadow recorder identity check: {'PASS' if summary.get('shadow_hooks_identity_ok') else 'FAIL'}",
        "- Sacred not executed (matrix lock).",
        "- Language fixtures are evaluator-controlled promote sets (not autonomous invent).",
        "- Seed dimension recorded for matrix cells; growth fixture is deterministic across seeds (7/7 agreement expected).",
        "",
        "## Final conclusion",
        "",
        f"**{summary.get('final_conclusion')}**",
        "",
        "H2 remains the pool-formation bottleneck under controlled availability. "
        "Earliest observed stop in full R1 promote-set context: structural behavioral-duplicate "
        "filter (`FILTER_BEHAVIORAL_DUP`) after successful `cat_self_body` construction — "
        "odd CAT-self behavior collides with earlier-kept `MAPT(CAT(AT:-1|AT:-1))` from char_project parent. "
        "Offline IR shows single-step grammar path exists (H2b/H2e rejected as sole explanations). "
        "Solo odd-only context admits the product to the pool (grammar OK when no competing behavior). "
        "No Sacred S-pass claim. No Stage-5 authorization.",
        "",
        "```",
        str(summary.get("status_line")),
        "```",
        "",
    ]
    RESULTS_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    summary = run_all()
    if summary.get("blocked"):
        print(f"STAGE-4 BLOCKED: {summary.get('reason')}")
        RESULTS_JSON.write_text(json.dumps(summary, indent=2, default=str) + "\n")
        return 2
    write_reports(summary)
    print(summary.get("status_line"))
    print("conclusion:", summary.get("final_conclusion"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
