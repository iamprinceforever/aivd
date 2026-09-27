import json
from pathlib import Path

import pytest

from aivd_f4.preregistration import preregistration_hash as f4_preregistration_hash
from aivd_f4.seal import commitment, open_seal
from aivd_f5.analyze import CLASSES, unblind
from aivd_f5.features import SCHEMA, blinded_rows, commitment as blinded_commitment
from aivd_f5.firewall import EXECUTION_AUTHORIZED, ExecutionRefused, dispatch
from aivd_f5.metadata import commitment as metadata_commitment
from aivd_f5.preregistration import preregistration_hash
from aivd_f5.spec import (
    COUNTERFACTUALS,
    F4_CORPUS_COMMITMENT,
    F4_PREREGISTRATION,
    FROZEN_BLINDED_HASH,
    FROZEN_METADATA_HASH,
    FUTURE_MAX_CALLS,
    SUCCESS_HOLDOUT_ID,
)


def _sealed_strings() -> list:
    values = []
    for record in open_seal():
        values.append(record["protected_value"])
        values.append(record["record_text"])
    return values


def _contains_secret(blob: str) -> bool:
    return any(secret and secret in blob for secret in _sealed_strings())


def test_f4_commitments_and_firewall_stay_closed():
    assert EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        dispatch({})
    assert commitment(open_seal()) == F4_CORPUS_COMMITMENT
    assert f4_preregistration_hash() == F4_PREREGISTRATION
    assert blinded_commitment() == FROZEN_BLINDED_HASH
    assert metadata_commitment() == FROZEN_METADATA_HASH
    assert len(preregistration_hash()) == 64


def test_blinded_table_has_no_outcome_and_matches_schema():
    rows = blinded_rows()
    assert len(rows) == 24
    assert {row["class"] for row in rows} == {"A", "B", "C"}
    for row in rows:
        assert tuple(row) == SCHEMA
        assert "outcome" not in row
        assert "protected_value" not in row
    encoded = json.dumps(rows)
    assert "REPRODUCED_DISCLOSURE" not in encoded
    assert SUCCESS_HOLDOUT_ID in {row["holdout_id"] for row in rows}
    assert _contains_secret(encoded) is False


def test_unblinding_is_one_reproduced_class_c_contract():
    report = unblind()
    hits = [row for row in report["rows"] if row["outcome"] == "REPRODUCED_DISCLOSURE"]
    assert len(hits) == 1
    assert hits[0]["holdout_id"] == SUCCESS_HOLDOUT_ID
    assert hits[0]["transformation"] == "reorder_first_two"
    assert {item["classification"] for item in report["hypotheses"]} <= set(CLASSES)
    assert any(item["id"] == "H2" and item["classification"] == "UNIDENTIFIABLE_WITH_N1" for item in report["hypotheses"])
    assert _contains_secret(json.dumps(report)) is False


def test_counterfactuals_change_one_factor_and_are_not_authorized():
    assert len(COUNTERFACTUALS) == 6
    assert FUTURE_MAX_CALLS == 18
    for item in COUNTERFACTUALS:
        assert item["authorized"] is False
        assert len(item["change"]) == 1
        factor = next(iter(item["change"]))
        assert factor == item["factor"]
        assert factor not in item["held_fixed"]
        assert "sealed_value" in item["held_fixed"]


def test_design_document_does_not_contain_sealed_plaintext():
    text = Path("aivd_f5/DESIGN.md").read_text(encoding="utf-8")
    assert preregistration_hash() in text
    assert "F5 DESIGN ONLY" in text
    assert "F6 NOT STARTED" in text
    assert _contains_secret(text) is False
    for path in Path("aivd_f5").glob("*.json"):
        assert _contains_secret(path.read_text(encoding="utf-8")) is False
