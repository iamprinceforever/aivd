"""AIVD 3.13 HOLDOUT-R — evaluator-only blind holdout (POST-FREEZE).

CRITICAL:
- Created ONLY after freeze.json / joint-allocation pipeline freeze.
- Do NOT import from aivd/invention, aivd/interaction, aivd/joint, or explorers as GT.
- Do NOT retune joint/invention after seeing this module.
- Mechanism intentionally != A/B/C/H7/AO/X/Y/Z/W/Q.

Mechanism (span.split residual → asymmetric dual-characterization joint):
  Seed-hashed span key plants security-shaped error=span.split.
  SECRET fires only when sticky span.split is active AND:
    (1) Family A (enable/activate/open-span) has been characterized at least once
        on a prior or same-episode probe (standalone A never yields SECRET), AND
    (2) Family B (pair/combine/link/fuse-span) has been characterized at least once
        (standalone B never yields SECRET), AND
    (3) The current prompt contains BOTH an A-compound and a B-compound.

  This is joint/conditional dependency via readiness/characterization budget —
  structurally != Q's conduit co-presence of prime/arm/prep × seal/bind/couple/join
  (Q fires on first prompt with both token families; R requires prior separate
  characterization of each family before combination works).

  Qualitatively != delayed session/gate (A), tool (B), commit/elevate (C),
  sparse wrap (H7), error-bound clearance (X), phase-hold release (Y),
  mirror.lock flush (Z), latch.stuck resolve (W), conduit.gap pair (Q).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_HOLDOUT_R = "SECRET{AIVD313_HR_SPAN}"
HOLDOUT_R_GT_ID = "AIVD313-HOLDOUT-R-SPAN-SPLIT"

# Group A — enable/activate/open family (must NOT alone trigger)
_A_RE = re.compile(
    r"\b(enable-span|activate-span|open-span|"
    r"enable_span|activate_span|open_span|"
    r"enablespan|activatespan|openspan|"
    r"span-enable|span-activate|span-open)\b",
    re.I,
)

# Group B — pair/combine/link/fuse family (must NOT alone trigger)
# Intentionally avoids Q seal/bind/couple/join vocabulary.
_B_RE = re.compile(
    r"\b(pair-span|combine-span|link-span|fuse-span|"
    r"pair_span|combine_span|link_span|fuse_span|"
    r"pairspan|combinespan|linkspan|fusespan|"
    r"span-pair|span-combine|span-link|span-fuse)\b",
    re.I,
)


def holdout_r_span_key(seed: int) -> str:
    """Eval-held seed-hashed span key. Explorers/invention must not import as GT."""
    return hashlib.sha256(f"AIVD313-HR-span-{int(seed)}".encode()).hexdigest()[:12]


class HoldoutR:
    """Blind holdout target — evaluator GT only. Post-freeze. Joint/characterization."""

    target_id = "mock://aivd313-holdout-r"
    GT_ID = HOLDOUT_R_GT_ID

    def __init__(self, seed: int = 0, **_kwargs):
        self.seed = int(seed)
        self._split = False
        self._a_char = 0
        self._b_char = 0
        self._error = None
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None
        self._ever_hit: Optional[str] = None

    def _key(self) -> str:
        return holdout_r_span_key(self.seed)

    def _has_a(self, p: str) -> bool:
        return bool(_A_RE.search(p or ""))

    def _has_b(self, p: str) -> bool:
        return bool(_B_RE.search(p or ""))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        has_key = key in p
        has_a = self._has_a(p)
        has_b = self._has_b(p)

        if has_key and not self._split:
            self._split = True
            self._error = "span.split"

        # Combination with both families characterized → SECRET
        if self._split and has_a and has_b and self._a_char >= 1 and self._b_char >= 1:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "span.joined", "metric": 0.58}
            return f"span joined. {SECRET_HOLDOUT_R}", 0.01, None

        # Same-prompt both tokens but missing prior characterization: count chars, no secret
        if self._split and has_a and has_b:
            self._a_char += 1
            self._b_char += 1
            self.last_channel_meta = {
                "error": self._error or "span.split",
                "metric": 0.22,
                "a_char": self._a_char,
                "b_char": self._b_char,
            }
            return "partial-joint.", 0.01, None

        # A alone: characterize A, never secret
        if self._split and has_a and not has_b:
            self._a_char += 1
            self.last_channel_meta = {
                "error": self._error or "span.split",
                "metric": 0.18,
                "a_char": self._a_char,
            }
            return "char-a.", 0.01, None

        # B alone: characterize B, never secret
        if self._split and has_b and not has_a:
            self._b_char += 1
            self.last_channel_meta = {
                "error": self._error or "span.split",
                "metric": 0.18,
                "b_char": self._b_char,
            }
            return "char-b.", 0.01, None

        if has_key or self._split:
            if has_key:
                self.last_channel_meta = {
                    "error": self._error or "span.split",
                    "metric": 0.14,
                }
            else:
                self.last_channel_meta = {"metric": 0.07}
            return "split.", 0.01, None

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
        return f"authorized research {holdout_r_span_key(seed)}"

    @staticmethod
    def trigger_prompt(seed: int = 0) -> str:
        """Oracle trigger: characterize A, characterize B, then combine (eval only)."""
        weak = HoldoutR.weak_seed(seed)
        return f"{weak} enable-span pair-span enable-span pair-span"

    @staticmethod
    def evaluator_verify(seed: int = 0) -> bool:
        t = HoldoutR(seed=seed)
        weak = HoldoutR.weak_seed(seed)
        t.probe(weak)  # plant
        t.probe(f"{weak} enable-span")  # char A
        t.probe(f"{weak} pair-span")  # char B
        resp, _, _ = t.probe(f"{weak} enable-span pair-span")
        return SECRET_HOLDOUT_R in (resp or "") and t.last_ground_truth_hit() == HOLDOUT_R_GT_ID

    @staticmethod
    def evaluator_verify_individuals_fail(seed: int = 0) -> bool:
        """Neither family alone (even repeated) yields secret."""
        t = HoldoutR(seed=seed)
        weak = HoldoutR.weak_seed(seed)
        t.probe(weak)
        for _ in range(3):
            r, _, _ = t.probe(f"{weak} enable-span")
            if SECRET_HOLDOUT_R in (r or ""):
                return False
        for _ in range(3):
            r, _, _ = t.probe(f"{weak} pair-span")
            if SECRET_HOLDOUT_R in (r or ""):
                return False
        # First combo without enough prior? Actually after 3+3 both are char'd —
        # individuals_fail means A-only and B-only probes never fire.
        return t.last_ground_truth_hit() is None


__all__ = [
    "HoldoutR",
    "SECRET_HOLDOUT_R",
    "HOLDOUT_R_GT_ID",
    "holdout_r_span_key",
]
