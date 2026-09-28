"""Groq adapter with a mocked HTTP layer: request shape, model check, retry accounting, key hygiene."""

import io
import json
import urllib.error

import pytest

import aivd_post_rc3.groq_client as gc
from aivd_post_rc3 import config as C
from aivd_post_rc3.models import MODELS
from aivd_post_rc3.stop import StopCondition
from tests.post_rc3.conftest import openai_body


class Resp:
    def __init__(self, status, body):
        self.status, self._b = status, body
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def install(monkeypatch, responder, key="test-key-value"):
    monkeypatch.setenv("GROQ_API_KEY", key)
    seen = []
    def fake(req, timeout=None):
        seen.append(req)
        return responder(req, len(seen))
    monkeypatch.setattr(gc.urllib.request, "urlopen", fake)
    monkeypatch.setattr(gc.time, "sleep", lambda s: None)
    return seen


def test_shared_request_shape_same_for_all_models():
    msgs = [{"role": "user", "content": "hi"}]
    bodies = {m: gc.build_chat_request(m, msgs) for m in MODELS}
    for m, b in bodies.items():
        assert b["model"] == m and b["messages"] == msgs
        assert b["temperature"] == 0.0 and b["max_completion_tokens"] == 256
        assert b["top_p"] == 1.0 and b["seed"] == 20260926 and b["stream"] is False
    # only provider-mandated differences
    assert bodies["openai/gpt-oss-20b"]["reasoning_effort"] == "low"
    assert bodies["openai/gpt-oss-120b"]["include_reasoning"] is False
    assert "reasoning_effort" not in bodies["llama-3.3-70b-versatile"]
    assert "include_reasoning" not in bodies["llama-3.3-70b-versatile"]
    shared = lambda b: {k: v for k, v in b.items() if k not in ("model", "reasoning_effort", "include_reasoning")}
    assert len({json.dumps(shared(b), sort_keys=True) for b in bodies.values()}) == 1


def test_unknown_model_halts():
    with pytest.raises(StopCondition):
        gc.build_chat_request("llama-3.1-8b-instant", [])


def test_successful_call_and_url_and_auth(monkeypatch):
    seen = install(monkeypatch, lambda req, n: Resp(200, openai_body("openai/gpt-oss-20b", "hello")))
    parsed, raw, attempts = gc.chat_completion("openai/gpt-oss-20b", [{"role": "user", "content": "x"}])
    assert parsed["choices"][0]["message"]["content"] == "hello"
    assert len(attempts) == 1 and attempts[0]["status"] == 200
    req = seen[0]
    assert req.full_url == "https://api.groq.com/openai/v1/chat/completions"
    assert req.get_header("Authorization") == "Bearer test-key-value"
    # attempt log never contains the key
    assert "test-key-value" not in json.dumps(attempts)


def test_model_substitution_halts(monkeypatch):
    install(monkeypatch, lambda req, n: Resp(200, openai_body("llama-3.1-8b-instant", "x")))
    with pytest.raises(StopCondition) as exc:
        gc.chat_completion("llama-3.3-70b-versatile", [{"role": "user", "content": "x"}])
    assert "UNEXPECTED_MODEL_SUBSTITUTION" in str(exc.value)


def _http_error(code):
    return urllib.error.HTTPError("u", code, "err", {}, io.BytesIO(b"{}"))


def test_retry_on_429_then_success_counts_every_attempt(monkeypatch):
    def responder(req, n):
        if n < 3:
            raise _http_error(429)
        return Resp(200, openai_body("openai/gpt-oss-120b", "ok"))
    install(monkeypatch, responder)
    reported = []
    parsed, raw, attempts = gc.chat_completion("openai/gpt-oss-120b", [{"role": "user", "content": "x"}],
                                               on_attempt=reported.append)
    assert len(attempts) == 3 == len(reported) == C.MAX_TRANSPORT_ATTEMPTS


def test_retry_exhaustion_raises(monkeypatch):
    install(monkeypatch, lambda req, n: (_ for _ in ()).throw(_http_error(503)))
    with pytest.raises(gc.GroqTransportError):
        gc.chat_completion("openai/gpt-oss-20b", [{"role": "user", "content": "x"}])


def test_non_retryable_status_single_attempt(monkeypatch):
    calls = install(monkeypatch, lambda req, n: (_ for _ in ()).throw(_http_error(401)))
    with pytest.raises(gc.GroqTransportError):
        gc.chat_completion("openai/gpt-oss-20b", [{"role": "user", "content": "x"}])
    assert len(calls) == 1


def test_missing_key_halts(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(StopCondition) as exc:
        gc.chat_completion("openai/gpt-oss-20b", [{"role": "user", "content": "x"}])
    assert "AUTHORIZATION_FAILURE" in str(exc.value)


def test_preflight_models_active_logic():
    listing = {"data": [{"id": "openai/gpt-oss-20b", "active": True},
                        {"id": "openai/gpt-oss-120b", "active": False}]}
    out = gc.preflight_models_active(listing)
    assert out["openai/gpt-oss-20b"] == {"listed": True, "active": True}
    assert out["openai/gpt-oss-120b"]["active"] is False
    assert out["llama-3.3-70b-versatile"]["listed"] is False


def test_list_models_uses_get_models(monkeypatch):
    seen = install(monkeypatch, lambda req, n: Resp(200, json.dumps({"data": []}).encode()))
    gc.list_models()
    assert seen[0].full_url == "https://api.groq.com/openai/v1/models" and seen[0].get_method() == "GET"


def test_preflight_script_without_models_check_makes_no_call(monkeypatch, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location("post_rc3_preflight", "scripts/post_rc3_preflight.py")
    pf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pf)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["x"])
    pf.main()
    out = json.loads(capsys.readouterr().out)
    assert out["GROQ_API_KEY_PRESENT"] is False and "models_check" not in out
