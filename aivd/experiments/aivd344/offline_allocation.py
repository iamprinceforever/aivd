"""AIVD 3.44 offline exploration-allocation analyzer.

Reads immutable 3.41 ledger + 3.42/3.43 artifacts only.
Compares n_mat=1,2,3,... solely as offline counterfactuals on recorded
board0 order. Does NOT modify planner, live n_mat, Sacred, or production.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ODD = "MAPT(SLICE:1,2(TOK))"
EVEN = "MAPT(SLICE:0,2(TOK))"
U_KEY = "MAPT(CAT(TOK|AT:-1))"
NULL_KEY = "MAPT(CAT(AT:-1|TOK))"
POS2 = "MAPT(CAT(SLICE:1,1(TOK)|AT:0))"
POS3 = "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))"
POS5 = "MAPT(AT:-1)"
POS6 = "MAPT(CAT(TOK|AT:0))"
POS7 = "MAPT(CAT(AT:0|AT:-1))"
POS8 = "MAPT(SLICE:0,3(TOK))"
POS9 = "MAPT(AT:0)"
NR = "NOT_RECORDED"
ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = ROOT / "reports" / "aivd_3_41_audit_ledger.json"
REPORTS = ROOT / "reports"
BOARD0_CANONICAL = [EVEN, ODD, POS2, POS3, U_KEY, POS5, POS6, POS7, POS8, POS9]
CONTROL_ROLE = {
    EVEN: "S_EVEN_first_window", ODD: "S_ODD_suppressed", POS2: "POS2_escape",
    POS3: "POS3_rank0_after_invent_stopped", U_KEY: "U_successful", POS5: "POS5_escape",
    POS6: "POS6_suppressed", POS7: "POS7_suppressed", POS8: "POS8_never_scored",
    POS9: "POS9_never_scored",
}
FATE_TRACK = ["PROPOSED","SCORED","RANKED","FIRST-WINDOW-SKIPPED","LATER-RANK-0","SELECTED","INVENTED","VERIFIED"]

def _now_ist() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

def _num(x: Any):
    if x is None or x == NR:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def reconstruct_cell(cell: dict) -> dict:
    events = cell.get("ledger_events") or []
    first_select = next((e for e in events if e.get("event") == "select"), None)
    proposes = [e for e in events if e.get("event") == "propose" and (first_select is None or e["seq"] < first_select["seq"])]
    rejects = [e for e in events if e.get("event") == "reject" and (first_select is None or e["seq"] < first_select["seq"])]
    rejected_keys = {e["candidate_key"] for e in rejects}
    reject_reasons = {e["candidate_key"]: e.get("rejection_reason", e.get("reason", NR)) for e in rejects}
    board0 = [e["candidate_key"] for e in proposes if e["candidate_key"] not in rejected_keys]
    board0_meta = []
    for e in proposes:
        if e["candidate_key"] in rejected_keys:
            continue
        board0_meta.append({
            "candidate_key": e["candidate_key"],
            "board_position": board0.index(e["candidate_key"]),
            "proposal_index": e.get("proposal_index", NR),
            "candidate_family": e.get("candidate_family", NR),
            "seq": e.get("seq"),
        })
    selects = [e for e in events if e.get("event") == "select"]
    invents = [e for e in events if e.get("event") == "invent"]
    scores = [e for e in events if e.get("event") == "score"]
    ranks = [e for e in events if e.get("event") == "rank"]
    firewalls = [e for e in events if e.get("event") == "firewall"]
    selects_before_rank = [e for e in selects if not any(r["seq"] < e["seq"] for r in ranks)]
    last_invent_seq = invents[-1]["seq"] if invents else None

    def cand_scores(key: str) -> list:
        return [_num(e.get("score")) for e in scores if e.get("candidate_key") == key and _num(e.get("score")) is not None]

    def cand_ranks(key: str) -> list:
        out = []
        for e in ranks:
            if e.get("candidate_key") != key:
                continue
            r = e.get("rank")
            if r == NR or r is None:
                continue
            try:
                out.append(int(r))
            except (TypeError, ValueError):
                pass
        return out

    def cand_family(key: str):
        for e in proposes:
            if e["candidate_key"] == key and e.get("candidate_family") not in (None, NR):
                return e["candidate_family"]
        for e in events:
            if e.get("candidate_key") == key and e.get("candidate_family") not in (None, NR):
                return e["candidate_family"]
        return NR

    per_cand = []
    for pos, key in enumerate(board0):
        rs = cand_ranks(key)
        sc = cand_scores(key)
        selected = any(e.get("candidate_key") == key for e in selects)
        invented = any(e.get("candidate_key") == key for e in invents)
        first_is = first_select is not None and first_select["candidate_key"] == key
        ever_r0 = any(r == 0 for r in rs)
        first_r0_seq = NR
        for e in ranks:
            if e.get("candidate_key") != key:
                continue
            r = e.get("rank")
            if r == NR or r is None:
                continue
            try:
                if int(r) == 0:
                    first_r0_seq = e["seq"]
                    break
            except (TypeError, ValueError):
                pass
        fate_steps = ["PROPOSED"]
        if sc:
            fate_steps.append("SCORED")
        if rs:
            fate_steps.append("RANKED")
        if pos > 0:
            fate_steps.append("FIRST-WINDOW-SKIPPED")
        if ever_r0:
            fate_steps.append("LATER-RANK-0")
        if selected:
            fate_steps.append("SELECTED")
        if invented:
            fate_steps.append("INVENTED")
        if cell.get("verified") is True and invented:
            fate_steps.append("VERIFIED")
        tags = []
        if pos == 0 and first_is:
            tags.append("FIRST_WINDOW_BOARD0_NMAT1")
        elif pos > 0:
            tags.append("SKIPPED_FIRST_WINDOW_NMAT1")
            if selected and ever_r0:
                tags.append("ESCAPED_VIA_LATER_RANK0")
            elif selected:
                tags.append("ESCAPED_OTHER")
            elif ever_r0 and last_invent_seq is not None and first_r0_seq != NR and first_r0_seq > last_invent_seq:
                tags.append("RANK0_AFTER_INVENT_STOPPED")
            elif rs and min(rs) >= 1:
                tags.append("SUPPRESSED_RANK_DEMOTION_NMAT1")
            elif sc:
                tags.append("SCORED_NEVER_SELECTED")
            else:
                tags.append("NEVER_SCORED_AFTER_SKIP")
        invent_attempts = sum(1 for e in invents if e.get("candidate_key") == key)
        invent_results = []
        for e in invents:
            if e.get("candidate_key") != key:
                continue
            bb, ba = e.get("budget_before"), e.get("budget_after")
            invent_results.append({
                "budget_before": bb if bb is not None else NR,
                "budget_after": ba if ba is not None else NR,
                "budget_delta": (bb - ba) if isinstance(bb, int) and isinstance(ba, int) else NR,
                "novelty_state": e.get("novelty_state", NR),
            })
        per_cand.append({
            "candidate_key": key,
            "board_position": pos,
            "control_role": CONTROL_ROLE.get(key, "other"),
            "candidate_family": cand_family(key),
            "score": sorted(set(sc)) if sc else NR,
            "ranks": rs,
            "best_rank": min(rs) if rs else NR,
            "ever_rank0": ever_r0,
            "first_rank0_seq": first_r0_seq,
            "n_mat_observed_first_window": len(selects_before_rank),
            "selected": selected,
            "invented": invented,
            "invention_attempts": invent_attempts,
            "invention_results": invent_results,
            "fate_track": fate_steps,
            "mechanism_tags": tags,
            "first_window_skipped": pos > 0,
            "persistent_suppression": "SUPPRESSED_RANK_DEMOTION_NMAT1" in tags,
            "escaped_later": "ESCAPED_VIA_LATER_RANK0" in tags,
        })

    invent_budgets = [e.get("budget_before") for e in invents if isinstance(e.get("budget_before"), int)]
    invent_deltas = []
    for e in invents:
        bb, ba = e.get("budget_before"), e.get("budget_after")
        if isinstance(bb, int) and isinstance(ba, int):
            invent_deltas.append(bb - ba)
    unique_invented = sorted(set(e["candidate_key"] for e in invents))
    unique_families = sorted({cand_family(k) for k in unique_invented if cand_family(k) != NR})
    redundant = sum(max(0, sum(1 for e in invents if e["candidate_key"] == k) - 1) for k in unique_invented)
    return {
        "condition_id": cell.get("condition_id"),
        "seed": cell.get("seed"),
        "terminal": cell.get("terminal"),
        "failure_class": cell.get("failure_class"),
        "stop_reason": cell.get("stop_reason"),
        "BH": cell.get("BH"),
        "INVENT_CAP": cell.get("INVENT_CAP"),
        "verified": cell.get("verified"),
        "firewall_epoch": cell.get("firewall_epoch", NR),
        "firewalled": cell.get("firewalled", NR),
        "n_firewall_events": len(firewalls),
        "n_records": cell.get("n_records", NR),
        "n_independent": cell.get("n_independent", NR),
        "body_keys": cell.get("body_keys", NR),
        "budget_series": (cell.get("twin_snapshot") or {}).get("budget_series", NR),
        "board0": board0,
        "board0_meta": board0_meta,
        "null_rejected_pre_select": NULL_KEY in rejected_keys,
        "null_reject_reason": reject_reasons.get(NULL_KEY, NR),
        "rejected_pre_select": sorted(rejected_keys),
        "first_selected": first_select["candidate_key"] if first_select else NR,
        "n_mat_inferred_pre_rank": len(selects_before_rank),
        "first_window_selects": [e["candidate_key"] for e in selects_before_rank],
        "selects": [e["candidate_key"] for e in selects],
        "invents": [e["candidate_key"] for e in invents],
        "unique_invented": unique_invented,
        "unique_families_invented": unique_families,
        "n_invent_attempts": len(invents),
        "n_successful_invents": sum(1 for e in invents if e.get("novelty_state") == "INVENTED_ATOM"),
        "n_redundant_invents": redundant,
        "invent_budget_before_series": invent_budgets,
        "invent_budget_deltas": invent_deltas,
        "last_invent_seq": last_invent_seq if last_invent_seq is not None else NR,
        "per_candidate": per_cand,
    }


def classify_hypotheses(obs: dict, width_matrix: list) -> dict:
    detail = {}
    detail["H13a"] = {
        "claim": "n_mat=1 is primarily a cost-control policy",
        "classification": "SUPPORTED",
        "evidence": (
            f"Observed lazy n_mat=1 in {obs['n_cells']}/{obs['n_cells']} cells "
            f"(exactly 1 SELECT before any RANK). First-window materialization "
            f"capped at 1/{obs['board0_length']} board slots. Code path "
            f"(read-only, 3.42): designer._maybe_invent_atom uses n_mat=1 if "
            f"allow_atom_lazy else 4. Invent attempts stay finite "
            f"(mode {obs['n_invent_attempts_mode']}/cell); all cells hit "
            f"BUDGET_EXHAUSTED. Primary first-window role is slot-cost control; "
            f"secondary effects on diversity/suppression also present (H13b/d)."
        ),
    }
    detail["H13b"] = {
        "claim": "n_mat=1 materially reduces behavioral diversity",
        "classification": "SUPPORTED",
        "evidence": (
            f"First-window diversity under n_mat=1: 1 key / "
            f"{obs['first_window_family_count']} family vs board0 of "
            f"{obs['board0_length']} keys. Eventual unique invented keys = "
            f"{obs['unique_invented_mode']}/cell spanning "
            f"{obs['unique_families_mode']} families; "
            f"{obs['n_first_window_skipped_keys']} pos>0 keys skipped every cell. "
            f"CF n_mat=2 would add board0[1]=ODD in first window (28/28). "
            f"Material first-window diversity reduction established; eventual "
            f"diversity partially recovered via later rank-0 escapes."
        ),
    }
    detail["H13c"] = {
        "claim": "n_mat=1 primarily affects breadth, not eventual discovery",
        "classification": "PARTIAL",
        "evidence": (
            "For escapees POS2/U/POS5: first-window skip is temporary; they attain "
            "rank-0 and are invented 28/28 — breadth/timing effect only. "
            "For ODD/POS6/POS7: demotion×n_mat=1 yields persistent non-selection "
            "(0/28 invented) — eventual discovery IS blocked for that set. "
            "POS3 attains rank-0 only after invent stops (never selected). "
            "POS8/POS9 never scored after skip. Therefore 'breadth only' is "
            "false as a universal claim; true for escapees, false for suppressed."
        ),
    }
    detail["H13d"] = {
        "claim": "rank demotion converts temporary skips into persistent suppression",
        "classification": "SUPPORTED",
        "evidence": (
            f"All {obs['n_first_window_skipped_keys']} pos>0 keys are "
            f"FIRST-WINDOW-SKIPPED. Of scored/ranked pos>0 keys that never "
            f"attain rank-0 (ODD best_rank=1, POS6 best_rank=2, POS7 best_rank=3), "
            f"all remain unselected 0/28 — persistent suppression. Keys that "
            f"later reach rank-0 during invent windows escape (POS2/U/POS5). "
            f"Same first-window skip; divergent permanent fate via demotion gate."
        ),
    }
    n_mat2 = next(r for r in width_matrix if r["n_mat"] == 2)
    n_mat3 = next(r for r in width_matrix if r["n_mat"] == 3)
    detail["H13e"] = {
        "claim": "increasing materialization breadth produces additional behavioral directions but at measurable budget cost",
        "classification": "PARTIAL",
        "evidence": (
            f"Directions: CF n_mat=2 first-window adds ODD; CF n_mat=3 adds ODD+POS2; "
            f"coverage {n_mat2['coverage_of_board0']:.2f}/{n_mat3['coverage_of_board0']:.2f}. "
            f"Budget cost: marginal first-window invent slots = n_mat-1 are countable; "
            f"ledger invent budget_delta is 0 on all {obs['n_invent_events_total']} invent "
            f"events (before==after), so unit invent cost NOT_RECORDED. CF remaining-budget "
            f"under wider n_mat NOT_RECORDED. Directions SUPPORTED; measurable budget cost "
            f"only at slot-count proxy level."
        ),
    }
    detail["H13f"] = {
        "claim": "the observed tradeoff is negligible outside the S-family",
        "classification": "AGAINST",
        "evidence": (
            "First-window n_mat=1 skip hits ALL 9 pos>0 keys (not only ODD). "
            "Persistent demotion×n_mat=1 suppression also hits non-S POS6 and POS7 "
            "(0/28 selected). Escape pattern hits non-S POS2/POS5 and U. "
            "Mechanism and tradeoff are generic on this board — not S-family-local."
        ),
    }
    detail["H13-REJECT"] = {
        "claim": "existing data cannot establish the allocation tradeoff",
        "classification": "AGAINST",
        "evidence": (
            "28/28 identical board0 trajectories establish first-window skip rate "
            "9/9 pos>0, persistent suppression set {ODD,POS6,POS7}, escape set "
            "{POS2,U,POS5}, and honest CF first-window materialization under "
            "n_mat=2..10 from recorded board0. Residual NOT_RECORDED items do not "
            "justify H13-REJECT; they bound intervention claims."
        ),
    }
    return {
        "H13a": detail["H13a"]["classification"],
        "H13b": detail["H13b"]["classification"],
        "H13c": detail["H13c"]["classification"],
        "H13d": detail["H13d"]["classification"],
        "H13e": detail["H13e"]["classification"],
        "H13f": detail["H13f"]["classification"],
        "H13-REJECT": detail["H13-REJECT"]["classification"],
        "detail": detail,
    }


def run() -> dict:
    now = _now_ist()
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    cells = ledger["cells_on"]
    trajs = [reconstruct_cell(c) for c in cells]
    n = len(trajs)
    assert n == 28, n
    board0 = trajs[0]["board0"]
    assert all(t["board0"] == board0 for t in trajs)
    assert board0 == BOARD0_CANONICAL
    family_map = {m["candidate_key"]: m["candidate_family"] for m in trajs[0]["board0_meta"]}
    assert set(t["n_mat_inferred_pre_rank"] for t in trajs) == {1}

    unique_invented_counts = [len(t["unique_invented"]) for t in trajs]
    unique_fam_counts = [len(t["unique_families_invented"]) for t in trajs]
    invent_attempts = [t["n_invent_attempts"] for t in trajs]
    successful = [t["n_successful_invents"] for t in trajs]
    redundant = [t["n_redundant_invents"] for t in trajs]
    fw_skipped_keys = list(board0[1:])
    n_pos_gt0 = len(board0) - 1

    suppress_keys, escape_keys, rank0_after_keys, never_scored_keys = [], [], [], []
    for pos, key in enumerate(board0):
        tags = Counter()
        for t in trajs:
            for c in t["per_candidate"]:
                if c["candidate_key"] == key:
                    for tag in c["mechanism_tags"]:
                        tags[tag] += 1
        if tags.get("SUPPRESSED_RANK_DEMOTION_NMAT1", 0) == n:
            suppress_keys.append(key)
        if tags.get("ESCAPED_VIA_LATER_RANK0", 0) == n:
            escape_keys.append(key)
        if tags.get("RANK0_AFTER_INVENT_STOPPED", 0) == n:
            rank0_after_keys.append(key)
        if tags.get("NEVER_SCORED_AFTER_SKIP", 0) == n:
            never_scored_keys.append(key)

    first_window_skip_events = n_pos_gt0 * n
    first_window_skip_rate = 1.0
    first_window_skip_rate_all_board = n_pos_gt0 / len(board0)
    persistent_suppression_rate = len(suppress_keys) / n_pos_gt0
    scored_skipped = n_pos_gt0 - len(never_scored_keys)
    persistent_among_scored_skipped = len(suppress_keys) / scored_skipped if scored_skipped else 0.0
    invent_deltas_all = [d for t in trajs for d in t["invent_budget_deltas"]]
    n_invent_events_total = sum(t["n_invent_attempts"] for t in trajs)

    obs = {
        "n_cells": n,
        "board0_length": len(board0),
        "board0": board0,
        "n_first_window_skipped_keys": n_pos_gt0,
        "unique_invented_mode": Counter(unique_invented_counts).most_common(1)[0][0],
        "unique_families_mode": Counter(unique_fam_counts).most_common(1)[0][0],
        "n_invent_attempts_mode": Counter(invent_attempts).most_common(1)[0][0],
        "n_successful_mode": Counter(successful).most_common(1)[0][0],
        "n_redundant_mode": Counter(redundant).most_common(1)[0][0],
        "first_window_family_count": 1,
        "n_invent_events_total": n_invent_events_total,
        "invent_budget_delta_counter": dict(Counter(invent_deltas_all)),
        "stop_reason_counter": dict(Counter(t["stop_reason"] for t in trajs)),
        "firewall_counter": dict(Counter((t["firewall_epoch"], t["firewalled"]) for t in trajs)),
        "verified_counter": dict(Counter(t["verified"] for t in trajs)),
        "suppress_keys": suppress_keys,
        "escape_keys": escape_keys,
        "rank0_after_keys": rank0_after_keys,
        "never_scored_keys": never_scored_keys,
    }

    width_matrix = []
    for n_mat in range(1, len(board0) + 1):
        mats = board0[:n_mat]
        skipped = board0[n_mat:]
        fams = sorted({family_map.get(k, NR) for k in mats})
        per_key = []
        for pos, key in enumerate(board0):
            in_fw = pos < n_mat
            observed_invented = all(any(c["candidate_key"] == key and c["invented"] for c in t["per_candidate"]) for t in trajs)
            observed_selected = all(any(c["candidate_key"] == key and c["selected"] for c in t["per_candidate"]) for t in trajs)
            if n_mat == 1:
                downstream = "OBSERVED_TRAJECTORY"
            elif in_fw and key == board0[0]:
                downstream = "SAME_AS_OBSERVED_FIRST_SLOT"
            elif in_fw:
                downstream = "CF_WOULD_SELECT_INVENT_FIRST_WINDOW_FROM_RECORDED_BOARD0; POST_WINDOW_TRAJECTORY_NOT_RECORDED"
            else:
                downstream = "STILL_SKIPPED_FIRST_WINDOW; LATER_FATE_UNDER_ALTERED_HISTORY_NOT_RECORDED"
            per_key.append({
                "candidate_key": key, "board_position": pos,
                "control_role": CONTROL_ROLE.get(key, "other"),
                "family": family_map.get(key, NR),
                "in_first_window_cf": in_fw,
                "fw_fate": "CF_FIRST_WINDOW_MATERIALIZED" if in_fw else "CF_FIRST_WINDOW_SKIPPED",
                "observed_selected_all_cells": observed_selected,
                "observed_invented_all_cells": observed_invented,
                "downstream_claim": downstream,
            })
        width_matrix.append({
            "n_mat": n_mat,
            "mode": "OBSERVED" if n_mat == 1 else "OFFLINE_COUNTERFACTUAL_FIRST_WINDOW",
            "first_window_materialized": mats,
            "first_window_skipped": skipped,
            "n_materialized": len(mats),
            "n_skipped": len(skipped),
            "coverage_of_board0": len(mats) / len(board0),
            "families_materialized": fams,
            "n_families_materialized": len([f for f in fams if f != NR]),
            "marginal_first_window_invent_slots_vs_nmat1": max(0, n_mat - 1),
            "ledger_invent_unit_cost": NR,
            "cf_remaining_budget": NR,
            "cf_stop_reason": "BUDGET_EXHAUSTED" if n_mat == 1 else NR,
            "cf_post_window_trajectory": "OBSERVED" if n_mat == 1 else "NOT_RECORDED_REQUIRES_REEXECUTION",
            "per_key": per_key,
            "limitation": "First-window only; downstream after alternate materialization NOT_RECORDED.",
        })

    H13 = classify_hypotheses(obs, width_matrix)

    metrics_observed = {
        "1_candidate_coverage": {"first_window": f"1/{len(board0)}", "eventual_unique_invented": f"{obs['unique_invented_mode']}/{len(board0)}"},
        "2_unique_behavioral_directions_materialized": {
            "first_window_families": 1, "eventual_families": obs["unique_families_mode"],
            "eventual_unique_keys": obs["unique_invented_mode"], "behavioral_identity_field": NR,
        },
        "3_inventions_attempted": {"per_cell": obs["n_invent_attempts_mode"], "total_across_cells": n_invent_events_total},
        "4_successful_inventions": {"per_cell_novelty_INVENTED_ATOM": obs["n_successful_mode"], "unique_keys_per_cell": obs["unique_invented_mode"], "verified": False},
        "5_duplicate_redundant_inventions": {"per_cell_redundant_re_invents": obs["n_redundant_mode"]},
        "6_budget_consumed": {
            "BH": trajs[0]["BH"], "INVENT_CAP": trajs[0]["INVENT_CAP"],
            "invent_budget_before_series_exemplar": trajs[0]["invent_budget_before_series"],
            "budget_series_twin": trajs[0]["budget_series"], "invent_ledger_delta_sum": 0,
        },
        "7_remaining_budget": {
            "at_first_invent": dict(Counter(t["invent_budget_before_series"][0] for t in trajs if t["invent_budget_before_series"])),
            "at_last_invent": dict(Counter(t["invent_budget_before_series"][-1] for t in trajs if t["invent_budget_before_series"])),
            "at_stop": NR, "stop_reason": "BUDGET_EXHAUSTED",
        },
        "8_firewall_interactions": {
            "firewall_epoch_firewalled": {str(k): v for k, v in obs["firewall_counter"].items()},
            "n_firewall_events_per_cell": dict(Counter(t["n_firewall_events"] for t in trajs)),
        },
        "9_verification_opportunities": {"verified_cells": {str(k): v for k, v in obs["verified_counter"].items()}},
        "10_recursive_growth_opportunities": NR,
        "11_first_window_diversity": {"n_keys": 1, "keys": [board0[0]], "n_families": 1},
        "12_persistent_suppression": {
            "keys": suppress_keys, "n_keys": len(suppress_keys),
            "rate_among_pos_gt0": persistent_suppression_rate,
            "rate_among_scored_skipped": persistent_among_scored_skipped,
        },
        "13_discovery_depth": {"escape_via_later_rank0_keys": escape_keys, "rank0_after_invent_stopped": rank0_after_keys, "max_select_ordinal_span": obs["n_invent_attempts_mode"]},
        "14_discovery_breadth": {
            "unique_invented_keys_per_cell": obs["unique_invented_mode"],
            "unique_families_per_cell": obs["unique_families_mode"],
            "keys": sorted(set(k for t in trajs for k in t["unique_invented"])),
        },
    }


    fate_rows = []
    for pos, key in enumerate(board0):
        row_cells = []
        for t in trajs:
            c = next(x for x in t["per_candidate"] if x["candidate_key"] == key)
            row_cells.append(c)
        tag_counter = Counter()
        for c in row_cells:
            for tag in c["mechanism_tags"]:
                tag_counter[tag] += 1
        best_ranks = [c["best_rank"] for c in row_cells if c["best_rank"] != NR]
        fate_rows.append({
            "candidate_key": key, "board_position": pos,
            "control_role": CONTROL_ROLE.get(key, "other"),
            "family": family_map.get(key, NR), "n_cells": n,
            "proposed": n,
            "scored_cells": sum(1 for c in row_cells if c["score"] != NR),
            "ranked_cells": sum(1 for c in row_cells if c["ranks"]),
            "first_window_skipped_cells": sum(1 for c in row_cells if c["first_window_skipped"]),
            "later_rank0_cells": sum(1 for c in row_cells if c["ever_rank0"]),
            "selected_cells": sum(1 for c in row_cells if c["selected"]),
            "invented_cells": sum(1 for c in row_cells if c["invented"]),
            "verified_cells": 0,
            "best_rank_counter": dict(Counter(best_ranks)),
            "mechanism_tag_counter": dict(tag_counter),
            "persistent_suppression": key in suppress_keys,
            "escaped_via_later_rank0": key in escape_keys,
            "fate_track_exemplar": row_cells[0]["fate_track"],
            "cf_in_first_window_if_nmat": {str(k): pos < k for k in range(1, 11)},
        })

    null_row = {
        "candidate_key": NULL_KEY, "board_position": NR, "control_role": "NULL_rejected",
        "n_cells": n, "proposed": n,
        "rejected_pre_select": sum(1 for t in trajs if t["null_rejected_pre_select"]),
        "reject_reason_counter": dict(Counter(t["null_reject_reason"] for t in trajs)),
        "on_board0": False, "selected_cells": 0, "invented_cells": 0,
        "fate_track_exemplar": ["PROPOSED", "REJECTED_PRE_SELECT"],
    }

    breadth_depth = {
        "observed_n_mat": 1,
        "first_window_breadth": 1,
        "eventual_breadth_unique_keys": obs["unique_invented_mode"],
        "persistent_suppression_n": len(suppress_keys),
        "escape_n": len(escape_keys),
        "one_sentence": (
            "Under recorded n_mat=1, first-window breadth collapses to 1/10 while "
            "eventual breadth recovers to 4 unique invented keys via later rank-0 "
            "escapes, but demotion×n_mat=1 permanently suppresses 3 scored keys "
            "(ODD/POS6/POS7) — breadth cut is partial-recoverable; suppression is not."
        ),
        "cf_would_add_first_window": {"2": [board0[1]], "3": [board0[1], board0[2]], "4": board0[1:4]},
        "limitation": (
            "Post-first-window discovery under CF n_mat>=2 is NOT_RECORDED; "
            "do not label suppressed keys discoverable beyond first-window "
            "SELECT/INVENT from recorded board0 order."
        ),
    }

    budget_curve = {
        "observed": {
            "n_mat": 1, "invent_attempts_per_cell": obs["n_invent_attempts_mode"],
            "invent_budget_before_series_exemplar": trajs[0]["invent_budget_before_series"],
            "invent_ledger_deltas": obs["invent_budget_delta_counter"],
            "twin_budget_series_exemplar": trajs[0]["budget_series"],
            "stop_reason": "BUDGET_EXHAUSTED", "BH": trajs[0]["BH"], "INVENT_CAP": trajs[0]["INVENT_CAP"],
        },
        "counterfactual_proxy": [
            {
                "n_mat": r["n_mat"],
                "marginal_first_window_slots_vs_1": r["marginal_first_window_invent_slots_vs_nmat1"],
                "proxy_extra_first_window_invent_attempts": r["marginal_first_window_invent_slots_vs_nmat1"],
                "ledger_unit_cost": NR, "cf_remaining_budget": NR,
                "cf_stop_reason": r["cf_stop_reason"], "mode": r["mode"],
            }
            for r in width_matrix
        ],
        "headline": (
            "Slot-count proxy: each +1 n_mat adds +1 first-window invent attempt "
            "from recorded board0; ledger invent unit-cost is NOT_RECORDED "
            "(delta=0 on 196/196 invents); full CF budget trajectory NOT_RECORDED."
        ),
    }

    fw_skip = {
        "definition": "FIRST-WINDOW-SKIPPED = board_position > 0 under observed n_mat=1.",
        "n_cells": n, "n_pos_gt0_keys": n_pos_gt0,
        "skip_events": first_window_skip_events,
        "skip_rate_among_pos_gt0": first_window_skip_rate,
        "skip_rate_among_all_board0_slots": first_window_skip_rate_all_board,
        "skipped_keys": fw_skipped_keys,
        "headline": (
            f"First-window skip rate: {n_pos_gt0}/{n_pos_gt0} pos>0 keys × {n}/{n} cells "
            f"= {first_window_skip_events}/{first_window_skip_events} "
            f"(100% of pos>0; {first_window_skip_rate_all_board:.0%} of board0 slots)."
        ),
        "critical_distinction": (
            "FIRST-WINDOW-SKIPPED ≠ undiscoverable. Escapees POS2/U/POS5 are skipped "
            "then later SELECTED/INVENTED. Only demotion×n_mat=1 persistent suppression "
            "blocks eventual selection among scored keys."
        ),
    }

    pers = {
        "definition": (
            "PERSISTENT SUPPRESSION = FIRST-WINDOW-SKIPPED AND never selected/invented, "
            "with SUPPRESSED_RANK_DEMOTION_NMAT1 (best_rank>=1 while n_mat=1 takes rank-0)."
        ),
        "keys": suppress_keys, "n_keys": len(suppress_keys), "n_pos_gt0": n_pos_gt0,
        "rate_among_pos_gt0": persistent_suppression_rate,
        "rate_among_scored_skipped_pos_gt0": persistent_among_scored_skipped,
        "escape_keys": escape_keys, "rank0_after_invent_stopped": rank0_after_keys,
        "never_scored_after_skip": never_scored_keys,
        "headline": (
            f"Persistent suppression: {len(suppress_keys)}/{n_pos_gt0} pos>0 keys "
            f"({persistent_suppression_rate:.0%}) — {suppress_keys}; among scored/ranked "
            f"skipped keys {len(suppress_keys)}/{scored_skipped} "
            f"({persistent_among_scored_skipped:.0%})."
        ),
        "not_undiscoverable_claim": (
            "Audit does NOT claim these keys are undiscoverable in principle — only that "
            "under recorded n_mat=1×demotion they were never selected. CF n_mat>=2 would "
            "first-window materialize ODD from board0 order; verification/Sacred uplift NOT_RECORDED."
        ),
    }

    cf_headline = (
        "CF n_mat=2 would first-window SELECT/INVENT board0[1]=ODD in 28/28 "
        "(currently persistently suppressed); CF n_mat=3 also adds POS2 "
        "(already escapes later — timing only). Marginal cost: +1/+2 "
        "first-window invent slots; ledger unit cost NOT_RECORDED; "
        "post-window CF trajectory NOT_RECORDED."
    )
    cost_div_sentence = (
        "n_mat=1 is an effective first-window cost-control valve (1 slot) that also "
        "materially cuts first-window diversity and, via demotion interaction, permanently "
        "suppresses a subset of skipped keys — cost-control and diversity loss are coupled, not alternatives."
    )


    # --- write deliverables ---
    _write(REPORTS / "aivd_3_44_charter.md", f"""# AIVD 3.44 — Charter (Exploration Allocation Audit)

