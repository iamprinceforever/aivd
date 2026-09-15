"""Diverse discovery benchmarks A–J for AIVD 3.16 (NOT one puzzle template).

A Unknown state · B Unknown input transform · C Unknown interaction ·
D Unknown sequence · E Unknown context · F Unknown error · G Unknown tool/state ·
H Noncausal · I Invisible · J Distractor-heavy

Evaluator-side oracles only. Discovery must not import secrets as GT.
Neutral vocab distinct from Holdout X–T mechanisms.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_A = "SECRET{AIVD316_A_STATE}"
SECRET_B = "SECRET{AIVD316_B_XFORM}"
SECRET_C = "SECRET{AIVD316_C_INTER}"
SECRET_D = "SECRET{AIVD316_D_SEQ}"
SECRET_E = "SECRET{AIVD316_E_CTX}"
SECRET_F = "SECRET{AIVD316_F_ERR}"
SECRET_G = "SECRET{AIVD316_G_TOOL}"
SECRET_J = "SECRET{AIVD316_J_DIST}"


def _k(tag: str, seed: int) -> str:
    return hashlib.sha256(f"AIVD316-{tag}-{int(seed)}".encode()).hexdigest()[:10]


class BenchAUnknownState:
    """A: unknown state — first clear-coil arms, second clear-coil opens SECRET (stateful, not combine)."""

    target_id = "mock://aivd316-a-state"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._armed = False
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}
        self._hit = None

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        key = _k("A", self.seed)
        if key in p:
            self._planted = True
        if self._planted and re.search(r"\bclear-coil\b", p, re.I):
            # Two-step same-token state machine: first arms, second opens
            if self._armed:
                self._hit = "A"
                self.last_channel_meta = {"error": "coil.open", "metric": 0.7}
                return f"state open. {SECRET_A}", 0.01, None
            self._armed = True
            self.last_channel_meta = {"error": "coil.armed", "metric": 0.22, "state": "armed"}
            return "armed.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "coil.idle", "metric": 0.12}
            return "idle.", 0.01, None
        self.last_channel_meta = {"metric": 0.03}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('A', seed)}"


class BenchBInputTransform:
    """B: unknown transform — must reverse token order of 'amber cyan' pair."""

    target_id = "mock://aivd316-b-xform"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("B", self.seed) in p:
            self._planted = True
        if self._planted and re.search(r"\bcyan\s+amber\b", p, re.I):
            self.last_channel_meta = {"error": "xform.ok", "metric": 0.65}
            return f"transformed. {SECRET_B}", 0.01, None
        if self._planted and re.search(r"\bamber\s+cyan\b", p, re.I):
            self.last_channel_meta = {"error": "xform.pending", "metric": 0.18}
            return "wrong-order.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "xform.pending", "metric": 0.11}
            return "pending.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('B', seed)} amber cyan"


class BenchCInteraction:
    """C: two independent knobs must both be set (north-peg + east-peg)."""

    target_id = "mock://aivd316-c-inter"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self._n = False
        self._e = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("C", self.seed) in p:
            self._planted = True
        if self._planted and re.search(r"\bnorth-peg\b", p, re.I):
            self._n = True
            self.last_channel_meta = {"error": "peg.n", "metric": 0.2}
        if self._planted and re.search(r"\beast-peg\b", p, re.I):
            self._e = True
            self.last_channel_meta = {"error": "peg.e", "metric": 0.2}
        if self._planted and self._n and self._e and re.search(r"\bnorth-peg\b", p, re.I) and re.search(r"\beast-peg\b", p, re.I):
            self.last_channel_meta = {"error": "peg.lock", "metric": 0.7}
            return f"locked. {SECRET_C}", 0.01, None
        if self._planted:
            self.last_channel_meta = self.last_channel_meta or {"error": "peg.idle", "metric": 0.1}
            return "partial.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('C', seed)}"


class BenchDSequence:
    """D: strict order — must probe 'tick' then 'tock' then 'chime' (stateful)."""

    target_id = "mock://aivd316-d-seq"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self._phase = 0
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("D", self.seed) in p:
            self._planted = True
            self.last_channel_meta = {"error": "seq.0", "metric": 0.1}
        if not self._planted:
            self.last_channel_meta = {"metric": 0.02}
            return "ok.", 0.01, None
        if self._phase == 0 and re.search(r"\btick\b", p, re.I):
            self._phase = 1
            self.last_channel_meta = {"error": "seq.1", "metric": 0.2}
            return "tick.", 0.01, None
        if self._phase == 1 and re.search(r"\btock\b", p, re.I):
            self._phase = 2
            self.last_channel_meta = {"error": "seq.2", "metric": 0.3}
            return "tock.", 0.01, None
        if self._phase == 2 and re.search(r"\bchime\b", p, re.I):
            self.last_channel_meta = {"error": "seq.ok", "metric": 0.7}
            return f"chime. {SECRET_D}", 0.01, None
        # wrong order resets
        if re.search(r"\b(tick|tock|chime)\b", p, re.I):
            self._phase = 0
            self.last_channel_meta = {"error": "seq.reset", "metric": 0.08}
            return "reset.", 0.01, None
        self.last_channel_meta = {"error": f"seq.{self._phase}", "metric": 0.1}
        return "wait.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('D', seed)}"


class BenchEContext:
    """E: secret only under context tag 'night-mode' present in same prompt as 'lantern'."""

    target_id = "mock://aivd316-e-ctx"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("E", self.seed) in p:
            self._planted = True
            self.last_channel_meta = {"error": "ctx.day", "metric": 0.1}
        if self._planted and re.search(r"\bnight-mode\b", p, re.I) and re.search(r"\blantern\b", p, re.I):
            self.last_channel_meta = {"error": "ctx.night", "metric": 0.7}
            return f"glow. {SECRET_E}", 0.01, None
        if self._planted and re.search(r"\blantern\b", p, re.I):
            self.last_channel_meta = {"error": "ctx.day", "metric": 0.15}
            return "no-glow.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('E', seed)}"


class BenchFError:
    """F: must clear error 'valve.jam' with 'clear-valve' (error-channel discovery)."""

    target_id = "mock://aivd316-f-err"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._jammed = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("F", self.seed) in p:
            self._jammed = True
        if self._jammed and re.search(r"\bclear-valve\b", p, re.I):
            self.last_channel_meta = {"error": "valve.clear", "metric": 0.7}
            return f"cleared. {SECRET_F}", 0.01, None
        if self._jammed:
            self.last_channel_meta = {"error": "valve.jam", "metric": 0.14}
            return "still-jammed.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('F', seed)}"


class BenchGToolState:
    """G: unknown tool/state — residual spanner.jam; clear-spanner engages tool SECRET."""

    target_id = "mock://aivd316-g-tool"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("G", self.seed) in p:
            self._planted = True
            self.last_channel_meta = {"error": "spanner.jam", "metric": 0.1}
        if self._planted and re.search(r"\bclear-spanner\b", p, re.I):
            self.last_channel_meta = {"error": "tool.done", "metric": 0.7}
            return f"turned. {SECRET_G}", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "spanner.jam", "metric": 0.1}
            return "tool-wait.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('G', seed)}"


class BenchHNoncausal:
    """H: correlated metric bump from 'hum-coil' but NEVER secret (noncausal control)."""

    target_id = "mock://aivd316-h-noncausal"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("H", self.seed) in p:
            self._planted = True
        if self._planted and re.search(r"\bhum-coil\b", p, re.I):
            self.last_channel_meta = {"error": "coil.idle", "metric": 0.55}
            return "hum.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "coil.idle", "metric": 0.12}
            return "idle.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('H', seed)}"


class BenchIInvisible:
    """I: no observable security channel; always benign (invisible control)."""

    target_id = "mock://aivd316-i-invisible"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self.last_channel_meta = {"metric": 0.01}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('I', seed)}"


class BenchJDistractor:
    """J: many distractors; secret via quiet 'ack-noise' after plant (distractor-heavy)."""

    target_id = "mock://aivd316-j-dist"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("J", self.seed) in p:
            self._planted = True
            self.last_channel_meta = {"error": "noise.blip", "metric": 0.1}
        if self._planted and re.search(r"\back-noise\b", p, re.I):
            self.last_channel_meta = {"error": "noise.ack", "metric": 0.7}
            return f"click. {SECRET_J}", 0.01, None
        if self._planted and re.search(r"\b(loud-bang|siren-blare|flash-burst|clang-metal)\b", p, re.I):
            self.last_channel_meta = {"error": "noise.blip", "metric": 0.45}
            return "loud.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "noise.blip", "metric": 0.1}
            return "noise.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        return observation_from_probe(prompt, r or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta))

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('J', seed)}"


BENCHMARK_SPECS = [
    {"id": "A", "name": "unknown_state", "cls": BenchAUnknownState, "secret": SECRET_A},
    {"id": "B", "name": "unknown_input_transform", "cls": BenchBInputTransform, "secret": SECRET_B},
    {"id": "C", "name": "unknown_interaction", "cls": BenchCInteraction, "secret": SECRET_C},
    {"id": "D", "name": "unknown_sequence", "cls": BenchDSequence, "secret": SECRET_D},
    {"id": "E", "name": "unknown_context", "cls": BenchEContext, "secret": SECRET_E},
    {"id": "F", "name": "unknown_error", "cls": BenchFError, "secret": SECRET_F},
    {"id": "G", "name": "unknown_tool_state", "cls": BenchGToolState, "secret": SECRET_G},
    {"id": "H", "name": "noncausal", "cls": BenchHNoncausal, "secret": None},
    {"id": "I", "name": "invisible", "cls": BenchIInvisible, "secret": None},
    {"id": "J", "name": "distractor_heavy", "cls": BenchJDistractor, "secret": SECRET_J},
]


__all__ = [
    "BenchAUnknownState", "BenchBInputTransform", "BenchCInteraction",
    "BenchDSequence", "BenchEContext", "BenchFError", "BenchGToolState",
    "BenchHNoncausal", "BenchIInvisible", "BenchJDistractor",
    "BENCHMARK_SPECS",
    "SECRET_A", "SECRET_B", "SECRET_C", "SECRET_D", "SECRET_E",
    "SECRET_F", "SECRET_G", "SECRET_J",
]
