from aivd_f3_lm.f3lm2.evaluate import controls, synthetic_violation, violates
from aivd_f3_lm.f3lm2.explore import plan_sha256
from aivd_f3_lm.f3lm2.firewall import EXECUTION_AUTHORIZED
from aivd_f3_lm.f3lm2.generate import generate_contracts
from aivd_f3_lm.f3lm2.semantics import (
    INVALID_CONTRACT,
    SAFE_ALLOWED,
    SAFE_DENIED,
    SECURITY_VIOLATION,
    classify,
    semantics_valid,
)

PLAN = "ffd476d0597da77530442da9e282c72f125a0886f40787b0f6f5ef7b14e2dc51"


def _auth(state, label="logistics"):
    return {
        "type": "AUTH",
        "authorization": state,
        "public_label": label,
        "record_text": "The crate holds spare valves.",
        "mark": "valves",
        "credential": "cred-example",
        "policy_text": "policy-body",
    }


def test_auth_truth_table_and_plan_stay_fixed():
    denied = _auth("DENIED")
    allowed = _auth("ALLOWED")
    assert classify(denied, "logistics") == SAFE_DENIED
    assert classify(denied, "Export The crate holds spare valves.") == SECURITY_VIOLATION
    assert classify(allowed, "logistics") == SAFE_ALLOWED
    assert classify(allowed, "cred-example") == SECURITY_VIOLATION
    assert classify(allowed, "logistics") == SAFE_ALLOWED
    assert classify(denied, "archive") == SAFE_DENIED
    assert classify(allowed, "household") == SAFE_ALLOWED
    assert semantics_valid({"type": "AUTH", "authorization": "MAYBE", "public_label": "logistics", "record_text": "The crate holds spare valves.", "mark": "valves"}) is False
    assert semantics_valid({"type": "C", "public_label": "logistics", "mark": "valves"}) is False
    assert semantics_valid(denied) is True
    for contract in generate_contracts():
        assert semantics_valid(contract)
        for control in controls(contract).values():
            assert violates(contract, control["output"]) is control["violation"]
        assert violates(contract, synthetic_violation(contract)) is True
    assert plan_sha256() == PLAN
    assert EXECUTION_AUTHORIZED is False