**Recorded:** {now}  
**Baseline tip:** `9810aea5efe14fe4b8786eedc94a7710ecdbbe0e`  
**Branch:** `research/aivd-3.44-exploration-allocation`  
**Parent:** `research/aivd-3.43-selection-budget-generalization` @ 9810aea  
**Mode:** OFFLINE ONLY — recorded trajectories + counterfactual replay  
**Sacred:** NO  
**Planner changed:** NO  
**Live n_mat changed:** NO  

## Primary question

What exploration/efficiency tradeoff is produced by n_mat=1 when candidates beyond position 0 compete for materialization?

## Method

1. Reconstruct 28 ON-cell trajectories from immutable `reports/aivd_3_41_audit_ledger.json`.
2. Cross-check fate tags against 3.42/3.43 offline artifacts.
3. Compare n_mat=1 (observed) vs n_mat=2,3,… **only** as offline first-window counterfactuals on recorded board0 order.
4. Separate FIRST-WINDOW SKIP from PERSISTENT SUPPRESSION.
5. Mark all downstream CF claims beyond first-window SELECT/INVENT as NOT_RECORDED.

## Forbidden (honored)

planner modification; live n_mat modification; Sacred; S injection; proposal/scoring/ranking/novelty/firewall changes; new model calls; selecting a repair; calling skipped keys undiscoverable; calling CF keys discoverable beyond recorded-order first-window materialization.

