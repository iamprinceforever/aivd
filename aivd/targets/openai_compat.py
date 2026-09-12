"""OpenAI-compatible stub — allowlisted local stub only, no real network by default."""
from __future__ import annotations

import time
from typing import Optional


class OpenAICompatStub:
    """Stub that mimics an OpenAI-compatible chat endpoint without network I/O."""

    target_id = "openai-compat://stub"

    def __init__(self, base_url: str | None = None, allow_network: bool = False):
        self.base_url = base_url
        self.allow_network = allow_network
        if allow_network:
            raise PermissionError(
                "Network calls to external OpenAI-compatible endpoints are disabled "
                "in this research MVP. Use mock://default."
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
