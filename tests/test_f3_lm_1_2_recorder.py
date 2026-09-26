import json
from pathlib import Path

import pytest

from aivd_f3_lm import recorder_1_2 as rec
from aivd_f3_lm.recorder_1_2 import (
    DuplicateTrial,
    ExecutionRefused,
    PersistenceFailure,
    Recorder,
    attempt_model_execution,
    new_experiment_state,
    regression_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
META = {
    "request_id": "req-1",
    "model_digest": "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7",
    "runtime_manifest_hash": "692c71f71f721a410d74928e681db92939566c6a22055944a56533c7bc3a6b82",
    "experiment_authorization_hash": "0" * 64,
}


def _body(**extra):
    payload = {"message": {"role": "assistant", "content": "SYNTHETIC_OK"}, "done": True}
    payload.update(extra)
    return json.dumps(payload).encode()


def test_normal_output_and_missing_template_id(tmp_path):
    recorder = Recorder(tmp_path)
    normal = recorder.process("normal", 200, _body(done_reason="stop", eval_count=8), META)
    assert normal["response_text"]["value"] == "SYNTHETIC_OK"
    assert normal["template_id_status"] == "MISSING_OPTIONAL"
    regression = recorder.process("regression", 200, regression_fixture(), META)
    assert regression["parse_status"] == "OK"
    assert regression["token_count"]["value"] == 17
    assert regression["template_id_status"] == "MISSING_OPTIONAL"
    assert regression["response_text"]["value"] == "SYNTHETIC_FIXTURE_TEXT"
    assert "template_id" not in regression["behavioral_signature"]


def test_thinking_is_separate_and_zero_tokens_are_kept(tmp_path):
    recorder = Recorder(tmp_path)
    disabled = recorder.process("think0", 200, _body(thinking=0, eval_count=17), META)
    assert disabled["thinking_text"]["status"] == "PRESENT"
    assert disabled["thinking_text"]["value"] == 0
    assert disabled["response_text"]["value"] == "SYNTHETIC_OK"
    text = recorder.process(
        "thinktext",
        200,
        json.dumps({"message": {"content": "VISIBLE", "thinking": "HIDDEN"}, "done": True}).encode(),
        META,
    )
    assert text["response_text"]["value"] == "VISIBLE"
    assert text["thinking_text"]["value"] == "HIDDEN"
    assert "HIDDEN" not in text["behavioral_signature"]
    empty = recorder.process("zero", 200, _body(eval_count=0, message={"content": ""}), META)
    assert empty["token_count"]["value"] == 0
    assert empty["response_text"]["value"] == ""


def test_optional_malformed_and_extra_metadata(tmp_path):
    recorder = Recorder(tmp_path)
    missing = recorder.process("missing", 200, _body(), META)
    assert missing["done_reason"]["status"] == "MISSING_OPTIONAL"
    extra = recorder.process("extra", 200, _body(unexpected="kept"), META)
    assert extra["model_metadata"]["value"]["unexpected"] == "kept"
    assert extra["response_text"]["value"] == "SYNTHETIC_OK"
    bad = recorder.process("bad-meta", 200, _body(template_id={"not": "a string"}), META)
    assert bad["template_id_status"] == "INVALID"
    assert bad["response_text"]["value"] == "SYNTHETIC_OK"


def test_http_error_and_parser_failure_keep_raw_bytes(tmp_path):
    recorder = Recorder(tmp_path)
    error = recorder.process("http", 500, b'{"error":"synthetic"}', META)
    assert error["parse_status"] == "HTTP_ERROR"
    assert error["response_text"]["status"] == "NOT_APPLICABLE"
    assert recorder.raw_path("http").exists()
    malformed = recorder.process("malformed", 200, b"not-json", META)
    assert malformed["parse_status"] == "RAW_RESPONSE_PERSISTED_PARSE_FAILURE"
    assert recorder.raw_path("malformed").exists()

    def explode(_record):
        raise RuntimeError("parser crash")

    crashed = recorder.process("crash", 200, _body(), META, parser=explode)
    assert crashed["parse_status"] == "RAW_RESPONSE_PERSISTED_PARSE_FAILURE"
    assert recorder.raw_path("crash").exists()


def test_persistence_failure_does_not_retry(tmp_path, monkeypatch):
    recorder = Recorder(tmp_path)
    calls = {"n": 0}

    def original(path, data):
        if "raw" in str(path):
            raise OSError("disk")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    monkeypatch.setattr(rec, "atomic_write", original)
    recorder.mark_executed("once", "abc", 1)
    calls["n"] += 1
    with pytest.raises(PersistenceFailure):
        recorder.capture("once", 200, _body(), META)
    with pytest.raises(DuplicateTrial):
        recorder.submit("once", "abc", 1, lambda: calls.__setitem__("n", calls["n"] + 1))
    assert calls["n"] == 1


def test_crash_recovery_does_not_call_the_model(tmp_path):
    first = Recorder(tmp_path)
    first.capture("orphan", 200, regression_fixture(), META)
    second = Recorder(tmp_path)
    recovered = second.recover()
    assert second.model_calls == 0
    assert recovered[0]["template_id_status"] == "MISSING_OPTIONAL"
    assert recovered[0]["token_count"]["value"] == 17
    assert second.recover() == []


def test_duplicate_protection_and_closed_firewall():
    state = new_experiment_state()
    assert state["trial_count"] == 0
    assert state["security_hypotheses"] == []
    with pytest.raises(ExecutionRefused):
        attempt_model_execution()
    previous = json.loads((ROOT / "reports" / "aivd_f3_lm_1_7b_execution.json").read_text())
    assert previous["classification"] == "F3-LM QWEN3 1.7B EXPERIMENT INVALIDATED"
    assert previous["calls_completed"] == 1
    assert previous["retained_outputs"] == 0
