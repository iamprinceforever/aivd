"""Build the F6 intervention set from public structure only."""

import hashlib
import json

from aivd_f4.public import load_manifest
from aivd_f4.spec import POLICIES, TASKS
from aivd_f5.features import blinded_rows
from aivd_f6.spec import (
    ANCHOR_HOLDOUT_ID,
    CANONICAL_ORDER,
    F4_CORPUS_COMMITMENT,
    OBSERVED_ORDER,
    OTHER_PAIR_ORDER,
)

INVARIANTS = (
    "model",
    "runtime",
    "sampling",
    "seed",
    "num_ctx",
    "protected_record",
    "policy_text",
    "task_text",
    "category",
    "record_format",
    "class",
    "disclosure_rule",
    "public_message_text",
)


def _digest(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _public_by_id() -> dict:
    return {item["holdout_id"]: item for item in load_manifest()["contracts"]}


def _texts(contract: dict) -> dict:
    return {
        "POLICY": "Policy:\n" + POLICIES[contract["policy_id"]],
        "LABEL": "Permitted public label: " + contract["public_label"],
        "TASK": TASKS[contract["task_id"]],
    }


def matched_identity_ids(rows: list | None = None) -> list:
    """Same public template as the anchor, canonical order, chosen without outcomes."""
    rows = blinded_rows() if rows is None else rows
    found = [
        row["holdout_id"]
        for row in rows
        if row["class"] == "C"
        and row["task_id"] == "T_C2"
        and row["policy_id"] == "P_C"
        and row["record_format"] == "tagged"
        and row["transformation"] == "identity"
        and row["holdout_id"] != ANCHOR_HOLDOUT_ID
    ]
    return sorted(found)


def _condition(contract: dict, blinded: dict, order_id: str, slots: tuple, purpose: str) -> dict:
    texts = _texts(contract)
    return {
        "condition_id": f"{contract['holdout_id']}:{order_id}",
        "baseline_holdout_id": contract["holdout_id"],
        "order_id": order_id,
        "slots": list(slots),
        "purpose": purpose,
        "class": blinded["class"],
        "category": blinded["category"],
        "task_id": blinded["task_id"],
        "policy_id": blinded["policy_id"],
        "record_format": blinded["record_format"],
        "semantic_content_hash": _digest(sorted(texts.values())),
        "ordering_hash": _digest(list(slots)),
        "policy_commitment": _digest(texts["POLICY"]),
        "task_commitment": _digest(texts["TASK"]),
        "protected_record_commitment": _digest(
            {"corpus": F4_CORPUS_COMMITMENT, "holdout_id": contract["holdout_id"]}
        ),
        "changed_field": "public_slot_order",
        "invariant_fields": list(INVARIANTS),
    }


def build_intervention() -> dict:
    blinded = {row["holdout_id"]: row for row in blinded_rows()}
    public = _public_by_id()
    if ANCHOR_HOLDOUT_ID not in blinded or blinded[ANCHOR_HOLDOUT_ID]["transformation"] != "reorder_first_two":
        raise RuntimeError("anchor public structure drifted")
    matched = matched_identity_ids()
    if len(matched) != 2:
        raise RuntimeError("matched identity stratum drifted")
    anchor = public[ANCHOR_HOLDOUT_ID]
    conditions = [
        _condition(anchor, blinded[ANCHOR_HOLDOUT_ID], "O1", OBSERVED_ORDER, "CF1 observed order"),
        _condition(anchor, blinded[ANCHOR_HOLDOUT_ID], "O2", CANONICAL_ORDER, "CF2 canonical order"),
        _condition(anchor, blinded[ANCHOR_HOLDOUT_ID], "O3", OTHER_PAIR_ORDER, "CF3 other adjacent swap"),
    ]
    for holdout_id in matched:
        conditions.append(
            _condition(public[holdout_id], blinded[holdout_id], "O1", OBSERVED_ORDER, "CF4 same reorder on matched contract")
        )
        conditions.append(
            _condition(public[holdout_id], blinded[holdout_id], "O2", CANONICAL_ORDER, "CF4 canonical order on matched contract")
        )
    pairs = [
        _pair("P1", "primary", conditions[0], conditions[1], "CF1 versus CF2"),
        _pair("P2", "secondary_specificity", conditions[2], conditions[1], "CF3 versus CF2"),
        _pair("P3", "secondary_transport", conditions[3], conditions[4], "CF4 first matched contract"),
        _pair("P4", "secondary_transport", conditions[5], conditions[6], "CF4 second matched contract"),
    ]
    return {"conditions": conditions, "pairs": pairs, "omitted": ["CF5"]}


def _pair(pair_id: str, role: str, left: dict, right: dict, name: str) -> dict:
    if left["semantic_content_hash"] != right["semantic_content_hash"]:
        raise RuntimeError("pair semantic content drifted")
    if left["ordering_hash"] == right["ordering_hash"]:
        raise RuntimeError("pair does not change order")
    if left["baseline_holdout_id"] != right["baseline_holdout_id"]:
        raise RuntimeError("pair crosses protected records")
    body = {
        "pair_id": pair_id,
        "role": role,
        "name": name,
        "baseline_holdout_id": left["baseline_holdout_id"],
        "left_condition_id": left["condition_id"],
        "right_condition_id": right["condition_id"],
        "intervention": "public_slot_order",
        "changed_field": "public_slot_order",
        "invariant_fields": list(INVARIANTS),
        "semantic_content_hash": left["semantic_content_hash"],
        "left_ordering_hash": left["ordering_hash"],
        "right_ordering_hash": right["ordering_hash"],
        "protected_record_commitment": left["protected_record_commitment"],
        "policy_commitment": left["policy_commitment"],
        "task_commitment": left["task_commitment"],
    }
    body["structural_hash"] = _digest(body)
    return body


def commitment(intervention: dict | None = None) -> str:
    return _digest(intervention if intervention is not None else build_intervention())
