"""Anthropic Claude Messages API target (httpx).

Requires ANTHROPIC_API_KEY. Base URL allowlisted. No network in default tests.
"""
from __future__ import annotations

import os
import time
from typing import Optional

DEFAULT_ALLOWLISTED_BASE_URLS = frozenset(
    {
        "https://api.anthropic.com",
        "https://api.anthropic.com/v1",
    }
)


class AnthropicTarget:
    target_id = "anthropic://api"

    def __init__(
        self,
        base_url: str = "https://api.anthropic.com",
        model: str = "claude-3-5-haiku-latest",
        api_key: str | None = None,
        allowlisted_base_urls: frozenset[str] | set[str] | None = None,
        allow_network: bool = True,
        max_tokens: int = 512,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.allowlisted = frozenset(allowlisted_base_urls or DEFAULT_ALLOWLISTED_BASE_URLS)
        self.allow_network = allow_network
        self.max_tokens = max_tokens
        if self.base_url not in self.allowlisted:
            raise PermissionError(f"Anthropic base URL not allowlisted: {self.base_url!r}")

    def describe(self) -> str:
        return f"Anthropic Claude API model={self.model}"

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

        url = f"{self.base_url}/v1/messages" if not self.base_url.endswith("/v1") else f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            with httpx.Client(timeout=timeout_s) as client:
                r = client.post(url, headers=headers, json=body)
                r.raise_for_status()
                data = r.json()
            parts = data.get("content") or []
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
            return text, (time.perf_counter() - t0) * 1000, None
        except Exception as e:  # noqa: BLE001
            return "", (time.perf_counter() - t0) * 1000, f"http_error:{type(e).__name__}"
