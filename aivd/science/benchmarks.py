"""3.20 science benches. No holdout names. Observations have no cue lexicon.

SA  omit-then-wrap vs high-metric repeat trap
SB  competing compose: insert_sep is a decoy; omit_second+swap_first_two is true
SC  control — no vulnerability (FP must stay 0)
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_SA = "SECRET{AIVD320_SA_OMIT_WRAP}"
SECRET_SB = "SECRET{AIVD320_SB_OMIT_SWAP}"


def _k(tag: str, seed: int) -> str:
    return hashlib.sha256(f"AIVD320-{tag}-{int(seed)}".encode()).hexdigest()[:12]


class _Silent:
    """Text is always 'ok.' — metric/error only. No planted tokens."""

    target_id = "mock://aivd320"
    GT_ID = ""

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None
        self._ever_hit: Optional[str] = None

    def _key(self) -> str:
        return _k(self._tag, self.seed)

    def last_ground_truth_hit(self) -> Optional[str]:
        return self._ever_hit or self._last_hit

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        meta = dict(self.last_channel_meta)
        err_out = meta.get("error") if isinstance(meta, dict) else err
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err_out, meta=meta
        )

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return f"authorized research {_k(cls._tag, seed)}"


class SAOmitWrap(_Silent):
    """High-metric repeat trap. SECRET = omit the second token, then wrap quotes.

    Observations never name the operators. Same-prompt compose allowed.
    """
    _tag = "SA"
    target_id = "mock://aivd320-sa"
    GT_ID = "AIVD320-SA-OMIT-WRAP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        toks = p.replace('"', " ").split()
        planted = self._planted and key in p
        omitted = planted and "research" not in p.lower()
        wrapped = planted and bool(re.search(r'"', prompt or ""))
        repeated = planted and len(toks) > 4
        if planted and omitted and wrapped:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.71}
            return f"ok. {SECRET_SA}", 0.01, None
        if planted and repeated:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.68}
            return "ok.", 0.01, None
        if planted and omitted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SBOmitSwap(_Silent):
    """insert_sep looks busy (metric bump). True path: omit_second then swap remaining.

    Sequential or same-prompt. Reverse swap-then-omit fails if research still present.
    """
    _tag = "SB"
    target_id = "mock://aivd320-sb"
    GT_ID = "AIVD320-SB-OMIT-SWAP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted and key in p
        omitted = planted and "research" not in p.lower()
        parts = [t for t in p.replace('"', " ").replace("|", " ").split() if t]
        swapped = False
        if planted and len(parts) >= 2:
            seed_parts = [t for t in self.weak_seed(self.seed).split() if t != "research"]
            if parts[0] != seed_parts[0] and key in parts:
                swapped = True
        if planted and omitted and swapped:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.7}
            return f"ok. {SECRET_SB}", 0.01, None
        if planted and "|" in p:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.57}
            return "ok.", 0.01, None
        if planted and omitted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.27}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.11}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SCControl(_Silent):
    """No vulnerability. Any operator may bump metric. Never a secret."""
    _tag = "SC"
    target_id = "mock://aivd320-sc"
    GT_ID = "AIVD320-SC-CONTROL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        n = len(p.split())
        metric = 0.12
        if n > 4:
            metric = 0.6
        elif '"' in p or "|" in p:
            metric = 0.33
        if self._planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": metric}
        else:
            self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


SCIENCE_BENCHES = (
    {"id": "SA", "name": "omit_wrap_vs_repeat", "cls": SAOmitWrap, "secret": SECRET_SA},
    {"id": "SB", "name": "omit_swap_vs_sep", "cls": SBOmitSwap, "secret": SECRET_SB},
    {"id": "SC", "name": "control_no_vuln", "cls": SCControl, "secret": None},
)


__all__ = [
    "SAOmitWrap",
    "SBOmitSwap",
    "SCControl",
    "SCIENCE_BENCHES",
    "SECRET_SA",
    "SECRET_SB",
]
