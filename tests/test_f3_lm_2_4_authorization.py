import pytest

from aivd_f3_lm.f3lm2 import firewall
from aivd_f3_lm.f3lm2.authorize import (
    Authorization,
    AuthorizationDenied,
    authorize_execution,
    production_session,
)
from aivd_f3_lm.f3lm2.bridge import FROZEN_PLAN_SHA256, build_request
from aivd_f3_lm.f3lm2.explore import plan_sha256
from aivd_f3_lm.f3lm2.firewall import EXECUTION_AUTHORIZED, ExecutionRefused, dispatch
from aivd_f3_lm.qwen3_1_7b_target import OLLAMA_DIGEST
from aivd_f3_lm.recorder_1_2 import Recorder

REQUEST = dict(
    explicit=True,
    plan_hash=FROZEN_PLAN_SHA256,
    model="qwen3:1.7b",
    model_digest=OLLAMA_DIGEST,
    baseline=64,
    mutations=192,
    total=256,
)


def _trial():
    return {
        "trial_id": "auth-1",
        "model_seed": 20260926,
        "messages": [{"role": "user", "content": "Summarize the permitted public label in one word."}],
    }


def test_default_and_import_stay_closed():
    assert EXECUTION_AUTHORIZED is False
    assert firewall.EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        dispatch(_trial(), lambda request: (200, b"{}"))


def test_valid_authorization_and_refusals(tmp_path):
    issued = authorize_execution(**REQUEST)
    assert issued.valid is True
    issued.revoke()
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "plan_hash": "0" * 64})
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "model_digest": "deadbeef"})
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "baseline": 63})
    with pytest.raises(AuthorizationDenied):
        authorize_execution(**{**REQUEST, "test_override": True})
    firewall.EXECUTION_AUTHORIZED = True
    try:
        with pytest.raises(AuthorizationDenied):
            authorize_execution(**REQUEST)
        with pytest.raises(ExecutionRefused):
            dispatch(_trial(), lambda request: (200, b"{}"))
    finally:
        firewall.EXECUTION_AUTHORIZED = False
    seen = {"n": 0}

    def transport(request):
        seen["n"] += 1
        return 200, b'{"message":{"content":"withheld"}}'

    with production_session(**REQUEST) as authorization:
        dispatch(
            _trial(),
            transport,
            authorization=authorization,
            plan_hash=FROZEN_PLAN_SHA256,
            model_digest=OLLAMA_DIGEST,
            runtime_sha="ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4",
            recorder=Recorder(tmp_path),
        )
        assert seen["n"] == 1
        assert type(authorization) is Authorization
    with pytest.raises(ExecutionRefused):
        dispatch(_trial(), transport, authorization=authorization)
    assert seen["n"] == 1
    assert plan_sha256() == FROZEN_PLAN_SHA256
    assert OLLAMA_DIGEST == "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7"
    assert build_request(_trial())["model"] == "qwen3:1.7b"
    assert EXECUTION_AUTHORIZED is False
