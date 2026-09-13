"""Google Gemini generateContent API target (httpx).

Requires GOOGLE_API_KEY or GEMINI_API_KEY. Base URL allowlisted.
"""
from __future__ import annotations

import os
import time
from typing import Optional

DEFAULT_ALLOWLISTED_BASE_URLS = frozenset(
    {
        "https://generativelanguage.googleapis.com",
        "https://generativelanguage.googleapis.com/v1beta",
    }
)


class GeminiTarget:
    target_id = "gemini://api"

    def __init__(
        self,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        model: str = "gemini-2.0-flash",
        api_key: str | None = None,
        allowlisted_base_urls: frozenset[str] | set[str] | None = None,
        allow_network: bool = True,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.model = model
        self.api_key = (
            api_key
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        self.allowlisted = frozenset(allowlisted_base_urls or DEFAULT_ALLOWLISTED_BASE_URLS)
        self.allow_network = allow_network
        if self.base_url not in self.allowlisted:
            raise PermissionError(f"Gemini base URL not allowlisted: {self.base_url!r}")

    def describe(self) -> str:
        return f"Gemini API model={self.model}"

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

        url = f"{self.base_url}/models/{self.model}:generateContent"
        params = {"key": self.api_key}
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            with httpx.Client(timeout=timeout_s) as client:
                r = client.post(url, params=params, json=body)
                r.raise_for_status()
                data = r.json()
            cands = data.get("candidates") or []
            if not cands:
                return "", (time.perf_counter() - t0) * 1000, "empty_candidates"
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
            return text, (time.perf_counter() - t0) * 1000, None
        except Exception as e:  # noqa: BLE001
            return "", (time.perf_counter() - t0) * 1000, f"http_error:{type(e).__name__}"
