"""Local open-weights model path OR local OpenAI-compatible server.

Prefer:
  - Closed models: official API + API key (see openai_compat / anthropic / gemini)
  - Open weights you already possess: AIVD_LOCAL_MODEL_PATH or local server
    via AIVD_LOCAL_BASE_URL (vLLM / Ollama OpenAI-compat)

Never auto-download / scrape vendor marketing sites for model files.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from aivd.targets.openai_compat import DEFAULT_ALLOWLISTED_BASE_URLS, OpenAICompatTarget


class LocalModelTarget:
    """Load/call local path OR local OpenAI-compatible endpoint."""

    target_id = "local://model"

    def __init__(
        self,
        model_path: str | None = None,
        base_url: str | None = None,
        model: str = "local-model",
        allow_network: bool = True,
        allowlisted_base_urls: frozenset[str] | set[str] | None = None,
    ):
        self.model_path = model_path or os.environ.get("AIVD_LOCAL_MODEL_PATH")
        self.base_url = (base_url or os.environ.get("AIVD_LOCAL_BASE_URL") or "").rstrip("/") or None
        self.model = model
        self.allow_network = allow_network
        self.allowlisted = frozenset(allowlisted_base_urls or DEFAULT_ALLOWLISTED_BASE_URLS)
        self._remote: OpenAICompatTarget | None = None
        self._local_ready = False

        if self.base_url:
            if self.base_url not in self.allowlisted:
                raise PermissionError(
                    f"Local base URL {self.base_url!r} not allowlisted for OpenAI-compat proxy."
                )
            # Local servers often need no key; pass placeholder if unset
            self._remote = OpenAICompatTarget(
                base_url=self.base_url,
                model=self.model,
                api_key=os.environ.get("AIVD_API_KEY") or os.environ.get("OPENAI_API_KEY") or "local",
                allowlisted_base_urls=self.allowlisted,
                allow_network=allow_network,
            )
        elif self.model_path:
            p = Path(self.model_path)
            if not p.exists():
                raise FileNotFoundError(
                    f"Local model path does not exist: {self.model_path}. "
                    "Provide an open-weights path you already possess; "
                    "AIVD will not auto-download from vendor sites."
                )
            self._local_ready = True
        else:
            raise ValueError(
                "Set AIVD_LOCAL_MODEL_PATH (open weights you already have) "
                "or AIVD_LOCAL_BASE_URL (local vLLM/Ollama OpenAI-compat server)."
            )

    def describe(self) -> str:
        if self._remote:
            return f"Local OpenAI-compat server at {self.base_url} model={self.model}"
        return f"Local model path={self.model_path}"

    def probe(self, prompt: str, timeout_s: float = 10.0) -> tuple[str, float, Optional[str]]:
        t0 = time.perf_counter()
        if not prompt.strip():
            return "", 0.0, "empty_prompt"
        if self._remote is not None:
            return self._remote.probe(prompt, timeout_s=timeout_s)
        # Path-based: without a full inference stack, return a safe stub signal.
        # Operators should prefer a local OpenAI-compatible server for real inference.
        if not self._local_ready:
            return "", 0.0, "local_model_unavailable"
        resp = (
            f"[local-model-path:{self.model_path}] "
            "No bundled inference runtime; start vLLM/Ollama and set AIVD_LOCAL_BASE_URL "
            "for real probes. Policy-bound refusal stub for empty local path mode."
        )
        return resp, (time.perf_counter() - t0) * 1000, None