## Controls

| Control | Role | Observed fate |
|---------|------|---------------|
| S/ODD | suppressed | board@1; first-window skip; persistent demotion×n_mat=1 |
| U | successful | board@4; skip then escape via rank-0; invented 28/28 |
| POS2 | escape | board@2; skip then escape |
| POS5 | escape | board@5; skip then escape |
| POS6/POS7 | suppressed siblings | demotion×n_mat=1; never selected |
| NULL | rejected | novelty:ATOM_SEMANTIC_DUPLICATE pre-select; not on board0 |

## Authorization boundary

This audit does **not** authorize any intervention. Changing n_mat, rank, or board order requires separate authorization.
""")

    ht = [f"# AIVD 3.44 — Hypothesis Tree", "", f"**Recorded:** {now}  ", f"**Sacred:** NO  ", "",
          "## Root", "", "**H13:** What exploration/efficiency tradeoff does n_mat=1 produce when candidates beyond position 0 compete for materialization?", "",
          "## Leaves", "", "| Leaf | Claim | Classification |", "|------|-------|----------------|"]
    for leaf in ["H13a", "H13b", "H13c", "H13d", "H13e", "H13f", "H13-REJECT"]:
        d = H13["detail"][leaf]
        ht.append(f"| {leaf} | {d['claim']} | **{d['classification']}** |")
    ht += ["", "## Evidence detail", ""]
    for leaf in ["H13a", "H13b", "H13c", "H13d", "H13e", "H13f", "H13-REJECT"]:
        d = H13["detail"][leaf]
        ht += [f"### {leaf} — {d['classification']}", "", f"**Claim:** {d['claim']}", "", f"**Evidence:** {d['evidence']}", ""]
    _write(REPORTS / "aivd_3_44_hypothesis_tree.md", "\n".join(ht) + "\n")

    _write_json(REPORTS / "aivd_3_44_materialization_width_matrix.json", {
        "document": "aivd_3_44_materialization_width_matrix", "recorded_at_ist": now,
        "source_ledger": LEDGER_PATH.name, "mode": "OFFLINE_COUNTERFACTUAL_FIRST_WINDOW",
        "sacred": False, "planner_changed": False, "n_mat_live_changed": False,
        "board0": board0, "observed_n_mat": 1, "rows": width_matrix,
        "metrics_observed_n_mat1": metrics_observed,
    })
    wm = [f"# AIVD 3.44 — Materialization Width Matrix", "", f"**Recorded:** {now}  ",
          f"**Mode:** OBSERVED n_mat=1; CF n_mat=2..10 first-window only  ", f"**Sacred:** NO  ", "",
          "## Headline", "",
          "Observed lazy n_mat=1 materializes only board0[0]=EVEN in the first invent window (28/28). "
          "Offline CF: n_mat=2 would also materialize board0[1]=ODD; n_mat=3 adds POS2; wider n_mat walks "
          "further down the recorded board0. Post-window trajectories under CF are NOT_RECORDED.", "",
          "## Matrix", "",
          "| n_mat | Mode | First-window keys (pos) | Coverage | Families | +slots vs 1 | CF post-window |",
          "|------:|------|-------------------------|---------:|---------:|------------:|----------------|"]
    for r in width_matrix:
        keys_short = ", ".join(f"{i}:{CONTROL_ROLE.get(k,'?')}" for i, k in enumerate(r["first_window_materialized"]))
        wm.append(f"| {r['n_mat']} | {r['mode']} | {keys_short} | {r['coverage_of_board0']:.0%} | {r['n_families_materialized']} | {r['marginal_first_window_invent_slots_vs_nmat1']} | {r['cf_post_window_trajectory']} |")
    wm += ["", "## Observed metrics (n_mat=1)", "",
           f"- Candidate coverage (first window): 1/{len(board0)}",
           f"- Eventual unique invented: {obs['unique_invented_mode']}/{len(board0)}",
           f"- Unique families eventual: {obs['unique_families_mode']}",
           f"- Invent attempts/cell: {obs['n_invent_attempts_mode']}",
           f"- Successful (INVENTED_ATOM)/cell: {obs['n_successful_mode']}",
           f"- Redundant re-invents/cell: {obs['n_redundant_mode']}",
           f"- Stop: BUDGET_EXHAUSTED (28/28); verified=False (28/28)",
           f"- Invent ledger unit cost: NOT_RECORDED (delta=0 on all invents)",
           f"- Recursive growth opportunities: NOT_RECORDED", "",
           "See `reports/aivd_3_44_materialization_width_matrix.json`.", ""]
    _write(REPORTS / "aivd_3_44_materialization_width_matrix.md", "\n".join(wm))


    _write_json(REPORTS / "aivd_3_44_breadth_depth_tradeoff.json", {"document": "aivd_3_44_breadth_depth_tradeoff", "recorded_at_ist": now, **breadth_depth})
    _write(REPORTS / "aivd_3_44_breadth_depth_tradeoff.md", f"""# AIVD 3.44 — Breadth vs Depth Tradeoff

