"""Frozen contract generator. Order is an opaque id hash, not a dimension priority."""

import hashlib

from aivd_f3_lm.relations import POLICY_TEXT

from aivd_f3_lm.f3lm2.contracts import (
    BRANCH_ASIDES,
    CONTRACT_COUNT,
    DIMENSIONS,
    DISCOVERY_SEED,
    RECORDS,
    TYPE_DIMENSION,
    TYPES,
)


def _order_key(token: str) -> str:
    return hashlib.sha256(f"{DISCOVERY_SEED}|{token}".encode()).hexdigest()


def _shuffled(items: tuple) -> tuple:
    return tuple(sorted(items, key=_order_key))


def generate_contracts() -> list:
    type_order = _shuffled(TYPES)
    contracts = []
    auth_count = 0
    for index in range(CONTRACT_COUNT):
        kind = type_order[index % len(type_order)]
        record = RECORDS[index % len(RECORDS)]
        contract_id = hashlib.sha256(f"{DISCOVERY_SEED}|{index}|{kind}".encode()).hexdigest()[:16]
        authorization = None
        credential = None
        if kind == "AUTH":
            authorization = "DENIED" if auth_count % 2 else "ALLOWED"
            credential = "cred-" + contract_id[:8]
            auth_count += 1
        contracts.append(
            {
                "contract_id": contract_id,
                "type": kind,
                "dimension": TYPE_DIMENSION[kind],
                "record_text": record["text"],
                "mark": record["mark"],
                "public_label": record["label"],
                "authorization": authorization,
                "credential": credential,
                "isolated_aside": BRANCH_ASIDES[1] if kind == "STATE" else None,
                "policy_text": POLICY_TEXT,
                "expected_failure": None,
            }
        )
    contracts.sort(key=lambda item: _order_key(item["contract_id"]))
    if [item["dimension"] for item in contracts] == list(DIMENSIONS):
        raise RuntimeError("dimension order matches a hand-built priority list")
    return contracts
