"""POST-RC3-LOCAL-V1 test fixtures. No network, no Ollama, no model call."""

import json
import urllib.request

import pytest


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("real network call attempted in tests")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    yield


@pytest.fixture
def bound(monkeypatch):
    """Apply aivd_post_rc3_local.bind for one test and restore the POST-RC3 modules afterwards."""
    import aivd_post_rc3.authorize as auth
    import aivd_post_rc3.driver as drv
    import aivd_post_rc3.session as sess
    for mod, name in ((auth, "EXPERIMENT_ID"), (drv, "EXPERIMENT_ID"), (drv, "request_contract"),
                      (sess, "build_chat_request")):
        monkeypatch.setattr(mod, name, getattr(mod, name))
    from aivd_post_rc3_local.bind import bind
    bind()
    yield


class Resp:
    def __init__(self, body, status=200):
        self.status, self._b = status, body
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def fake_ollama_opener(model_fn, model_name, log):
    """Stands in for urllib.request.urlopen against 127.0.0.1:11434/api/chat."""
    def opener(req, timeout=None):
        body = json.loads(req.data)
        log.append({"url": req.full_url, "body": body})
        content = model_fn(body["messages"])
        return Resp(json.dumps({"model": model_name, "message": {"role": "assistant", "content": content},
                                "done": True, "prompt_eval_count": 5, "eval_count": 3}).encode())
    return opener
