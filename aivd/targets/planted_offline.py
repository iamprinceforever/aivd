"""Offline planted-vulnerability target (deterministic, no network).

Mirrors scripts/planted_llama_proxy.py trigger logic for fast multi-seed /
budget sweeps. Explorers must NOT import ground-truth details from
reports/llama_planted_vuln/ground_truth_OFFLINE_ONLY.json.
"""
from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Optional

_PROXY_PATH = Path(__file__).resolve().parents[2] / "scripts" / "planted_llama_proxy.py"


def _load_proxy_fns():
    spec = importlib.util.spec_from_file_location("planted_llama_proxy", _PROXY_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.planted_response, mod.benign_refusal


class PlantedOfflineTarget:
    """Local planted suite without Ollama. target_id = mock://planted-offline."""

    target_id = "mock://planted-offline"

    def __init__(self, seed: int = 42, stochastic: bool = False, **_kwargs):
        self.seed = seed
        self.stochastic = stochastic
        self._last_hit: Optional[str] = None
        self._planted_response, self._benign = _load_proxy_fns()

    def describe(self) -> str:
        return (
            "Offline planted-vulnerability suite (proxy-equivalent triggers). "
            "Not stock Llama weights. Authorized research mock only."
        )

    def last_ground_truth_hit(self) -> Optional[str]:
        return self._last_hit

    def probe(self, prompt: str, timeout_s: float = 10.0) -> tuple[str, float, Optional[str]]:
        t0 = time.perf_counter()
        if not prompt or not prompt.strip():
            self._last_hit = None
            return "", (time.perf_counter() - t0) * 1000, "empty_prompt"
        hit = self._planted_response(prompt)
        if hit is not None:
            content, vid = hit
            self._last_hit = vid
            return content, (time.perf_counter() - t0) * 1000, None
        self._last_hit = None
        return self._benign(prompt), (time.perf_counter() - t0) * 1000, None
