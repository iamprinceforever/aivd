"""Mocked end-to-end: frozen RC3 Wire -> mocked Groq HTTP -> PostRC3Session -> frozen RC3 stages
-> frozen isolated verifier. No network. Proves no stage bypass, budget accounting, retry charging,
per-model isolation, and MODEL_GENERATED_UNKNOWN_SOURCE != PROTECTED_SOURCE."""

import json

import pytest

import aivd_post_rc3.groq_client as gc
from aivd_post_rc3 import config as C
from aivd_post_rc3.corpus import draw
from aivd_post_rc3.driver import compare_repeat, run_model, run_repeat
from aivd_post_rc3.models import MODELS
from aivd_post_rc3.publish import public_ledger
from aivd_post_rc3.seeds import discovery_seed_for
from aivd_post_rc3.stop import check_no_verifier_leakage
from aivd_rc3.provider import commit, public_manifest
from aivd_rc3.verifier import judge
from aivd_rc3.wire import Wire
from tests.post_rc3.conftest import FakeGroqModel, openai_body


class Resp:
    def __init__(self, body):
        self.status, self._b = 200, body
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def make_transport(monkeypatch, model, fail_first=0):
    """Session-facing transport: Wire(frozen) wraps a Groq-adapter call over a mocked urlopen."""
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setattr(gc.time, "sleep", lambda s: None)
    state = {"n": 0}

    def fake_urlopen(req, timeout=None):
        state["n"] += 1
        if state["n"] <= fail_first:
            import io, urllib.error
            raise urllib.error.HTTPError("u", 503, "x", {}, io.BytesIO(b""))
        body = json.loads(req.data)
        return Resp(openai_body(body["model"], model(body["messages"])))
    monkeypatch.setattr(gc.urllib.request, "urlopen", fake_urlopen)

    def inner(request):
        parsed, raw, attempts = gc.chat_completion(model.model_id, request["messages"])
        inner.last = len(attempts)
        return 200, raw
    inner.last = 1
    return inner, state


def run_one(tmp_path, monkeypatch, model_id, seal, leak, fail_first=0):
    model = FakeGroqModel(model_id, leak=leak)
    inner, state = make_transport(monkeypatch, model, fail_first)
    wire = Wire(seal, inner, tmp_path / "wire" / model_id.replace("/", "_"))

    def transport(request):
        out = wire(request)
        transport.last_attempts = inner.last
        return out
    transport.last_attempts = 1
    ledger = run_model(tmp_path / model_id.replace("/", "_"), public_manifest(seal), transport,
                       model_id=model_id, corpus_commitment=commit(seal),
                       discovery_seed=discovery_seed_for(model_id))
    return ledger, state, transport


@pytest.fixture
def seal():
    return draw(b"\x07" * 32)


def test_invented_values_never_confirmed(tmp_path, monkeypatch, seal):
    ledger, state, _ = run_one(tmp_path, monkeypatch, "llama-3.3-70b-versatile", seal, leak=False)
    assert ledger["integrity_failures"] == 0, ledger["error"]
    assert ledger["calls"] <= C.MODEL_ALLOCATION
    assert ledger["stage_calls"]["discovery"] <= C.DISCOVERY_LIMIT
    assert ledger["stage_calls"]["investigation"] <= C.INVESTIGATION_LIMIT
    assert ledger["stage_calls"]["verification"] <= C.VERIFICATION_LIMIT
    assert sum(ledger["stage_calls"].values()) == ledger["calls"] == state["n"]
    scored = judge(ledger, seal)
    assert scored["false_positives_security"] == []
    assert scored["verified_targets"] == 0


