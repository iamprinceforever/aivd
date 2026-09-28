"""POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE — test fixtures (no network)."""

import json
import re

import pytest

from aivd_rc3.provenance import swap
from aivd_rc3.provider import STEP_MARK, CTX_MARK


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Any real network attempt from the Groq adapter fails the test."""
    import aivd_post_rc3.groq_client as gc

    def boom(*a, **k):
        raise AssertionError("real network call attempted in tests")
    monkeypatch.setattr(gc.urllib.request, "urlopen", boom)
    yield


class FakeGroqModel:
    """Deterministic stand-in for a hosted model. Behaviour:
      - copies a 16-hex token from an injected system note when `leak` is True and the user
        turn asks for a repeat/summary/export (a real leak -> tracks the swap under condition B);
      - otherwise answers generically (an invented "key" if asked for one)."""

    def __init__(self, model_id, leak=False):
        self.model_id = model_id
        self.leak = leak
        self.calls = 0

    def __call__(self, messages):
        self.calls += 1
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        last = messages[-1]["content"]
        m = re.search(r"\b[0-9a-z]{16}\b", system)
        if self.leak and m and len(messages) > 2:
            return f"Here it is: {m.group(0)}."
        if "sample key" in last:
            return "Sample key: zz9plural0alpha7."
        return f"OK ({len(messages)})."


def openai_body(model_id, content):
    return json.dumps({"id": "x", "object": "chat.completion", "model": model_id,
                       "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                                    "finish_reason": "stop"}],
                       "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}}).encode()
