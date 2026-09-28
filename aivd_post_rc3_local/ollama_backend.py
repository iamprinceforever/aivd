"""Local Ollama /api/chat backend for POST-RC3-LOCAL-V1 (evaluation code).

Importing this module makes NO request. `make_inner` returns a callable; a request is sent only
when that callable is invoked by an authorized run (scripts/local_v1_run_all.sh). No remote
API, no API key, no retries. Only 127.0.0.1 is accepted as the endpoint.
"""

from __future__ import annotations

import json
import urllib.request
from hashlib import sha256
from urllib.parse import urlparse

from aivd_post_rc3_local import config as C
from aivd_post_rc3_local.models import MODELS, RUNTIME, THINKING_MODELS


class LocalModelRefused(Exception):
    pass


def build_request(model_id: str, messages: list) -> dict:
    if model_id not in MODELS:
        raise LocalModelRefused(f"UNEXPECTED_MODEL_SUBSTITUTION: {model_id!r}")
    body = {"model": model_id, "messages": messages, "stream": C.STREAM,
            "options": dict(C.COMMON_OPTIONS)}
    if model_id in THINKING_MODELS:
        body["think"] = C.THINK
    return body


def request_contract() -> dict:
    return {
        "provider": RUNTIME["provider"],
        "remote_api": RUNTIME["remote_api"],
        "engine": RUNTIME["engine"],
        "version": RUNTIME["version"],
        "base_url": RUNTIME["base_url"],
        "chat_path": RUNTIME["chat_path"],
        "stream": C.STREAM,
        "options": dict(C.COMMON_OPTIONS),
        "think": {m: C.THINK for m in sorted(THINKING_MODELS)},
        "omissions": {m: list(v) for m, v in C.PER_MODEL_OMISSIONS.items()},
        "retries": C.MAX_TRANSPORT_ATTEMPTS - 1,
        "models": list(MODELS),
    }


def _check_local(url: str) -> None:
    host = urlparse(url).hostname
    if host not in ("127.0.0.1", "localhost"):
        raise LocalModelRefused(f"REMOTE_ENDPOINT_REFUSED: {host!r}")


def make_inner(model_id: str, base_url: str = RUNTIME["base_url"], opener=None):
    """Wire-facing inner transport: request dict (with messages) -> (status, bytes)."""
    if model_id not in MODELS:
        raise LocalModelRefused(f"UNEXPECTED_MODEL_SUBSTITUTION: {model_id!r}")
    url = base_url.rstrip("/") + RUNTIME["chat_path"]
    _check_local(url)
    open_fn = opener or urllib.request.urlopen

    def inner(request: dict):
        body = build_request(model_id, request["messages"])
        raw_req = json.dumps(body, sort_keys=True).encode()
        call = urllib.request.Request(url, data=raw_req, headers={"Content-Type": "application/json"},
                                      method="POST")
        try:
            with open_fn(call, timeout=C.TRANSPORT_TIMEOUT_SECONDS) as resp:
                status, raw = resp.status, resp.read()
        except Exception:
            inner.last_attempts = 1
            return 502, b""
        inner.last_attempts = 1
        try:
            parsed = json.loads(raw)
            content = parsed["message"]["content"]
            returned = parsed.get("model", "")
        except Exception:
            return 502, b""
        if returned != model_id:
            raise LocalModelRefused(f"UNEXPECTED_MODEL_SUBSTITUTION: requested={model_id!r} got={returned!r}")
        shaped = {"model": returned, "message": {"role": "assistant", "content": content},
                  "usage": {k: parsed[k] for k in ("prompt_eval_count", "eval_count") if k in parsed},
                  "ollama_raw_sha256": sha256(raw).hexdigest()}
        return status, json.dumps(shaped).encode()

    inner.last_attempts = 1
    return inner
