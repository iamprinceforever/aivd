"""Groq OpenAI-compatible chat-completions adapter.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Reads GROQ_API_KEY only from the environment at call time. Never prints, logs,
echoes or persists the key. Every HTTP attempt (including retries) is reported
to the caller so the driver can charge one budget unit per attempt.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from hashlib import sha256
from typing import Callable

from aivd_post_rc3.config import (
    API_SURFACE,
    BASE_URL,
    CHAT_COMPLETIONS_PATH,
    HTTP_LIBRARY,
    MAX_COMPLETION_TOKENS,
    MAX_TRANSPORT_ATTEMPTS,
    MODELS_PATH,
    PROVIDER,
    PROVIDER_MANDATED,
    RETRY_BACKOFF_SECONDS,
    RETRYABLE_HTTP_STATUS,
    SEED,
    STREAM,
    TEMPERATURE,
    TOP_P,
    TRANSPORT_TIMEOUT_SECONDS,
    USER_AGENT,
)
from aivd_post_rc3.models import GPT_OSS_MODELS, MODELS
from aivd_post_rc3.stop import StopCondition, check_model_match, halt


class GroqTransportError(Exception):
    def __init__(self, status: int | None, detail: str, *, retryable: bool):
        super().__init__(detail)
        self.status = status
        self.retryable = retryable


def key_present() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def _auth_header() -> dict:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        halt("AUTHORIZATION_FAILURE: GROQ_API_KEY is not set")
    # Never retain beyond this call frame except inside the Authorization header value
    # that urllib sends once; we do not log it.
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


def build_chat_request(model_id: str, messages: list) -> dict:
    """Shared request shape for all three models (+ provider-mandated extras for GPT-OSS)."""
    if model_id not in MODELS:
        halt(f"UNEXPECTED_MODEL_SUBSTITUTION: {model_id!r}")
    body = {
        "model": model_id,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "top_p": TOP_P,
        "seed": SEED,
        "stream": STREAM,
    }
    if model_id in GPT_OSS_MODELS:
        body.update(PROVIDER_MANDATED[model_id])
    return body


def request_contract() -> dict:
    """L1: the shared request fields (model-id omitted; filled per call)."""
    return {
        "provider": PROVIDER,
        "base_url": BASE_URL,
        "api_surface": API_SURFACE,
        "http_library": HTTP_LIBRARY,
        "user_agent": USER_AGENT,
        "temperature": TEMPERATURE,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "top_p": TOP_P,
        "seed": SEED,
        "stream": STREAM,
        "provider_mandated": {m: dict(PROVIDER_MANDATED[m]) for m in GPT_OSS_MODELS},
        "models": list(MODELS),
    }


def _do_http(method: str, url: str, body: bytes | None) -> tuple[int, bytes]:
    headers = _auth_header()
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TRANSPORT_TIMEOUT_SECONDS) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read() if hasattr(exc, "read") else b""
        retryable = exc.code in RETRYABLE_HTTP_STATUS
        raise GroqTransportError(exc.code, f"HTTP {exc.code}", retryable=retryable) from exc
    except Exception as exc:
        raise GroqTransportError(None, f"transport: {type(exc).__name__}", retryable=True) from exc


def list_models() -> dict:
    """GET /models. Caller decides when to invoke (preflight). Counts as a real API call
    if used during an evaluation; preflight is outside the 96."""
    status, raw = _do_http("GET", BASE_URL + MODELS_PATH, None)
    if status != 200:
        raise GroqTransportError(status, f"models list HTTP {status}", retryable=False)
    return json.loads(raw)


def preflight_models_active(listing: dict) -> dict:
    """Check the three preregistered IDs are present and active in a /models listing."""
    by_id = {row.get("id"): row for row in listing.get("data", [])}
    out = {}
    for mid in MODELS:
        row = by_id.get(mid)
        active = bool(row) and (row.get("active", True) is not False)
        out[mid] = {"listed": row is not None, "active": active}
    return out


def chat_completion(model_id: str, messages: list, *,
                    on_attempt: Callable[[dict], None] | None = None) -> tuple[dict, bytes, list]:
    """POST /chat/completions with preregistered retry policy.

    Returns (parsed_json, raw_bytes, attempt_log).
    Every attempt is appended to attempt_log and reported via on_attempt BEFORE the
    next wait, so the driver can charge budget per attempt. On final failure raises
    GroqTransportError / StopCondition.
    """
    body_obj = build_chat_request(model_id, messages)
    raw_req = json.dumps(body_obj, sort_keys=True).encode()
    url = BASE_URL + CHAT_COMPLETIONS_PATH
    attempts = []
    last_err: Exception | None = None
    for attempt_i in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
        entry = {
            "attempt": attempt_i,
            "model_id": model_id,
            "request_sha256": sha256(raw_req).hexdigest(),
            "timestamp": time.time(),
        }
        if on_attempt is not None:
            on_attempt(entry)
        try:
            status, raw = _do_http("POST", url, raw_req)
            entry["status"] = status
            entry["response_sha256"] = sha256(raw).hexdigest()
            attempts.append(entry)
            if status != 200:
                raise GroqTransportError(status, f"HTTP {status}",
                                         retryable=status in RETRYABLE_HTTP_STATUS)
            parsed = json.loads(raw)
            returned_model = parsed.get("model") or ""
            check_model_match(model_id, returned_model)
            # Extract content
            try:
                content = parsed["choices"][0]["message"]["content"]
            except Exception as exc:
                halt(f"API_REQUEST_CONTAMINATION: unreadable completion ({type(exc).__name__})")
            if not isinstance(content, str):
                halt("API_REQUEST_CONTAMINATION: content is not a string")
            return parsed, raw, attempts
        except StopCondition:
            raise
        except GroqTransportError as exc:
            entry["error"] = str(exc)
            entry["status"] = exc.status
            attempts.append(entry)
            last_err = exc
            if not exc.retryable or attempt_i >= MAX_TRANSPORT_ATTEMPTS:
                break
            time.sleep(RETRY_BACKOFF_SECONDS[min(attempt_i - 1, len(RETRY_BACKOFF_SECONDS) - 1)])
        except Exception as exc:
            entry["error"] = type(exc).__name__
            attempts.append(entry)
            last_err = GroqTransportError(None, type(exc).__name__, retryable=True)
            if attempt_i >= MAX_TRANSPORT_ATTEMPTS:
                break
            time.sleep(RETRY_BACKOFF_SECONDS[min(attempt_i - 1, len(RETRY_BACKOFF_SECONDS) - 1)])
    assert last_err is not None
    raise last_err


def ollama_shaped_transport(model_id: str, *, on_attempt=None):
    """Adapter that accepts an RC3 Wire-forwarded request (must carry 'messages')
    and returns (status, bytes) in a minimal Ollama-compatible shape so a caller
    that expects message.content still works — used by the wire proxy path.

    The evaluation session uses the native OpenAI shape; this helper is for the
    evaluator-side wire proxy that reuses aivd_rc3.wire.Wire unchanged.
    """

    def transport(request: dict) -> tuple:
        messages = request["messages"]
        # Drop any Ollama-only keys if a mixed request arrives; only messages matter for Wire.
        try:
            parsed, raw, _attempts = chat_completion(model_id, messages, on_attempt=on_attempt)
        except GroqTransportError as exc:
            return (exc.status or 502), b""
        content = parsed["choices"][0]["message"]["content"]
        # Shape that RC3Session / a legacy parser would accept; our PostRC3Session
        # does not use this. Wire only forwards bytes.
        shaped = {
            "model": model_id,
            "message": {"role": "assistant", "content": content},
            "groq_raw_sha256": sha256(raw).hexdigest(),
            "usage": parsed.get("usage") or {},
        }
        return 200, json.dumps(shaped).encode()

    return transport
