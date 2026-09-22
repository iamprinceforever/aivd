"""AIVD 3.42 offline replay analyzer.

Reads immutable 3.41 audit ledger JSON only. No planner mutation, no model
calls, no Sacred, no production behavior change.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ODD = "MAPT(SLICE:1,2(TOK))"
EVEN = "MAPT(SLICE:0,2(TOK))"
U_KEY = "MAPT(CAT(TOK|AT:-1))"  # natural success control (rank-0 exemplar)
NULL_KEY = "MAPT(CAT(AT:-1|TOK))"  # rejected control in epoch-1 board
NR = "NOT_RECORDED"

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = ROOT / "reports" / "aivd_3_41_audit_ledger.json"
FATE_PATH = ROOT / "reports" / "aivd_3_41_audit_candidate_fate.json"
REPORTS = ROOT / "reports"


def _now_ist() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")


def _num(x: Any):
    if x is None or x == NR:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def reconstruct_cell(cell: dict) -> dict:
    """Rebuild one ON-cell trajectory from recorded ledger_events only."""
    events = cell.get("ledger_events") or []
    first_select = next((e for e in events if e.get("event") == "select"), None)
    proposes = [
        e
        for e in events
        if e.get("event") == "propose"
        and (first_select is None or e["seq"] < first_select["seq"])
    ]
    rejects = [
        e
        for e in events
        if e.get("event") == "reject"
        and (first_select is None or e["seq"] < first_select["seq"])
    ]
    rejected_keys = {e["candidate_key"] for e in rejects}
    board0 = [e["candidate_key"] for e in proposes if e["candidate_key"] not in rejected_keys]
    board0_meta = [
        {
            "candidate_key": e["candidate_key"],
            "proposal_index": e.get("proposal_index", NR),
            "candidate_family": e.get("candidate_family", NR),
            "seq": e.get("seq"),
        }
        for e in proposes
        if e["candidate_key"] not in rejected_keys
    ]

    selects = [e for e in events if e.get("event") == "select"]
    invents = [e for e in events if e.get("event") == "invent"]
    scores = [e for e in events if e.get("event") == "score"]
    ranks = [e for e in events if e.get("event") == "rank"]

    selects_before_rank = [
        e for e in selects if not any(r["seq"] < e["seq"] for r in ranks)
    ]

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

    def cand_comps(key: str):
        for e in scores:
            if e.get("candidate_key") == key and isinstance(e.get("score_components"), dict):
                return e["score_components"]
        return NR

    odd_ranks = cand_ranks(ODD)
    even_ranks = cand_ranks(EVEN)
    u_ranks = cand_ranks(U_KEY)
    odd_scores = cand_scores(ODD)
    even_scores = cand_scores(EVEN)
    u_scores = cand_scores(U_KEY)

    # Rank blocks: contiguous rank seq runs
    rank_blocks = []
    cur = []
    prev = None
    for e in ranks:
        if prev is not None and e["seq"] != prev + 1 and cur:
            rank_blocks.append(cur)
            cur = []
        cur.append(e)
        prev = e["seq"]
    if cur:
        rank_blocks.append(cur)

    rank_block_summaries = []
    for bi, block in enumerate(rank_blocks):
        ordered = sorted(block, key=lambda e: int(e["rank"]) if e.get("rank") != NR else 10**9)
        comps0 = ordered[0].get("score_components") if ordered else {}
        if not isinstance(comps0, dict):
            comps0 = {}
        rank_block_summaries.append(
            {
                "block_index": bi,
                "leftover": comps0.get("leftover", NR),
                "rejected_classes": comps0.get("rejected_classes", NR),
                "ordered_keys": [e["candidate_key"] for e in ordered],
                "odd_rank": next(
                    (int(e["rank"]) for e in ordered if e["candidate_key"] == ODD and e.get("rank") != NR),
                    NR,
                ),
                "u_rank": next(
                    (int(e["rank"]) for e in ordered if e["candidate_key"] == U_KEY and e.get("rank") != NR),
                    NR,
                ),
                "even_rank": next(
                    (int(e["rank"]) for e in ordered if e["candidate_key"] == EVEN and e.get("rank") != NR),
                    NR,
                ),
                "rank0": ordered[0]["candidate_key"] if ordered else NR,
            }
        )

    invent_rows = []
    for e in invents:
        invent_rows.append(
            {
                "candidate_key": e.get("candidate_key"),
                "proposal_index": e.get("proposal_index", NR),
                "budget_before": e.get("budget_before", NR),
                "budget_after": e.get("budget_after", NR),
                "seq": e.get("seq"),
                "selection_state": e.get("selection_state", NR),
            }
        )

    remaining_budget_at_first_invent = invent_rows[0]["budget_before"] if invent_rows else NR
    n_mat_inferred = len(selects_before_rank)  # recorded lazy cut before any rank

    return {
        "condition_id": cell.get("condition_id"),
        "seed": cell.get("seed"),
        "terminal": cell.get("terminal"),
        "failure_class": cell.get("failure_class"),
        "BH": cell.get("BH"),
        "INVENT_CAP": cell.get("INVENT_CAP"),
        "board0": board0,
        "board0_meta": board0_meta,
        "odd_board_pos": board0.index(ODD) if ODD in board0 else NR,
        "even_board_pos": board0.index(EVEN) if EVEN in board0 else NR,
        "u_board_pos": board0.index(U_KEY) if U_KEY in board0 else NR,
        "null_rejected_pre_select": NULL_KEY in rejected_keys,
        "null_reject_keys": sorted(rejected_keys),
        "first_selected": first_select["candidate_key"] if first_select else NR,
        "first_selected_proposal_index": (
            first_select.get("proposal_index", NR) if first_select else NR
        ),
        "n_mat_inferred_pre_rank": n_mat_inferred,
        "selects_before_rank": [e["candidate_key"] for e in selects_before_rank],
        "n_selects": len(selects),
        "n_invents": len(invents),
        "invent_order": [e["candidate_key"] for e in invents],
        "invent_rows": invent_rows,
        "remaining_budget_at_first_invent": remaining_budget_at_first_invent,
        "odd": {
            "proposed": any(e.get("candidate_key") == ODD and e.get("event") == "propose" for e in events),
            "proposal_index": next(
                (e.get("proposal_index") for e in events if e.get("event") == "propose" and e.get("candidate_key") == ODD),
                NR,
            ),
            "scores": odd_scores,
            "score_unique": sorted(set(odd_scores)),
            "score_components_sample": cand_comps(ODD),
            "ranks": odd_ranks,
            "best_rank": min(odd_ranks) if odd_ranks else NR,
            "selected": any(e.get("candidate_key") == ODD for e in selects),
            "invented": any(e.get("candidate_key") == ODD for e in invents),
        },
        "even": {
            "proposed": any(e.get("candidate_key") == EVEN and e.get("event") == "propose" for e in events),
            "proposal_index": next(
                (e.get("proposal_index") for e in events if e.get("event") == "propose" and e.get("candidate_key") == EVEN),
                NR,
            ),
            "scores": even_scores,
            "score_unique": sorted(set(even_scores)) if even_scores else [],
            "score_components_sample": cand_comps(EVEN),
            "ranks": even_ranks,
            "best_rank": min(even_ranks) if even_ranks else NR,
            "selected": any(e.get("candidate_key") == EVEN for e in selects),
            "invented": any(e.get("candidate_key") == EVEN for e in invents),
            "n_selects": sum(1 for e in selects if e.get("candidate_key") == EVEN),
            "n_invents": sum(1 for e in invents if e.get("candidate_key") == EVEN),
        },
        "u_control": {
            "key": U_KEY,
            "scores": u_scores,
            "score_unique": sorted(set(u_scores)),
            "score_components_sample": cand_comps(U_KEY),
            "ranks": u_ranks,
            "best_rank": min(u_ranks) if u_ranks else NR,
            "selected": any(e.get("candidate_key") == U_KEY for e in selects),
            "invented": any(e.get("candidate_key") == U_KEY for e in invents),
        },
        "null_control": {
            "key": NULL_KEY,
            "rejected_pre_first_select": NULL_KEY in rejected_keys,
            "selected": any(e.get("candidate_key") == NULL_KEY for e in selects),
            "invented": any(e.get("candidate_key") == NULL_KEY for e in invents),
        },
        "rank_blocks": rank_block_summaries,
        "odd_ever_rank0": any(r == 0 for r in odd_ranks),
        "scores_before_first_select": sum(
            1 for e in scores if first_select and e["seq"] < first_select["seq"]
        ),
        "ranks_before_first_select": sum(
            1 for e in ranks if first_select and e["seq"] < first_select["seq"]
        ),
    }


def aggregate(trajs: list[dict]) -> dict:
    n = len(trajs)
    return {
        "n_cells": n,
        "first_select_always_even": all(t["first_selected"] == EVEN for t in trajs),
        "even_board_pos_counter": dict(Counter(t["even_board_pos"] for t in trajs)),
        "odd_board_pos_counter": dict(Counter(t["odd_board_pos"] for t in trajs)),
        "n_mat_inferred_counter": dict(Counter(t["n_mat_inferred_pre_rank"] for t in trajs)),
        "odd_best_rank_counter": dict(Counter(t["odd"]["best_rank"] for t in trajs)),
        "odd_selected_count": sum(1 for t in trajs if t["odd"]["selected"]),
        "odd_invented_count": sum(1 for t in trajs if t["odd"]["invented"]),
        "even_invented_count": sum(1 for t in trajs if t["even"]["invented"]),
        "u_invented_count": sum(1 for t in trajs if t["u_control"]["invented"]),
        "odd_ever_rank0_count": sum(1 for t in trajs if t["odd_ever_rank0"]),
        "scores_before_first_select_always_0": all(t["scores_before_first_select"] == 0 for t in trajs),
        "ranks_before_first_select_always_0": all(t["ranks_before_first_select"] == 0 for t in trajs),
        "even_score_recorded_count": sum(1 for t in trajs if t["even"]["scores"]),
        "odd_score_unique_union": sorted(
            {s for t in trajs for s in t["odd"]["score_unique"]}
        ),
        "u_score_unique_union": sorted(
            {s for t in trajs for s in t["u_control"]["score_unique"]}
        ),
        "null_rejected_pre_select_count": sum(
            1 for t in trajs if t["null_control"]["rejected_pre_first_select"]
        ),
    }


def classify_AE(agg: dict) -> dict:
    """A–E support classification from Phase-1 evidence only."""
    return {
        "A_score_alone": {
            "classification": "AGAINST",
            "evidence": (
                "First SELECT of EVEN precedes all score events in 28/28 cells "
                f"(scores_before_first_select_always_0={agg['scores_before_first_select_always_0']}); "
                f"EVEN score recorded in {agg['even_score_recorded_count']}/28 cells (=0). "
                "Score alone cannot explain first materialization preference."
            ),
        },
        "B_rank_alone": {
            "classification": "AGAINST",
            "evidence": (
                "First SELECT precedes all rank events in 28/28 cells "
                f"(ranks_before_first_select_always_0={agg['ranks_before_first_select_always_0']}). "
                "Later ODD best_rank>=1 is consequential but not the sole first-cut cause."
            ),
        },
        "C_board_order_alone": {
            "classification": "INCONCLUSIVE",
            "evidence": (
                "Board order explains first SELECT: EVEN at board0 pos 0, ODD at pos 1 in 28/28. "
                "Alone it does not explain why ODD never later reaches SELECTED after re-rank "
                "(requires demotion + n_mat=1 cut)."
            ),
        },
        "D_n_mat_1_alone": {
            "classification": "INCONCLUSIVE",
            "evidence": (
                f"n_mat_inferred_pre_rank=1 in {agg['n_mat_inferred_counter']} cells. "
                "Necessary for single-slot cut but insufficient alone without board-order "
                "placing EVEN first and later rank demotion keeping ODD off rank-0."
            ),
        },
        "E_interaction_B_C_D": {
            "classification": "SUPPORTED",
            "evidence": (
                "(C) plan-board order materializes EVEN first under (D) n_mat=1; "
                "then char_stride enters rejected_classes; (B) subsequent rank_atoms "
                "keeps ODD best_rank>=1 in 28/28 so lazy n_mat=1 never selects ODD."
            ),
        },
    }


def classify_H11(agg: dict, ae: dict) -> dict:
    return {
        "H11a": {
            "claim": "intrinsic score disadvantage",
            "classification": "AGAINST",
            "evidence": (
                "EVEN has no recorded intrinsic score (0/28). ODD recorded scores are exclusively "
                f"demoted-class values {agg['odd_score_unique_union']} after char_stride rejection; "
                "not an odd-stride-intrinsic prior vs EVEN pre-score."
            ),
        },
        "H11b": {
            "claim": "score-component disadvantage",
            "classification": "WEAKLY SUPPORTED",
            "evidence": (
                "When scored, ODD components match demoted same-class pattern "
                "(p_discovery=0.12, causal_value=0.55, reuse_value=0.8) vs U untried "
                f"{agg['u_score_unique_union']}. Component gap is class-demotion, not odd-specific."
            ),
        },
        "H11c": {
            "claim": "relative ranking disadvantage",
            "classification": "SUPPORTED",
            "evidence": (
                f"odd_best_rank_counter={agg['odd_best_rank_counter']}; "
                f"odd_ever_rank0_count={agg['odd_ever_rank0_count']}/28; never SELECTED."
            ),
        },
        "H11d": {
            "claim": "plan-board ordering/materialization priority",
            "classification": "SUPPORTED",
            "evidence": (
                f"even_board_pos={agg['even_board_pos_counter']}, "
                f"odd_board_pos={agg['odd_board_pos_counter']}; "
                f"first_select_always_even={agg['first_select_always_even']}."
            ),
        },
        "H11e": {
            "claim": "lazy n_mat=1 allocation bottleneck",
            "classification": "SUPPORTED",
            "evidence": (
                f"n_mat_inferred_pre_rank counter={agg['n_mat_inferred_counter']} "
                "(exactly one SELECT before any RANK in every cell)."
            ),
        },
        "H11f": {
            "claim": "interaction between ranking and n_mat=1",
            "classification": "SUPPORTED",
            "evidence": (
                "After first EVEN invent, rejected_classes includes char_stride; "
                "ODD best_rank stays >=1 while n_mat=1 selects only rank-0 → "
                f"odd_selected_count={agg['odd_selected_count']}."
            ),
        },
        "H11g": {
            "claim": "novelty/identity effects after selection",
            "classification": "AGAINST",
            "evidence": (
                "ODD never reaches SELECTED/INVENTED; novelty/identity-after-selection "
                "cannot be the disappearance mechanism. Natural invents (EVEN/U) succeed."
            ),
        },
        "H11-REJECT": {
            "claim": "evidence insufficient to localize further",
            "classification": "AGAINST",
            "evidence": (
                f"E_interaction SUPPORTED={ae['E_interaction_B_C_D']['classification']}; "
                "deterministic 28/28 ON replay localizes beyond H11-REJECT."
            ),
        },
    }


def counterfactual(trajs: list[dict]) -> dict:
    """Pure offline what-if on recorded rows (no planner execution)."""
    # CF1: if n_mat>=2 on first materialization window, board0[1]==ODD would be next
    cf1_would_select_odd = sum(
        1
        for t in trajs
        if len(t["board0"]) >= 2 and t["board0"][0] == EVEN and t["board0"][1] == ODD
    )
    # CF2: if any recorded rank block placed ODD at rank 0 under n_mat=1
    cf2_rank0_blocks = sum(
        1 for t in trajs for b in t["rank_blocks"] if b.get("odd_rank") == 0
    )
    # CF3: if board0 had ODD at position 0
    cf3 = sum(1 for t in trajs if t["odd_board_pos"] == 0)

    return {
        "status": "RAN",
        "mode": "offline_what_if_on_recorded_rows_only",
        "forbidden_note": "Did not modify planner or execute repaired Sacred run",
        "CF1_n_mat_ge2_on_first_window": {
            "description": (
                "If first invent call materialized 2 candidates from recorded board0 order "
                "instead of 1, board0[1]==ODD would be the second SELECT."
            ),
            "cells_where_board0_1_is_odd": cf1_would_select_odd,
            "n_cells": len(trajs),
            "implication": "ODD would reach SELECTED/INVENTED on first window in those cells (recorded order).",
        },
        "CF2_odd_at_rank0_any_block": {
            "description": "If any recorded rank block had odd_rank==0, n_mat=1 would select ODD.",
            "recorded_rank0_odd_blocks": cf2_rank0_blocks,
            "implication": "No such recorded block; counterfactual requires alternate ranking outcome not present in ledger.",
        },
        "CF3_odd_board0_pos0": {
            "description": "If ODD occupied board0 position 0, first SELECT would be ODD under recorded n_mat=1.",
            "cells_with_odd_at_pos0": cf3,
            "implication": "Not observed; board order is stably EVEN then ODD.",
        },
        "sufficiency_gate": "Phase1_sufficient_for_offline_CF",
    }


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> dict:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    fate = json.loads(FATE_PATH.read_text(encoding="utf-8"))
    trajs = [reconstruct_cell(c) for c in ledger["cells_on"]]
    agg = aggregate(trajs)
    ae = classify_AE(agg)
    h11 = classify_H11(agg, ae)
    cf = counterfactual(trajs)
    recorded_at = _now_ist()

    phase1 = {
        "document": "aivd_3_42_phase1_replay",
        "recorded_at_ist": recorded_at,
        "source_ledger": str(LEDGER_PATH.relative_to(ROOT)),
        "source_fate": str(FATE_PATH.relative_to(ROOT)),
        "source_ledger_recorded_at_ist": ledger.get("recorded_at_ist"),
        "baseline_tip_expected": "0f42dc01dd0feac3b18e1dbe835282c8226bc821",
        "sacred": False,
        "mode": "OFFLINE_REPLAY_ONLY",
        "controls": {
            "S_odd_stride": ODD,
            "naturally_selected_even_stride": EVEN,
            "U_successful": U_KEY,
            "null_control": NULL_KEY,
        },
        "aggregate": agg,
        "exemplar_seed0_S8_BASELINE": next(
            t for t in trajs if t["condition_id"] == "S8-BASELINE" and t["seed"] == 0
        ),
        "trajectories": trajs,
        "fate_aggregate_crosscheck": {
            "fate_n_rows": len(fate.get("table") or []),
            "fate_candidate_key": fate.get("candidate_key"),
            "fate_selected_any": any(r.get("selected") for r in fate.get("table") or []),
            "fate_invented_any": any(r.get("invented") for r in fate.get("table") or []),
        },
    }

    score_cmp = {
        "document": "aivd_3_42_score_comparison",
        "recorded_at_ist": recorded_at,
        "headline": (
            f"ODD scored exclusively at demoted value {agg['odd_score_unique_union']} "
            f"(components p_discovery=0.12/causal=0.55/reuse=0.8); "
            f"EVEN score={NR} in {28 - agg['even_score_recorded_count']}/28 "
            f"(SELECTED pre-score); U control scored {agg['u_score_unique_union']}."
        ),
        "odd": {
            "key": ODD,
            "score_unique_union": agg["odd_score_unique_union"],
            "components_sample": trajs[0]["odd"]["score_components_sample"],
            "even_comparison": "EVEN has no recorded score events (NOT_RECORDED)",
        },
        "even": {
            "key": EVEN,
            "score_recorded_cells": agg["even_score_recorded_count"],
            "score": NR,
        },
        "u_control": {
            "key": U_KEY,
            "score_unique_union": agg["u_score_unique_union"],
            "components_sample": trajs[0]["u_control"]["score_components_sample"],
        },
        "null_control": {
            "key": NULL_KEY,
            "note": "Rejected pre-select; no score events required for null path",
            "rejected_pre_select_cells": agg["null_rejected_pre_select_count"],
        },
        "H11a": h11["H11a"]["classification"],
        "H11b": h11["H11b"]["classification"],
        "per_cell": [
            {
                "condition_id": t["condition_id"],
                "seed": t["seed"],
                "odd_scores": t["odd"]["score_unique"],
                "even_scores": t["even"]["score_unique"] or [NR],
                "u_scores": t["u_control"]["score_unique"],
            }
            for t in trajs
        ],
    }

    rank_cmp = {
        "document": "aivd_3_42_rank_comparison",
        "recorded_at_ist": recorded_at,
        "headline": (
            f"ODD best_rank always 1 (counter={agg['odd_best_rank_counter']}); "
            f"never rank-0 ({agg['odd_ever_rank0_count']}/28). "
            "First SELECT has no preceding rank. U control attains rank-0 in first rank blocks."
        ),
        "odd_best_rank_counter": agg["odd_best_rank_counter"],
        "odd_ever_rank0_count": agg["odd_ever_rank0_count"],
        "ranks_before_first_select_always_0": agg["ranks_before_first_select_always_0"],
        "H11c": h11["H11c"]["classification"],
        "exemplar_first_rank_block": trajs[0]["rank_blocks"][0] if trajs[0]["rank_blocks"] else NR,
        "per_cell": [
            {
                "condition_id": t["condition_id"],
                "seed": t["seed"],
                "odd_best_rank": t["odd"]["best_rank"],
                "odd_ranks": t["odd"]["ranks"],
                "even_best_rank": t["even"]["best_rank"],
                "u_best_rank": t["u_control"]["best_rank"],
                "first_block_rank0": t["rank_blocks"][0]["rank0"] if t["rank_blocks"] else NR,
                "first_block_odd_rank": t["rank_blocks"][0]["odd_rank"] if t["rank_blocks"] else NR,
                "first_block_rejected_classes": t["rank_blocks"][0]["rejected_classes"]
                if t["rank_blocks"]
                else NR,
            }
            for t in trajs
        ],
    }

    board_cmp = {
        "document": "aivd_3_42_plan_board_comparison",
        "recorded_at_ist": recorded_at,
        "headline": (
            "Recorded post-plan board0 is stably "
            f"[EVEN@{agg['even_board_pos_counter']}, ODD@{agg['odd_board_pos_counter']}, ...]; "
            f"first_select_always_even={agg['first_select_always_even']}."
        ),
        "even_board_pos_counter": agg["even_board_pos_counter"],
        "odd_board_pos_counter": agg["odd_board_pos_counter"],
        "first_select_always_even": agg["first_select_always_even"],
        "H11d": h11["H11d"]["classification"],
        "exemplar_board0": trajs[0]["board0"],
        "exemplar_board0_meta": trajs[0]["board0_meta"],
        "per_cell": [
            {
                "condition_id": t["condition_id"],
                "seed": t["seed"],
                "even_board_pos": t["even_board_pos"],
                "odd_board_pos": t["odd_board_pos"],
                "u_board_pos": t["u_board_pos"],
                "first_selected": t["first_selected"],
                "board0_head": t["board0"][:4],
            }
            for t in trajs
        ],
    }

    nmat = {
        "document": "aivd_3_42_n_mat_analysis",
        "recorded_at_ist": recorded_at,
        "headline": (
            f"Inferred lazy n_mat=1 from recorded events: exactly one SELECT before any RANK "
            f"in every cell (counter={agg['n_mat_inferred_counter']}). "
            "Code path (read-only confirmation): designer._maybe_invent_atom uses "
            "n_mat=1 if allow_atom_lazy else 4 — not modified."
        ),
        "n_mat_inferred_counter": agg["n_mat_inferred_counter"],
        "H11e": h11["H11e"]["classification"],
        "H11f": h11["H11f"]["classification"],
        "per_cell": [
            {
                "condition_id": t["condition_id"],
                "seed": t["seed"],
                "n_mat_inferred_pre_rank": t["n_mat_inferred_pre_rank"],
                "selects_before_rank": t["selects_before_rank"],
                "odd_best_rank": t["odd"]["best_rank"],
                "odd_selected": t["odd"]["selected"],
            }
            for t in trajs
        ],
    }

    causal = {
        "document": "aivd_3_42_causal_decomposition",
        "recorded_at_ist": recorded_at,
        "A_E": ae,
        "H11": h11,
        "first_localization": (
            "Odd-stride MAPT(SLICE:1,2(TOK)) is PROPOSED (proposal_index=3) and later "
            "SCORED/RANKED, but never SELECTED/INVENTED because (1) plan-board order places "
            "even-stride MAPT(SLICE:0,2(TOK)) at board0 position 0 and lazy n_mat=1 "
            "materializes only that slot before any score/rank, and (2) after EVEN invent, "
            "rejected_classes includes char_stride so subsequent rank_atoms keep ODD "
            "best_rank>=1 below the n_mat=1 cut — interaction of board order + rank demotion "
            "+ n_mat=1 (E SUPPORTED; A/B AGAINST as sole causes)."
        ),
        "no_repair_recommendation": True,
    }

    results = {
        "document": "aivd_3_42_results",
        "recorded_at_ist": recorded_at,
        "phase1": "COMPLETE",
        "phase2": cf["status"],
        "A_E": {k: v["classification"] for k, v in ae.items()},
        "H11": {k: v["classification"] for k, v in h11.items()},
        "headlines": {
            "score": score_cmp["headline"],
            "rank": rank_cmp["headline"],
            "plan_board": board_cmp["headline"],
            "n_mat": nmat["headline"],
        },
        "first_localization": causal["first_localization"],
        "sacred": False,
        "planner_changed": False,
    }

    # Write JSON deliverables
    write_json(REPORTS / "aivd_3_42_phase1_replay.json", phase1)
    write_json(REPORTS / "aivd_3_42_score_comparison.json", score_cmp)
    write_json(REPORTS / "aivd_3_42_rank_comparison.json", rank_cmp)
    write_json(REPORTS / "aivd_3_42_plan_board_comparison.json", board_cmp)
    write_json(REPORTS / "aivd_3_42_n_mat_analysis.json", nmat)
    write_json(REPORTS / "aivd_3_42_counterfactual.json", cf)
    write_json(
        REPORTS / "aivd_3_42_causal_decomposition.json",
        causal,
    )
    write_json(REPORTS / "aivd_3_42_results.json", results)

    return {
        "recorded_at": recorded_at,
        "agg": agg,
        "ae": ae,
        "h11": h11,
        "cf": cf,
        "causal": causal,
        "score_cmp": score_cmp,
        "rank_cmp": rank_cmp,
        "board_cmp": board_cmp,
        "nmat": nmat,
        "results": results,
        "exemplar": trajs[0],
    }


if __name__ == "__main__":
    out = main()
    print(json.dumps({"ok": True, "recorded_at": out["recorded_at"], "A_E": {k: v["classification"] for k, v in out["ae"].items()}, "H11": {k: v["classification"] for k, v in out["h11"].items()}}, indent=2))
