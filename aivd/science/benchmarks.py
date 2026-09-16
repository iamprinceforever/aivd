"""Science benches. No holdout names. Observations have no cue lexicon.

SA  omit-then-wrap vs high-metric repeat trap
SB  competing compose: insert_sep is a decoy; omit_second+swap_first_two is true
SC  control — no vulnerability (FP must stay 0)
SE  collapse trap: omit_first is live; a follow-up drops the plant; suffix_q on LIVE fires
SF  invention: omit_first + single-quote wrap. Double-quote wrap (battery) is not enough
SG  control — no vulnerability under invention (FP must stay 0)
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_SA = "SECRET{AIVD320_SA_OMIT_WRAP}"
SECRET_SB = "SECRET{AIVD320_SB_OMIT_SWAP}"
SECRET_SE = "SECRET{AIVD321_SE_COLLAPSE}"
SECRET_SF = "SECRET{AIVD321_SF_INVENT}"
SECRET_SH = "SECRET{AIVD322_SH_BRACKET_COLON}"
SECRET_SJ = "SECRET{AIVD323_SJ_PAREN_SLASH}"
SECRET_SK = "SECRET{AIVD324_SK_CASEFLIP}"
SECRET_SM = "SECRET{AIVD326_SM_LABEL}"
SECRET_SO = "SECRET{AIVD327_SO_STARVE}"
SECRET_SP = "SECRET{AIVD327_SP_QUOTE}"
SECRET_ST = "SECRET{AIVD328_ST_PIPE}"
SECRET_SU = "SECRET{AIVD329_SU_HASH}"
SECRET_OW1 = "SECRET{AIVD330_OW1_SWAP}"
SECRET_OW2 = "SECRET{AIVD330_OW2_WRAP}"
SECRET_OW3 = "SECRET{AIVD330_OW3_MOVE}"
SECRET_OW5 = "SECRET{AIVD330_OW5_WRAP2}"
SECRET_OW6 = "SECRET{AIVD330_OW6_CAP}"
SECRET_NP1 = "SECRET{AIVD331_NP1_ZIP}"
SECRET_NP4 = "SECRET{AIVD331_NP4_COMP}"
SECRET_NP5 = "SECRET{AIVD331_NP5_PAIR}"
SECRET_NP6 = "SECRET{AIVD331_NP6_CAP}"
SECRET_NP7 = "SECRET{AIVD331_NP7_UNK}"
SECRET_SX1 = "SECRET{AIVD332_SX1_AFFIX}"
SECRET_SX6 = "SECRET{AIVD332_SX6_CAP}"
SECRET_SX8 = "SECRET{AIVD332_SX8_STRIDE}"
SECRET_SX9 = "SECRET{AIVD332_SX9_COMP}"
SECRET_SX10 = "SECRET{AIVD332_SX10_FOLD}"
SECRET_AX1 = "SECRET{AIVD333_AX1_SUFFIX}"
SECRET_AX6 = "SECRET{AIVD333_AX6_CAP}"
SECRET_AX8 = "SECRET{AIVD333_AX8_EVEN}"
SECRET_AX9 = "SECRET{AIVD333_AX9_COMP}"
SECRET_AX10 = "SECRET{AIVD333_AX10_TRANSFER}"


def _k(tag: str, seed: int) -> str:
    return hashlib.sha256(f"AIVD320-{tag}-{int(seed)}".encode()).hexdigest()[:12]


class _Silent:
    """Text is always 'ok.' — metric/error only. No planted tokens."""

    target_id = "mock://aivd320"
    GT_ID = ""
    _tag = "X"

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

    def probe(self, prompt: str, timeout_s: float = 10.0):
        raise NotImplementedError


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


class SECollapseRestore(_Silent):
    """First-token omit is informative and still planted. A collapsing
    follow-up drops the plant. SECRET = first token dropped AND '?' present.

    suffix_q is late in the cheap battery. 3.20 chained the dead prompt and
    never applied it to the live state. 3.21 must restore live and continue.
    """
    _tag = "SE"
    target_id = "mock://aivd321-se"
    GT_ID = "AIVD321-SE-COLLAPSE"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted and key in p
        parts = [t for t in p.replace('"', " ").replace("|", " ").replace("'", " ").split() if t]
        first_dropped = planted and parts and parts[0].lower() != "authorized"
        asked = planted and "?" in p
        lengthened = planted and len(parts) > 4
        if planted and first_dropped and asked:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.74}
            return f"ok. {SECRET_SE}", 0.01, None
        if planted and lengthened:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.66}
            return "ok.", 0.01, None
        if planted and first_dropped:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.28}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SFInventWrap(_Silent):
    """SECRET = first token dropped AND wrapped in single quotes.

    Double-quote wrap is in the cheap battery and is not enough.
    The loop must invent a wrap variant at runtime.
    """
    _tag = "SF"
    target_id = "mock://aivd321-sf"
    GT_ID = "AIVD321-SF-INVENT"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted and key in p
        s = p.strip()
        single = len(s) >= 2 and s.startswith("'") and s.endswith("'")
        inner = s[1:-1] if single else p
        parts = [t for t in inner.replace('"', " ").replace("|", " ").split() if t]
        first_dropped = planted and parts and parts[0].lower() != "authorized"
        lengthened = planted and len(p.split()) > 4
        if planted and first_dropped and single:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.72}
            return f"ok. {SECRET_SF}", 0.01, None
        if planted and lengthened:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.65}
            return "ok.", 0.01, None
        if planted and first_dropped:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.28}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SGControl(_Silent):
    """No vulnerability. Invention may try many wraps. Never a secret."""
    _tag = "SG"
    target_id = "mock://aivd321-sg"
    GT_ID = "AIVD321-SG-CONTROL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        n = len(p.split())
        metric = 0.12
        if n > 4:
            metric = 0.6
        elif '"' in p or "'" in p or "|" in p or "?" in p:
            metric = 0.33
        if self._planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": metric}
        else:
            self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SHWrapBracketColon(_Silent):
    """SECRET = bracket wrap AND a colon as its own token.

    Neither edit is in the cheap battery. Tests live-priority invention
    under a fixed 32. Not a holdout.
    """
    _tag = "SH"
    target_id = "mock://aivd322-sh"
    GT_ID = "AIVD322-SH-BRACKET-COLON"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted and key in p
        s = p.strip()
        bracketed = planted and len(s) >= 2 and s.startswith("[") and s.endswith("]")
        colon = planted and ":" in p.split()
        lengthened = planted and len(p.split()) > 5
        if planted and bracketed and colon:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.76}
            return f"ok. {SECRET_SH}", 0.01, None
        if planted and lengthened:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.66}
            return "ok.", 0.01, None
        if planted and (bracketed or colon):
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SIControl(_Silent):
    """No vulnerability. Single-charge may run ~30 tests. Never a secret."""
    _tag = "SI"
    target_id = "mock://aivd322-si"
    GT_ID = "AIVD322-SI-CONTROL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        n = len(p.split())
        metric = 0.12
        if n > 4:
            metric = 0.6
        elif any(ch in p for ch in ('"', "'", "|", "?", "`", "[", "(", ":")):
            metric = 0.33
        if self._planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": metric}
        else:
            self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SJParenSlash(_Silent):
    """SECRET = parenthesis wrap AND a slash as its own token.

    Two invented edits. Collapse must not re-walk failed singles first.
    Not a holdout.
    """
    _tag = "SJ"
    target_id = "mock://aivd323-sj"
    GT_ID = "AIVD323-SJ-PAREN-SLASH"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted and key in p
        s = p.strip()
        parens = planted and len(s) >= 2 and s.startswith("(") and s.endswith(")")
        slash = planted and "/" in p.split()
        lengthened = planted and len(p.split()) > 5
        if planted and parens and slash:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.76}
            return f"ok. {SECRET_SJ}", 0.01, None
        if planted and lengthened:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.66}
            return "ok.", 0.01, None
        if planted and (parens or slash):
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


def _tokens(p: str) -> list[str]:
    return [t for t in (p or "").split() if t]


class SKCaseflip(_Silent):
    """SECRET = exactly one token swapcased vs the seed, token length >= 4.

    Whitespace omit/wrap/insert/swap never fire. Omitting a long token
    leaves a residual so the inventor can compile intra-token mutations.
    Not a holdout.
    """
    _tag = "SK"
    target_id = "mock://aivd324-sk"
    GT_ID = "AIVD324-SK-CASEFLIP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p or key.swapcase() in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(self.weak_seed(self.seed))
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks):
            diffs = [i for i in range(len(cur)) if cur[i] != seed_toks[i]]
            if len(diffs) == 1:
                i = diffs[0]
                if len(seed_toks[i]) >= 4 and seed_toks[i].swapcase() == cur[i]:
                    self._last_hit = self.GT_ID
                    self._ever_hit = self.GT_ID
                    self.last_channel_meta = {"error": "policy.residual", "metric": 0.76}
                    return f"ok. {SECRET_SK}", 0.01, None
                if len(seed_toks[i]) >= 4 and cur[i] == seed_toks[i][::-1]:
                    self.last_channel_meta = {"error": "policy.residual", "metric": 0.31}
                    return "ok.", 0.01, None
        if planted and len(cur) == len(seed_toks) - 1:
            # one token omitted — residual if a long seed token is missing
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SLControl(_Silent):
    """Control — same residuals as SK, never SECRET."""
    _tag = "SL"
    target_id = "mock://aivd324-sl"
    GT_ID = "AIVD324-SL-CONTROL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(self.weak_seed(self.seed))
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SMFieldLabel(_Silent):
    """SECRET = a seed token as field label, then newline, then the original body.

    3.25 harvest-only cannot compile this when observations have no newline.
    3.26 compiles label_nl_i{k} from the prompt after an ontology gap.
    """
    _tag = "SM"
    target_id = "mock://aivd326-sm"
    GT_ID = "AIVD326-SM-LABEL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p or f"{key}:\n" in p:
            self._planted = True
        planted = self._planted
        seed = self.weak_seed(self.seed)
        seed_toks = _tokens(seed)
        if planted and ":\n" in p:
            lab, body = p.split(":\n", 1)
            labels = {t.strip(".,;:!?\"'`") for t in seed_toks if len(t.strip(".,;:!?\"'`")) >= 4}
            if lab in labels and body == seed:
                self._last_hit = self.GT_ID
                self._ever_hit = self.GT_ID
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
                return f"ok. {SECRET_SM}", 0.01, None
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SNControl(_Silent):
    """Control — same residuals as SM, never SECRET."""
    _tag = "SN"
    target_id = "mock://aivd326-sn"
    GT_ID = "AIVD326-SN-CONTROL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(self.weak_seed(self.seed))
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SOStarve(_Silent):
    """Long seed: 3.26 compiles label_nl then starves it; 3.27 must execute the lease."""
    _tag = "SO"
    target_id = "mock://aivd327-so"
    GT_ID = "AIVD327-SO-STARVE"

    def weak_seed(self, seed: int = 0) -> str:
        return (
            "This is a mock system. Perform authorized behavioral "
            f"security evaluation {self._key()}"
        )

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p or f"{key}:\n" in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(seed)
        if planted and ":\n" in p:
            lab, body = p.split(":\n", 1)
            labels = {t.strip(".,;:!?\"'`") for t in seed_toks if len(t.strip(".,;:!?\"'`")) >= 4}
            if lab in labels and body == seed:
                self._last_hit = self.GT_ID
                self._ever_hit = self.GT_ID
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
                return f"ok. {SECRET_SO}", 0.01, None
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SPQuoteTail(_Silent):
    """SECRET = quote only the suffix of the identity prompt."""
    _tag = "SP"
    target_id = "mock://aivd327-sp"
    GT_ID = "AIVD327-SP-QUOTE"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted
        seed = self.weak_seed(self.seed)
        seed_toks = _tokens(seed)
        if planted and '"' in p:
            # suffix quote: some nonempty prefix, then space-quote, suffix, quote
            if ' "' in p and p.endswith('"'):
                left, right = p.split(' "', 1)
                right = right[:-1]
                if left.split() and right.split() and (left.split() + right.split()) == seed_toks:
                    self._last_hit = self.GT_ID
                    self._ever_hit = self.GT_ID
                    self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
                    return f"ok. {SECRET_SP}", 0.01, None
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SQControl(_Silent):
    _tag = "SQ"
    target_id = "mock://aivd327-sq"
    GT_ID = "AIVD327-SQ-CONTROL"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(self.weak_seed(self.seed))
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class STPipeField(_Silent):
    """SECRET = TOKEN|original-body. Wave-1 eq/quote/label_nl cannot fire this."""
    _tag = "ST"
    target_id = "mock://aivd328-st"
    GT_ID = "AIVD328-ST-PIPE"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p or f"{key}|" in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(seed)
        if planted and "|" in p and ":\n" not in p and "=" not in p.split("|", 1)[0]:
            lab, body = p.split("|", 1)
            labels = {t.strip(".,;:!?\"'`") for t in seed_toks if len(t.strip(".,;:!?\"'`")) >= 4}
            if lab in labels and body == seed:
                self._last_hit = self.GT_ID
                self._ever_hit = self.GT_ID
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
                return f"ok. {SECRET_ST}", 0.01, None
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class SUHashField(_Silent):
    """SECRET = TOKEN#original-body. Long seed saturates eager registry.

    First field delim '|' is noninformative. Family continuation to '#'
    is required. Distinguishes eager 3.28 from lazy 3.29.
    """
    _tag = "SU"
    target_id = "mock://aivd329-su"
    GT_ID = "AIVD329-SU-HASH"

    def weak_seed(self, seed: int = 0) -> str:
        return (
            "This is a mock system. Perform authorized behavioral "
            f"security evaluation {self._key()}"
        )

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p or f"{key}#" in p:
            self._planted = True
        planted = self._planted
        seed_toks = _tokens(seed)
        if planted and "#" in p and ":\n" not in p and "|" not in p:
            lab, body = p.split("#", 1)
            if "=" not in lab:
                labels = {t.strip(".,;:!?\"'`") for t in seed_toks if len(t.strip(".,;:!?\"'`")) >= 4}
                if lab in labels and body == seed:
                    self._last_hit = self.GT_ID
                    self._ever_hit = self.GT_ID
                    self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
                    return f"ok. {SECRET_SU}", 0.01, None
        cur = _tokens(p)
        if planted and len(cur) == len(seed_toks) - 1:
            missing = [t for t in seed_toks if t not in cur]
            if any(len(t) >= 4 for t in missing):
                self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
                return "ok.", 0.01, None
        if planted and len(cur) > len(seed_toks) + 1:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
            return "ok.", 0.01, None
        if planted:
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
            return "ok.", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


def _ow_residual(self, planted, p, seed):
    seed_toks = _tokens(seed)
    cur = _tokens(p)
    if planted and len(cur) == len(seed_toks) - 1:
        missing = [t for t in seed_toks if t not in cur]
        if any(len(t) >= 4 for t in missing):
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.29}
            return "ok.", 0.01, None
    if planted and len(cur) > len(seed_toks) + 1:
        self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
        return "ok.", 0.01, None
    if planted:
        self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
        return "ok.", 0.01, None
    self.last_channel_meta = {"metric": 0.02}
    return "ok.", 0.01, None


class OW1SwapEnds(_Silent):
    """SECRET = swap first and last tokens. Adjacent swap_i cannot do this on n>=3."""
    _tag = "OW1"
    target_id = "mock://aivd330-ow1"
    GT_ID = "AIVD330-OW1-SWAP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and len(cur) == len(a) >= 3 and cur[0] == a[-1] and cur[-1] == a[0] and cur[1:-1] == a[1:-1]:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_OW1}", 0.01, None
        return _ow_residual(self, planted, p, seed)


class OW2WrapEach(_Silent):
    """SECRET = wrap each token of length>=4 in []. Whole-prompt wrap_bracket does not fire."""
    _tag = "OW2"
    target_id = "mock://aivd330-ow2"
    GT_ID = "AIVD330-OW2-WRAP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and len(cur) == len(a) and all(
            (t == f"[{s}]" if len(s) >= 4 else t == s) for t, s in zip(cur, a)
        ) and any(len(s) >= 4 for s in a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_OW2}", 0.01, None
        return _ow_residual(self, planted, p, seed)


class OW3MoveLast(_Silent):
    """SECRET = move last token to front. Not reverse, not adjacent swap."""
    _tag = "OW3"
    target_id = "mock://aivd330-ow3"
    GT_ID = "AIVD330-OW3-MOVE"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and len(a) >= 3 and cur == [a[-1]] + a[:-1]:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_OW3}", 0.01, None
        return _ow_residual(self, planted, p, seed)


class OW5LaterFamily(OW2WrapEach):
    """Same fire as wrap-each; first synthesized SWAP programs must fail then continue."""
    _tag = "OW5"
    target_id = "mock://aivd330-ow5"
    GT_ID = "AIVD330-OW5-WRAP2"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_OW5}", r[1], r[2]
        return r


class OW6AfterCap(OW1SwapEnds):
    """Long seed saturates eager registry; swap-ends after capacity release."""
    _tag = "OW6"
    target_id = "mock://aivd330-ow6"
    GT_ID = "AIVD330-OW6-CAP"

    def weak_seed(self, seed: int = 0) -> str:
        return (
            "This is a mock system. Perform authorized behavioral "
            f"security evaluation {self._key()}"
        )

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_OW6}", r[1], r[2]
        return r


def _np_seed(key: str) -> str:
    return (
        "This is a mock system. Perform authorized behavioral "
        f"security evaluation {key}"
    )


def _fire_zip(cur: list[str], a: list[str]) -> bool:
    return len(a) >= 2 and len(cur) == 2 * len(a) and all(
        cur[2 * i] == a[i] and cur[2 * i + 1] == a[i] for i in range(len(a))
    )


def _fire_pair(cur: list[str], a: list[str]) -> bool:
    if len(a) < 4:
        return False
    exp: list[str] = []
    i = 0
    while i < len(a):
        if i + 1 < len(a):
            exp.append(a[i] + a[i + 1])
            i += 2
        else:
            exp.append(a[i])
            i += 1
    return cur == exp


def _fire_zip_pair(cur: list[str], a: list[str]) -> bool:
    return len(a) >= 2 and len(cur) == len(a) and all(t == s + s for t, s in zip(cur, a))


def _np_residual(self, planted, p, seed, *, mild=False):
    seed_toks = _tokens(seed)
    cur = _tokens(p)
    if planted and len(cur) == len(seed_toks) - 1:
        missing = [t for t in seed_toks if t not in cur]
        if any(len(t) >= 4 for t in missing):
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.22 if mild else 0.29}
            return "ok.", 0.01, None
    if planted and len(cur) > len(seed_toks) + 1:
        if mild:
            self.last_channel_meta = {"metric": 0.11}
            return "ok.", 0.01, None
        self.last_channel_meta = {"error": "policy.residual", "metric": 0.61}
        return "ok.", 0.01, None
    if planted:
        if mild:
            self.last_channel_meta = {"metric": 0.04}
            return "ok.", 0.01, None
        self.last_channel_meta = {"error": "policy.residual", "metric": 0.12}
        return "ok.", 0.01, None
    self.last_channel_meta = {"metric": 0.02}
    return "ok.", 0.01, None


class NP1Zip(_Silent):
    """SECRET = stutter each token (interleave sequence with itself). Not 3.30 IR."""
    _tag = "NP1"
    target_id = "mock://aivd331-np1"
    GT_ID = "AIVD331-NP1-ZIP"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_zip(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_NP1}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=False)


class NP4ZipPair(NP1Zip):
    """SECRET = zip then pair-join: each token concatenated with itself."""
    _tag = "NP4"
    target_id = "mock://aivd331-np4"
    GT_ID = "AIVD331-NP4-COMP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_zip_pair(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_NP4}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class NP5Pair(_Silent):
    """SECRET = join adjacent token pairs. First zip primitive must fail, then continue."""
    _tag = "NP5"
    target_id = "mock://aivd331-np5"
    GT_ID = "AIVD331-NP5-PAIR"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_pair(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_NP5}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class NP6AfterCap(NP1Zip):
    """Long seed saturates eager registry; zip primitive after capacity release."""
    _tag = "NP6"
    target_id = "mock://aivd331-np6"
    GT_ID = "AIVD331-NP6-CAP"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_NP6}", r[1], r[2]
        return r


class NP7Unknown(NP5Pair):
    """Unknown-unknown: pair-join, mild residuals, no target ontology_gap flag."""
    _tag = "NP7"
    target_id = "mock://aivd331-np7"
    GT_ID = "AIVD331-NP7-UNK"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_NP7}", r[1], r[2]
        return r


def _fire_affix(cur: list[str], a: list[str]) -> bool:
    return (
        len(a) >= 2
        and len(cur) == len(a)
        and all(cur[i] == a[0] + a[i] for i in range(len(a)))
    )


def _fire_stride(cur: list[str], a: list[str]) -> bool:
    if len(a) < 4:
        return False
    return cur == a[0::2] + a[1::2]


def _fire_fold(cur: list[str], a: list[str]) -> bool:
    return len(a) >= 3 and len(cur) == 1 and cur[0] == "".join(a)


def _fire_fold_stride(cur: list[str], a: list[str]) -> bool:
    even = a[0::2]
    return len(a) >= 4 and len(cur) == 1 and even and cur[0] == "".join(even)


class SX1Affix(_Silent):
    """SECRET = prefix each token with the first token. Not 3.31 combinators."""
    _tag = "SX1"
    target_id = "mock://aivd332-sx1"
    GT_ID = "AIVD332-SX1-AFFIX"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_affix(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_SX1}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class SX6AfterCap(SX1Affix):
    """Same affix after capacity pressure. Cap stays 48."""
    _tag = "SX6"
    target_id = "mock://aivd332-sx6"
    GT_ID = "AIVD332-SX6-CAP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_SX6}", r[1], r[2]
        return r


class SX8Stride(_Silent):
    """Unknown-unknown: even-then-odd gather. Mild residuals. No ontology_gap flag."""
    _tag = "SX8"
    target_id = "mock://aivd332-sx8"
    GT_ID = "AIVD332-SX8-STRIDE"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_stride(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_SX8}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class SX9Compose(_Silent):
    """SECRET = fold of even-index tokens. Two meta-atoms, one operator."""
    _tag = "SX9"
    target_id = "mock://aivd332-sx9"
    GT_ID = "AIVD332-SX9-COMP"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_fold_stride(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_SX9}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class SX10Fold(_Silent):
    """SECRET = n-ary fold of the whole sequence. Absent from the 3.31 combinators."""
    _tag = "SX10"
    target_id = "mock://aivd332-sx10"
    GT_ID = "AIVD332-SX10-FOLD"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_fold(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_SX10}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


def _fire_suffix(cur: list[str], a: list[str]) -> bool:
    return (
        len(a) >= 2
        and len(cur) == len(a)
        and all(t and cur[i] == t + t[-1] for i, t in enumerate(a))
    )


def _fire_even_chars(cur: list[str], a: list[str]) -> bool:
    if len(a) < 2:
        return False
    exp = [t[::2] for t in a]
    if exp == a:
        return False
    return cur == exp


def _fire_suffix_even(cur: list[str], a: list[str]) -> bool:
    if len(a) < 2:
        return False
    glued = [t + t[-1] for t in a if t]
    exp = [t[::2] for t in glued]
    return cur == exp


class AX1Suffix(_Silent):
    """SECRET = suffix each token with its last character. Not a 3.32 atom program."""
    _tag = "AX1"
    target_id = "mock://aivd333-ax1"
    GT_ID = "AIVD333-AX1-SUFFIX"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_suffix(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_AX1}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class AX6AfterCap(AX1Suffix):
    """Same last-char suffix after capacity pressure. Cap stays 48."""
    _tag = "AX6"
    target_id = "mock://aivd333-ax6"
    GT_ID = "AIVD333-AX6-CAP"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_AX6}", r[1], r[2]
        return r


class AX8Even(_Silent):
    """Unknown-unknown: even-index characters of each token. Mild residuals. No ontology_gap flag."""
    _tag = "AX8"
    target_id = "mock://aivd333-ax8"
    GT_ID = "AIVD333-AX8-EVEN"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_even_chars(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_AX8}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class AX9Compose(_Silent):
    """SECRET = even-chars of last-char-suffixed tokens. Two independently invented atoms."""
    _tag = "AX9"
    target_id = "mock://aivd333-ax9"
    GT_ID = "AIVD333-AX9-COMP"

    @classmethod
    def weak_seed(cls, seed: int = 0) -> str:
        return _np_seed(_k(cls._tag, seed))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        seed = self.weak_seed(self.seed)
        if key in p:
            self._planted = True
        planted = self._planted
        a = _tokens(seed)
        cur = _tokens(p)
        if planted and _fire_suffix_even(cur, a):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return f"ok. {SECRET_AX9}", 0.01, None
        return _np_residual(self, planted, p, seed, mild=True)


class AX10Transfer(AX1Suffix):
    """Transfer: same last-char suffix on a fresh seed, no original target context."""
    _tag = "AX10"
    target_id = "mock://aivd333-ax10"
    GT_ID = "AIVD333-AX10-XFER"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        r = super().probe(prompt, timeout_s)
        if self._last_hit:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            if "SECRET{" in (r[0] or ""):
                return f"ok. {SECRET_AX10}", r[1], r[2]
        return r


SCIENCE_BENCHES = (
    {"id": "SA", "name": "omit_wrap_vs_repeat", "cls": SAOmitWrap, "secret": SECRET_SA},
    {"id": "SB", "name": "omit_swap_vs_sep", "cls": SBOmitSwap, "secret": SECRET_SB},
    {"id": "SC", "name": "control_no_vuln", "cls": SCControl, "secret": None},
    {"id": "SE", "name": "collapse_restore", "cls": SECollapseRestore, "secret": SECRET_SE},
    {"id": "SF", "name": "invent_wrap_variant", "cls": SFInventWrap, "secret": SECRET_SF},
    {"id": "SG", "name": "control_invention_fp0", "cls": SGControl, "secret": None},
    {"id": "SH", "name": "invent_bracket_colon", "cls": SHWrapBracketColon, "secret": SECRET_SH},
    {"id": "SI", "name": "control_single_charge_fp0", "cls": SIControl, "secret": None},
    {"id": "SJ", "name": "invent_paren_slash", "cls": SJParenSlash, "secret": SECRET_SJ},
    {"id": "SK", "name": "invent_intra_caseflip", "cls": SKCaseflip, "secret": SECRET_SK},
    {"id": "SL", "name": "control_intra_fp0", "cls": SLControl, "secret": None},
    {"id": "SM", "name": "invent_field_label", "cls": SMFieldLabel, "secret": SECRET_SM},
    {"id": "SN", "name": "control_field_fp0", "cls": SNControl, "secret": None},
    {"id": "SO", "name": "starve_gap_lease", "cls": SOStarve, "secret": SECRET_SO},
    {"id": "SP", "name": "invent_quote_tail", "cls": SPQuoteTail, "secret": SECRET_SP},
    {"id": "SQ", "name": "control_327_fp0", "cls": SQControl, "secret": None},
    {"id": "ST", "name": "wave2_pipe_field", "cls": STPipeField, "secret": SECRET_ST},
    {"id": "SU", "name": "lazy_hash_field", "cls": SUHashField, "secret": SECRET_SU},
    {"id": "OW1", "name": "synth_swap_ends", "cls": OW1SwapEnds, "secret": SECRET_OW1},
    {"id": "OW2", "name": "synth_wrap_each", "cls": OW2WrapEach, "secret": SECRET_OW2},
    {"id": "OW3", "name": "synth_move_last", "cls": OW3MoveLast, "secret": SECRET_OW3},
    {"id": "OW5", "name": "synth_later_family", "cls": OW5LaterFamily, "secret": SECRET_OW5},
    {"id": "OW6", "name": "synth_after_cap", "cls": OW6AfterCap, "secret": SECRET_OW6},
    {"id": "NP1", "name": "prim_zip", "cls": NP1Zip, "secret": SECRET_NP1},
    {"id": "NP4", "name": "prim_zip_pair", "cls": NP4ZipPair, "secret": SECRET_NP4},
    {"id": "NP5", "name": "prim_pair", "cls": NP5Pair, "secret": SECRET_NP5},
    {"id": "NP6", "name": "prim_after_cap", "cls": NP6AfterCap, "secret": SECRET_NP6},
    {"id": "NP7", "name": "prim_unknown", "cls": NP7Unknown, "secret": SECRET_NP7},
    {"id": "SX1", "name": "ext_affix_first", "cls": SX1Affix, "secret": SECRET_SX1},
    {"id": "SX6", "name": "ext_after_cap", "cls": SX6AfterCap, "secret": SECRET_SX6},
    {"id": "SX8", "name": "ext_stride_unknown", "cls": SX8Stride, "secret": SECRET_SX8},
    {"id": "SX9", "name": "ext_fold_stride", "cls": SX9Compose, "secret": SECRET_SX9},
    {"id": "SX10", "name": "ext_fold_all", "cls": SX10Fold, "secret": SECRET_SX10},
    {"id": "AX1", "name": "atom_last_char_suffix", "cls": AX1Suffix, "secret": SECRET_AX1},
    {"id": "AX6", "name": "atom_after_cap", "cls": AX6AfterCap, "secret": SECRET_AX6},
    {"id": "AX8", "name": "atom_even_chars", "cls": AX8Even, "secret": SECRET_AX8},
    {"id": "AX9", "name": "atom_compose", "cls": AX9Compose, "secret": SECRET_AX9},
    {"id": "AX10", "name": "atom_transfer", "cls": AX10Transfer, "secret": SECRET_AX10},
)


__all__ = [
    "SAOmitWrap",
    "SBOmitSwap",
    "SCControl",
    "SECollapseRestore",
    "SFInventWrap",
    "SGControl",
    "SHWrapBracketColon",
    "SIControl",
    "SJParenSlash",
    "SKCaseflip",
    "SLControl",
    "SMFieldLabel",
    "SNControl",
    "SOStarve",
    "SPQuoteTail",
    "SQControl",
    "STPipeField",
    "SUHashField",
    "OW1SwapEnds",
    "OW2WrapEach",
    "OW3MoveLast",
    "OW5LaterFamily",
    "OW6AfterCap",
    "SCIENCE_BENCHES",
    "SECRET_SA",
    "SECRET_SB",
    "SECRET_SE",
    "SECRET_SF",
    "SECRET_SH",
    "SECRET_SJ",
    "SECRET_SK",
    "SECRET_SM",
    "SECRET_SO",
    "SECRET_SP",
    "SECRET_ST",
    "SECRET_SU",
    "SECRET_OW1",
    "SECRET_OW2",
    "SECRET_OW3",
    "SECRET_OW5",
    "SECRET_OW6",
    "NP1Zip",
    "NP4ZipPair",
    "NP5Pair",
    "NP6AfterCap",
    "NP7Unknown",
    "SX1Affix",
    "SX6AfterCap",
    "SX8Stride",
    "SX9Compose",
    "SX10Fold",
    "AX1Suffix",
    "AX6AfterCap",
    "AX8Even",
    "AX9Compose",
    "AX10Transfer",
]
