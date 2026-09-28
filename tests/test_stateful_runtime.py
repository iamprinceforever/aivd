import json
from pathlib import Path

import pytest

from aivd_stateful.authorize import AuthorizationRefused, authorize_execution, close_session, open_session, plan_commitment, session_open
from aivd_stateful.behaviors import corpus_commitment, public_manifest, seal_document
from aivd_stateful.contract import HOLDOUT_CALLS, MODEL_SEED, NUM_CTX, OLLAMA_DIGEST, SMOKE_CALLS, TEMPERATURE
from aivd_stateful.discover import run
from aivd_stateful.evaluate import evaluate, ledger_hash
from aivd_stateful.model import Budget, Config
from aivd_stateful.session import Session, SessionRefused
from aivd_stateful.smoke import run_smoke
from aivd_f3_lm.qwen3_1_7b_target import NUM_CTX as FROZEN_CTX
from aivd_f3_lm.qwen3_1_7b_target import TEMPERATURE as FROZEN_TEMPERATURE


def _fake(request):
    messages = request["messages"]
    prior = "\n".join(item["content"] for item in messages[:-1])
    last = messages[-1]["content"]
    if "KITE-5520" in prior:
        text = "KITE-5520"
    elif "warehouse badge" in last:
        text = "READY"
    elif "VIOLET" in prior:
        text = "VIOLET"
    elif "VIOLET" in last:
        text = "READY"
    elif "ROW:" in prior:
        text = "ROW: hello"
    elif last.startswith("Say hello"):
        text = "hello"
    elif "moth" in prior and "tool" in last:
        text = "moth"
    elif "carp" in prior and "tool" in last:
        text = "carp"
    elif "bench" in last:
        text = "READY"
    elif "PLUM-8831" in prior:
        text = "PLUM-8831"
    elif "badge code" in last:
        text = "READY"
    elif "elm" in prior:
        text = "elm"
    elif "yew" in prior:
        text = "yew"
    elif "note" in last:
        text = "READY"
    else:
        text = "READY"
    return 200, json.dumps({"message": {"content": text}}).encode()


def _open(tmp_path):
    token = authorize_execution(
        explicit=True,
        experiment_id="STATEFUL-1",
        plan_hash=plan_commitment(corpus_commitment()),
        corpus_commitment=corpus_commitment(),
    )
    open_session(token)
    session = Session(tmp_path, _fake, Budget(limit=HOLDOUT_CALLS))
    return session


def test_pinned_sampling_matches_the_1_7b_target():
    assert NUM_CTX == FROZEN_CTX == 4096
    assert TEMPERATURE == FROZEN_TEMPERATURE == 0.0
    assert OLLAMA_DIGEST.startswith("8f68893c")
    assert MODEL_SEED == 20260926


def test_authorization_is_fail_closed(tmp_path):
    assert session_open() is False
    with pytest.raises(AuthorizationRefused):
        authorize_execution(explicit=False, experiment_id="STATEFUL-1", plan_hash="x", corpus_commitment="y")
    with pytest.raises(AuthorizationRefused):
        authorize_execution(explicit=True, experiment_id="F6", plan_hash=plan_commitment(corpus_commitment()), corpus_commitment=corpus_commitment())
    session = Session(tmp_path, _fake, Budget(limit=1))
    with pytest.raises(SessionRefused):
        session.execute(None, "x", "continue", "closed")
    _open(tmp_path)
    assert session_open() is True
    close_session()
    assert session_open() is False


def test_smoke_continuation_reset_and_branch(tmp_path):
    session = _open(tmp_path)
    session.budget = Budget(limit=SMOKE_CALLS)
    result = run_smoke(session)
    close_session()
    assert result["checks"]["pass"] is True
    assert result["calls"] == 7


def test_blind_holdout_retains_trajectory_signatures(tmp_path):
    source = Path("aivd_stateful/discover.py").read_text(encoding="utf-8")
    for label in ("PERSISTED_FACT", "PERSISTED_INSTRUCTION", "PERSISTED_FORMAT", "BRANCH_SPLIT", "KITE-5520"):
        assert label not in source
    session = _open(tmp_path / "holdout")
    ledger = run(public_manifest(), session)
    close_session()
    assert session.calls == 17
    assert len(ledger["retained"]) == 4
    assert len(ledger["verified"]) == 4
    assert ledger["retained"][0]["signature"]
    body = dict(ledger)
    body["frozen_hash"] = ledger_hash(body)
    scored = evaluate(body, seal_document(), corpus_commitment())
    assert scored["discovered_count"] == 4
    assert scored["false_positives"] == []


def test_equal_outputs_are_not_retained(tmp_path):
    def constant(_request):
        return 200, json.dumps({"message": {"content": "SAME"}}).encode()

    token = authorize_execution(
        explicit=True,
        experiment_id="STATEFUL-1",
        plan_hash=plan_commitment(corpus_commitment()),
        corpus_commitment=corpus_commitment(),
    )
    open_session(token)
    session = Session(tmp_path, constant, Budget(limit=HOLDOUT_CALLS))
    ledger = run(public_manifest(), session)
    close_session()
    assert ledger["retained"] == []
    assert ledger["verified"] == []
    assert set(ledger["rejected"]) == {item["scenario_id"] for item in public_manifest()}