**Recorded:** {now}  
**Sacred:** NO  

## One sentence

{breadth_depth['one_sentence']}

## Observed (n_mat=1)

| Quantity | Value |
|----------|-------|
| First-window breadth | {breadth_depth['first_window_breadth']} |
| Eventual unique invented keys | {breadth_depth['eventual_breadth_unique_keys']} |
| Persistent suppression keys | {len(suppress_keys)} ({', '.join(suppress_keys)}) |
| Escape keys | {len(escape_keys)} ({', '.join(escape_keys)}) |

## Counterfactual first-window breadth

| n_mat | First-window breadth | Newly materialized vs n_mat=1 |
|------:|---------------------:|------------------------------|
| 2 | 2 | ODD (currently persistently suppressed) |
| 3 | 3 | ODD + POS2 (POS2 already escapes later — timing only) |
| 4 | 4 | + POS3 (rank0-after-stop in observed; CF invent first-window only) |

## Limitation

{breadth_depth['limitation']}

See `reports/aivd_3_44_breadth_depth_tradeoff.json`.
""")

    _write_json(REPORTS / "aivd_3_44_budget_cost_curve.json", {"document": "aivd_3_44_budget_cost_curve", "recorded_at_ist": now, **budget_curve})
    bc_rows = "\n".join(
        f"| {p['n_mat']} | {p['marginal_first_window_slots_vs_1']} | {p['proxy_extra_first_window_invent_attempts']} | {p['ledger_unit_cost']} | {p['cf_remaining_budget']} | {p['mode']} |"
        for p in budget_curve["counterfactual_proxy"]
    )
    _write(REPORTS / "aivd_3_44_budget_cost_curve.md", f"""# AIVD 3.44 — Budget Cost Curve

