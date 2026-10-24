"""DEMO – not a research result. Minimal Ollama chat client (loopback only)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request


class OllamaError(RuntimeError):
    pass


def chat(
    host: str,
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.0,
    seed: int = 7,
    num_ctx: int = 4096,
    format_json: bool = True,
    timeout: int = 180,
) -> dict:
    if not host.startswith("http://127.0.0.1:") and not host.startswith("http://localhost:"):
        raise OllamaError("host must be loopback")
    body = {
        "model": model,
        "stream": False,
        "keep_alive": 0,
        "options": {"temperature": temperature, "seed": seed, "num_ctx": num_ctx},
        "messages": messages,
    }
    if format_json:
        body["format"] = "json"
    # qwen3 thinking models: disable thinking for short structured answers when supported
    if model.startswith("qwen3"):
        body["think"] = False
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise OllamaError(str(e)) from e


def list_models(host: str, timeout: int = 10) -> list[str]:
    if not host.startswith("http://127.0.0.1:") and not host.startswith("http://localhost:"):
        raise OllamaError("host must be loopback")
    req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        doc = json.loads(resp.read().decode())
    return [m["name"] for m in doc.get("models", [])]
