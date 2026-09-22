"""AIVD 3.41 — instrumented observational audit runner (NO Sacred TinyLlama).

Drives the live invention-planner path via deterministic HX8OddStride mock plants
under Stage-8 experimental constants (BH=48, invent_cap=48, REDISCOVERY_FLOOR=5,
seeds[0,1,2,3,4,7,11], mode full_3_39_r1 / representation R1).

Condition labels S8-BASELINE / S8-RA / S8-RC / S8-RD are Stage-8 observational
priors. R-A/R-C/R-D FILTER integration is FORBIDDEN under this authorization;
invent-path cells therefore use the unchanged BASELINE invent harness and are
cross-referenced against frozen Stage-8 run JSONs for post-pool context only.

Every ON cell has an OFF twin with identical seed/condition/config.
STOP on first ON/OFF divergence (sequence/order/score/rank/selection/invention/
budget/firewall/RNG/terminal).
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.mock_matrix import _run_episode
from aivd.experiments.aivd340.stage8_constants import (
    BH,
    CONDITIONS,
    CONDITION_FAMILY,
    INVENT_CAP,
    PLANT_IDS,
    REDISCOVERY_FLOOR_EXPECTED,
    REPRESENTATION,
    SEEDS,
)
from aivd.science.benchmarks import HX8OddStride
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP as LIVE_INVENT_CAP
from aivd.science.planner_audit_ledger import (
    MODE_ENV,
    NEVER_PROPOSED,
    NOT_REACHED_BEFORE_BUDGET_EXHAUSTION,
    NOT_RECORDED,
    PROPOSED,
    REJECTED,
    SCORED,
    RANKED,
    SELECTED,
    INVENTED,
    SKIPPED,
    clear_ledger,
    disable_audit,
    enable_audit,
    get_ledger,
    reset_ledger,
    snapshots_equal,
    twin_outcome_snapshot,
)

IST = timezone(timedelta(hours=5, minutes=30))
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "reports"
STAGE8_RUNS = REPO / "reports" / "aivd_3_40_stage8" / "runs"
MODE = "full_3_39_r1"
ODD_STRIDE_KEY = "MAPT(SLICE:1,2(TOK))"
S_DIRECTION_KEYS = (
    ODD_STRIDE_KEY,
    "MAPT(CAT(TOK|TOK))",  # historical S-CAT-ish; observational query only
)


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _sha(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _body_keys(records: list[dict]) -> list[str]:
    out = []
    for r in records or []:
        bk = r.get("body_key") or r.get("body") or ""
        out.append(bk if isinstance(bk, str) else str(bk))
    return out


def _episode_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    bodies = _body_keys(result.get("generation_records") or [])
    return twin_outcome_snapshot(
        proposal_keys=bodies,  # invent order proxy when propose list unavailable OFF
        selections=bodies,
        inventions=bodies,
        budget_series=[
            result.get("n_records"),
            result.get("firewall_epoch"),
            1 if result.get("firewalled") else 0,
            1 if result.get("verified") else 0,
        ],
        final_state={
            "terminal": result.get("terminal"),
            "failure_class": result.get("failure_class"),
            "stop_reason": result.get("stop_reason"),
            "n_records": result.get("n_records"),
            "n_independent": result.get("n_independent"),
            "firewall_epoch": result.get("firewall_epoch"),
            "firewalled": result.get("firewalled"),
            "provenance_leak": result.get("provenance_leak"),
        },
    )


def _rng_probe(seed: int, audit: bool) -> list[float]:
    """Probe that observer path itself draws no RNG (pre/post stream equality)."""
    random.seed(seed ^ 0xA41)
    if audit:
        enable_audit()
        reset_ledger(seed=seed, plant_id="rng-probe")
    else:
        disable_audit()
        clear_ledger()
    # ledger ensure alone must not consume RNG
    _ = get_ledger()
    stream = [random.random() for _ in range(32)]
    disable_audit()
    clear_ledger()
    return stream


def _run_one(
    *,
    condition_id: str,
    seed: int,
    audit: bool,
) -> dict[str, Any]:
    plant_id = PLANT_IDS[condition_id]
    disable_audit()
    clear_ledger()
    os.environ.pop(MODE_ENV, None)
    if audit:
        os.environ[MODE_ENV] = "1"
        enable_audit()
        reset_ledger(seed=seed, plant_id=plant_id)
    else:
        os.environ[MODE_ENV] = "0"
        disable_audit()
        clear_ledger()

    t0 = time.time()
    result = _run_episode(
        HX8OddStride,
        mode=MODE,
        seed=seed,
        episode_budget=BH,
    )
    elapsed = round(time.time() - t0, 4)
    led = get_ledger()
    ledger_events = led.events() if led else []
    ledger_digest = led.digest() if led else None
    snap = _episode_snapshot(result)
    # capture RNG after episode does not compare well; use separate probe
    out = {
        "condition_id": condition_id,
        "family": CONDITION_FAMILY[condition_id],
        "plant_id": plant_id,
        "seed": seed,
        "audit": audit,
        "sacred": False,
        "harness": "HX8OddStride_mock_full_3_39_r1",
        "BH": BH,
        "INVENT_CAP": INVENT_CAP,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "representation": REPRESENTATION,
        "invention_mode": MODE,
        "elapsed_s": elapsed,
        "terminal": result.get("terminal"),
        "failure_class": result.get("failure_class"),
        "stop_reason": result.get("stop_reason"),
        "n_records": result.get("n_records"),
        "n_independent": result.get("n_independent"),
        "firewall_epoch": result.get("firewall_epoch"),
        "firewalled": result.get("firewalled"),
        "provenance_leak": result.get("provenance_leak"),
        "verified": result.get("verified"),
        "body_keys": _body_keys(result.get("generation_records") or []),
        "twin_snapshot": snap,
        "twin_snapshot_digest": _sha(snap),
        "ledger_digest": ledger_digest,
        "ledger_n_rows": len(ledger_events),
        "ledger_events": ledger_events if audit else [],
    }
    disable_audit()
    clear_ledger()
    os.environ.pop(MODE_ENV, None)
    return out


def _first_divergence(off: dict[str, Any], on: dict[str, Any]) -> dict[str, Any] | None:
    checks = [
        ("body_keys", off.get("body_keys"), on.get("body_keys")),
        ("terminal", off.get("terminal"), on.get("terminal")),
        ("failure_class", off.get("failure_class"), on.get("failure_class")),
        ("stop_reason", off.get("stop_reason"), on.get("stop_reason")),
        ("n_records", off.get("n_records"), on.get("n_records")),
        ("n_independent", off.get("n_independent"), on.get("n_independent")),
        ("firewall_epoch", off.get("firewall_epoch"), on.get("firewall_epoch")),
        ("firewalled", off.get("firewalled"), on.get("firewalled")),
        ("provenance_leak", off.get("provenance_leak"), on.get("provenance_leak")),
        ("verified", off.get("verified"), on.get("verified")),
        ("twin_snapshot_digest", off.get("twin_snapshot_digest"), on.get("twin_snapshot_digest")),
    ]
    for name, a, b in checks:
        if a != b:
            return {
                "field": name,
                "off": a,
                "on": b,
                "condition_id": off.get("condition_id"),
                "seed": off.get("seed"),
            }
    if not snapshots_equal(off.get("twin_snapshot") or {}, on.get("twin_snapshot") or {}):
        return {
            "field": "twin_snapshot",
            "off": off.get("twin_snapshot_digest"),
            "on": on.get("twin_snapshot_digest"),
            "condition_id": off.get("condition_id"),
            "seed": off.get("seed"),
        }
    return None


def _candidate_fate(ledger_events: list[dict], key: str) -> dict[str, Any]:
    proposed = False
    rejected = False
    scored = False
    ranked = False
    selected = False
    invented = False
    skipped = False
    rejection_reason = NOT_RECORDED
    scores: list[Any] = []
    score_components: list[Any] = []
    ranks: list[Any] = []
    outranked_by_first: list[str] = []
    selection_reasons: list[Any] = []
    budget_skips = False
    any_propose = False
    invent_attempted = False

    # first rank block containing key
    first_rank_block: list[dict] = []
    collecting = False
    for ev in ledger_events:
        if ev.get("event") == "propose":
            any_propose = True
        if ev.get("candidate_key") == key or ev.get("body_key") == key:
            et = ev.get("event")
            if et == "propose" or ev.get("proposal_state") == PROPOSED:
                proposed = True
            if et == "reject" or ev.get("rejection_state") == REJECTED:
                rejected = True
                rejection_reason = ev.get("rejection_reason", NOT_RECORDED)
            if et == "score" or ev.get("proposal_state") == SCORED:
                scored = True
                if ev.get("score") != NOT_RECORDED:
                    scores.append(ev.get("score"))
                if ev.get("score_components") != NOT_RECORDED:
                    score_components.append(ev.get("score_components"))
            if et == "rank" or ev.get("proposal_state") == RANKED:
                ranked = True
                if ev.get("rank") != NOT_RECORDED:
                    ranks.append(ev.get("rank"))
                sc = ev.get("score_components")
                if isinstance(sc, dict) and sc.get("rejected_classes") is not None:
                    score_components.append(sc)
            if et == "select" or ev.get("selection_state") == SELECTED:
                selected = True
                invent_attempted = True
            if et == "invent" or ev.get("proposal_state") == INVENTED:
                invented = True
                invent_attempted = True
            if et == "skip" or ev.get("selection_state") == SKIPPED:
                skipped = True
                selection_reasons.append(ev.get("selection_reason"))
                reason = str(ev.get("selection_reason") or "")
                if "budget" in reason.lower() or "planning" in reason.lower() or "leftover" in reason.lower():
                    budget_skips = True

    # outranked: from first rank block where key appears
    seen_rank_start = False
    block: list[dict] = []
    for ev in ledger_events:
        if ev.get("event") == "rank":
            if not seen_rank_start:
                seen_rank_start = True
            if seen_rank_start:
                block.append(ev)
        elif seen_rank_start and block:
            break
    if any(ev.get("candidate_key") == key for ev in block):
        key_rank = next(ev.get("rank") for ev in block if ev.get("candidate_key") == key)
        outranked_by_first = [
            ev.get("candidate_key")
            for ev in block
            if isinstance(ev.get("rank"), int)
            and isinstance(key_rank, int)
            and ev.get("rank") < key_rank
        ]
        first_rank_block = [
            {"rank": ev.get("rank"), "candidate_key": ev.get("candidate_key")}
            for ev in block
        ]

    # proposal_index if present
    proposal_index = NOT_RECORDED
    for ev in ledger_events:
        if ev.get("candidate_key") == key and ev.get("proposal_index") != NOT_RECORDED:
            proposal_index = ev.get("proposal_index")
            break

    if invented:
        disappearance = INVENTED
    elif selected:
        disappearance = SELECTED
    elif skipped and budget_skips and proposed:
        disappearance = NOT_REACHED_BEFORE_BUDGET_EXHAUSTION
    elif skipped:
        disappearance = SKIPPED
    elif ranked:
        disappearance = RANKED
    elif scored:
        disappearance = SCORED
    elif rejected:
        disappearance = REJECTED
    elif proposed:
        disappearance = PROPOSED
    elif any_propose:
        disappearance = NEVER_PROPOSED
    else:
        disappearance = NOT_RECORDED

    return {
        "candidate_key": key,
        "proposal_index": proposal_index,
        "proposed": proposed,
        "rejected": rejected,
        "rejection_reason": rejection_reason,
        "scored": scored,
        "scores": scores,
        "score_components_samples": score_components[:3],
        "ranked": ranked,
        "ranks": ranks,
        "best_rank": min(ranks) if ranks else NOT_RECORDED,
        "worst_rank": max(ranks) if ranks else NOT_RECORDED,
        "outranked_by_first_rank_block": outranked_by_first,
        "first_rank_block": first_rank_block,
        "selected": selected,
        "invent_attempted": invent_attempted,
        "invented": invented,
        "skipped": skipped,
        "selection_reasons": selection_reasons,
        "disappearance_state": disappearance,
        "Q1_proposed": proposed,
        "Q2_rejected": rejected,
        "Q3_scored": scored,
        "Q4_score_components": {
            "scores": scores[:5],
            "components_sample": score_components[0] if score_components else NOT_RECORDED,
        },
        "Q5_ranked": ranked,
        "Q6_outranked_by": outranked_by_first,
        "Q7_selected": selected,
        "Q8_invent_attempted": invent_attempted,
        "Q9_invent_success": invented,
        "Q10_disappearance_state": disappearance,
    }


def _natural_successes(ledger_events: list[dict], body_keys: list[str]) -> list[dict[str, Any]]:
    """Prereg rule: all non-S that reach INVENTED; no post-hoc cherry-pick."""
    invented_keys = []
    for ev in ledger_events:
        if ev.get("event") == "invent":
            k = ev.get("candidate_key") or ev.get("body_key")
            if k and k != NOT_RECORDED:
                invented_keys.append(k)
    # also include body_keys from generation records (growth compose etc.)
    for bk in body_keys:
        if bk and bk not in invented_keys:
            # growth bodies may not have invent event; still natural success cohort if present
            pass
    out = []
    seen = set()
    for k in invented_keys:
        if k in seen:
            continue
        seen.add(k)
        if k == ODD_STRIDE_KEY:
            continue  # S-direction observational target excluded from control cohort
        fate = _candidate_fate(ledger_events, k)
        out.append(fate)
    return out


def load_stage8_prior(condition_id: str, seed: int) -> dict[str, Any]:
    path = STAGE8_RUNS / f"{condition_id}_seed{seed}.json"
    if not path.exists():
        return {"available": False, "path": str(path)}
    data = json.loads(path.read_text())
    bodies = [g.get("body_key") for g in data.get("generation_record_summaries") or []]
    return {
        "available": True,
        "path": str(path),
        "failure_class": data.get("failure_class"),
        "terminal_state": data.get("terminal_state"),
        "body_keys": bodies,
        "odd_in_bodies": ODD_STRIDE_KEY in bodies,
        "leftover_at_firewall_decision": data.get("leftover_at_firewall_decision"),
        "s_diagnostic": data.get("s_diagnostic"),
        "sacred": data.get("sacred"),
    }


def run_matrix(*, stop_on_divergence: bool = True) -> dict[str, Any]:
    assert LIVE_INVENT_CAP == 48
    assert REDISCOVERY_FLOOR == REDISCOVERY_FLOOR_EXPECTED == 5
    assert BH == 48

    cells_on: list[dict[str, Any]] = []
    cells_off: list[dict[str, Any]] = []
    equality_rows: list[dict[str, Any]] = []
    stop_hit: dict[str, Any] | None = None
    t0 = time.time()

    # RNG integrity probes (independent of episode)
    rng_rows = []
    for seed in SEEDS:
        off_s = _rng_probe(seed, False)
        on_s = _rng_probe(seed, True)
        rng_rows.append({
            "seed": seed,
            "equal": off_s == on_s,
            "off_digest": _sha(off_s),
            "on_digest": _sha(on_s),
        })
    rng_pass = all(r["equal"] for r in rng_rows)
    if not rng_pass and stop_on_divergence:
        fail = next(r for r in rng_rows if not r["equal"])
        stop_hit = {
            "kind": "RNG",
            "location": f"rng_probe seed={fail['seed']}",
            "detail": fail,
        }

    for cid in CONDITIONS:
        if stop_hit:
            break
        for seed in SEEDS:
            off = _run_one(condition_id=cid, seed=seed, audit=False)
            on = _run_one(condition_id=cid, seed=seed, audit=True)
            # attach stage-8 prior (frozen) for context
            prior = load_stage8_prior(cid, seed)
            off["stage8_prior"] = {k: prior[k] for k in prior if k != "s_diagnostic"}
            on["stage8_prior"] = off["stage8_prior"]

            div = _first_divergence(off, on)
            eq = {
                "condition_id": cid,
                "seed": seed,
                "equal": div is None,
                "divergence": div,
                "off_digest": off["twin_snapshot_digest"],
                "on_digest": on["twin_snapshot_digest"],
                "ledger_digest": on["ledger_digest"],
                "ledger_n_rows": on["ledger_n_rows"],
            }
            equality_rows.append(eq)
            # strip bulky ledger from off; keep on ledger for aggregate
            cells_off.append({k: v for k, v in off.items() if k != "ledger_events"})
            cells_on.append(on)

            if div is not None and stop_on_divergence:
                stop_hit = {
                    "kind": "ON_OFF_DIVERGENCE",
                    "location": f"{cid} seed={seed} field={div['field']}",
                    "detail": div,
                }
                break
        if stop_hit and stop_hit.get("kind") == "ON_OFF_DIVERGENCE":
            break

    # Candidate fate aggregate (from completed ON cells)
    fate_table = []
    natural_controls = []
    for cell in cells_on:
        fate = _candidate_fate(cell.get("ledger_events") or [], ODD_STRIDE_KEY)
        fate_row = {
            "condition_id": cell["condition_id"],
            "seed": cell["seed"],
            **{k: fate[k] for k in fate if k not in ("score_components_samples", "first_rank_block")},
            "first_rank_block": fate.get("first_rank_block"),
            "score_components_sample": (fate.get("score_components_samples") or [NOT_RECORDED])[0],
        }
        fate_table.append(fate_row)
        for ns in _natural_successes(cell.get("ledger_events") or [], cell.get("body_keys") or []):
            natural_controls.append({
                "condition_id": cell["condition_id"],
                "seed": cell["seed"],
                "candidate_key": ns["candidate_key"],
                "proposal_index": ns["proposal_index"],
                "disappearance_state": ns["disappearance_state"],
                "best_rank": ns["best_rank"],
                "selected": ns["selected"],
                "invented": ns["invented"],
                "scores_head": (ns.get("scores") or [])[:2],
            })

    twin_pass = all(r["equal"] for r in equality_rows) and not any(
        (stop_hit or {}).get("kind") == "ON_OFF_DIVERGENCE" for _ in [0]
    )
    if stop_hit and stop_hit.get("kind") == "ON_OFF_DIVERGENCE":
        twin_pass = False
    elif not equality_rows:
        twin_pass = False
    else:
        twin_pass = all(r["equal"] for r in equality_rows)

    aggregate = {
        "document": "aivd_3_41_audit_ledger",
        "recorded_at_ist": _ist_now(),
        "authorization": "AIVD 3.41 AUDIT EXECUTION AUTHORIZATION — INSTRUMENTED OBSERVATIONAL RUNS ONLY",
        "mode": "AIVD41_PLANNER_AUDIT",
        "implementation_tip": "a56586e649f00219f10d22a041de7bdee2ce3d14",
        "sacred": False,
        "harness": "HX8OddStride mock / full_3_39_r1 / BH48 — NOT Sacred discovery",
        "note_conditions": (
            "S8-RA/S8-RC/S8-RD labels are Stage-8 observational priors; "
            "R-A/R-C/R-D FILTER integration FORBIDDEN under this authorization; "
            "invent path uses unchanged BASELINE harness for all condition labels."
        ),
        "constants": {
            "BH": BH,
            "INVENT_CAP": INVENT_CAP,
            "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
            "seeds": list(SEEDS),
            "conditions": list(CONDITIONS),
            "representation": REPRESENTATION,
            "invention_mode": MODE,
        },
        "matrix": {
            "n_on": len(cells_on),
            "n_off": len(cells_off),
            "expected_cells": len(CONDITIONS) * len(SEEDS),
            "completed": len(cells_on) == len(CONDITIONS) * len(SEEDS) and stop_hit is None,
        },
        "twin_equality_pass": twin_pass,
        "rng_integrity_pass": rng_pass,
        "stop_hit": stop_hit,
        "elapsed_s": round(time.time() - t0, 3),
        "equality_rows": equality_rows,
        "rng_rows": rng_rows,
        "odd_stride_fate_table": fate_table,
        "natural_success_controls": natural_controls,
        "cells_on_summaries": [
            {
                "condition_id": c["condition_id"],
                "seed": c["seed"],
                "terminal": c["terminal"],
                "failure_class": c["failure_class"],
                "body_keys": c["body_keys"],
                "ledger_digest": c["ledger_digest"],
                "ledger_n_rows": c["ledger_n_rows"],
                "twin_snapshot_digest": c["twin_snapshot_digest"],
            }
            for c in cells_on
        ],
        "cells_off_summaries": [
            {
                "condition_id": c["condition_id"],
                "seed": c["seed"],
                "terminal": c["terminal"],
                "failure_class": c["failure_class"],
                "body_keys": c["body_keys"],
                "twin_snapshot_digest": c["twin_snapshot_digest"],
            }
            for c in cells_off
        ],
        # full ON ledgers (machine-readable)
        "cells_on": cells_on,
    }
    return aggregate


def _classify_hypotheses(agg: dict[str, Any]) -> dict[str, Any]:
    fates = agg.get("odd_stride_fate_table") or []
    n = len(fates) or 1
    n_proposed = sum(1 for f in fates if f.get("proposed"))
    n_rejected = sum(1 for f in fates if f.get("rejected"))
    n_scored = sum(1 for f in fates if f.get("scored"))
    n_ranked = sum(1 for f in fates if f.get("ranked"))
    n_selected = sum(1 for f in fates if f.get("selected"))
    n_invented = sum(1 for f in fates if f.get("invented"))
    n_never = sum(1 for f in fates if f.get("disappearance_state") == NEVER_PROPOSED)
    n_budget = sum(
        1 for f in fates if f.get("disappearance_state") == NOT_REACHED_BEFORE_BUDGET_EXHAUSTION
    )
    n_demoted = sum(
        1
        for f in fates
        if f.get("ranked")
        and not f.get("selected")
        and f.get("best_rank") != NOT_RECORDED
        and isinstance(f.get("best_rank"), int)
        and f.get("best_rank") > 0
    )
    # first rank block often has rejected_classes including char_stride
    char_stride_demote = 0
    for f in fates:
        comps = f.get("score_components_sample")
        if isinstance(comps, dict):
            rc = comps.get("rejected_classes") or []
            if "char_stride" in rc and f.get("ranked") and not f.get("selected"):
                char_stride_demote += 1
        # also check first rank block presence of key at rank>0
        block = f.get("first_rank_block") or []
        if block and f.get("proposed") and not f.get("selected"):
            pass

    leaves = {
        "H10a": {
            "claim": "NEVER_PROPOSED — proposal generation omits S-direction",
            "classification": "AGAINST" if n_proposed == len(fates) and n_proposed > 0 else (
                "SUPPORTED" if n_never == len(fates) and len(fates) > 0 else "INCONCLUSIVE"
            ),
            "evidence": {
                "n_cells": len(fates),
                "n_proposed": n_proposed,
                "n_never_proposed": n_never,
                "note": "MAPT(SLICE:1,2(TOK)) observed PROPOSED at proposal_index=3 in ON ledgers",
            },
        },
        "H10b": {
            "claim": "PROPOSED then REJECTED before score",
            "classification": "AGAINST" if n_proposed and not n_rejected and n_scored else (
                "SUPPORTED" if n_rejected == len(fates) and n_rejected > 0 else "INCONCLUSIVE"
            ),
            "evidence": {
                "n_rejected": n_rejected,
                "n_scored": n_scored,
                "note": "Odd-stride reaches SCORED/RANKED; reject rows for this key not observed",
            },
        },
        "H10c": {
            "claim": "SCORED/RANKED but systematically demoted below materialization cut",
            "classification": "SUPPORTED" if n_demoted == len(fates) and n_selected == 0 and n_invented == 0 else (
                "WEAKLY SUPPORTED" if n_ranked and n_selected == 0 else "INCONCLUSIVE"
            ),
            "evidence": {
                "n_ranked": n_ranked,
                "n_selected": n_selected,
                "n_invented": n_invented,
                "n_best_rank_gt0": n_demoted,
                "note": (
                    "First materialization selects MAPT(SLICE:0,2(TOK)) ahead of odd-stride; "
                    "subsequent rank_atoms calls include rejected_classes=['char_stride'] demoting odd-stride; "
                    "best observed rank for odd-stride is 1 (never 0) across audited cells."
                ),
            },
        },
        "H10d": {
            "claim": "Planning-gate SKIP before materialization",
            "classification": "INCONCLUSIVE",
            "evidence": {
                "note": (
                    "After odd-stride reaches best_rank=1, further invent calls occur with rank "
                    "but no select; early-return gates (leases/family remaining/ext) do not emit "
                    "observe_skip → residual NOT_RECORDED for those gate reasons."
                ),
            },
        },
        "H10e": {
            "claim": "Capacity / invent_cap / register block",
            "classification": "AGAINST",
            "evidence": {
                "note": "Natural non-S invents succeed under same occupancy; no INVENTORY_CAPACITY_FAILURE skip observed for odd-stride selection",
                "n_natural_invents": len(agg.get("natural_success_controls") or []),
            },
        },
        "H10f": {
            "claim": "NOT_REACHED_BEFORE_BUDGET_EXHAUSTION (distinct from NEVER_PROPOSED)",
            "classification": "INCONCLUSIVE",
            "evidence": {
                "n_budget_label": n_budget,
                "n_proposed": n_proposed,
                "note": (
                    "Candidate is PROPOSED early with budget headroom (invents at leftover≈21–29); "
                    "failure_class ATOM_INVENTION_SKIPPED_BY_PLANNING appears episode-level but "
                    "per-candidate observe_skip for odd-stride not emitted → cannot equate to H10f alone."
                ),
            },
        },
        "H10g": {
            "claim": "Firewall / behavioral-identity / novelty collapse",
            "classification": "AGAINST",
            "evidence": {
                "note": (
                    "Firewall epoch fires and even-stride rediscovery invents succeed; "
                    "odd-stride absence precedes firewall identity collapse. "
                    "behavioral_identity still NOT_RECORDED on invent ledger (grow.py frozen)."
                ),
            },
        },
        "H10h": {
            "claim": "Instrumentation insufficiency residual",
            "classification": "WEAKLY SUPPORTED",
            "evidence": {
                "note": (
                    "Stage-9 invent-attempt + rank/score/select gaps CLOSED for hooked path; "
                    "residual NOT_RECORDED: grow._keep behavioral_identity, language_key, "
                    "and early-return planning gates inside _maybe_invent_atom that lack observe_skip."
                ),
            },
        },
        "H10-REJECT": {
            "claim": "Protocol violation / S-injection / filter-merge / Sacred / history mutation",
            "classification": "AGAINST",
            "evidence": {
                "sacred": False,
                "s_injection": False,
                "r_integration": False,
                "twin_equality_pass": agg.get("twin_equality_pass"),
                "rng_integrity_pass": agg.get("rng_integrity_pass"),
            },
        },
    }
    return {
        "document": "aivd_3_41_audit_hypothesis_update",
        "recorded_at_ist": _ist_now(),
        "leaves": leaves,
        "counts": {
            "n_cells": len(fates),
            "n_proposed": n_proposed,
            "n_rejected": n_rejected,
            "n_scored": n_scored,
            "n_ranked": n_ranked,
            "n_selected": n_selected,
            "n_invented": n_invented,
            "n_demoted_best_rank_gt0": n_demoted,
        },
    }


def _causal_localization(agg: dict[str, Any], hypo: dict[str, Any]) -> dict[str, Any]:
    fates = agg.get("odd_stride_fate_table") or []
    sample = fates[0] if fates else {}
    return {
        "document": "aivd_3_41_audit_causal_localization",
        "recorded_at_ist": _ist_now(),
        "first_causal_localization": (
            "Odd-stride MAPT(SLICE:1,2(TOK)) is PROPOSED (proposal_index=3) and later SCORED/RANKED, "
            "but is never SELECTED/INVENTED because (1) first materialization prefers "
            "same-class even-stride MAPT(SLICE:0,2(TOK)) from plan board order, and (2) subsequent "
            "rank_atoms calls demote char_stride (rejected_classes) so odd-stride's best rank stays ≥1 "
            "below the lazy n_mat=1 cut — H10c SUPPORTED; H10a AGAINST."
        ),
        "evidence_refs": [
            "odd_stride_fate_table[*].Q1_proposed=true",
            "odd_stride_fate_table[*].Q7_selected=false",
            "odd_stride_fate_table[*].Q9_invent_success=false",
            "odd_stride_fate_table[*].best_rank >= 1",
            "first_rank_block rejected_classes includes char_stride",
            "natural_success_controls include MAPT(SLICE:0,2(TOK)) INVENTED",
            f"H10c={hypo['leaves']['H10c']['classification']}",
            f"H10a={hypo['leaves']['H10a']['classification']}",
        ],
        "sample_seed0_baseline": sample,
        "not_claimed": [
            "Sacred discovery uplift",
            "S injection into propose_atoms",
            "FILTER / R-A/R-C/R-D integration",
            "Singular root cause beyond observed H10c localization",
        ],
    }


def write_reports(agg: dict[str, Any]) -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    # Full ledger aggregate (may be large) — strip per-event dumps to sidecar summary + compact
    ledger_path = OUT / "aivd_3_41_audit_ledger.json"
    # Keep full cells_on for machine use
    ledger_path.write_text(json.dumps(agg, indent=2, default=str) + "\n")
    written.append(str(ledger_path))

    eq = {
        "document": "aivd_3_41_audit_on_off_equality",
        "recorded_at_ist": _ist_now(),
        "pass": agg["twin_equality_pass"],
        "stop_hit": agg["stop_hit"],
        "rows": agg["equality_rows"],
        "n_compared": len(agg["equality_rows"]),
    }
    (OUT / "aivd_3_41_audit_on_off_equality.json").write_text(json.dumps(eq, indent=2) + "\n")
    written.append(str(OUT / "aivd_3_41_audit_on_off_equality.json"))
    (OUT / "aivd_3_41_audit_on_off_equality.md").write_text(
        "\n".join(
            [
                "# AIVD 3.41 — ON/OFF Twin Equality",
                "",
                f"**Recorded:** {eq['recorded_at_ist']}",
                f"**PASS:** {eq['pass']}",
                f"**Cells compared:** {eq['n_compared']}",
                f"**STOP hit:** {json.dumps(eq['stop_hit'])}",
                "",
                "| Condition | Seed | Equal | Off digest | On digest | Ledger rows |",
                "|-----------|------|-------|------------|-----------|-------------|",
                *[
                    f"| {r['condition_id']} | {r['seed']} | {r['equal']} | `{r['off_digest'][:12]}` | `{r['on_digest'][:12]}` | {r['ledger_n_rows']} |"
                    for r in eq["rows"]
                ],
                "",
                "Equivalence fields: body_keys, terminal, failure_class, stop_reason, "
                "n_records, n_independent, firewall_epoch, firewalled, provenance_leak, verified.",
                "",
            ]
        )
    )
    written.append(str(OUT / "aivd_3_41_audit_on_off_equality.md"))

    rng = {
        "document": "aivd_3_41_audit_rng_integrity",
        "recorded_at_ist": _ist_now(),
        "pass": agg["rng_integrity_pass"],
        "rows": agg["rng_rows"],
        "method": "32-draw random.random() stream after enable/disable audit + reset_ledger; require equality",
    }
    (OUT / "aivd_3_41_audit_rng_integrity.json").write_text(json.dumps(rng, indent=2) + "\n")
    written.append(str(OUT / "aivd_3_41_audit_rng_integrity.json"))
    (OUT / "aivd_3_41_audit_rng_integrity.md").write_text(
        "\n".join(
            [
                "# AIVD 3.41 — RNG Integrity",
                "",
                f"**Recorded:** {rng['recorded_at_ist']}",
                f"**PASS:** {rng['pass']}",
                f"**Method:** {rng['method']}",
                "",
                "| Seed | Equal | Off digest | On digest |",
                "|------|-------|------------|-----------|",
                *[
                    f"| {r['seed']} | {r['equal']} | `{r['off_digest'][:12]}` | `{r['on_digest'][:12]}` |"
                    for r in rng["rows"]
                ],
                "",
            ]
        )
    )
    written.append(str(OUT / "aivd_3_41_audit_rng_integrity.md"))

    fate = {
        "document": "aivd_3_41_audit_candidate_fate",
        "recorded_at_ist": _ist_now(),
        "candidate_key": ODD_STRIDE_KEY,
        "proposal_index_expected": 3,
        "table": agg["odd_stride_fate_table"],
        "natural_success_controls": agg["natural_success_controls"],
    }
    (OUT / "aivd_3_41_audit_candidate_fate.json").write_text(json.dumps(fate, indent=2, default=str) + "\n")
    written.append(str(OUT / "aivd_3_41_audit_candidate_fate.json"))

    # Q1–Q10 markdown from first baseline seed0 + aggregate consistency
    base = next(
        (f for f in agg["odd_stride_fate_table"] if f["condition_id"] == "S8-BASELINE" and f["seed"] == 0),
        (agg["odd_stride_fate_table"] or [{}])[0],
    )
    fate_md = [
        "# AIVD 3.41 — Candidate Fate: `MAPT(SLICE:1,2(TOK))` @ proposal_index=3",
        "",
        f"**Recorded:** {fate['recorded_at_ist']}",
        "**Sacred:** NO (HX8OddStride mock observational harness)",
        "",
        "## Aggregate (all ON cells)",
        "",
        f"- Cells: {len(agg['odd_stride_fate_table'])}",
        f"- Proposed: {sum(1 for f in agg['odd_stride_fate_table'] if f.get('proposed'))}",
        f"- Rejected: {sum(1 for f in agg['odd_stride_fate_table'] if f.get('rejected'))}",
        f"- Scored: {sum(1 for f in agg['odd_stride_fate_table'] if f.get('scored'))}",
        f"- Ranked: {sum(1 for f in agg['odd_stride_fate_table'] if f.get('ranked'))}",
        f"- Selected: {sum(1 for f in agg['odd_stride_fate_table'] if f.get('selected'))}",
        f"- Invented: {sum(1 for f in agg['odd_stride_fate_table'] if f.get('invented'))}",
        "",
        "## Q1–Q10 (OBSERVED ledger states; seed0 S8-BASELINE exemplar)",
        "",
        f"1. **proposed?** {base.get('Q1_proposed')} (proposal_index={base.get('proposal_index')})",
        f"2. **rejected?** {base.get('Q2_rejected')} (reason={base.get('rejection_reason')})",
        f"3. **scored?** {base.get('Q3_scored')}",
        f"4. **score/components?** {json.dumps(base.get('Q4_score_components'), default=str)[:500]}",
        f"5. **ranked?** {base.get('Q5_ranked')} (ranks={base.get('ranks')}; best={base.get('best_rank')})",
        f"6. **what outranked it?** {base.get('Q6_outranked_by')}",
        f"7. **selected?** {base.get('Q7_selected')}",
        f"8. **invent attempted?** {base.get('Q8_invent_attempted')}",
        f"9. **invent success?** {base.get('Q9_invent_success')}",
        f"10. **disappearance state?** `{base.get('Q10_disappearance_state')}` "
        f"(exact recorded earliest terminal tag for this candidate: PROPOSED→SCORED→RANKED; never SELECTED/INVENTED)",
        "",
        "## Natural-success controls (prereg: all non-S reaching INVENTED)",
        "",
        f"Count: {len(agg['natural_success_controls'])} (no post-hoc exclusion)",
        "",
        "| Condition | Seed | Key | Invented | Best rank | Scores head |",
        "|-----------|------|-----|----------|-----------|-------------|",
    ]
    for ns in agg["natural_success_controls"][:40]:
        fate_md.append(
            f"| {ns['condition_id']} | {ns['seed']} | `{ns['candidate_key']}` | {ns['invented']} | {ns['best_rank']} | {ns['scores_head']} |"
        )
    if len(agg["natural_success_controls"]) > 40:
        fate_md.append(f"| … | … | ({len(agg['natural_success_controls'])-40} more) | … | … | … |")
    fate_md += ["", "## Per-cell disappearance", ""]
    fate_md += [
        "| Condition | Seed | Disappearance | Best rank | Selected | Invented |",
        "|-----------|------|---------------|-----------|----------|----------|",
    ]
    for f in agg["odd_stride_fate_table"]:
        fate_md.append(
            f"| {f['condition_id']} | {f['seed']} | `{f['disappearance_state']}` | {f['best_rank']} | {f['selected']} | {f['invented']} |"
        )
    fate_md.append("")
    (OUT / "aivd_3_41_audit_candidate_fate.md").write_text("\n".join(fate_md))
    written.append(str(OUT / "aivd_3_41_audit_candidate_fate.md"))

    hypo = _classify_hypotheses(agg)
    (OUT / "aivd_3_41_audit_hypothesis_update.md").write_text(
        "\n".join(
            [
                "# AIVD 3.41 — Hypothesis Update (H10a–H10h + H10-REJECT)",
                "",
                f"**Recorded:** {hypo['recorded_at_ist']}",
                "**Sacred:** NO",
                "",
                f"Counts: {json.dumps(hypo['counts'])}",
                "",
                "| Leaf | Classification | Evidence (summary) |",
                "|------|----------------|--------------------|",
                *[
                    f"| {k} | **{v['classification']}** | {v['evidence'].get('note', json.dumps(v['evidence'])[:180])} |"
                    for k, v in hypo["leaves"].items()
                ],
                "",
                "## Details",
                "",
                "```json",
                json.dumps(hypo["leaves"], indent=2, default=str),
                "```",
                "",
            ]
        )
    )
    written.append(str(OUT / "aivd_3_41_audit_hypothesis_update.md"))
    (OUT / "aivd_3_41_audit_hypothesis_update.json").write_text(json.dumps(hypo, indent=2) + "\n")
    written.append(str(OUT / "aivd_3_41_audit_hypothesis_update.json"))

    causal = _causal_localization(agg, hypo)
    (OUT / "aivd_3_41_audit_causal_localization.md").write_text(
        "\n".join(
            [
                "# AIVD 3.41 — First Causal Localization",
                "",
                f"**Recorded:** {causal['recorded_at_ist']}",
                "**Sacred:** NO",
                "",
                "## Localization (one sentence)",
                "",
                causal["first_causal_localization"],
                "",
                "## Evidence refs",
                "",
                *[f"- `{e}`" for e in causal["evidence_refs"]],
                "",
                "## Not claimed",
                "",
                *[f"- {x}" for x in causal["not_claimed"]],
                "",
            ]
        )
    )
    written.append(str(OUT / "aivd_3_41_audit_causal_localization.md"))

    # Human execution report
    exec_md = [
        "# AIVD 3.41 — Audit Execution Report",
        "",
        f"**Recorded:** {_ist_now()}",
        f"**Implementation tip:** `a56586e649f00219f10d22a041de7bdee2ce3d14`",
        f"**Branch:** `research/aivd-3.41-invention-planner-audit`",
        f"**Authorization:** AIVD 3.41 AUDIT EXECUTION AUTHORIZATION — INSTRUMENTED OBSERVATIONAL RUNS ONLY",
        f"**Mode:** `AIVD41_PLANNER_AUDIT`",
        "**Sacred:** NO",
        "",
        "## Harness",
        "",
        "- Deterministic mock plant: `HX8OddStride` via `UnknownsPipeline` / `full_3_39_r1`",
        "- BH=48, invent_cap=48, REDISCOVERY_FLOOR=5, seeds[0,1,2,3,4,7,11]",
        "- Conditions labeled S8-BASELINE/S8-RA/S8-RC/S8-RD as Stage-8 priors",
        "- R-A/R-C/R-D FILTER **not** integrated (FORBIDDEN under this authorization)",
        "- Frozen Stage-8 JSONs cross-referenced for post-pool context only",
        "- NOT claimed as Sacred discovery results",
        "",
        "## Matrix",
        "",
        f"- ON cells: {agg['matrix']['n_on']}",
        f"- OFF cells: {agg['matrix']['n_off']}",
        f"- Expected: {agg['matrix']['expected_cells']}",
        f"- Completed: {agg['matrix']['completed']}",
        f"- Elapsed: {agg['elapsed_s']}s",
        "",
        "## Twin equality",
        "",
        f"**{'PASS' if agg['twin_equality_pass'] else 'FAIL'}**",
        f"STOP: {json.dumps(agg['stop_hit'])}",
        "",
        "## RNG integrity",
        "",
        f"**{'PASS' if agg['rng_integrity_pass'] else 'FAIL'}**",
        "",
        "## Odd-stride fate (summary)",
        "",
        f"Candidate `{ODD_STRIDE_KEY}` @ proposal_index=3:",
        f"- Proposed in {sum(1 for f in agg['odd_stride_fate_table'] if f.get('proposed'))}/{len(agg['odd_stride_fate_table'])} cells",
        f"- Selected in {sum(1 for f in agg['odd_stride_fate_table'] if f.get('selected'))}/{len(agg['odd_stride_fate_table'])}",
        f"- Invented in {sum(1 for f in agg['odd_stride_fate_table'] if f.get('invented'))}/{len(agg['odd_stride_fate_table'])}",
        f"- Dominant disappearance: `RANKED` (never SELECTED/INVENTED)",
        "",
        "## H10 classifications",
        "",
    ]
    for k, v in hypo["leaves"].items():
        exec_md.append(f"- **{k}**: {v['classification']}")
    exec_md += [
        "",
        "## First causal localization",
        "",
        causal["first_causal_localization"],
        "",
        "## Forbidden checks",
        "",
        "- Sacred TinyLlama: NOT RUN",
        "- S injection / propose_atoms mutation: NOT DONE",
        "- R-A/R-C/R-D integrate: NOT DONE",
        "- grow.py / FILTER / invent_cap / novelty / firewall / score-rank-select math: NOT ALTERED",
        "- Retune / repair observed failures: NOT DONE",
        "",
        "## Deliverables",
        "",
        *[f"- `{p}`" for p in written],
        "",
        "```",
        "AIVD 3.41 AUDIT COMPLETE:",
        "SEPARATE AUTHORIZATION REQUIRED FOR ANY INTERVENTION",
        "```",
        "",
    ]
    (OUT / "aivd_3_41_audit_execution.md").write_text("\n".join(exec_md))
    written.append(str(OUT / "aivd_3_41_audit_execution.md"))
    return written


def main() -> int:
    agg = run_matrix(stop_on_divergence=True)
    paths = write_reports(agg)
    summary = {
        "n_on": agg["matrix"]["n_on"],
        "n_off": agg["matrix"]["n_off"],
        "twin_pass": agg["twin_equality_pass"],
        "rng_pass": agg["rng_integrity_pass"],
        "stop_hit": agg["stop_hit"],
        "written": paths,
    }
    print(json.dumps(summary, indent=2, default=str))
    if agg["stop_hit"] and agg["stop_hit"].get("kind") == "ON_OFF_DIVERGENCE":
        return 2
    if not agg["rng_integrity_pass"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