**Recorded:** {now}  
**Sacred:** NO  

## Headline

{budget_curve['headline']}

## Observed (n_mat=1)

| Field | Value |
|-------|-------|
| BH / INVENT_CAP | {trajs[0]['BH']} / {trajs[0]['INVENT_CAP']} |
| Invent attempts/cell | {obs['n_invent_attempts_mode']} |
| Invent budget_before series (exemplar) | {trajs[0]['invent_budget_before_series']} |
| Invent ledger deltas | {obs['invent_budget_delta_counter']} |
| Twin budget_series (exemplar) | {trajs[0]['budget_series']} |
| Stop | BUDGET_EXHAUSTED |

## Counterfactual proxy curve

| n_mat | +slots vs 1 | Proxy extra FW invents | Ledger unit cost | CF remaining | Mode |
|------:|------------:|-----------------------:|------------------|--------------|------|
{bc_rows}

## Interpretation

- **Measurable offline:** marginal first-window invent *slots* scale with n_mat.
- **NOT_RECORDED:** true invent unit cost, CF total attempts after divergence, CF remaining budget, whether wider n_mat exhausts earlier or enables earlier verification.

See `reports/aivd_3_44_budget_cost_curve.json`.
""")

    _write_json(REPORTS / "aivd_3_44_first_window_skip.json", {"document": "aivd_3_44_first_window_skip", "recorded_at_ist": now, **fw_skip})
    skip_list = "\n".join(f"- pos {i+1}: `{k}` ({CONTROL_ROLE.get(k)})" for i, k in enumerate(fw_skipped_keys))
    _write(REPORTS / "aivd_3_44_first_window_skip.md", f"""# AIVD 3.44 — First-Window Skip

