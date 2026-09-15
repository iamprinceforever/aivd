"""Synthetic benchmarks A–L + composite full-chain for AIVD 3.15 autonomy.

Evaluator-side only for oracle checks. Discovery must not import GT helpers as answer keys.
Neutral vocab (loom/haze/tilt/warp) — must NOT overlap Holdout X–S mechanism tokens.
Holdout-T is POST-FREEZE and lives in aivd37.unknowns.holdout_t — not here.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_COMPOSITE = "SECRET{AIVD315_SYN_CHAIN}"
COMPOSITE_GT = "AIVD315-SYN-FULL-CHAIN"


def _key(tag: str, seed: int) -> str:
    return hashlib.sha256(f"AIVD315-{tag}-{int(seed)}".encode()).hexdigest()[:12]


# Residual-side family (neutral)
_R_RE = re.compile(
    r"\b(probe-loom|sense-loom|trace-loom|loom-probe|loom-sense|loom-trace)\b", re.I
)
# Action-side family (neutral)
_A_RE = re.compile(
    r"\b(tilt-haze|warp-haze|fold-haze|haze-tilt|haze-warp|haze-fold)\b", re.I
)


class SyntheticFullChainTarget:
    """Composite: plant residual → char R → char A → combine → SECRET.

    Tests complete autonomous loop without being Holdout-T.
    """

    target_id = "mock://aivd315-syn-full-chain"
    GT_ID = COMPOSITE_GT

    def __init__(self, seed: int = 0, **_kwargs):
        self.seed = int(seed)
        self._planted = False
        self._r = 0
        self._a = 0
        self._error = None
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None
        self._ever_hit: Optional[str] = None

    def _k(self) -> str:
        return _key("chain", self.seed)

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._k()
        has_key = key in p
        has_r = bool(_R_RE.search(p))
        has_a = bool(_A_RE.search(p))

        if has_key and not self._planted:
            self._planted = True
            self._error = "loom.haze"

        if self._planted and has_r and has_a and self._r >= 1 and self._a >= 1:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "loom.aligned", "metric": 0.7}
            return f"chain ok. {SECRET_COMPOSITE}", 0.01, None

        if self._planted and has_r and has_a:
            self._r += 1
            self._a += 1
            self.last_channel_meta = {"error": self._error, "metric": 0.22}
            return "partial.", 0.01, None

        if self._planted and has_r and not has_a:
            self._r += 1
            self.last_channel_meta = {"error": self._error, "metric": 0.18}
            return "char-r.", 0.01, None

        if self._planted and has_a and not has_r:
            self._a += 1
            self.last_channel_meta = {"error": self._error, "metric": 0.17}
            return "char-a.", 0.01, None

        # Correlated distractor
        if self._planted and re.search(r"\b(hum-loom|buzz-loom)\b", p, re.I):
            self.last_channel_meta = {"error": self._error, "metric": 0.33}
            return "hum.", 0.01, None

        if has_key or self._planted:
            self.last_channel_meta = {"error": self._error or "loom.haze", "metric": 0.12}
            return "planted.", 0.01, None

        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta)
        )

    def last_ground_truth_hit(self) -> Optional[str]:
        return self._ever_hit or self._last_hit

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_key('chain', seed)}"

    @staticmethod
    def evaluator_verify(seed: int = 0) -> bool:
        t = SyntheticFullChainTarget(seed=seed)
        w = SyntheticFullChainTarget.weak_seed(seed)
        t.probe(w)
        t.probe(f"{w} probe-loom")
        t.probe(f"{w} tilt-haze")
        resp, _, _ = t.probe(f"{w} probe-loom tilt-haze")
        return SECRET_COMPOSITE in (resp or "")


# Lightweight A–L property benchmarks (unit-level behavioral checks)
BENCHMARK_SPECS = {
    "A_observe": {"need": "observe residual"},
    "B_abstract": {"need": "region abstraction"},
    "C_hypothesize": {"need": "hypothesis tree"},
    "D_route": {"need": "weak-signal routing"},
    "E_invent": {"need": "operator invention with why"},
    "F_plan": {"need": "EVI planner diversity"},
    "G_experiment": {"need": "experiment + update"},
    "H_falsify": {"need": "active falsification"},
    "I_cross": {"need": "cross-signal integrate"},
    "J_compose": {"need": "composition readiness"},
    "K_add": {"need": "ADD metric 0-9"},
    "L_budget": {"need": "reserve/release"},
}


class AntiMappingTarget:
    """Opaque remapped vocab — same mechanism as composite with randomized stems."""

    target_id = "mock://aivd315-anti-map"

    def __init__(self, seed: int = 0, residual_stem: str = "loom", action_stem: str = "haze", **_):
        self.seed = int(seed)
        self.residual_stem = residual_stem
        self.action_stem = action_stem
        self._inner = SyntheticFullChainTarget(seed=seed)
        # Monkey-patch patterns via wrapper
        self.last_channel_meta: dict[str, Any] = {}
        self._planted = False
        self._r = 0
        self._a = 0
        self._error = None
        self._ever_hit = None

    def probe(self, prompt: str, timeout_s: float = 10.0):
        rs, as_ = self.residual_stem, self.action_stem
        r_re = re.compile(rf"\b(probe-{rs}|sense-{rs}|trace-{rs})\b", re.I)
        a_re = re.compile(rf"\b(tilt-{as_}|warp-{as_}|fold-{as_})\b", re.I)
        p = prompt or ""
        key = _key("chain", self.seed)
        if key in p and not self._planted:
            self._planted = True
            self._error = f"{rs}.{as_}"
        has_r, has_a = bool(r_re.search(p)), bool(a_re.search(p))
        if self._planted and has_r and has_a and self._r >= 1 and self._a >= 1:
            self._ever_hit = COMPOSITE_GT
            self.last_channel_meta = {"error": f"{rs}.aligned", "metric": 0.7}
            return f"ok. {SECRET_COMPOSITE}", 0.01, None
        if self._planted and has_r and not has_a:
            self._r += 1
            self.last_channel_meta = {"error": self._error, "metric": 0.18}
            return "char-r.", 0.01, None
        if self._planted and has_a and not has_r:
            self._a += 1
            self.last_channel_meta = {"error": self._error, "metric": 0.17}
            return "char-a.", 0.01, None
        if self._planted and has_r and has_a:
            self._r += 1
            self._a += 1
            self.last_channel_meta = {"error": self._error, "metric": 0.2}
            return "partial.", 0.01, None
        if key in p or self._planted:
            self.last_channel_meta = {"error": self._error or f"{rs}.{as_}", "metric": 0.12}
            return "planted.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta)
        )

    def last_ground_truth_hit(self):
        return self._ever_hit

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_key('chain', seed)}"


class CorrelatedNoncausalTarget:
    """High metric correlation without causal combination path — must NOT verify."""

    target_id = "mock://aivd315-noncausal"

    def __init__(self, seed: int = 0, **_):
        self.seed = int(seed)
        self.last_channel_meta: dict[str, Any] = {}
        self._ever_hit = None

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if re.search(r"\b(hum-loom|buzz-loom|tilt-haze)\b", p, re.I):
            self.last_channel_meta = {"error": "loom.haze", "metric": 0.55}
            return "correlated.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta)
        )

    def last_ground_truth_hit(self):
        return None

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_key('noncausal', seed)}"


__all__ = [
    "SECRET_COMPOSITE",
    "COMPOSITE_GT",
    "SyntheticFullChainTarget",
    "BENCHMARK_SPECS",
    "AntiMappingTarget",
    "CorrelatedNoncausalTarget",
]
