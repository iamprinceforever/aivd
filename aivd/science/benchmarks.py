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
]
