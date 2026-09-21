"""Phase-2 mechanism classification (outcomes 1–6) — Mode A/B namespaces separate."""
from __future__ import annotations

from typing import Any

from aivd.experiments.aivd340.phase2_constants import (
    HIGH_RANK_CUTOFF,
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    OUTCOME_ABSENT_POOL,
    OUTCOME_GROWTH_DIVERGE,
    OUTCOME_HIGH_NOT_SELECTED,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_LOW_RANK,
    OUTCOME_VERIFY_FAIL,
)


def _is_relevant_growth_cand(c: dict[str, Any]) -> bool:
    bk = c.get("body_key") or ""
    parent = str(c.get("parent_id") or "")
    cid = str(c.get("candidate_id") or "")
    if bk == ODD_CAT_SELF_BODY_KEY:
        return True
    if "SLICE:1,2" in bk and "CAT(" in bk:
        return True
    if c.get("growth_or_composition_op") == "CAT_SELF" and (
        "slice_1_2" in parent.lower()
        or "slice_1_2" in cid.lower()
        or ODD_STRIDE_BODY_KEY in parent
    ):
        return True
    return False


def _growth_pre_snaps(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        r
        for r in records
        if r.get("snapshot_phase") == "pre_selection"
        and (
            r.get("event_kind") == "grow"
            or r.get("selection_rule_id") == "pick_generation_action"
        )
    ]


def _post_selects(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in records if r.get("snapshot_phase") == "post_selection"]


