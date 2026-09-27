import pytest

from aivd_f3_lm.f3lm2.authorize import authorize_execution as authorize_f3
from aivd_f3_lm.f3lm2.bridge import FROZEN_PLAN_SHA256
from aivd_f3_lm.f3lm2.firewall import ExecutionRefused as F3Refused
from aivd_f3_lm.f3lm2.firewall import dispatch as dispatch_f3
from aivd_f3_lm.qwen3_1_7b_target import OLLAMA_DIGEST
from aivd_f6 import firewall
from aivd_f6.authorize import (
    ALLOCATION,
    EXPERIMENT_ID,
    AuthorizationDenied,
    authorize_execution,
    execution_plan_commitment,
    production_session,
)
from aivd_f6.firewall import EXECUTION_AUTHORIZED, ExecutionRefused, dispatch
from aivd_f6.spec import CONDITIONS, FROZEN_INTERVENTION_HASH, MAX_CALLS, PAIRED_CALLS

REQUEST = dict(
    explicit=True,
    experiment_id=EXPERIMENT_ID,
    preregistration="1cb07df37fe82d1924d19398b234587256169fc323ec629100c5310d096c81f9",
    intervention=FROZEN_INTERVENTION_HASH,
    model="qwen3:1.7b",
    model_digest=OLLAMA_DIGEST,
    runtime_version="0.34.4",
    runtime_commit="b2da9e468af2479058ae18c6d908ed29de410684",
    runtime_digest="ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4",
    conditions=CONDITIONS,
    paired_calls=PAIRED_CALLS,
    max_calls=MAX_CALLS,
)
F3_REQUEST = dict(
    explicit=True,
    plan_hash=FROZEN_PLAN_SHA256,
    model="qwen3:1.7b",
    model_digest=OLLAMA_DIGEST,
    baseline=64,
    mutations=192,
    total=256,
)


def _fake(box):
    def transport(trial):
        box["n"] += 1
        return {"status": "held"}

    return transport


def test_01_no_request_rejects_dispatch():
    with pytest.raises(ExecutionRefused):
        dispatch({"condition_id": "none"})


def test_02_f3_plan_with_f6_id_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "preregistration": FROZEN_PLAN_SHA256})


def test_03_f6_plan_with_f3_id_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "experiment_id": "F3-LM-2"})


def test_04_modified_preregistration_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "preregistration": "0" * 64})


def test_05_modified_intervention_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "intervention": "1" * 64})


def test_06_modified_model_digest_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "model_digest": "2" * 64})


def test_07_modified_runtime_digest_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "runtime_digest": "3" * 64})


def test_08_modified_allocation_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "max_calls": MAX_CALLS + 1})


def test_09_wrong_model_identity_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "model": "qwen3:8b"})


def test_10_wrong_runtime_identity_is_rejected():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "runtime_version": "0.0.0"})


def test_11_f3_token_cannot_dispatch_f6():
    issued = authorize_f3(**F3_REQUEST)
    try:
        with pytest.raises(ExecutionRefused):
            dispatch({"condition_id": "f6"}, _fake({"n": 0}), authorization=issued)
    finally:
        issued.revoke()


def test_12_f6_token_cannot_dispatch_f3():
    issued = authorize_execution(**REQUEST)
    try:
        with pytest.raises(F3Refused):
            dispatch_f3(
                {"trial_id": "cross", "model_seed": 1, "messages": []},
                lambda request: (_ for _ in ()).throw(AssertionError("f3 transport called")),
                authorization=issued,
            )
    finally:
        issued.revoke()


def test_13_test_override_cannot_authorize():
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "test_override": True})
    with pytest.raises(ExecutionRefused):
        dispatch({"condition_id": "override"})


def test_14_import_does_not_authorize():
    assert firewall.EXECUTION_AUTHORIZED is False
    assert EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        dispatch({"condition_id": "import"})


def test_15_firewall_flag_does_not_authorize():
    firewall.EXECUTION_AUTHORIZED = True
    try:
        with pytest.raises(ExecutionRefused):
            dispatch({"condition_id": "flag"}, _fake({"n": 0}))
        with pytest.raises(AuthorizationDenied):
            authorize_execution(**REQUEST)
    finally:
        firewall.EXECUTION_AUTHORIZED = False


def test_16_valid_token_permits_only_the_f6_path():
    box = {"n": 0}
    issued = authorize_execution(**REQUEST)
    try:
        assert issued.experiment_id == "F6"
        assert issued.allocation == ALLOCATION
        result = dispatch({"condition_id": "40eebcd450359f23:O1"}, _fake(box), authorization=issued)
        assert result["status"] == "held"
        assert box["n"] == 1
    finally:
        issued.revoke()


def test_17_revoked_token_cannot_dispatch_again():
    box = {"n": 0}
    issued = authorize_execution(**REQUEST)
    issued.revoke()
    with pytest.raises(ExecutionRefused):
        dispatch({"condition_id": "again"}, _fake(box), authorization=issued)
    assert box["n"] == 0


def test_18_abort_revokes_the_token():
    box = {"n": 0}
    held = {}
    with pytest.raises(RuntimeError):
        with production_session(**REQUEST) as issued:
            held["token"] = issued
            dispatch({"condition_id": "before-abort"}, _fake(box), authorization=issued)
            raise RuntimeError("abort")
    assert box["n"] == 1
    with pytest.raises(ExecutionRefused):
        dispatch({"condition_id": "after-abort"}, _fake(box), authorization=held["token"])
    assert box["n"] == 1


def test_19_intervention_change_after_issue_is_rejected(monkeypatch):
    issued = authorize_execution(**REQUEST)
    monkeypatch.setattr("aivd_f6.pairs.commitment", lambda: "4" * 64)
    try:
        with pytest.raises(ExecutionRefused):
            dispatch({"condition_id": "drift"}, _fake({"n": 0}), authorization=issued)
    finally:
        issued.revoke()


def test_20_plan_change_after_issue_is_rejected(monkeypatch):
    issued = authorize_execution(**REQUEST)
    monkeypatch.setattr("aivd_f6.authorize.execution_plan_commitment", lambda: "5" * 64)
    try:
        with pytest.raises(ExecutionRefused):
            dispatch({"condition_id": "plan-drift"}, _fake({"n": 0}), authorization=issued)
    finally:
        issued.revoke()


def test_plan_commitment_is_stable_and_not_the_f3_plan():
    assert execution_plan_commitment() != FROZEN_PLAN_SHA256
    assert len(execution_plan_commitment()) == 64
