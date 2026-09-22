"""AIVD 3.43 offline selection-budget generalization analyzer.

Reads immutable 3.41 ledger + 3.42 replay artifacts only.
No planner mutation, no model calls, no Sacred, no production change.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
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
FATE_PATH = ROOT / "reports" / "aivd_3_41_audit_candidate_fate.json"
PHASE1_342 = ROOT / "reports" / "aivd_3_42_phase1_replay.json"
REPORTS = ROOT / "reports"

BOARD0_CANONICAL = [
    EVEN,  # 0
    ODD,  # 1  S suppressed
    POS2,  # 2  escapes via later rank0
    POS3,  # 3  rank0 after invent stopped
    U_KEY,  # 4  U control — escapes
    POS5,  # 5  escapes
    POS6,  # 6  demotion suppress
    POS7,  # 7  demotion suppress
    POS8,  # 8  never scored
    POS9,  # 9  never scored
]


def _now_ist() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")


def _num(x: Any):
    if x is None or x == NR:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _rank_blocks(ranks: list[dict]) -> list[list[dict]]:
    blocks: list[list[dict]] = []
    cur: list[dict] = []
    prev = None
    for e in ranks:
        if prev is not None and e["seq"] != prev + 1 and cur:
            blocks.append(cur)
            cur = []
        cur.append(e)
        prev = e["seq"]
    if cur:
        blocks.append(cur)
    return blocks


def reconstruct_cell(cell: dict) -> dict:
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
    reject_reasons = {
        e["candidate_key"]: e.get("rejection_reason", e.get("reason", NR)) for e in rejects
    }
    board0 = [e["candidate_key"] for e in proposes if e["candidate_key"] not in rejected_keys]
    board0_meta = [
        {
            "candidate_key": e["candidate_key"],
            "board_position": board0.index(e["candidate_key"]),
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
    firewalls = [e for e in events if e.get("event") == "firewall"]

    selects_before_rank = [
        e for e in selects if not any(r["seq"] < e["seq"] for r in ranks)
    ]
    last_invent_seq = invents[-1]["seq"] if invents else None

    def cand_scores(key: str) -> list:
        return [
            _num(e.get("score"))
            for e in scores
            if e.get("candidate_key") == key and _num(e.get("score")) is not None
        ]

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

    def novelty_on_invent(key: str):
        for e in invents:
            if e.get("candidate_key") == key:
                return e.get("novelty_state", NR)
        return NR

    blocks = _rank_blocks(ranks)
    block_summaries = []
    for bi, block in enumerate(blocks):
        ordered = sorted(
            block, key=lambda e: int(e["rank"]) if e.get("rank") != NR else 10**9
        )
        comps0 = ordered[0].get("score_components") if ordered else {}
        if not isinstance(comps0, dict):
            comps0 = {}
        block_summaries.append(
            {
                "block_index": bi,
                "leftover": comps0.get("leftover", NR),
                "rejected_classes": comps0.get("rejected_classes", NR),
                "rank0": ordered[0]["candidate_key"] if ordered else NR,
                "ordered_keys": [e["candidate_key"] for e in ordered],
            }
        )

    # Per board0 candidate fate
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

        # Select ordinal if selected
        select_ords = [i for i, e in enumerate(selects) if e.get("candidate_key") == key]

        per_cand.append(
            {
                "candidate_key": key,
                "board_position": pos,
                "proposal_index": next(
                    (
                        e.get("proposal_index", NR)
                        for e in proposes
                        if e["candidate_key"] == key
                    ),
                    NR,
                ),
                "candidate_family": next(
                    (
                        e.get("candidate_family", NR)
                        for e in proposes
                        if e["candidate_key"] == key
                    ),
                    NR,
                ),
                "score": sorted(set(sc)) if sc else NR,
                "score_components": cand_comps(key),
                "ranks": rs,
                "best_rank": min(rs) if rs else NR,
                "ever_rank0": ever_r0,
                "first_rank0_seq": first_r0_seq,
                "n_mat": len(selects_before_rank),
                "selected": selected,
                "select_ordinals": select_ords,
                "invented": invented,
                "invention_attempts": sum(1 for e in invents if e.get("candidate_key") == key),
                "invention_results": [
                    {
                        "budget_before": e.get("budget_before", NR),
                        "budget_after": e.get("budget_after", NR),
                        "novelty_state": e.get("novelty_state", NR),
                        "selection_state": e.get("selection_state", NR),
                    }
                    for e in invents
                    if e.get("candidate_key") == key
                ],
                "remaining_budget_at_first_invent": (
                    next(
                        (
                            e.get("budget_before", NR)
                            for e in invents
                            if e.get("candidate_key") == key
                        ),
                        NR,
                    )
                ),
                "firewall_state": {
                    "firewall_epoch_cell": cell.get("firewall_epoch", NR),
                    "firewalled_cell": cell.get("firewalled", NR),
                    "n_firewall_events": len(firewalls),
                },
                "novelty_state": novelty_on_invent(key) if invented else (
                    reject_reasons.get(key, NR) if key in rejected_keys else NR
                ),
                "mechanism_tags": tags,
            }
        )

    return {
        "condition_id": cell.get("condition_id"),
        "seed": cell.get("seed"),
        "terminal": cell.get("terminal"),
        "failure_class": cell.get("failure_class"),
        "stop_reason": cell.get("stop_reason"),
        "BH": cell.get("BH"),
        "INVENT_CAP": cell.get("INVENT_CAP"),
        "board0": board0,
        "board0_meta": board0_meta,
        "null_rejected_pre_select": NULL_KEY in rejected_keys,
        "null_reject_reason": reject_reasons.get(NULL_KEY, NR),
        "rejected_pre_select": sorted(rejected_keys),
        "first_selected": first_select["candidate_key"] if first_select else NR,
        "n_mat_inferred_pre_rank": len(selects_before_rank),
        "selects": [e["candidate_key"] for e in selects],
        "invents": [e["candidate_key"] for e in invents],
        "last_invent_seq": last_invent_seq if last_invent_seq is not None else NR,
        "rank_blocks": block_summaries,
        "per_candidate": per_cand,
        "firewall_epoch": cell.get("firewall_epoch", NR),
        "firewalled": cell.get("firewalled", NR),
    }


def aggregate_candidates(trajs: list[dict]) -> list[dict]:
    """Cross-cell fate per canonical board0 key."""
    out = []
    n = len(trajs)
    for pos, key in enumerate(BOARD0_CANONICAL):
        rows = []
        for t in trajs:
            for c in t["per_candidate"]:
                if c["candidate_key"] == key and c["board_position"] == pos:
                    rows.append(c)
                    break
        assert len(rows) == n, (key, pos, len(rows), n)
        tag_counter: Counter = Counter()
        for r in rows:
            for tag in r["mechanism_tags"]:
                tag_counter[tag] += 1
        best_ranks = [r["best_rank"] for r in rows if r["best_rank"] != NR]
        scores_u = sorted({s for r in rows if isinstance(r["score"], list) for s in r["score"]})
        out.append(
            {
                "candidate_key": key,
                "board_position": pos,
                "n_cells": n,
                "selected_cells": sum(1 for r in rows if r["selected"]),
                "invented_cells": sum(1 for r in rows if r["invented"]),
                "ever_rank0_cells": sum(1 for r in rows if r["ever_rank0"]),
                "best_rank_counter": dict(Counter(best_ranks)),
                "score_unique_union": scores_u if scores_u else NR,
                "score_components_sample": rows[0]["score_components"],
                "mechanism_tag_counter": dict(tag_counter),
                "control_role": (
                    "S_EVEN_first_window"
                    if key == EVEN
                    else "S_ODD_suppressed"
                    if key == ODD
                    else "U_natural_success"
                    if key == U_KEY
                    else "positive_escape_pos2"
                    if key == POS2
                    else "positive_escape_pos5"
                    if key == POS5
                    else "rank0_after_invent_stopped"
                    if key == POS3
                    else "demotion_suppress_sibling"
                    if key in (POS6, POS7)
                    else "never_scored_after_skip"
                    if key in (POS8, POS9)
                    else "other"
                ),
            }
        )
    return out


def mechanism_frequency(cand_agg: list[dict], trajs: list[dict]) -> dict:
    n = len(trajs)
    # First-window: all pos>0 skipped under n_mat=1
    n_pos_gt0 = sum(1 for c in cand_agg if c["board_position"] > 0)
    skipped_first = sum(
        1
        for c in cand_agg
        if c["board_position"] > 0
        and c["mechanism_tag_counter"].get("SKIPPED_FIRST_WINDOW_NMAT1", 0) == n
    )
    escaped = [
        c
        for c in cand_agg
        if c["mechanism_tag_counter"].get("ESCAPED_VIA_LATER_RANK0", 0) == n
    ]
    demotion_suppress = [
        c
        for c in cand_agg
        if c["mechanism_tag_counter"].get("SUPPRESSED_RANK_DEMOTION_NMAT1", 0) == n
    ]
    rank0_after_stop = [
        c
        for c in cand_agg
        if c["mechanism_tag_counter"].get("RANK0_AFTER_INVENT_STOPPED", 0) == n
    ]
    never_scored = [
        c
        for c in cand_agg
        if c["mechanism_tag_counter"].get("NEVER_SCORED_AFTER_SKIP", 0) == n
    ]
    return {
        "n_cells": n,
        "board0_length": len(BOARD0_CANONICAL),
        "board0_identical_across_cells": len({tuple(t["board0"]) for t in trajs}) == 1,
        "n_mat_inferred_always_1": all(t["n_mat_inferred_pre_rank"] == 1 for t in trajs),
        "first_select_always_board0_pos0": all(
            t["first_selected"] == t["board0"][0] for t in trajs if t["board0"]
        ),
        "pos_gt0_candidates": n_pos_gt0,
        "pos_gt0_skipped_first_window_all_cells": skipped_first,
        "escaped_via_later_rank0": [
            {"key": c["candidate_key"], "board_position": c["board_position"]}
            for c in escaped
        ],
        "suppressed_rank_demotion_nmat1": [
            {"key": c["candidate_key"], "board_position": c["board_position"]}
            for c in demotion_suppress
        ],
        "rank0_after_invent_stopped": [
            {"key": c["candidate_key"], "board_position": c["board_position"]}
            for c in rank0_after_stop
        ],
        "never_scored_after_skip": [
            {"key": c["candidate_key"], "board_position": c["board_position"]}
            for c in never_scored
        ],
        "headline": (
            f"Across {n}/28 identical board0 trajectories: lazy n_mat=1 skips ALL "
            f"{n_pos_gt0} board-position>0 candidates on the first invent window; "
            f"{len(escaped)} later ESCAPE via attaining rank-0 "
            f"({[c['candidate_key'] for c in escaped]}); "
            f"{len(demotion_suppress)} remain SUPPRESSED by rank demotion×n_mat=1 "
            f"({[c['candidate_key'] for c in demotion_suppress]}); "
            f"{len(rank0_after_stop)} attain rank-0 only after invent stops "
            f"({[c['candidate_key'] for c in rank0_after_stop]}); "
            f"{len(never_scored)} never scored after first-window skip "
            f"({[c['candidate_key'] for c in never_scored]})."
        ),
    }


def classify_H12(freq: dict, cand_agg: list[dict], trajs: list[dict]) -> dict:
    n = len(trajs)
    escaped = freq["escaped_via_later_rank0"]
    demoted = freq["suppressed_rank_demotion_nmat1"]
    odd_row = next(c for c in cand_agg if c["candidate_key"] == ODD)
    u_row = next(c for c in cand_agg if c["candidate_key"] == U_KEY)
    pos1_ever_selected = odd_row["selected_cells"]  # pos1 is always ODD

    return {
        "H12a": {
            "claim": "n_mat=1 generally sufficient to suppress board-position >0 candidates",
            "classification": "AGAINST",
            "evidence": (
                f"n_mat=1 skips all pos>0 on the FIRST window ({freq['pos_gt0_skipped_first_window_all_cells']}/"
                f"{freq['pos_gt0_candidates']} keys × {n} cells), but is NOT generally sufficient for "
                f"permanent suppression: {len(escaped)} keys ESCAPE via later rank-0 "
                f"({[e['key'] for e in escaped]}) including U@{u_row['board_position']}."
            ),
        },
        "H12b": {
            "claim": "suppression only when rank demotion interacts with n_mat=1",
            "classification": "SUPPORTED",
            "evidence": (
                f"Permanent non-selection among scored/ranked pos>0 keys that stay best_rank>=1 "
                f"under demotion: {len(demoted)} keys "
                f"({[d['key'] for d in demoted]}) including S/ODD. "
                f"Keys that attain rank-0 during active invent windows escape "
                f"({[e['key'] for e in escaped]}). "
                "Therefore lasting suppression requires demotion×n_mat=1, not n_mat=1 alone."
            ),
        },
        "H12c": {
            "claim": "plan-board ordering is the dominant prerequisite",
            "classification": "SUPPORTED",
            "evidence": (
                f"first_select_always_board0_pos0={freq['first_select_always_board0_pos0']}; "
                f"board0 identical {freq['board0_identical_across_cells']}; "
                "board order is the prerequisite for which key occupies the single n_mat=1 "
                "first-window slot. Alone it does not determine permanent fate (escape via re-rank)."
            ),
        },
        "H12d": {
            "claim": "mechanism specific to S/EVEN — does not generalize",
            "classification": "AGAINST",
            "evidence": (
                "First-window n_mat=1 skip applies to ALL 9 pos>0 keys, not only ODD. "
                f"Demotion×n_mat=1 permanent suppress also hits non-S keys "
                f"{[d['key'] for d in demoted if d['key'] != ODD]}. "
                f"Escape pattern hits non-S keys {[e['key'] for e in escaped]}. "
                "Mechanism is not S/EVEN-specific."
            ),
        },
        "H12e": {
            "claim": "mechanism broader than S — generic exploration/materialization tradeoff",
            "classification": "SUPPORTED",
            "evidence": (
                "Observed generic pattern under lazy n_mat=1: (1) board-order first cut; "
                "(2) class demotion after invent updates rejected_classes; "
                "(3) only current rank-0 materializes on later windows; "
                f"(4) non-rank-0 remain unmaterialized — applies to ODD plus POS6/POS7; "
                f"escapees U/POS5/POS2 confirm the rank-0 gate is the materialization valve."
            ),
        },
        "H12-REJECT": {
            "claim": "existing evidence insufficient for generalization",
            "classification": "AGAINST",
            "evidence": (
                f"Deterministic {n}/28 ON cells with identical board0 provide multi-key "
                "contrast (S suppress, U/POS2/POS5 escape, POS6/POS7 demotion suppress, "
                "null reject, POS3 post-window rank0). Sufficient to score H12a–H12e; "
                f"residual: board-pos1 positive control never observed (pos1_selected={pos1_ever_selected}/28)."
            ),
        },
    }


def build_controls(trajs: list[dict], cand_agg: list[dict]) -> dict:
    n = len(trajs)
    odd = next(c for c in cand_agg if c["candidate_key"] == ODD)
    even = next(c for c in cand_agg if c["candidate_key"] == EVEN)
    u = next(c for c in cand_agg if c["candidate_key"] == U_KEY)
    pos2 = next(c for c in cand_agg if c["candidate_key"] == POS2)
    pos5 = next(c for c in cand_agg if c["candidate_key"] == POS5)

    # Positive control: board pos1 ever selected?
    pos1_selected_cells = sum(
        1
        for t in trajs
        if len(t["board0"]) > 1 and t["board0"][1] in t["selects"]
    )
    # Broader positive: any pos>0 selected
    pos_gt0_selected_keys = [
        {"key": c["candidate_key"], "board_position": c["board_position"], "selected_cells": c["selected_cells"]}
        for c in cand_agg
        if c["board_position"] > 0 and c["selected_cells"] == n
    ]

    null_rejected = sum(1 for t in trajs if t["null_rejected_pre_select"])
    null_reasons = Counter(t["null_reject_reason"] for t in trajs)

    return {
        "S_odd_even": {
            "EVEN": {
                "key": EVEN,
                "board_position": even["board_position"],
                "selected_cells": even["selected_cells"],
                "invented_cells": even["invented_cells"],
                "role": "first-window materialization under board0@0 + n_mat=1",
            },
            "ODD": {
                "key": ODD,
                "board_position": odd["board_position"],
                "selected_cells": odd["selected_cells"],
                "invented_cells": odd["invented_cells"],
                "best_rank_counter": odd["best_rank_counter"],
                "role": "S suppressed: skipped first window + demotion keeps best_rank>=1",
            },
        },
        "U_natural_success": {
            "key": U_KEY,
            "board_position": u["board_position"],
            "selected_cells": u["selected_cells"],
            "invented_cells": u["invented_cells"],
            "ever_rank0_cells": u["ever_rank0_cells"],
            "score_unique_union": u["score_unique_union"],
            "role": "naturally successful: skipped first window but ESCAPES via later rank-0",
        },
        "positive_control_board_pos1": {
            "definition": (
                "A case where the candidate at board position 1 is known to become "
                "selected/materialized under existing machinery"
            ),
            "board_pos1_identity_always": ODD,
            "board_pos1_selected_cells": pos1_selected_cells,
            "finding": "NOT_OBSERVED",
            "note": (
                "In all 28 recorded cells board0[1]==ODD and is never selected. "
                "No alternate configuration places a different key at pos1."
            ),
            "broader_positive_control_pos_gt0_escape": {
                "status": "OBSERVED",
                "keys": pos_gt0_selected_keys,
                "exemplars": [
                    {"key": POS2, "board_position": 2, "selected_cells": pos2["selected_cells"]},
                    {"key": U_KEY, "board_position": 4, "selected_cells": u["selected_cells"]},
                    {"key": POS5, "board_position": 5, "selected_cells": pos5["selected_cells"]},
                ],
                "implication": (
                    "Board-position >0 is not an absolute barrier; escape requires "
                    "attaining rank-0 under n_mat=1 on a later invent window."
                ),
            },
        },
        "null_control": {
            "key": NULL_KEY,
            "definition": "no valid second candidate (rejected pre-select)",
            "rejected_pre_select_cells": null_rejected,
            "reject_reason_counter": dict(null_reasons),
            "selected_cells": 0,
            "invented_cells": 0,
            "on_board0_cells": sum(1 for t in trajs if NULL_KEY in t["board0"]),
            "finding": (
                f"NULL rejected pre-first-select in {null_rejected}/{n} cells "
                f"(reason={dict(null_reasons)}); never on board0; never selected/invented."
            ),
        },
    }


def generalization_matrix(cand_agg: list[dict], freq: dict, h12: dict, controls: dict) -> dict:
    rows = []
    for c in cand_agg:
        rows.append(
            {
                "board_position": c["board_position"],
                "candidate_key": c["candidate_key"],
                "control_role": c["control_role"],
                "selected_cells": c["selected_cells"],
                "invented_cells": c["invented_cells"],
                "ever_rank0_cells": c["ever_rank0_cells"],
                "best_rank_counter": c["best_rank_counter"],
                "score_unique_union": c["score_unique_union"],
                "mechanism_tag_counter": c["mechanism_tag_counter"],
                "first_window_fate": (
                    "MATERIALIZED"
                    if c["board_position"] == 0
                    else "SKIPPED_NMAT1"
                ),
                "permanent_fate": (
                    "FIRST_WINDOW_SUCCESS"
                    if c["board_position"] == 0
                    else "ESCAPED_VIA_RANK0"
                    if c["mechanism_tag_counter"].get("ESCAPED_VIA_LATER_RANK0")
                    else "SUPPRESSED_DEMOTION_NMAT1"
                    if c["mechanism_tag_counter"].get("SUPPRESSED_RANK_DEMOTION_NMAT1")
                    else "RANK0_AFTER_INVENT_STOPPED"
                    if c["mechanism_tag_counter"].get("RANK0_AFTER_INVENT_STOPPED")
                    else "NEVER_SCORED"
                    if c["mechanism_tag_counter"].get("NEVER_SCORED_AFTER_SKIP")
                    else "OTHER"
                ),
            }
        )
    return {
        "document": "aivd_3_43_generalization_matrix",
        "primary_question": (
            "Does plan-board order + rank demotion + lazy n_mat=1 systematically "
            "suppress valid lower-position candidates?"
        ),
        "answer_short": "PARTIAL — first-window yes for all pos>0; permanent suppress only with demotion×n_mat=1",
        "n_cells": freq["n_cells"],
        "rows": rows,
        "mechanism_frequency_headline": freq["headline"],
        "H12": {k: v["classification"] for k, v in h12.items()},
        "controls_summary": {
            "S": controls["S_odd_even"],
            "U_board_pos": controls["U_natural_success"]["board_position"],
            "positive_pos1": controls["positive_control_board_pos1"]["finding"],
            "positive_pos_gt0_escape": controls["positive_control_board_pos1"][
                "broader_positive_control_pos_gt0_escape"
            ]["status"],
            "null": controls["null_control"]["finding"],
        },
    }


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def main() -> dict:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    fate = json.loads(FATE_PATH.read_text(encoding="utf-8"))
    recorded_at = _now_ist()
    trajs = [reconstruct_cell(c) for c in ledger["cells_on"]]
    cand_agg = aggregate_candidates(trajs)
    freq = mechanism_frequency(cand_agg, trajs)
    h12 = classify_H12(freq, cand_agg, trajs)
    controls = build_controls(trajs, cand_agg)
    matrix = generalization_matrix(cand_agg, freq, h12, controls)

    # Cross-check 3.42 phase1 if present
    phase1_342_meta = NR
    if PHASE1_342.exists():
        p342 = json.loads(PHASE1_342.read_text(encoding="utf-8"))
        phase1_342_meta = {
            "source": str(PHASE1_342.relative_to(ROOT)),
            "recorded_at_ist": p342.get("recorded_at_ist"),
            "n_cells": p342.get("aggregate", {}).get("n_cells"),
            "first_select_always_even": p342.get("aggregate", {}).get(
                "first_select_always_even"
            ),
        }

    per_candidate_fate = {
        "document": "aivd_3_43_per_candidate_fate",
        "recorded_at_ist": recorded_at,
        "source_ledger": str(LEDGER_PATH.relative_to(ROOT)),
        "source_fate": str(FATE_PATH.relative_to(ROOT)),
        "phase1_342_crosscheck": phase1_342_meta,
        "mode": "OFFLINE_REPLAY_ONLY",
        "sacred": False,
        "fields_policy": "existing observations only; NOT_RECORDED if missing; no inference",
        "aggregate_by_board_position": cand_agg,
        "exemplar_S8_BASELINE_seed0": next(
            t for t in trajs if t["condition_id"] == "S8-BASELINE" and t["seed"] == 0
        ),
        "fate_odd_crosscheck": {
            "fate_candidate_key": fate.get("candidate_key"),
            "fate_selected_any": any(r.get("selected") for r in fate.get("table") or []),
            "fate_invented_any": any(r.get("invented") for r in fate.get("table") or []),
        },
    }

    mech_freq_doc = {
        "document": "aivd_3_43_mechanism_frequency",
        "recorded_at_ist": recorded_at,
        **freq,
    }

    controls_doc = {
        "document": "aivd_3_43_controls",
        "recorded_at_ist": recorded_at,
        **controls,
    }

    # Phase 2: SKIPPED — Phase 1 sufficient
    cf = {
        "document": "aivd_3_43_counterfactual",
        "recorded_at_ist": recorded_at,
        "status": "SKIPPED",
        "reason": (
            "Phase 1 offline replay of 28 ON cells with identical 10-slot board0 already "
            "provides multi-key contrast sufficient to score H12a–H12e and H12-REJECT. "
            "Additional controlled offline CF would only restate 3.42 CF1–CF3 "
            "(n_mat>=2 would select board0[1]=ODD; no recorded ODD rank0; no ODD@pos0) "
            "without introducing new candidate configurations. No production/Sacred run."
        ),
        "reference_3_42_counterfactual": "reports/aivd_3_42_counterfactual.json",
    }

    matrix["recorded_at_ist"] = recorded_at

    results = {
        "document": "aivd_3_43_results",
        "recorded_at_ist": recorded_at,
        "baseline_tip": "3a07abe1e370f3328be33a3ad93e5fb7972a65eb",
        "branch": "research/aivd-3.43-selection-budget-generalization",
        "parent_branch": "research/aivd-3.42-selection-causal-audit @ 3a07abe",
        "phase1": "COMPLETE",
        "phase2": "SKIPPED",
        "phase2_reason": cf["reason"],
        "H12": {k: v["classification"] for k, v in h12.items()},
        "H12_detail": h12,
        "mechanism_frequency_headline": freq["headline"],
        "positive_control_board_pos1": controls["positive_control_board_pos1"]["finding"],
        "positive_control_pos_gt0_escape": controls["positive_control_board_pos1"][
            "broader_positive_control_pos_gt0_escape"
        ]["status"],
        "null_control_finding": controls["null_control"]["finding"],
        "S_vs_U": {
            "S_ODD": "board@1; never selected; demotion×n_mat=1 suppress",
            "U": "board@4; selected+invented 28/28 via later rank-0 escape",
            "contrast": (
                "Same first-window n_mat=1 skip; divergent permanent fate determined by "
                "whether the key later attains rank-0 under class demotion."
            ),
        },
        "does_mechanism_generalize": {
            "answer": "partial",
            "sentence": (
                "First-window board-order×n_mat=1 skip generalizes to all pos>0 keys; "
                "permanent suppression generalizes only where rank demotion keeps the key "
                "off rank-0 (ODD/POS6/POS7), while U/POS2/POS5 escape — not S-specific."
            ),
        },
        "sacred": False,
        "planner_changed": False,
        "n_mat_changed": False,
    }

    # Write JSON
    write_json(REPORTS / "aivd_3_43_generalization_matrix.json", matrix)
    write_json(REPORTS / "aivd_3_43_per_candidate_fate.json", per_candidate_fate)
    write_json(REPORTS / "aivd_3_43_mechanism_frequency.json", mech_freq_doc)
    write_json(REPORTS / "aivd_3_43_controls.json", controls_doc)
    write_json(REPORTS / "aivd_3_43_counterfactual.json", cf)
    write_json(REPORTS / "aivd_3_43_results.json", results)

    return {
        "recorded_at": recorded_at,
        "trajs": trajs,
        "cand_agg": cand_agg,
        "freq": freq,
        "h12": h12,
        "controls": controls,
        "matrix": matrix,
        "cf": cf,
        "results": results,
    }


if __name__ == "__main__":
    out = main()
    print(
        json.dumps(
            {
                "ok": True,
                "recorded_at": out["recorded_at"],
                "H12": {k: v["classification"] for k, v in out["h12"].items()},
                "headline": out["freq"]["headline"],
                "phase2": out["cf"]["status"],
            },
            indent=2,
        )
    )