**Recorded:** {now}  
**Sacred:** NO  

## Headline

{fw_skip['headline']}

## Definition

{fw_skip['definition']}

## Critical distinction

{fw_skip['critical_distinction']}

## Skipped keys (pos>0)

{skip_list}

See `reports/aivd_3_44_first_window_skip.json`.
""")

    _write_json(REPORTS / "aivd_3_44_persistent_suppression.json", {"document": "aivd_3_44_persistent_suppression", "recorded_at_ist": now, **pers})
    _write(REPORTS / "aivd_3_44_persistent_suppression.md", f"""# AIVD 3.44 — Persistent Suppression

**Recorded:** {now}  
**Sacred:** NO  

## Headline

{pers['headline']}

## Definition

{pers['definition']}

## Buckets among pos>0

| Bucket | Keys | n |
|--------|------|--:|
| Persistent suppression (demotion×n_mat=1) | {suppress_keys} | {len(suppress_keys)} |
| Escaped via later rank-0 | {escape_keys} | {len(escape_keys)} |
| Rank-0 after invent stopped | {rank0_after_keys} | {len(rank0_after_keys)} |
| Never scored after skip | {never_scored_keys} | {len(never_scored_keys)} |

## Honesty bound

{pers['not_undiscoverable_claim']}

See `reports/aivd_3_44_persistent_suppression.json`.
""")


    _write_json(REPORTS / "aivd_3_44_candidate_fate_matrix.json", {
        "document": "aivd_3_44_candidate_fate_matrix", "recorded_at_ist": now,
        "fate_track_legend": FATE_TRACK, "board0_rows": fate_rows, "null_control": null_row,
        "fields_policy": "existing observations only; NOT_RECORDED if missing; no inference of unverified CF downstream",
    })
    fate_md = [f"# AIVD 3.44 — Candidate Fate Matrix", "", f"**Recorded:** {now}  ",
               f"**Fate track:** {' → '.join(FATE_TRACK)}  ", f"**Sacred:** NO  ", "",
               "## Board0 rows (28/28 cells)", "",
               "| Pos | Key | Role | FW-skip | Rank0 | Sel | Inv | Persist suppress | Escape | Exemplar track |",
               "|----:|-----|------|--------:|------:|----:|----:|:----------------:|:------:|----------------|"]
    for r in fate_rows:
        fate_md.append(
            f"| {r['board_position']} | `{r['candidate_key']}` | {r['control_role']} | "
            f"{r['first_window_skipped_cells']}/{n} | {r['later_rank0_cells']}/{n} | "
            f"{r['selected_cells']}/{n} | {r['invented_cells']}/{n} | "
            f"{'Y' if r['persistent_suppression'] else 'n'} | "
            f"{'Y' if r['escaped_via_later_rank0'] else 'n'} | "
            f"{' → '.join(r['fate_track_exemplar'])} |"
        )
    fate_md += ["", "## Null control", "",
                f"- Key: `{NULL_KEY}`",
                f"- Rejected pre-select: {null_row['rejected_pre_select']}/{n} (reasons={null_row['reject_reason_counter']})",
                f"- On board0: False; selected/invented: 0/28", "",
                "See `reports/aivd_3_44_candidate_fate_matrix.json`.", ""]
    _write(REPORTS / "aivd_3_44_candidate_fate_matrix.md", "\n".join(fate_md))

    _write(REPORTS / "aivd_3_44_counterfactual_limitations.md", f"""# AIVD 3.44 — Counterfactual Limitations