def classify_seed_mechanism(episode: dict[str, Any]) -> dict[str, Any]:
    """Classify one episode into outcomes 1–6 for relevant odd CAT-self candidate."""
    instr = episode.get("instrumentation") or {}
    records = instr.get("records") or []
    mode = episode.get("mode") or instr.get("mode") or "A"
    role = episode.get("target_role") or instr.get("target_role") or "S"
    integrity = bool(instr.get("integrity_ok", True))
    claim_ns = "AUTONOMOUS" if mode == "A" else "CONTROLLED_INPUT"
    base_label = "OBSERVED" if mode == "A" else "CONTROLLED"

    if not integrity:
        return {
            "outcome": OUTCOME_INCONCLUSIVE,
            "reading": "INCONCLUSIVE",
            "label": "UNKNOWN",
            "claim_namespace": claim_ns,
            "reason": "recorder integrity failure",
            "integrity_notes": instr.get("integrity_notes") or [],
        }

    growth_snaps = _growth_pre_snaps(records)
    gen_records = episode.get("generation_records") or []
    produced_keys = {
        (r.get("body_key") or r.get("key"))
        for r in gen_records
        if (r.get("body_key") or r.get("key"))
    }
    mode_b_injected = bool(instr.get("mode_b_injected")) or any(
        r.get("event_kind") == "mode_b_availability" for r in records
    )

    # Mode B × S must show controlled availability (inject or body already present).
    if mode == "B" and role == "S":
        if not mode_b_injected and ODD_STRIDE_BODY_KEY not in produced_keys:
            # Check methods_log
            methods = episode.get("methods_log") or []
            if not any(e.get("event") == "mode_b_availability" for e in methods):
                return {
                    "outcome": OUTCOME_INCONCLUSIVE,
                    "reading": "INCONCLUSIVE",
                    "label": "UNKNOWN",
                    "claim_namespace": claim_ns,
                    "reason": "Mode B S without controlled availability evidence",
                }

    if mode == "B" and role == "U":
        # Null injection control — no S-favoring; mechanism N/A for odd CAT-self.
        return {
            "outcome": OUTCOME_INCONCLUSIVE,
            "reading": "INCONCLUSIVE",
            "label": "CONTROLLED",
            "claim_namespace": claim_ns,
            "reason": "Mode B U is null-injection instrumentation control (not H2/H3 primary)",
            "present_any": False,
            "present_ranks": [],
            "selected_any": False,
            "odd_stride_in_produced": ODD_STRIDE_BODY_KEY in produced_keys,
            "odd_cat_self_in_produced": ODD_CAT_SELF_BODY_KEY in produced_keys,
            "mode_b_injected": mode_b_injected,
            "growth_snapshot_count": len(growth_snaps),
        }

    present_ranks: list[int] = []
    present_any = False
    for snap in growth_snaps:
        for c in snap.get("candidates") or []:
            if _is_relevant_growth_cand(c):
                present_any = True
                if c.get("rank") is not None:
                    present_ranks.append(int(c["rank"]))

    selected_any = False
    for ps in _post_selects(records):
        sb = ps.get("selected_body_key") or ""
        if sb == ODD_CAT_SELF_BODY_KEY or ("SLICE:1,2" in sb and "CAT(" in sb):
            selected_any = True
        # Also: selected grow cand id referencing odd stride parent
        sid = str(ps.get("selected_candidate_id") or "")
        if "slice_1_2" in sid.lower() and ps.get("action") == "grow":
            selected_any = True

    odd_cat_produced = ODD_CAT_SELF_BODY_KEY in produced_keys
    methods = episode.get("methods_log") or []
    verify_reject = any(
        str(e.get("event") or "").lower() in {
            "verify_reject",
            "verification_reject",
            "atom_reject",
            "reject",
        }
        for e in methods
    )

    if not growth_snaps:
        # No growth decisions recorded — if Mode A, still informative for invent;
        # mechanism for H2/H3 growth pool is inconclusive without snapshots.
        outcome = OUTCOME_INCONCLUSIVE
        reading = "INCONCLUSIVE"
        reason = "no growth pre_selection snapshots"
        # Special case: Mode A with no growth snaps and odd absent from invent → still
        # report invent continuity separately; outcome 6 for H2/H3 growth question.
    elif not present_any:
        outcome = OUTCOME_ABSENT_POOL
        reading = "H2/earlier growth"
        reason = f"relevant candidate absent from growth pools (looking for {ODD_CAT_SELF_BODY_KEY})"
    elif present_ranks and all(r > HIGH_RANK_CUTOFF for r in present_ranks):
        outcome = OUTCOME_LOW_RANK
        reading = "H3 selection pressure"
        reason = f"present but consistently low-ranked ranks={present_ranks}"
    elif present_ranks and any(r <= HIGH_RANK_CUTOFF for r in present_ranks) and not selected_any:
        outcome = OUTCOME_HIGH_NOT_SELECTED
        reading = "tie-break/selection mechanism"
        reason = f"high-ranked (ranks={present_ranks}) but not selected"
    elif selected_any and verify_reject and not odd_cat_produced:
        outcome = OUTCOME_VERIFY_FAIL
        reading = "H4"
        reason = "selected but verify failed"
    elif selected_any and not odd_cat_produced:
        outcome = OUTCOME_GROWTH_DIVERGE
        reading = "H2 post-selection composition"
        reason = "selected earlier; finished odd CAT-self never in generation_records"
    elif selected_any and odd_cat_produced:
        # Instrumentation shows present+selected+produced — H2/H3 failure not supported
        outcome = OUTCOME_GROWTH_DIVERGE
        reading = "H2 post-selection composition"
        reason = (
            "present+selected+produced; if terminal still fails, bottleneck is downstream — "
            "NOT classified as H2-absent or H3-lowrank"
        )
        # Prefer: no H2/H3 failure pattern 1–3. Use outcome 5 only if later diverge;
        # if produced, mark as inconclusive for failure-localization.
        if episode.get("pipeline_verified"):
            outcome = OUTCOME_INCONCLUSIVE
            reading = "INCONCLUSIVE"
            reason = "relevant body present+selected+produced and verified — H2/H3 failure not indicated"
        else:
            outcome = OUTCOME_GROWTH_DIVERGE
            reading = "H2 post-selection composition"
            reason = "present+selected+produced but episode not verified — downstream"
    else:
        outcome = OUTCOME_INCONCLUSIVE
        reading = "INCONCLUSIVE"
        reason = f"unresolved pattern present={present_any} ranks={present_ranks} selected={selected_any}"

    return {
        "outcome": int(outcome),
        "reading": reading,
        "label": base_label,
        "claim_namespace": claim_ns,
        "reason": reason,
        "present_any": present_any,
        "present_ranks": present_ranks,
        "selected_any": selected_any,
        "odd_stride_in_produced": ODD_STRIDE_BODY_KEY in produced_keys,
        "odd_cat_self_in_produced": odd_cat_produced,
        "odd_invented_autonomous": (
            mode == "A" and ODD_STRIDE_BODY_KEY in produced_keys
        ),
        "mode_b_injected": mode_b_injected,
        "growth_snapshot_count": len(growth_snaps),
    }


