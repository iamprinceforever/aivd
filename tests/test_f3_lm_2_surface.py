import json
from pathlib import Path

import pytest

from aivd_f3_lm.grammar import OPERATORS
from aivd_f3_lm.f3lm2.contracts import CONTRACT_COUNT, FORBIDDEN_ASKS, TRIAL_BUDGET
from aivd_f3_lm.f3lm2.evaluate import controls, synthetic_violation, violates
from aivd_f3_lm.f3lm2.explore import build_plan, plan_sha256
from aivd_f3_lm.f3lm2.firewall import ExecutionRefused, dispatch
from aivd_f3_lm.f3lm2.generate import generate_contracts

ROOT = Path(__file__).resolve().parents[1]


def test_plan_is_a_closed_surface_and_the_firewall_stays_shut():
    contracts = generate_contracts()
    assert len(contracts) == CONTRACT_COUNT
    assert len({item["type"] for item in contracts}) == 6
    assert all(item["expected_failure"] is None for item in contracts)
    assert contracts != sorted(contracts, key=lambda item: item["dimension"])
    plan = build_plan()
    assert len(plan) == TRIAL_BUDGET
    assert len({item["trial_id"] for item in plan}) == TRIAL_BUDGET
    assert not any(item["trial_id"].startswith("PIPELINE") for item in plan)
    assert {item["operator"] for item in plan if item["operator"]} == set(OPERATORS)
    report = json.loads((ROOT / "reports" / "aivd_f3_lm_2_implementation.json").read_text())
    assert report["plan_sha256"] == plan_sha256()
    assert report["execution_authorized"] is False
    for item in plan:
        public = "\n".join(message["content"] for message in item["messages"] if message["role"] != "system")
        assert not any(phrase in public.lower() for phrase in FORBIDDEN_ASKS)
    with pytest.raises(ExecutionRefused):
        dispatch(plan[0], lambda trial: trial)


def test_checker_separates_novelty_from_a_boundary_and_leaves_history_frozen():
    contract = next(item for item in generate_contracts() if item["type"] == "C")
    denied = next(item for item in generate_contracts() if item["authorization"] == "DENIED")
    assert violates(contract, contract["public_label"]) is False
    assert violates(contract, synthetic_violation(contract)) is True
    for name, control in controls(contract).items():
        assert violates(contract, control["output"]) is control["violation"]
    assert violates(denied, "withheld") is False
    assert violates(denied, denied["public_label"]) is False
    assert violates(denied, denied["credential"]) is True
    frozen = json.loads((ROOT / "reports" / "aivd_f3_lm_1_4_execution.json").read_text())
    assert frozen["model_calls"] == 27
