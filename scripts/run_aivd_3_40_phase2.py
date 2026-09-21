#!/usr/bin/env python3
"""AIVD 3.40 PHASE-2 — H2/H3 instrumentation (Mode A + Mode B).

Mechanism-localization ONLY. NOT make S pass.
Hard STOP after Phase-2 reports. Does NOT auto-launch P2-R1b-SACRED-AS-EXECUTED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd340.phase2_analyze import (
    aggregate_outcomes,
    classify_seed_mechanism,
    final_h2_h3_conclusion,
)
from aivd.experiments.aivd340.phase2_condition import phase2_condition
from aivd.experiments.aivd340.phase2_constants import (
    BH48,
    CONDITION_INSTR,
    CONDITION_MODEB,
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    SEEDS,
)
from aivd.experiments.aivd340.phase2_hooks import observational_session
from aivd.experiments.aivd340.phase2_recorder import Phase2Recorder
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_340_phase2 import (
    WEAK_SEED,
    LlamaP2STarget,
    LlamaP2UTarget,
    PLANT_P2_S,
    PLANT_P2_U,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path("reports/aivd_3_40_phase2")
RESULTS_MD = Path("reports/aivd_3_40_phase2_results.md")
RESULTS_JSON = Path("reports/aivd_3_40_phase2_results.json")
ENV_GATE = Path("reports/aivd_3_40_environment_gate.json")
DESIGN_TIP = "7be4124"
PLANTS = (
    ("S", LlamaP2STarget, PLANT_P2_S),
    ("U", LlamaP2UTarget, PLANT_P2_U),
)


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _pipe(target, seed: int, mode: str, episode_budget: int) -> UnknownsPipeline:
    bt = BudgetTracker(BudgetConfig(max_experiments=max(40, episode_budget + 8)))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=episode_budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=episode_budget,
        epistemic_mode=mode,
        epistemic_max_steps=episode_budget,
        epistemic_max_candidates=episode_budget,
    )


def _extract_leftover_at_firewall(methods_log: list) -> dict[str, Any]:
    out: dict[str, Any] = {
        "leftover_at_firewall_decision": None,
        "firewall_armed": False,
        "firewall_skipped": False,
    }
    for e in methods_log or []:
        ev = e.get("event")
        if ev == "REDISCOVERY_BUDGET_FAILURE":
            out["firewall_skipped"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                out["leftover_at_firewall_decision"] = e.get("leftover")
        elif ev == "provenance_firewall":
            out["firewall_armed"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                if out["leftover_at_firewall_decision"] is None:
                    out["leftover_at_firewall_decision"] = e.get("leftover")
    return out


def env_gate() -> dict[str, Any]:
    failures = []
    if not ENV_GATE.is_file():
        failures.append("missing environment_gate.json")
    else:
        eg = json.loads(ENV_GATE.read_text())
        if eg.get("gate_status") != "PASS":
            failures.append(f"gate_status={eg.get('gate_status')}")
    if not available():
        failures.append("llama_infer.available() False")
    leak = scan_discovery_target_leakage()
    sci = scan_science_source()
    if not leak.get("pass"):
        failures.append("discovery leakage fail")
    if not sci.get("pass"):
        failures.append("science source leakage fail")
    # Freeze tip check
    head = _git_head()
    if not head.startswith(DESIGN_TIP) and DESIGN_TIP not in head:
        # allow commits after 7be4124 during execution; require ancestry
        try:
            subprocess.check_call(
                ["git", "merge-base", "--is-ancestor", DESIGN_TIP, "HEAD"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            failures.append(f"HEAD {head[:12]} not descended from design tip {DESIGN_TIP}")
    status = "PASS" if not failures else "FAIL"
    return {
        "gate_status": status,
        "failures": failures,
        "runtime": runtime_info(),
        "leakage": {"discovery": leak, "science": sci},
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH48,
        "design_tip": DESIGN_TIP,
        "head": head,
        "recorded_at_ist": _ist_now(),
    }


def run_one(
    *,
    condition_id: str,
    role: str,
    cls,
    plant_id: str,
    seed: int,
) -> dict[str, Any]:
    cond = phase2_condition(condition_id)
    mode = str(cond.meta.get("mode") or "A")
    auto_credit = bool(cond.meta.get("autonomous_discovery_credit", mode == "A"))
    controlled = bool(cond.meta.get("controlled_availability", False))
    # Mode B inject only on S cells (U = null injection control).
    mode_b_inject = mode == "B" and role == "S" and controlled

    episode_id = f"{condition_id}_{role}_seed{seed}"
    recorder = Phase2Recorder(
        episode_id=episode_id,
        condition_id=condition_id,
        mode=mode,
        autonomous_discovery_credit=auto_credit and not (mode == "B"),
        controlled_availability=controlled,
        target_role=role,
        seed=seed,
        representation_id="R1",
    )

    t0 = time.time()
    runner = ConditionRunner(condition=cond)

    def _ep(ctx, _cls=cls, _seed=seed, _plant_id=plant_id):
        target = _cls(seed=_seed)
        pipe = _pipe(target, _seed, ctx["invention_mode"], ctx["episode_budget"])
        with observational_session(recorder, mode_b_inject=mode_b_inject):
            term = pipe.run(WEAK_SEED)
        src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
        lang = src.get("language") or {}
        methods_log = src.get("methods_log") or []
        records = lang.get("generation_records") or []
        verdicts = [independence_verdict(r) for r in records]
        fw = _extract_leftover_at_firewall(methods_log)
        n_ind = sum(
            1
            for v in verdicts
            if (v.get("independently_discovered") if isinstance(v, dict) else getattr(v, "independently_discovered", False))
        )
        n_ind_origin = sum(
            1
            for r in records
            if (r.get("candidate_origin") or r.get("origin")) == "independent_rediscovery"
        )
        verified = term.state is TerminalState.VERIFIED
        # Integrity: expect at least some instrumentation if growth/invent ran
        if recorder.pre_selection_count() == 0 and not recorder.records:
            recorder.mark_integrity_failure("no instrumentation records emitted")
        payload = {
            "condition_id": condition_id,
            "mode": mode,
            "autonomous_discovery_credit": recorder.autonomous_discovery_credit,
            "controlled_availability": controlled,
            "claim_namespace": "AUTONOMOUS" if mode == "A" else "CONTROLLED_INPUT",
            "budget_level": "BH",
            "representation": "R1",
            "invention_mode": ctx["invention_mode"],
            "episode_budget": ctx["episode_budget"],
            "target_role": role,
            "plant_id": _plant_id,
            "seed": _seed,
            "sacred": True,
            "phase": 2,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "terminal_state": str(term.state),
            "discovered": bool(getattr(term, "discovered", verified)),
            "pipeline_verified": verified,
            "secret_found": bool(getattr(target, "_ever_hit", None) or getattr(target, "_last_hit", None)),
            "budget_used": src.get("budget_used")
            or (ctx["episode_budget"] - int(getattr(pipe, "remaining_steps", 0) or 0)),
            "budget_remaining": src.get("budget_remaining"),
            "firewall_epoch": lang.get("firewall_epoch"),
            "firewalled": lang.get("firewalled"),
            "provenance_leak": lang.get("provenance_leak"),
            "leftover_at_firewall_decision": fw["leftover_at_firewall_decision"],
            "firewall_skipped": fw["firewall_skipped"],
            "firewall_armed": fw["firewall_armed"],
            "failure_class": src.get("failure_class"),
            "stop_reason": lang.get("stop_reason"),
            "occupancy": src.get("occupancy"),
            "n_generation_records": len(records),
            "n_independent": n_ind,
            "n_independent_rediscovery_origin": n_ind_origin,
            "independence_verdicts": verdicts,
            "generation_records": records,
            "methods_log": methods_log,
            "language": {
                "firewall_epoch": lang.get("firewall_epoch"),
                "firewalled": lang.get("firewalled"),
                "provenance_leak": lang.get("provenance_leak"),
                "stop_reason": lang.get("stop_reason"),
                "programs": lang.get("programs"),
            },
            "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
            "INVENT_CAP": INVENT_CAP,
            "odd_stride_body_key": ODD_STRIDE_BODY_KEY,
            "odd_cat_self_body_key": ODD_CAT_SELF_BODY_KEY,
        }
        strict = (
            verified
            and int(lang.get("firewall_epoch") or 0) >= 1
            and n_ind > 0
            and not bool(lang.get("provenance_leak"))
            and mode == "A"  # Mode B never gets autonomous independence credit
        )
        payload["strict_independence"] = strict
        if mode == "B":
            payload["strict_independence_note"] = (
                "Mode B: autonomous_discovery_credit=false; strict_independence forced false for invent credit"
            )
            payload["strict_independence"] = False
        recorder.record_terminal(payload=payload)
        payload["instrumentation"] = recorder.to_dict()
        payload["mechanism"] = classify_seed_mechanism(payload)
        return payload

    return runner.run_sacred(seed=seed, plant_id=plant_id, episode_fn=_ep)


def _u_gate(mode_a_u: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(mode_a_u)
    v = sum(1 for r in mode_a_u if r.get("pipeline_verified"))
    fw = sum(1 for r in mode_a_u if int(r.get("firewall_epoch") or 0) >= 1)
    ind = sum(1 for r in mode_a_u if r.get("strict_independence"))
    # Stage-2 BH-R1×U was F7/I7/V7. Require same class: all 7 verified+fw+ind.
    ok = n == 7 and v == 7 and fw == 7 and ind == 7
    return {
        "n": n,
        "verified": v,
        "firewall": fw,
        "independent_strict": ind,
        "expect": "F7/I7/V7",
        "pass": ok,
        "label": "OBSERVED",
        "historical_reference": "Stage-2 BH-R1×U F7/I7/V7 on S2-U plant",
        "note": "Phase-2 uses fresh P2-U plant; same behavioral family",
    }


def write_reports(*, episodes: list[dict[str, Any]], gate: dict[str, Any], head: str) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    mode_a = [e for e in episodes if e.get("mode") == "A"]
    mode_b = [e for e in episodes if e.get("mode") == "B"]
    mode_a_s = [e for e in mode_a if e.get("target_role") == "S"]
    mode_a_u = [e for e in mode_a if e.get("target_role") == "U"]
    mode_b_s = [e for e in mode_b if e.get("target_role") == "S"]
    mode_b_u = [e for e in mode_b if e.get("target_role") == "U"]

    u_gate = _u_gate(mode_a_u)
    agg_a_s = aggregate_outcomes(episodes, mode="A", role="S")
    agg_a_u = aggregate_outcomes(episodes, mode="A", role="U")
    agg_b_s = aggregate_outcomes(episodes, mode="B", role="S")
    agg_b_u = aggregate_outcomes(episodes, mode="B", role="U")
    conclusion = final_h2_h3_conclusion(mode_b_s=agg_b_s) if mode_b_s else "INCONCLUSIVE"

    # Persist per-episode
    runs_dir = OUT / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    for e in episodes:
        fn = runs_dir / f"{e['condition_id']}_seed{e['seed']}_{e['target_role']}.json"
        fn.write_text(json.dumps(e, indent=2, default=str) + "\n")

    summary = {
        "document": "aivd_3_40_phase2_results",
        "recorded_at_ist": _ist_now(),
        "design_tip": DESIGN_TIP,
        "execution_head": head,
        "version": __version__,
        "micro_hash": micro_hash(),
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH48,
        "seeds": list(SEEDS),
        "plants": {"S": PLANT_P2_S, "U": PLANT_P2_U},
        "odd_stride_body_key": ODD_STRIDE_BODY_KEY,
        "odd_cat_self_body_key": ODD_CAT_SELF_BODY_KEY,
        "env_gate": gate,
        "u_positive_control": u_gate,
        "n_episodes": len(episodes),
        "mode_a_n": len(mode_a),
        "mode_b_n": len(mode_b),
        "aggregates": {
            "mode_a_s": agg_a_s,
            "mode_a_u": agg_a_u,
            "mode_b_s": agg_b_s,
            "mode_b_u": agg_b_u,
        },
        "final_conclusion": conclusion,
        "r1b_optional_executed": False,
        "r1b_optional_note": (
            "P2-R1b-SACRED-AS-EXECUTED NOT auto-launched; only if Mode A/B cannot distinguish "
            "— STOP to report necessity (do not auto-launch)."
        ),
        "episodes_index": [
            {
                "condition_id": e.get("condition_id"),
                "mode": e.get("mode"),
                "target_role": e.get("target_role"),
                "seed": e.get("seed"),
                "pipeline_verified": e.get("pipeline_verified"),
                "firewall_epoch": e.get("firewall_epoch"),
                "strict_independence": e.get("strict_independence"),
                "mechanism_outcome": (e.get("mechanism") or {}).get("outcome"),
                "claim_namespace": e.get("claim_namespace"),
            }
            for e in episodes
        ],
        "status_line": "PHASE-2 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED",
    }
    RESULTS_JSON.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    (OUT / "results.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    md = []
    md.append("# AIVD 3.40 Phase-2 Results — H2/H3 Mechanism Localization")
    md.append("")
    md.append(f"**Recorded:** {summary['recorded_at_ist']}")
    md.append(f"**Design tip (frozen):** `{DESIGN_TIP}`")
    md.append(f"**Execution HEAD:** `{head}`")
    md.append(f"**Status:** `{summary['status_line']}`")
    md.append("")
    md.append("## Manifest")
    md.append("")
    md.append("| Field | Value |")
    md.append("|-------|-------|")
    md.append(f"| Seeds | `{list(SEEDS)}` |")
    md.append(f"| Budget | BH48 ({BH48}) |")
    md.append(f"| invent_cap | {INVENT_CAP} (unchanged) |")
    md.append(f"| REDISCOVERY_FLOOR | {REDISCOVERY_FLOOR} (unchanged) |")
    md.append(f"| Plants | S=`{PLANT_P2_S}` U=`{PLANT_P2_U}` (fresh Phase-2) |")
    md.append(f"| Odd-stride body (historical) | `{ODD_STRIDE_BODY_KEY}` |")
    md.append(f"| Odd CAT-self body | `{ODD_CAT_SELF_BODY_KEY}` |")
    md.append(f"| micro_hash | `{summary['micro_hash']}` |")
    md.append(f"| version | `{__version__}` |")
    md.append("")
    md.append("## Integrity")
    md.append("")
    md.append(f"- Env gate: **{gate.get('gate_status')}** failures={gate.get('failures')}")
    md.append(f"- U positive control (Mode A × U): **{'PASS' if u_gate['pass'] else 'FAIL'}** "
              f"V{u_gate['verified']}/F{u_gate['firewall']}/I{u_gate['independent_strict']} "
              f"(expect F7/I7/V7) — label `{u_gate['label']}`")
    md.append("- Frozen historical artifacts (Stage-2/Phase-1/Stage-3/3.38/3.39) were not mutated by this runner.")
    md.append("- Instrumentation is observational; Mode B injection uses CONTROLLED_INPUT provenance only.")
    md.append("")
    md.append("## Mode A (AUTONOMOUS namespace) — P2-R1-INSTR")
    md.append("")
    md.append("### Mode A × U (positive control)")
    md.append("")
    md.append(f"- n={len(mode_a_u)} verified={sum(1 for e in mode_a_u if e.get('pipeline_verified'))} "
              f"fw={sum(1 for e in mode_a_u if int(e.get('firewall_epoch') or 0)>=1)} "
              f"strict_ind={sum(1 for e in mode_a_u if e.get('strict_independence'))}")
    md.append("")
    md.append("### Mode A × S")
    md.append("")
    md.append(f"- n={len(mode_a_s)} verified={sum(1 for e in mode_a_s if e.get('pipeline_verified'))}")
    md.append(f"- Mechanism aggregate: `{json.dumps(agg_a_s.get('outcome_counts'))}` → **{agg_a_s.get('cell_conclusion')}**")
    md.append(f"- Claim namespace: `{agg_a_s.get('claim_namespace')}` (autonomous invent credit allowed for invent path)")
    odd_abs = sum(1 for e in mode_a_s if not (e.get('mechanism') or {}).get('odd_stride_in_produced'))
    md.append(f"- Odd-stride in produced generation_records: absent in {odd_abs}/{len(mode_a_s)} "
              "(H1 continuity expectation under R1) — label OBSERVED")
    md.append("")
    md.append("## Mode B (CONTROLLED_INPUT namespace) — P2-R1-MODEB-ODD")
    md.append("")
    md.append("**NOT autonomous discovery.** `autonomous_discovery_credit=false`.")
    md.append("")
    md.append("### Mode B × S (primary H2/H3 path)")
    md.append("")
    md.append(f"- n={len(mode_b_s)} verified={sum(1 for e in mode_b_s if e.get('pipeline_verified'))} "
              "(verify reported for engineering continuity only; no invent credit)")
    md.append(f"- Outcome counts 1–6: `{json.dumps(agg_b_s.get('outcome_counts'))}`")
    md.append(f"- Cell conclusion: **{agg_b_s.get('cell_conclusion')}**")
    for c in agg_b_s.get("classifications") or []:
        md.append(
            f"  - seed {c.get('seed')}: outcome={c.get('outcome')} reading={c.get('reading')} "
            f"present={c.get('present_any')} ranks={c.get('present_ranks')} "
            f"selected={c.get('selected_any')} — {c.get('reason')}"
        )
    md.append("")
    md.append("### Mode B × U (null-injection control)")
    md.append("")
    md.append(f"- n={len(mode_b_u)} verified={sum(1 for e in mode_b_u if e.get('pipeline_verified'))}")
    md.append("- Odd-stride injection: **null** (must not privilege S). Instrumentation path active.")
    md.append("")
    md.append("## Autonomous vs Controlled separation")
    md.append("")
    md.append("| Namespace | Conditions | Discovery credit |")
    md.append("|-----------|------------|------------------|")
    md.append("| AUTONOMOUS | P2-R1-INSTR | Yes (invent/grow under R1+instr) |")
    md.append("| CONTROLLED_INPUT | P2-R1-MODEB-ODD | **No** — availability is evaluator-controlled |")
    md.append("")
    md.append("Do **not** merge Mode A and Mode B discovery counts.")
    md.append("")
    md.append("## H1–H6 (Phase-2 update)")
    md.append("")
    md.append("| H | Status | Evidence class |")
    md.append("|---|--------|----------------|")
    md.append("| H1 | Continuity check under Mode A R1×S (odd-stride invent absence) | OBSERVED |")
    md.append(f"| H2 vs H3 | **{conclusion}** from Mode B×S outcomes 1–6 | CONTROLLED (availability) + OBSERVED (pool/rank/select) |")
    md.append("| H4 | Only if outcome 4 dominates | OBSERVED |")
    md.append("| H5 | Not reopened (budget frozen BH48) | — |")
    md.append("| H6 | Not primary | — |")
    md.append("")
    md.append("## Comparison note (not identical conditions)")
    md.append("")
    md.append("Compare Stage-2 BH-R1 S, BH-R1b S, Phase-2 Mode-A S/U, Mode-B S **without** treating as identical conditions "
              "(different plants; Mode B controlled availability; instrumentation additive).")
    md.append("")
    md.append("## Uncertainty / R1b caveat")
    md.append("")
    md.append("- Optional `P2-R1b-SACRED-AS-EXECUTED` **not executed**.")
    md.append("- Sacred R1b remains observational under caveat `7a3457e` (invent-basis trim after smoke).")
    md.append("- If Mode A/B cannot distinguish and R1b continuity were needed: STOP and report necessity — do not auto-launch.")
    md.append("")
    md.append("## Data quality")
    md.append("")
    md.append(f"- Episodes written under `{OUT}/runs/`.")
    md.append("- Labels used: OBSERVED | CONTROLLED | COUNTERFACTUAL | UNKNOWN as applicable.")
    md.append("- No COUNTERFACTUAL claims in primary conclusion.")
    md.append("")
    md.append("## Conclusion")
    md.append("")
    md.append(f"**Final (Mode B primary): `{conclusion}`**")
    md.append("")
    md.append("```")
    md.append(summary["status_line"])
    md.append("```")
    md.append("")
    RESULTS_MD.write_text("\n".join(md) + "\n")
    (OUT / "results.md").write_text("\n".join(md) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["u-gate", "mode-a", "mode-b", "all"], default="all")
    ap.add_argument("--seed", type=int, default=None, help="optional single seed")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    gate = env_gate()
    (OUT / "env_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    if gate["gate_status"] != "PASS":
        print("PHASE-2 BLOCKED: env gate FAIL:", gate["failures"])
        raise SystemExit(2)

    seeds = list(SEEDS) if args.seed is None else [args.seed]
    head = _git_head()
    episodes: list[dict[str, Any]] = []

    def run_cell(condition_id: str, role: str, cls, plant_id: str, seed: int) -> dict[str, Any]:
        print(f"[Phase-2] {condition_id} {role} seed={seed} ...", flush=True)
        row = run_one(condition_id=condition_id, role=role, cls=cls, plant_id=plant_id, seed=seed)
        print(
            f"  verified={row.get('pipeline_verified')} fw={row.get('firewall_epoch')} "
            f"outcome={(row.get('mechanism') or {}).get('outcome')} elapsed={row.get('elapsed_s')}s",
            flush=True,
        )
        return row

    # 1) Mode A U first (positive control gate)
    if args.only in ("u-gate", "mode-a", "all"):
        for seed in seeds:
            episodes.append(run_cell(CONDITION_INSTR, "U", LlamaP2UTarget, PLANT_P2_U, seed))
        if args.seed is None and args.only in ("u-gate", "mode-a", "all"):
            ug = _u_gate([e for e in episodes if e.get("mode") == "A" and e.get("target_role") == "U"])
            (OUT / "u_positive_control_gate.json").write_text(json.dumps(ug, indent=2) + "\n")
            if not ug["pass"]:
                print("PHASE-2 BLOCKED: U positive control failed", ug)
                # Still write partial
                write_reports(episodes=episodes, gate=gate, head=head)
                raise SystemExit(3)

    if args.only == "u-gate":
        write_reports(episodes=episodes, gate=gate, head=head)
        return

    # 2) Mode A S
    if args.only in ("mode-a", "all"):
        for seed in seeds:
            episodes.append(run_cell(CONDITION_INSTR, "S", LlamaP2STarget, PLANT_P2_S, seed))

    # 3) Mode B only if U gate passed (already enforced)
    if args.only in ("mode-b", "all"):
        for seed in seeds:
            episodes.append(run_cell(CONDITION_MODEB, "S", LlamaP2STarget, PLANT_P2_S, seed))
        for seed in seeds:
            episodes.append(run_cell(CONDITION_MODEB, "U", LlamaP2UTarget, PLANT_P2_U, seed))

    summary = write_reports(episodes=episodes, gate=gate, head=head)
    print(summary["status_line"])
    print("final_conclusion=", summary["final_conclusion"])


if __name__ == "__main__":
    main()