def aggregate_outcomes(episodes: list[dict[str, Any]], *, mode: str, role: str) -> dict[str, Any]:
    subset = [e for e in episodes if e.get("mode") == mode and e.get("target_role") == role]
    classifications = []
    for e in subset:
        c = e.get("mechanism") or classify_seed_mechanism(e)
        classifications.append({"seed": e.get("seed"), **c})
    counts = {str(i): 0 for i in range(1, 7)}
    for c in classifications:
        k = str(int(c["outcome"]))
        counts[k] = counts.get(k, 0) + 1

    non_inc = [c for c in classifications if int(c["outcome"]) != OUTCOME_INCONCLUSIVE]
    if not classifications or (role == "U" and mode == "B"):
        final = "INCONCLUSIVE"
    elif not non_inc:
        final = "INCONCLUSIVE"
    else:
        h2 = sum(1 for c in non_inc if int(c["outcome"]) in (OUTCOME_ABSENT_POOL, OUTCOME_GROWTH_DIVERGE))
        h3 = sum(1 for c in non_inc if int(c["outcome"]) == OUTCOME_LOW_RANK)
        tie_sel = sum(1 for c in non_inc if int(c["outcome"]) == OUTCOME_HIGH_NOT_SELECTED)
        h4 = sum(1 for c in non_inc if int(c["outcome"]) == OUTCOME_VERIFY_FAIL)
        if h4 and h4 >= max(h2, h3, tie_sel):
            final = "DOWNSTREAM H4"
        elif h2 >= 1 and h3 >= 1:
            final = "H2 + H3"
        elif h2 > 0 and h2 >= h3 and h2 >= tie_sel and h2 >= h4:
            final = "H2 SUPPORTED"
        elif h3 > 0 and h3 >= h2 and h3 >= tie_sel:
            final = "H3 SUPPORTED"
        elif tie_sel > 0 and tie_sel >= max(h2, h3):
            # Outcome 3 = tie-break/selection — not pure H3; do not force H3.
            final = "INCONCLUSIVE"
        else:
            final = "INCONCLUSIVE"

    # Mode A × S with invent-absent odd-stride is H1 continuity, not H2 localization.
    if mode == "A" and role == "S":
        odd_absent = sum(
            1
            for e in subset
            if not (e.get("mechanism") or {}).get("odd_stride_in_produced")
        )
        if odd_absent == len(subset) and len(subset) > 0:
            final = "H1_CONTINUITY_ODD_ABSENT"

    return {
        "mode": mode,
        "target_role": role,
        "n": len(subset),
        "outcome_counts": counts,
        "classifications": classifications,
        "cell_conclusion": final,
        "claim_namespace": "AUTONOMOUS" if mode == "A" else "CONTROLLED_INPUT",
        "autonomous_discovery_credit": mode == "A",
    }


def final_h2_h3_conclusion(*, mode_b_s: dict[str, Any]) -> str:
    """Primary H2/H3 localization prefers Mode B (availability given)."""
    return mode_b_s.get("cell_conclusion") or "INCONCLUSIVE"


__all__ = [
    "classify_seed_mechanism",
    "aggregate_outcomes",
    "final_h2_h3_conclusion",
]
