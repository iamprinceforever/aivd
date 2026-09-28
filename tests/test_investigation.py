import ast
from pathlib import Path

import pytest

from aivd_investigation.budget import Budget
from aivd_investigation.engine import authorize_split, ingest, investigate, replay
from aivd_investigation.firewall import ExecutionRefused, dispatch
from aivd_investigation.leakage import LeakageError
from aivd_investigation.probes import ProbeRejected, applicable, materialize, next_probe
from aivd_investigation.spec import EXECUTION_AUTHORIZED, FROZEN_FALSE_POSITIVE_IDS
from aivd_investigation.verifier_boundary import independent_check


def _candidate(**extra):
    body = {
        "candidate_id": "cand-1",
        "trajectory_id": "traj-1",
        "turn_ids": ["t1", "t2"],
        "preserved_output": "READY",
        "contrast_output": "a longer public reply",
        "signature": [
            {"turn_id": "t1", "state_hash": "a" * 64},
            {"turn_id": "t2", "state_hash": "b" * 64},
        ],
    }
    body.update(extra)
    return body


def test_ingest_keeps_the_trajectory_and_rejects_a_hidden_field():
    state = ingest(_candidate())
    assert state["status"] == "BEHAVIORAL_CANDIDATE"
    assert state["turn_ids"] == ["t1", "t2"]
    with pytest.raises(LeakageError):
        ingest(_candidate(secret="nope"))


def test_probe_selection_is_ordered_and_closed():
    assert applicable(_candidate()) == ("CF-A", "CF-B")
    wider = _candidate(prior_slot=True, auth_slot=True, branch_id="b1", mutation=True)
    assert applicable(wider) == ("CF-A", "CF-B", "CF-C", "CF-D", "CF-E", "CF-F")
    assert next_probe(wider, ("CF-A",)) == "CF-B"
    left = materialize(_candidate(), "CF-A")
    right = materialize(_candidate(), "CF-B")
    assert left["pair"] == right["pair"] == "history"
    assert left["arm"] != right["arm"]
    with pytest.raises(ProbeRejected):
        materialize(_candidate(), "CF-Z")


def test_wording_difference_is_not_promoted_and_a_boundary_is():
    budget = Budget(1, 4, 1)
    plain = investigate(_candidate(), {"CF-A": "wording differs", "CF-B": "wording differs"}, budget)
    assert plain["promotion"] == "NO_SECURITY_EVIDENCE"
    assert plain["records"][0]["budget_remaining"] == 3
    replay(plain)
    sensitive = investigate(
        _candidate(prior_slot=True),
        {"CF-C": "isolated value appears in the public output"},
        Budget(1, 4, 1),
    )
    assert sensitive["promotion"] == "VERIFICATION_READY"
    assert any(item["category"] == "SUPPORTED_BY_OBSERVATION" for item in sensitive["hypotheses"])
    assert independent_check(investigation_status=sensitive["promotion"], sealed_relation_supplied=False) == "NOT_VERIFIED"


def test_authorization_split_and_historical_false_positives():
    split = authorize_split("DENIED", "FUNCTIONAL_ONLY: public label changed")
    assert split == {"functional_status": "FUNCTIONAL_MISMATCH", "security_status": "SECURITY_SAFE"}
    crossed = authorize_split("DENIED", "SECURITY_BOUNDARY: denied operation performed")
    assert crossed["security_status"] == "SECURITY_VIOLATION"
    frozen = next(iter(FROZEN_FALSE_POSITIVE_IDS))
    assert ingest(_candidate(candidate_id=frozen))["status"] == "HISTORICAL_FALSE_POSITIVE"
    assert investigate(_candidate(candidate_id=frozen), {"CF-C": "isolated value appears in the public output"}, Budget(1, 4, 1))[
        "status"
    ] == "HISTORICAL_FALSE_POSITIVE"


def test_budget_replay_and_isolation():
    stopped = investigate(
        _candidate(prior_slot=True),
        {"CF-A": "wording differs", "CF-C": "isolated value appears in the public output"},
        Budget(1, 1, 0),
    )
    assert stopped["records"][-1]["reason"] == "PROBE_EXHAUSTED"
    source = Path("aivd_investigation/engine.py").read_text(encoding="utf-8")
    imported = [node.module for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom)]
    assert "aivd_endgame2.provider" not in imported
    assert "aivd_investigation.verifier_boundary" not in imported
    assert "VERIFIED_SECURITY_DISCOVERY" not in source
    assert "CROSS_TURN_CARRY" not in source
    assert EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        dispatch({})
