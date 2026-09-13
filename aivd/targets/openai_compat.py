"""OpenAI-compatible chat completions client (httpx) + local stub.

Closed models (GPT, GPT Astra if OpenAI-compatible): use official API + API key
via env vars. Base URL and model id must be allowlisted. No network in default tests.
"""
from __future__ import annotations

import os
import time
from typing import Optional

# Allowlisted OpenAI-compatible base URLs (no trailing path beyond /v1 optional)
DEFAULT_ALLOWLISTED_BASE_URLS = frozenset(
    {
        "https://api.openai.com/v1",
        "https://api.openai.com",
        "http://127.0.0.1:8000/v1",
        "http://127.0.0.1:8000",
        "http://localhost:8000/v1",
        "http://localhost:8000",
        "http://127.0.0.1:11434/v1",  # Ollama OpenAI-compat
        "http://localhost:11434/v1",
    }
)


class OpenAICompatStub:
    """Stub that mimics an OpenAI-compatible chat endpoint without network I/O."""

    target_id = "openai-compat://stub"

    def __init__(self, base_url: str | None = None, allow_network: bool = False, **_kwargs):
        self.base_url = base_url
        self.allow_network = allow_network
        if allow_network:
            raise PermissionError(
                "Use OpenAICompatTarget for real network calls, not the stub."
            )

    def describe(self) -> str:
        return "OpenAI-compatible local stub (network disabled)."

    def probe(self, prompt: str, timeout_s: float = 10.0) -> tuple[str, float, Optional[str]]:
        t0 = time.perf_counter()
        if not prompt.strip():
            return "", 0.0, "empty_prompt"
        resp = (
            "[openai-compat-stub] Refusing to perform security-sensitive actions. "
            f"Echo prefix: {prompt[:80]!r}"
        )
        return resp, (time.perf_counter() - t0) * 1000, None


class OpenAICompatTarget:
    """Real HTTP client for OpenAI-compatible chat completions.

    Env: OPENAI_API_KEY or AIVD_API_KEY.
    """

    target_id = "openai-compat://api"

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        allowlisted_base_urls: frozenset[str] | set[str] | None = None,
        timeout_s: float = 30.0,
        allow_network: bool = True,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("AIVD_API_KEY")
        self.allowlisted = frozenset(allowlisted_base_urls or DEFAULT_ALLOWLISTED_BASE_URLS)
        self.timeout_s = timeout_s
        self.allow_network = allow_network
        self._validate_allowlist()

    def _validate_allowlist(self) -> None:
        if self.base_url not in self.allowlisted:
            raise PermissionError(
                f"Base URL {self.base_url!r} not in allowlist. "
                f"Allowed: {sorted(self.allowlisted)}"
            )

    def describe(self) -> str:
        return f"OpenAI-compatible API target model={self.model} base={self.base_url}"

    def probe(self, prompt: str, timeout_s: float = 10.0) -> tuple[str, float, Optional[str]]:
        t0 = time.perf_counter()
        if not prompt.strip():
            return "", 0.0, "empty_prompt"
        if not self.allow_network:
            return "", 0.0, "network_disabled"
        if not self.api_key:
            return "", (time.perf_counter() - t0) * 1000, "missing_api_key"
        try:
            import httpx
        except ImportError:
            return "", 0.0, "httpx_not_installed"

        url = f"{self.base_url}/chat/completions"
        if self.base_url.endswith("/v1"):
            url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        try:
            with httpx.Client(timeout=timeout_s or self.timeout_s) as client:
                r = client.post(url, headers=headers, json=body)
                r.raise_for_status()
                data = r.json()
            text = data["choices"][0]["message"]["content"]
            return text, (time.perf_counter() - t0) * 1000, None
        except Exception as e:  # noqa: BLE001 — surface as probe error
            return "", (time.perf_counter() - t0) * 1000, f"http_error:{type(e).__name__}"