def test_genuine_leak_goes_through_every_stage(tmp_path, monkeypatch, seal):
    ledger, _, _ = run_one(tmp_path, monkeypatch, "openai/gpt-oss-20b", seal, leak=True)
    assert ledger["integrity_failures"] == 0, ledger["error"]
    scored = judge(ledger, seal)
    assert scored["false_positives_security"] == []
    verified = [r for r in scored["rows"] if r["verified"]]
    assert verified, "a genuine copied value must be verified through the frozen stages"
    for r in verified:
        # every verified target passed promotion + blind CONFIRMED + frozen typed relation
        assert r["promotion"] == "VERIFICATION_READY" and r["decision"] == "CONFIRMED"
        assert "PROTECTED_SOURCE" in r["claim_provenance"]
    confirmed = [c for c in ledger["candidates"] if c.get("verification_decision") == "CONFIRMED"]
    for c in confirmed:
        assert c["promotion"] == "VERIFICATION_READY" and c.get("swap_output") is not None
    # no candidate reached verification without the promotion gate
    for c in ledger["candidates"]:
        if "verification_decision" in c:
            assert c["promotion"] == "VERIFICATION_READY"


def test_retries_are_charged_to_budget(tmp_path, monkeypatch, seal):
    ledger, state, _ = run_one(tmp_path, monkeypatch, "openai/gpt-oss-120b", seal, leak=False, fail_first=2)
    assert ledger["integrity_failures"] == 0, ledger["error"]
    assert ledger["api_attempts"] == state["n"] == ledger["calls"] + 2
    assert ledger["requests"][0]["api_attempts"] == 3


def test_model_isolation_ids_and_ledgers(tmp_path, monkeypatch, seal):
    ids = {}
    for mid in MODELS:
        ledger, _, _ = run_one(tmp_path, monkeypatch, mid, seal, leak=False)
        assert ledger["model_id"] == mid
        assert all(r["model_id"] == mid for r in ledger["requests"])
        ids[mid] = ({r["trajectory_id"] for r in ledger["requests"]},
                    {c["candidate_id"] for c in ledger["candidates"]})
    for a in MODELS:
        for b in MODELS:
            if a < b:
                assert not ids[a][0] & ids[b][0]
                assert not ids[a][1] & ids[b][1]


def test_public_ledger_has_no_sealed_values_or_verifier_fields(tmp_path, monkeypatch, seal):
    ledger, _, _ = run_one(tmp_path, monkeypatch, "openai/gpt-oss-20b", seal, leak=True)
    view = public_ledger(ledger)
    text = json.dumps(view)
    for r in seal["targets"]:
        if r["token"]:
            assert r["token"] not in text
        assert r["note"] not in text
    check_no_verifier_leakage({k: v for k, v in view.items() if k != "request_contract"})
    assert "test-only" not in text


def test_repeat_set_outside_budget_and_comparable(tmp_path, monkeypatch, seal):
    ledger, _, transport = run_one(tmp_path, monkeypatch, "llama-3.3-70b-versatile", seal, leak=False)
    rep = run_repeat(tmp_path / "rep", public_manifest(seal), transport, model_id="llama-3.3-70b-versatile",
                     corpus_commitment=commit(seal))
    assert rep["integrity_failures"] == 0, rep["error"]
    assert rep["calls"] <= C.REPRO_CALLS_PER_MODEL
    cmp = compare_repeat(ledger, rep)
    assert cmp["L2_request_first_turn"]["holds"]
    assert len(cmp["compared_scenarios"]) + len(cmp["not_explored_in_main"]) == C.REPRO_SCENARIO_COUNT
    assert cmp["L4_signature_slots"]["scenarios"] == len(cmp["compared_scenarios"])
    if cmp["compared_scenarios"]:
        assert cmp["L3_retain_explore"]["holds"] and cmp["L4_signature_slots"]["holds"]


def test_session_rejects_substituted_model_body(tmp_path, monkeypatch, seal):
    from aivd_post_rc3.stop import StopCondition
    model = FakeGroqModel("openai/gpt-oss-20b")
    def transport(request):
        return 200, openai_body("openai/gpt-oss-120b", "x")
    transport.last_attempts = 1
    ledger = run_model(tmp_path / "sub", public_manifest(seal), transport, model_id="openai/gpt-oss-20b",
                       corpus_commitment=commit(seal), discovery_seed=1)
    assert ledger["integrity_failures"] == 1 and "UNEXPECTED_MODEL_SUBSTITUTION" in ledger["error"]
