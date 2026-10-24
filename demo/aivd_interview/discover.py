"""DEMO – not a research result. Prompt a local model to analyze one target's source."""
from __future__ import annotations

import json
import re

from . import ollama_client

SYSTEM = (
    "You are a security code reviewer. Analyze the Python function for vulnerabilities. "
    "Reply with ONLY a JSON object of the form "
    '{"vulnerable": true|false, "class": "<short class or null>", '
    '"cwe": "<CWE-ID or null>", "evidence": "<one sentence>", '
    '"exploit_hint": "<payload idea or null>"}. '
    "Look specifically for path traversal (unsanitized path join) and SQL injection "
    "(string-built queries). If the code looks safe, set vulnerable to false."
)


def _extract_json(text: str) -> dict | None:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None


def analyze_with_model(host: str, model: str, target: str, source: str) -> dict:
    user = (
        f"Target module name: {target}\n"
        f"Source:\n```python\n{source}\n```\n"
        "Is this vulnerable? Respond with the JSON schema only."
    )
    try:
        resp = ollama_client.chat(
            host,
            model,
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
        )
        content = (resp.get("message") or {}).get("content") or ""
        parsed = _extract_json(content)
        return {
            "ok": True,
            "model": model,
            "target": target,
            "raw": content[:2000],
            "parsed": parsed,
            "error": None if parsed else "could not parse model JSON",
        }
    except ollama_client.OllamaError as e:
        return {
            "ok": False,
            "model": model,
            "target": target,
            "raw": None,
            "parsed": None,
            "error": str(e),
        }