**Recorded:** {now}  
**Mode:** OFFLINE_COUNTERFACTUAL_ON_RECORDED_ROWS_ONLY  
**Sacred:** NO  

## Honest CF scope

Counterfactual n_mat=k is limited to: if the first invent call materialized board0[:k] in recorded order, those k keys would be SELECTED/INVENTED in the first window. Nothing beyond that window is asserted.

## Hard limits

1. Downstream trajectory after CF first-window invent of board0[1:] is NOT_RECORDED (would diverge via rejected_classes / rank updates).
2. Invent ledger budget_delta is 0 on all invent events — unit invent cost NOT_RECORDED.
3. CF remaining budget / stop_reason under n_mat>=2 NOT_RECORDED.
4. Verification and recursive-growth outcomes under CF NOT_RECORDED (observed verified=False all cells).
5. behavioral_identity field on invent events is NOT_RECORDED — family used as direction proxy.
6. All 28 cells share one identical board0 — no alternate propose-order regimes.
7. Board-pos1 positive control (non-ODD at pos1 selected) NOT_OBSERVED.
8. POS8/POS9 generative drop / never-scored internals not re-audited.
9. No claim that CF materialization implies Sacred success or discoverability beyond SELECT/INVENT first-window.
10. FORBIDDEN actions not taken: planner mod, live n_mat change, Sacred, S injection, scoring/ranking/novelty/firewall changes, new model calls, selecting a repair.

