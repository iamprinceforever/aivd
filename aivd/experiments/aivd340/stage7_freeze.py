"""Stage-7 EXECUTION freeze: pin context bank, pairs, independence, GT BEFORE repair outcomes.

OUTAGE_RECOVERY: prior freeze artifacts lost after tooling outage; prior hashes
(context_bank_hash=b521e4ff…, pair_list_hash=5d613c21…, gt_hash=57753bb3…) could not be
reproduced bit-identical. This module regenerates a NEW freeze from frozen Stage-7
design specs (d0ef7b6) before any repair evaluation. Independence labels follow
generalization_spec; no Stage-6 outcome tuning.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.stage4_constants import (
    ODD_CAT_SELF_BODY_KEY,
    U_GOOD_CAT_SELF_BODY_KEY,
    U_GOOD_BODY_KEY,
)
from aivd.experiments.aivd340.stage6_constants import (
    IDENTITY_DEFAULT,
    load_matrix as load_stage6_matrix,
    pinned_core_bank,
    reserve_bank,
)
from aivd.experiments.aivd340.stage7_constants import (
    CRITICAL_BODY_KEYS,
    DESIGN_TIP,
    DESIGN_TIP_FULL,
    FREEZE_PATH,
    MATRIX_PATH,
    REQUIRED_FAMILIES,
    STAGE6_BANK_HASH_REF,
    sha256_json,
)
from aivd.experiments.aivd340.stage7_resolve import resolve_token
from aivd.science.micro import apply_micro

IST = timezone(timedelta(hours=5, minutes=30))
REPO = Path(__file__).resolve().parents[3]

# Prior attempt hashes (not reproduced — documented for audit)
PRIOR_ATTEMPT_HASHES = {
    "context_bank_hash": "b521e4ffa14e4997b844f4ca7a73c3aec9186b3dd4290ea40f753a1809b02f6f",
    "pair_list_hash": "5d613c219e96de9345ca831d174351e09c0e61934f5a99d9611ccb3b90381d7e",
    "gt_hash": "57753bb3724d9302647d8b972a35c8ae7e1dabcac84f1f3417286f7f5e08dfd3",
    "n_pairs": 25,
}

# Concrete pair tokens pinned at EXECUTION freeze (from condition_sketch; non-critical IND bodies)
PAIR_DEFS_RAW: list[dict[str, Any]] = [
    # TRUE_DUP (3)
    {"condition_id": "S7-TD-01", "pair_class": "TRUE_DUP", "independence": "INDEPENDENT",
     "body_a": "IDENTICAL_AT0_TWICE", "body_b": "IDENTICAL_AT0_TWICE"},
    {"condition_id": "S7-TD-02", "pair_class": "TRUE_DUP", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:0|AT:0))", "body_b": "MAPT(CAT(AT:0|AT:0))"},
    {"condition_id": "S7-TD-03", "pair_class": "TRUE_DUP", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
     "body_b": "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))"},
    # KNOWN_NONDUP (4)
    {"condition_id": "S7-ND-01", "pair_class": "KNOWN_NONDUP", "independence": "INDEPENDENT",
     "body_a": "MAPT(AT:-1)", "body_b": "MAPT(AT:0)"},
    {"condition_id": "S7-ND-02", "pair_class": "KNOWN_NONDUP", "independence": "INDEPENDENT",
     "body_a": "MAPT(SLICE:0,2(TOK))", "body_b": "MAPT(SLICE:0,3(TOK))"},
    {"condition_id": "S7-ND-03", "pair_class": "KNOWN_NONDUP", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:-1|AT:0))", "body_b": "MAPT(CAT(AT:0|AT:-1))"},
    {"condition_id": "S7-ND-04", "pair_class": "KNOWN_NONDUP", "independence": "INDEPENDENT",
     "body_a": "MAPT(AT:1)", "body_b": "MAPT(SLICE:0,2(TOK))"},
    # CONTEXT_DEPENDENT (2) — agree IDENTITY/ORDERING, diverge TR/BD/CO; non-critical
    {"condition_id": "S7-CD-01", "pair_class": "CONTEXT_DEPENDENT", "independence": "INDEPENDENT",
     "body_a": "MAPT(AT:0)", "body_b": "MAPT(SLICE:0,2(TOK))"},
    {"condition_id": "S7-CD-02", "pair_class": "CONTEXT_DEPENDENT", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:0|AT:0))", "body_b": "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))"},
    # TEXT_EQ_BEH_DIFF (2)
    {"condition_id": "S7-TEBD-01", "pair_class": "TEXT_EQ_BEH_DIFF", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:0|AT:0))", "body_b": "MAPT(CAT(AT:1|AT:1))"},
    {"condition_id": "S7-TEBD-02", "pair_class": "TEXT_EQ_BEH_DIFF", "independence": "INDEPENDENT",
     "body_a": "MAPT(AT:0)", "body_b": "MAPT(AT:1)"},
    # TEXT_DIFF_BEH_EQ (2) — token text differs; resolve to same canonical key
    {"condition_id": "S7-TDBE-01", "pair_class": "TEXT_DIFF_BEH_EQ", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:0|AT:0))", "body_b": "RE_CAT_SELF(MAPT(AT:0))"},
    {"condition_id": "S7-TDBE-02", "pair_class": "TEXT_DIFF_BEH_EQ", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:1|AT:1))", "body_b": "RE_CAT_SELF(MAPT(AT:1))"},
    # STATE_CONTEXT_SENSITIVE (2)
    {"condition_id": "S7-ST-01", "pair_class": "STATE_CONTEXT_SENSITIVE", "independence": "INDEPENDENT",
     "body_a": "MAPT(AT:2)", "body_b": "MAPT(CAT(AT:2|AT:2))"},
    {"condition_id": "S7-ST-02", "pair_class": "STATE_CONTEXT_SENSITIVE", "independence": "INDEPENDENT",
     "body_a": "MAPT(AT:1)", "body_b": "MAPT(AT:-1)"},
    # COMPOSITION_SENSITIVE (2)
    {"condition_id": "S7-CO-01", "pair_class": "COMPOSITION_SENSITIVE", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:0|AT:1))", "body_b": "MAPT(CAT(AT:1|AT:0))"},
    {"condition_id": "S7-CO-02", "pair_class": "COMPOSITION_SENSITIVE", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(SLICE:0,2(TOK)|AT:-1))", "body_b": "MAPT(CAT(AT:-1|SLICE:0,2(TOK)))"},
    # U_GOOD (1)
    {"condition_id": "S7-UG-01", "pair_class": "U_GOOD", "independence": "INDEPENDENT",
     "body_a": U_GOOD_BODY_KEY, "body_b": "MAPT(CAT(AT:0|AT:0))"},
    # ADV_TS (2)
    {"condition_id": "S7-ADV-TS-01", "pair_class": "ADV_TEXT_DIFF_BEH_SAME", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:2|AT:2))", "body_b": "RE_CAT_SELF(MAPT(AT:2))"},
    {"condition_id": "S7-ADV-TS-02", "pair_class": "ADV_TEXT_DIFF_BEH_SAME", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(SLICE:0,3(TOK)|SLICE:0,3(TOK)))",
     "body_b": "RE_CAT_SELF(MAPT(SLICE:0,3(TOK)))"},
    # ADV_TD (2)
    {"condition_id": "S7-ADV-TD-01", "pair_class": "ADV_TEXT_SIM_BEH_DIFF", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:0|AT:0))", "body_b": "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))"},
    {"condition_id": "S7-ADV-TD-02", "pair_class": "ADV_TEXT_SIM_BEH_DIFF", "independence": "INDEPENDENT",
     "body_a": "MAPT(CAT(AT:1|AT:1))", "body_b": "MAPT(CAT(AT:1|AT:-1))"},
    # Side cells (not independent evidence)
    {"condition_id": "S7-REPLAY-01", "pair_class": "S6_REPLAY", "independence": "S6_REPLAY",
     "body_a": "S6_REPLAY_TD01", "body_b": "S6_REPLAY_TD01"},
    {"condition_id": "S7-REL-01", "pair_class": "RELATED", "independence": "RELATED",
     "body_a": ODD_CAT_SELF_BODY_KEY, "body_b": U_GOOD_CAT_SELF_BODY_KEY},
    {"condition_id": "S7-SDIAG-01", "pair_class": "S_DIAGNOSTIC", "independence": "S_DIAGNOSTIC",
     "body_a": ODD_CAT_SELF_BODY_KEY, "body_b": U_GOOD_CAT_SELF_BODY_KEY},
]


def build_context_bank() -> dict[str, Any]:
    s6 = load_stage6_matrix()
    continuity = pinned_core_bank(s6)  # Stage-6 core; CTX-ID-02 pinned to IDENTITY_DEFAULT
    # Continuity STATE_CONTEXT (Stage-6 STATE was meta-only; pin concrete probe)
    state_continuity = [
        ("CTX-ST-01", "STATE_CONTEXT", "keep-order probe: ab cd ef gh ij kl"),
    ]
    novel = [
        ("S7-TR-N1", "TRANSFORMED", "alpha beta gamma delta"),
        ("S7-TR-N2", "TRANSFORMED", "Zebra Yellow Xray"),
        ("S7-BD-N1", "BOUNDARY", "z"),
        ("S7-BD-N2", "BOUNDARY", "tok1 tok22 tok333"),
        ("S7-CO-N1", "COMPOSITION", "red green blue yellow"),
        ("S7-CO-N2", "COMPOSITION", "moon star sun sky cloud"),
        ("S7-OR-N1", "ORDERING", "kl ab ef ij cd gh"),
        ("S7-ID-N1", "BASELINE_IDENTITY", "pq rs tu vw xy za"),
        ("S7-ST-N1", "STATE_CONTEXT", "identity-alt meta: pq rs tu vw xy za"),
    ]
    core = list(continuity) + state_continuity + novel
    reserve = reserve_bank(s6)

    # Disjointness vs Stage-6 bank prompts
    s6_prompts = {p for _, _, p in continuity} | {p for _, _, p in reserve}
    novel_prompts = {p for _, _, p in novel}
    overlap = novel_prompts & s6_prompts
    if overlap:
        raise RuntimeError(f"novel prompts overlap Stage-6 bank: {overlap}")

    # Novel family quotas
    novel_by_fam: dict[str, int] = {}
    for _, fam, _ in novel:
        novel_by_fam[fam] = novel_by_fam.get(fam, 0) + 1
    required_novel = {
        "TRANSFORMED": 2, "BOUNDARY": 2, "COMPOSITION": 2,
        "ORDERING": 1, "BASELINE_IDENTITY": 1, "STATE_CONTEXT": 1,
    }
    for fam, n in required_novel.items():
        if novel_by_fam.get(fam, 0) < n:
            raise RuntimeError(f"novel quota fail {fam}: {novel_by_fam.get(fam, 0)} < {n}")

    if len(reserve) > 8:
        raise RuntimeError("reserve > 8")

    bank_obj = {
        "core": [{"id": a, "family": b, "prompt": c, "continuity": a.startswith("CTX-") and not a.startswith("S7-")}
                 for a, b, c in core],
        "reserve": [{"id": a, "family": b, "prompt": c} for a, b, c in reserve],
        "novel_ids": [a for a, _, _ in novel],
        "stage6_bank_hash_ref": STAGE6_BANK_HASH_REF,
        "identity_default": IDENTITY_DEFAULT,
    }
    # continuity flag: Stage-6 continuity ids + CTX-ST-01
    for item in bank_obj["core"]:
        item["continuity"] = item["id"] not in bank_obj["novel_ids"]

    return {
        "core_tuples": core,
        "reserve_tuples": reserve,
        "bank_obj": bank_obj,
        "context_bank_hash": sha256_json({
            "core": [{"id": a, "family": b, "prompt": c} for a, b, c in core],
            "reserve": [{"id": a, "family": b, "prompt": c} for a, b, c in reserve],
        }),
    }


def compute_gt(body_a, body_b, core) -> dict[str, Any]:
    if body_a.key() == body_b.key():
        return {
            "gt_label": "DUP",
            "gt_raw": "DUP",
            "reason": "identical_canonical_key",
            "n_equal": len(core),
            "n_differ": 0,
            "n_unknown": 0,
            "families_diverged": [],
            "families_touched": sorted({f for _, f, _ in core}),
        }
    n_eq = n_diff = n_unk = 0
    fam_div: set[str] = set()
    fam_touch: set[str] = set()
    for cid, fam, prompt in core:
        fam_touch.add(fam)
        try:
            ga = apply_micro(prompt, body_a)
            gb = apply_micro(prompt, body_b)
        except Exception:
            n_unk += 1
            continue
        if ga == gb:
            n_eq += 1
        else:
            n_diff += 1
            fam_div.add(fam)
    if n_diff == 0 and n_unk == 0:
        raw, label = "DUP", "DUP"
    elif n_diff >= 1:
        raw, label = "DISTINCT", "DISTINCT"
    else:
        raw, label = "MIXED", "DISTINCT"
    return {
        "gt_label": label,
        "gt_raw": raw,
        "reason": "core_bank_audit",
        "n_equal": n_eq,
        "n_differ": n_diff,
        "n_unknown": n_unk,
        "families_diverged": sorted(fam_div),
        "families_touched": sorted(fam_touch),
    }


def build_freeze() -> dict[str, Any]:
    bank = build_context_bank()
    core = bank["core_tuples"]
    reserve = bank["reserve_tuples"]

    pairs = []
    for raw in PAIR_DEFS_RAW:
        ba = resolve_token(raw["body_a"])
        bb = resolve_token(raw["body_b"])
        # Independence contamination check
        ind = raw["independence"]
        keys = {ba.key(), bb.key()}
        if ind == "INDEPENDENT" and (keys & CRITICAL_BODY_KEYS):
            raise RuntimeError(
                f"{raw['condition_id']}: INDEPENDENT pair uses critical body keys {keys & CRITICAL_BODY_KEYS}"
            )
        gt = compute_gt(ba, bb, core)
        pairs.append({
            "condition_id": raw["condition_id"],
            "pair_class": raw["pair_class"],
            "independence": ind,
            "body_a_token": raw["body_a"],
            "body_b_token": raw["body_b"],
            "body_key_a": ba.key(),
            "body_key_b": bb.key(),
            "gt_label": gt["gt_label"],
            "gt_raw": gt["gt_raw"],
            "gt_reason": gt["reason"],
            "families_diverged": gt["families_diverged"],
            "families_touched": gt["families_touched"],
            "n_equal": gt["n_equal"],
            "n_differ": gt["n_differ"],
            "n_unknown": gt["n_unknown"],
        })

    # Quotas
    matrix = json.loads(MATRIX_PATH.read_text())
    ind_counts: dict[str, int] = {}
    for p in pairs:
        if p["independence"] == "INDEPENDENT":
            ind_counts[p["pair_class"]] = ind_counts.get(p["pair_class"], 0) + 1
    for cls, mn in matrix["phase_A_min_independent_counts"].items():
        if ind_counts.get(cls, 0) < mn:
            raise RuntimeError(f"IND quota fail {cls}: {ind_counts.get(cls, 0)} < {mn}")
    side = {p["independence"] for p in pairs}
    for need in ("S6_REPLAY", "RELATED", "S_DIAGNOSTIC"):
        if need not in side:
            raise RuntimeError(f"missing side cell independence={need}")

    if len(pairs) != 25:
        raise RuntimeError(f"expected 25 pairs, got {len(pairs)}")

    pair_list_obj = [
        {
            "condition_id": p["condition_id"],
            "body_key_a": p["body_key_a"],
            "body_key_b": p["body_key_b"],
            "body_a_token": p["body_a_token"],
            "body_b_token": p["body_b_token"],
            "independence": p["independence"],
            "pair_class": p["pair_class"],
            "gt_label": p["gt_label"],
        }
        for p in pairs
    ]
    gt_obj = {
        p["condition_id"]: {
            "gt_label": p["gt_label"],
            "gt_raw": p["gt_raw"],
            "body_key_a": p["body_key_a"],
            "body_key_b": p["body_key_b"],
            "families_diverged": p["families_diverged"],
            "reason": p["gt_reason"],
        }
        for p in pairs
    }

    pair_list_hash = sha256_json(pair_list_obj)
    gt_hash = sha256_json(gt_obj)
    context_bank_hash = bank["context_bank_hash"]

    # Context family coverage potential on IND
    fams_from_ind: set[str] = set()
    for p in pairs:
        if p["independence"] == "INDEPENDENT":
            fams_from_ind.update(p["families_touched"])
    coverage_ok = all(f in fams_from_ind for f in REQUIRED_FAMILIES)

    freeze = {
        "document": "aivd_3_40_stage7_execution_freeze",
        "recorded_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "design_tip": DESIGN_TIP,
        "design_tip_full": DESIGN_TIP_FULL,
        "authorization": "STAGE-7 EXECUTION AUTHORIZED (Phase A then B; classification-only)",
        "outage_recovery": {
            "note": "OUTAGE_RECOVERY",
            "detail": (
                "Prior Phase-0 passed then Shell/Read outage; freeze JSON and runners lost. "
                "Prior hashes could not be reproduced bit-identical; NEW freeze regenerated "
                "from d0ef7b6 Stage-7 specs BEFORE repair outcomes. Independence labels follow "
                "generalization_spec; no Stage-6 per-pair prediction tuning."
            ),
            "prior_attempt_hashes": PRIOR_ATTEMPT_HASHES,
            "prior_hashes_matched": False,
            "contamination_status": "NOT_COUNTED_AS_CONTAMINATION_IF_INDEPENDENCE_LABELS_CORRECT",
        },
        "executed_repairs_before_freeze": False,
        "context_bank_hash": context_bank_hash,
        "pair_list_hash": pair_list_hash,
        "gt_hash": gt_hash,
        "stage6_bank_hash_ref": STAGE6_BANK_HASH_REF,
        "n_pairs": len(pairs),
        "n_independent": sum(1 for p in pairs if p["independence"] == "INDEPENDENT"),
        "ind_class_counts": ind_counts,
        "context_family_coverage_potential": sorted(fams_from_ind),
        "context_family_coverage_ok": coverage_ok,
        "core_context_count": len(core),
        "reserve_context_count": len(reserve),
        "novel_context_count": len(bank["bank_obj"]["novel_ids"]),
        "identity_default": IDENTITY_DEFAULT,
        "context_bank": bank["bank_obj"],
        "pairs": pairs,
        "pair_list_canonical": pair_list_obj,
        "gt_freeze": gt_obj,
        "family_spec_version": "ac152c6",
        "budget_envelope_version": "stage7_prereg_§9",
        "sacred_bh_draws_allowed": 0,
        "filter_replacement_authorized": False,
        "grow_py_edits_authorized": False,
    }
    if not coverage_ok:
        raise RuntimeError(f"context family coverage incomplete: {fams_from_ind}")
    return freeze


def write_freeze(path: Path | None = None) -> dict[str, Any]:
    freeze = build_freeze()
    out = path or FREEZE_PATH
    out.write_text(json.dumps(freeze, indent=2) + "\n")
    return freeze


def load_freeze(path: Path | None = None) -> dict[str, Any]:
    p = path or FREEZE_PATH
    return json.loads(p.read_text())


def core_from_freeze(freeze: dict) -> list[tuple[str, str, str]]:
    return [(c["id"], c["family"], c["prompt"]) for c in freeze["context_bank"]["core"]]


def reserve_from_freeze(freeze: dict) -> list[tuple[str, str, str]]:
    return [(c["id"], c["family"], c["prompt"]) for c in freeze["context_bank"]["reserve"]]


if __name__ == "__main__":
    fr = write_freeze()
    print("context_bank_hash", fr["context_bank_hash"])
    print("pair_list_hash", fr["pair_list_hash"])
    print("gt_hash", fr["gt_hash"])
    print("n_pairs", fr["n_pairs"], "n_ind", fr["n_independent"])
    print("ind_counts", fr["ind_class_counts"])
    print("wrote", FREEZE_PATH)
