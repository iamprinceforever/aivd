"""Local stub target for adapter tests."""
from __future__ import annotations

import time
from typing import Optional


class LocalStubTarget:
    target_id = "local://stub"

    def describe(self) -> str:
        return "Local echo stub for adapter/unit tests."

    def probe(self, prompt: str, timeout_s: float = 10.0) -> tuple[str, float, Optional[str]]:
        t0 = time.perf_counter()
        if not prompt.strip():
            return "", 0.0, "empty_prompt"
        return f"local-stub-ack:{len(prompt)}", (time.perf_counter() - t0) * 1000, None