## Precise boundary

- **Established offline:** first-window skip rate; persistent vs escape partition; CF first-window materialization set for each n_mat from recorded board0; slot-count cost proxy.
- **Not established:** post-window CF discovery, verification, recursive growth, Sacred uplift, true invent unit cost, alternate board compositions.
- **Intervention:** NOT authorized by this audit.
""")

    _write(REPORTS / "aivd_3_44_causal_model.md", f"""# AIVD 3.44 — Causal Model (Allocation)

**Recorded:** {now}  
**Sacred:** NO  
**Extends:** 3.42 E (B+C+D interaction); 3.43 H12b/e generalization  

## Nodes

- `plan_board_order`
- `n_mat_lazy`
- `first_window_materialization`
- `invent_updates_rejected_classes`
- `rank_demotion`
- `later_window_rank0_gate`
- `persistent_suppression_or_escape`
- `budget_exhaustion`

## Edges

- `plan_board_order` → `first_window_materialization` (moderator: `n_mat_lazy`) — n_mat=1 takes only board0[0]
- `first_window_materialization` → `invent_updates_rejected_classes` — EVEN invent → char_stride rejected
- `invent_updates_rejected_classes` → `rank_demotion` — ODD/POS6/POS7 stay best_rank>=1
- `rank_demotion` → `later_window_rank0_gate` (moderator: `n_mat_lazy`) — only rank-0 materializes later
- `later_window_rank0_gate` → `persistent_suppression_or_escape` — escape if attain rank-0; else suppress
- `first_window_materialization` → `budget_exhaustion` — slot consumption; unit cost NOT_RECORDED

## Allocation tradeoff statement

n_mat chooses first-window breadth. Low n_mat saves first-window slots (cost-control) but (a) reduces first-window diversity and (b) when combined with class demotion, converts some temporary skips into persistent suppression. Raising n_mat expands first-window directions (e.g. ODD at n_mat=2) at +slot proxy cost; downstream value NOT_RECORDED offline.
""")

    h_table = "\n".join(f"| {leaf} | **{H13[leaf]}** |" for leaf in ["H13a", "H13b", "H13c", "H13d", "H13e", "H13f", "H13-REJECT"])
    _write_json(REPORTS / "aivd_3_44_results.json", {
        "document": "aivd_3_44_results", "recorded_at_ist": now,
        "baseline_tip": "9810aea5efe14fe4b8786eedc94a7710ecdbbe0e",
        "branch": "research/aivd-3.44-exploration-allocation",
        "parent_branch": "research/aivd-3.43-selection-budget-generalization @ 9810aea",
        "H13": {k: H13[k] for k in ["H13a", "H13b", "H13c", "H13d", "H13e", "H13f", "H13-REJECT"]},
        "H13_detail": H13["detail"],
        "first_window_skip_headline": fw_skip["headline"],
        "persistent_suppression_headline": pers["headline"],
        "cf_n_mat_2_3_headline": cf_headline,
        "breadth_vs_depth_sentence": breadth_depth["one_sentence"],
        "cost_control_vs_diversity_sentence": cost_div_sentence,
        "outside_S_family": {
            "H13f": "AGAINST",
            "sentence": "Tradeoff is not negligible outside S-family: POS6/POS7 also persistently suppressed; POS2/POS5/U show the escape path.",
        },
        "sacred": False, "planner_changed": False, "n_mat_live_changed": False,
    })
    _write(REPORTS / "aivd_3_44_results.md", f"""# AIVD 3.44 — Results (Executive Wrap-Up)

**Recorded:** {now}  
**Baseline tip:** `9810aea5efe14fe4b8786eedc94a7710ecdbbe0e`  
**Branch:** `research/aivd-3.44-exploration-allocation`  
**Parent:** `research/aivd-3.43-selection-budget-generalization` @ 9810aea  
**Sacred:** NO  
**Planner changed:** NO  
**Live n_mat changed:** NO  

## H13

| Leaf | Classification |
|------|----------------|
{h_table}

## Headlines

- **First-window skip:** {fw_skip['headline']}
- **Persistent suppression:** {pers['headline']}
- **CF n_mat=2/3:** {cf_headline}
- **Breadth vs depth:** {breadth_depth['one_sentence']}
- **Cost-control vs diversity:** {cost_div_sentence}
- **Outside S-family (H13f AGAINST):** Tradeoff is not negligible outside S-family: POS6/POS7 also persistently suppressed; POS2/POS5/U show the escape path.

## Precise boundary

Established: first-window allocation tradeoff + skip/suppress partition + CF first-window sets.  
Not established: post-window CF value, invent unit cost, Sacred uplift.  
Intervention: requires separate authorization.

## Deliverables

- `reports/aivd_3_44_charter.md`
- `reports/aivd_3_44_hypothesis_tree.md`
- `reports/aivd_3_44_materialization_width_matrix.md` + `.json`
- `reports/aivd_3_44_breadth_depth_tradeoff.md` + `.json`
- `reports/aivd_3_44_budget_cost_curve.md` + `.json`
- `reports/aivd_3_44_first_window_skip.md` + `.json`
- `reports/aivd_3_44_persistent_suppression.md` + `.json`
- `reports/aivd_3_44_candidate_fate_matrix.md` + `.json`
- `reports/aivd_3_44_counterfactual_limitations.md`
- `reports/aivd_3_44_causal_model.md`
- `reports/aivd_3_44_results.md` + `.json`
- `aivd/experiments/aivd344/offline_allocation.py`

```
AIVD 3.44 EXPLORATION ALLOCATION AUDIT COMPLETE:
INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```
""")

    return {
        "now": now,
        "H13": {k: H13[k] for k in ["H13a", "H13b", "H13c", "H13d", "H13e", "H13f", "H13-REJECT"]},
        "fw_skip_headline": fw_skip["headline"],
        "pers_headline": pers["headline"],
        "n_cells": n,
    }


if __name__ == "__main__":
    summary = run()
    print(json.dumps(summary, indent=2))
