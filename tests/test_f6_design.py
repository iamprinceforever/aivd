import json
from pathlib import Path

from aivd_f4.seal import commitment, open_seal
from aivd_f5.features import commitment as blinded_commitment
from aivd_f6.firewall import EXECUTION_AUTHORIZED, MODEL_CALLS, ExecutionRefused, dispatch
from aivd_f6.pairs import build_intervention, commitment as intervention_commitment, matched_identity_ids
from aivd_f6.preregistration import preregistration_hash
from aivd_f6.spec import (
    ANCHOR_HOLDOUT_ID,
    F4_CORPUS_COMMITMENT,
    F5_BLINDED_HASH,
    FROZEN_INTERVENTION_HASH,
    MAX_CALLS,
    PAIRED_CALLS,
)


def _contains_secret(blob: str) -> bool:
    secrets = []
    for record in open_seal():
        secrets.append(record["protected_value"])
        secrets.append(record["record_text"])
    return any(secret and secret in blob for secret in secrets)


def test_frozen_inputs_and_closed_firewall():
    assert EXECUTION_AUTHORIZED is False
    assert MODEL_CALLS == 0
    try:
        dispatch({})
    except ExecutionRefused:
        pass
    else:
        raise AssertionError("dispatch should refuse")
    assert commitment(open_seal()) == F4_CORPUS_COMMITMENT
    assert blinded_commitment() == F5_BLINDED_HASH
    assert intervention_commitment() == FROZEN_INTERVENTION_HASH
    assert len(preregistration_hash()) == 64


def test_pairs_change_only_order_and_do_not_use_outcomes():
    source = Path("aivd_f6/pairs.py").read_text(encoding="utf-8")
    assert "holdout_execution" not in source
    assert "open_seal" not in source
    assert "unblind" not in source
    intervention = build_intervention()
    assert matched_identity_ids() == ["0a4aad21faf3fbd4", "4b02919c24fc3260"]
    assert len(intervention["conditions"]) == 7
    assert len(intervention["pairs"]) == 4
    assert intervention["omitted"] == ["CF5"]
    primary = intervention["pairs"][0]
    assert primary["pair_id"] == "P1"
    assert primary["baseline_holdout_id"] == ANCHOR_HOLDOUT_ID
    assert primary["changed_field"] == "public_slot_order"
    assert primary["semantic_content_hash"]
    assert primary["left_ordering_hash"] != primary["right_ordering_hash"]
    assert PAIRED_CALLS == 14
    assert MAX_CALLS == 21
    assert _contains_secret(json.dumps(intervention)) is False


def test_documents_freeze_the_falsifier_and_contain_no_secrets():
    design = Path("aivd_f6/DESIGN.md").read_text(encoding="utf-8")
    prereg = Path("aivd_f6/PREREGISTRATION.md").read_text(encoding="utf-8")
    assert preregistration_hash() in design
    assert preregistration_hash() in prereg
    assert "F6 execution is not authorized" in design
    assert "MODEL CALLS: 0" in design
    assert "NOT SUPPORTED" in design
    assert _contains_secret(design) is False
    assert _contains_secret(prereg) is False
    for path in Path("aivd_f6").glob("*.json"):
        assert _contains_secret(path.read_text(encoding="utf-8")) is False
