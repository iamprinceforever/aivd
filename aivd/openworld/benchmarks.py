"""OW-1..OW-7 open-world benchmarks (evaluator oracles). Created before Holdout-V.

OW-1 unknown primitive · OW-2 compositional family · OW-3 XOR ·
OW-4 state-conditioned · OW-5 sequence · OW-6 representation escape ·
OW-7 noncausal distractor (FP=0)

Neutral vocab distinct from Holdout X–U and 3.16 A–J. Discovery must not
import secrets as GT. Structures are generic (not impl-detail-shaped).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_OW1 = "SECRET{AIVD317_OW1_PRIM}"
SECRET_OW2 = "SECRET{AIVD317_OW2_AND}"
SECRET_OW3 = "SECRET{AIVD317_OW3_XOR}"
SECRET_OW4 = "SECRET{AIVD317_OW4_STATE}"
SECRET_OW5 = "SECRET{AIVD317_OW5_SEQ}"
SECRET_OW6 = "SECRET{AIVD317_OW6_ESC}"


def _k(tag: str, seed: int) -> str:
    return hashlib.sha256(f"AIVD317-OW-{tag}-{int(seed)}".encode()).hexdigest()[:10]


class _Base:
    _tag = "0"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}
        self._hit: Optional[str] = None

    def _key(self) -> str:
        return _k(self._tag, self.seed)

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        meta = dict(self.last_channel_meta)
        # Residual-sweep contrast: sticky plant without key omits error
        if self._key() not in (prompt or ""):
            meta.pop("error", None)
        err_out = meta.get("error")
        return observation_from_probe(
            prompt, r or "", latency_s=float(lat or 0), error=err_out, meta=meta,
        )


class OW1UnknownPrimitive(_Base):
    _tag = "1"
    """Unknown primitive not in ACTION_STEMS; revealed in observation text."""

    target_id = "mock://aivd317-ow1-primitive"

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('1', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("1", self.seed) in p:
            self._planted = True
        if self._planted and re.search(r"\bloom\b", p, re.I):
            self._hit = "OW1"
            self.last_channel_meta = {"error": "frame.open", "metric": 0.7}
            return f"opened. {SECRET_OW1}", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "frame.idle", "metric": 0.12}
            return "operator-available: loom", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class OW2CompositionalFamily(_Base):
    _tag = "2"
    """AND of two harvested primitives (compositional family)."""

    target_id = "mock://aivd317-ow2-family"

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('2', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("2", self.seed) in p:
            self._planted = True
        has_a = bool(re.search(r"\banvil\b", p, re.I))
        has_t = bool(re.search(r"\btemper\b", p, re.I))
        if self._planted and has_a and has_t:
            self._hit = "OW2"
            self.last_channel_meta = {"error": "hearth.open", "metric": 0.68}
            return f"composed. {SECRET_OW2}", 0.01, None
        if self._planted and (has_a or has_t):
            self.last_channel_meta = {"error": "hearth.scale", "metric": 0.22}
            return "partial family.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "hearth.scale", "metric": 0.11}
            return "family: anvil temper", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class OW3Xor(_Base):
    _tag = "3"
    """First-class XOR: confirm token AND exactly one of two harvested primitives."""

    target_id = "mock://aivd317-ow3-xor"

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('3', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("3", self.seed) in p:
            self._planted = True
        has_sel = bool(re.search(r"\bselect\b", p, re.I))
        has_oak = bool(re.search(r"\boak\b", p, re.I))
        has_pine = bool(re.search(r"\bpine\b", p, re.I))
        xor = int(has_oak) ^ int(has_pine)
        if self._planted and has_sel and xor == 1:
            self._hit = "OW3"
            self.last_channel_meta = {"error": "grove.open", "metric": 0.7}
            return f"exclusive. {SECRET_OW3}", 0.01, None
        if self._planted and has_sel and has_oak and has_pine:
            self.last_channel_meta = {"error": "grove.split", "metric": 0.25}
            return "both-present.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "grove.split", "metric": 0.12}
            return "xor: oak versus pine; apply select", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class OW4State(_Base):
    _tag = "4"
    """State-conditioned: same harvested token twice across probes (not same prompt)."""

    target_id = "mock://aivd317-ow4-state"

    def __init__(self, seed: int = 0, **_k):
        super().__init__(seed=seed)
        self._armed = False

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('4', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("4", self.seed) in p:
            self._planted = True
        if self._planted and re.search(r"\bwick\b", p, re.I):
            if self._armed:
                self._hit = "OW4"
                self.last_channel_meta = {"error": "lamp.open", "metric": 0.72, "state": "open"}
                return f"state open. {SECRET_OW4}", 0.01, None
            self._armed = True
            self.last_channel_meta = {"error": "lamp.wick", "metric": 0.22, "state": "armed"}
            return "armed.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "lamp.wick", "metric": 0.12, "state": "idle"}
            return "state: wick (arm twice)", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class OW5Sequence(_Base):
    _tag = "5"
    """Sequence/order: silk before hemp in the same prompt."""

    target_id = "mock://aivd317-ow5-sequence"

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('5', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("5", self.seed) in p:
            self._planted = True
        m_s = re.search(r"\bsilk\b", p, re.I)
        m_h = re.search(r"\bhemp\b", p, re.I)
        if self._planted and m_s and m_h and m_s.start() < m_h.start():
            self._hit = "OW5"
            self.last_channel_meta = {"error": "fiber.open", "metric": 0.7}
            return f"ordered. {SECRET_OW5}", 0.01, None
        if self._planted and m_s and m_h:
            self.last_channel_meta = {"error": "fiber.order", "metric": 0.2}
            return "wrong-order.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "fiber.order", "metric": 0.11}
            return "order: silk before hemp", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class OW6RepresentationEscape(_Base):
    _tag = "6"
    """TRANSITION across probes: anneal then later quench. Same-prompt both fails.

    Legacy closed lexicon cannot name anneal/quench from residual crucible/slag.
    """

    target_id = "mock://aivd317-ow6-escape"

    def __init__(self, seed: int = 0, **_k):
        super().__init__(seed=seed)
        self._annealed = False

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('6', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("6", self.seed) in p:
            self._planted = True
        has_an = bool(re.search(r"\banneal\b", p, re.I))
        has_q = bool(re.search(r"\bquench\b", p, re.I))
        # Same-prompt both does not count as prior-state transition
        if self._planted and has_q and self._annealed and not has_an:
            self._hit = "OW6"
            self.last_channel_meta = {"error": "crucible.open", "metric": 0.75, "state": "set"}
            return f"transition. {SECRET_OW6}", 0.01, None
        if self._planted and has_an and not has_q:
            self._annealed = True
            self.last_channel_meta = {"error": "crucible.slag", "metric": 0.24, "state": "annealed"}
            return "annealed.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "crucible.slag", "metric": 0.12}
            return "phase: anneal then quench", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class OW7Noncausal(_Base):
    _tag = "7"
    """Correlated-noncausal distractor. Metric moves; never SECRET. FP must be 0."""

    target_id = "mock://aivd317-ow7-noncausal"

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('7', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if _k("7", self.seed) in p:
            self._planted = True
        if re.search(r"hum-bell|buzz-bell|glow-tone", p, re.I):
            self.last_channel_meta = {"error": "bell.tone", "metric": 0.82}
            return "loud.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "bell.tone", "metric": 0.18}
            return "hum-bell distractor", 0.01, None
        self.last_channel_meta = {"metric": 0.03}
        return "ok.", 0.01, None


BENCHMARK_SPECS = [
    {"id": "OW-1", "name": "unknown_primitive", "cls": OW1UnknownPrimitive, "secret": SECRET_OW1, "expect_legacy": False},
    {"id": "OW-2", "name": "compositional_family", "cls": OW2CompositionalFamily, "secret": SECRET_OW2, "expect_legacy": False},
    {"id": "OW-3", "name": "xor", "cls": OW3Xor, "secret": SECRET_OW3, "expect_legacy": False},
    {"id": "OW-4", "name": "state", "cls": OW4State, "secret": SECRET_OW4, "expect_legacy": False},
    {"id": "OW-5", "name": "sequence", "cls": OW5Sequence, "secret": SECRET_OW5, "expect_legacy": False},
    {"id": "OW-6", "name": "representation_escape", "cls": OW6RepresentationEscape, "secret": SECRET_OW6, "expect_legacy": False},
    {"id": "OW-7", "name": "noncausal", "cls": OW7Noncausal, "secret": None, "expect_legacy": True},
]


__all__ = [
    "OW1UnknownPrimitive", "OW2CompositionalFamily", "OW3Xor", "OW4State",
    "OW5Sequence", "OW6RepresentationEscape", "OW7Noncausal",
    "BENCHMARK_SPECS",
    "SECRET_OW1", "SECRET_OW2", "SECRET_OW3", "SECRET_OW4", "SECRET_OW5", "SECRET_OW6",
]
