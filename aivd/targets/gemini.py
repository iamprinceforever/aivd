"""Google Gemini generateContent API target (httpx).

Requires GOOGLE_API_KEY or GEMINI_API_KEY. Base URL allowlisted.
Includes exponential backoff on 429/503 (capped ~60s, limited retries).
"""
from __future__ import annotations

import os
import random
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
        max_retries: int = 5,
        max_backoff_s: float = 60.0,
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
        self.max_retries = max(0, int(max_retries))
        self.max_backoff_s = float(max_backoff_s)
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
        last_err: Optional[str] = None
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=timeout_s) as client:
                    r = client.post(url, params=params, json=body)
                    if r.status_code in (429, 503) and attempt < attempts - 1:
                        # Retryable: exponential backoff with jitter, capped.
                        delay = min(self.max_backoff_s, (2 ** attempt) + random.uniform(0, 1))
                        last_err = f"http_{r.status_code}"
                        time.sleep(delay)
                        continue
                    if r.status_code == 429:
                        return "", (time.perf_counter() - t0) * 1000, "http_429_quota"
                    if r.status_code == 503:
                        return "", (time.perf_counter() - t0) * 1000, "http_503"
                    r.raise_for_status()
                    data = r.json()
                cands = data.get("candidates") or []
                if not cands:
                    return "", (time.perf_counter() - t0) * 1000, "empty_candidates"
                parts = (cands[0].get("content") or {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
                return text, (time.perf_counter() - t0) * 1000, None
            except Exception as e:  # noqa: BLE001
                # Never include request URL (may contain key in query) or response bodies.
                last_err = f"http_error:{type(e).__name__}"
                if attempt < attempts - 1:
                    delay = min(self.max_backoff_s, (2 ** attempt) + random.uniform(0, 1))
                    time.sleep(delay)
                    continue
                return "", (time.perf_counter() - t0) * 1000, last_err
        return "", (time.perf_counter() - t0) * 1000, last_err or "http_error:unknown"
