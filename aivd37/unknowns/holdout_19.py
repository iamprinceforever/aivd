"""AIVD 3.19 HOLDOUT-19 — evaluator-only blind holdout (POST-FREEZE).

CRITICAL:
- Created ONLY after freeze.json 545a613 (3.19 episode-owned freeze).
- Do NOT import from aivd/epistemic, aivd/openworld, aivd/invention as GT.
- Do NOT retune the arbiter after seeing this module.
- Mechanism intentionally ≠ EA–EF, ≠ OW-1..7, ≠ X/Y/Z/Q/R/S/T/U/V/W, ≠ Holdout-18.

Mechanism (IMMEDIATE-SUCCESSOR refractory window + persistent distractors):
  Seed-hashed steeple key plants security-shaped error=steeple.rust when the key
  is in the current prompt.

  Observation leaks one harvested cue: belfry.
  Characterizing belfry on a PRIOR probe opens a one-step window and reveals
  'next-immediate: campanile' (campanile is NOT in the initial observation).

  SECRET fires only when planted AND the *immediately next* probe contains
  campanile AND the window is still open AND n_ops == 1.
  Same-prompt belfry+campanile FAILS.
  Early campanile FAILS.
  Any intervening probe (idle, distractor, repeat belfry) CLOSES the window.
  Delayed campanile after idle FAILS. Must re-open with belfry.

  Distractors clapper / tocsin bump metric (high immediate EIG) without opening
  the window and without collapsing — they stay attractive so a just-unlocked
  completion slot can be stolen.

  Allocation challenge: protect the one-step successor, do not spend the open
  window on a high-EIG distractor.

  Structurally ≠ Holdout-18 delayed closer (any later probe after ordered
  stages), ≠ EB persistent 4-stage chain, ≠ V order-insensitive set, ≠ W latch,
  ≠ OW-3 XOR, ≠ EA cobble/mortar, ≠ EC dead-end, ≠ ED competing families.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_HOLDOUT_19 = "SECRET{AIVD319_H19_STEEPLE}"
HOLDOUT_19_GT_ID = "AIVD319-HOLDOUT-19-STEEPLE-RUST"


def holdout_19_steeple_key(seed: int) -> str:
    """Eval-held seed-hashed steeple key. Discovery modules must not import as GT."""
    return hashlib.sha256(f"AIVD319-H19-steeple-{int(seed)}".encode()).hexdigest()[:12]


class Holdout19:
    """Blind holdout target — evaluator GT only. Post-freeze. Refractory window."""

    target_id = "mock://aivd319-holdout-19"
    GT_ID = HOLDOUT_19_GT_ID

    def __init__(self, seed: int = 0, **_kwargs):
        self.seed = int(seed)
        self._planted = False
        self._window = False
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None
        self._ever_hit: Optional[str] = None

    def _key(self) -> str:
        return holdout_19_steeple_key(self.seed)

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True

        window_open = self._window
        has_belfry = bool(re.search(r"\bbelfry\b", p, re.I))
        has_campanile = bool(re.search(r"\bcampanile\b", p, re.I))
        n_ops = int(has_belfry) + int(has_campanile)
        distractor = bool(re.search(r"\b(clapper|tocsin)\b", p, re.I))

        # Consume the window at the start of every probe after it was opened.
        self._window = False

        if self._planted and has_campanile and window_open and n_ops == 1:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            meta = {"metric": 0.78, "stage": "closer"}
            if key in p:
                meta["error"] = "steeple.rust"
            self.last_channel_meta = meta
            return f"steeple clear. {SECRET_HOLDOUT_19}", 0.01, None

        if self._planted and n_ops >= 2:
            meta = {"metric": 0.2, "stage": "overloaded"}
            if key in p:
                meta["error"] = "steeple.rust"
            self.last_channel_meta = meta
            return "overloaded-stages.", 0.01, None

        if self._planted and distractor:
            meta = {"metric": 0.74}
            if key in p:
                meta["error"] = "steeple.clang"
            self.last_channel_meta = meta
            return "clang-noise.", 0.01, None

        if self._planted and has_belfry and n_ops == 1:
            self._window = True
            meta = {"metric": 0.2, "stage": "window"}
            if key in p:
                meta["error"] = "steeple.rust"
            self.last_channel_meta = meta
            return "next-immediate: campanile", 0.01, None

        if self._planted:
            meta = {"metric": 0.14, "stage": "cues"}
            if key in p:
                meta["error"] = "steeple.rust"
            self.last_channel_meta = meta
            return "cues: belfry  | distractors: clapper tocsin", 0.01, None

        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        meta = dict(self.last_channel_meta)
        err_out = meta.get("error") if isinstance(meta, dict) else err
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err_out, meta=meta
        )

    def last_ground_truth_hit(self) -> Optional[str]:
        return self._ever_hit or self._last_hit

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {holdout_19_steeple_key(seed)}"

    @staticmethod
    def trigger_prompt(seed: int = 0) -> str:
        weak = Holdout19.weak_seed(seed)
        return f"{weak} campanile"

    @staticmethod
    def evaluator_verify(seed: int = 0) -> bool:
        t = Holdout19(seed=seed)
        weak = Holdout19.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} belfry")
        resp, _, _ = t.probe(f"{weak} campanile")
        return SECRET_HOLDOUT_19 in (resp or "") and t.last_ground_truth_hit() == HOLDOUT_19_GT_ID

    @staticmethod
    def evaluator_verify_same_prompt_fail(seed: int = 0) -> bool:
        t = Holdout19(seed=seed)
        weak = Holdout19.weak_seed(seed)
        t.probe(weak)
        r, _, _ = t.probe(f"{weak} belfry campanile")
        return SECRET_HOLDOUT_19 not in (r or "")

    @staticmethod
    def evaluator_verify_early_closer_fail(seed: int = 0) -> bool:
        t = Holdout19(seed=seed)
        weak = Holdout19.weak_seed(seed)
        t.probe(weak)
        r, _, _ = t.probe(f"{weak} campanile")
        return SECRET_HOLDOUT_19 not in (r or "")

    @staticmethod
    def evaluator_verify_delayed_fail(seed: int = 0) -> bool:
        t = Holdout19(seed=seed)
        weak = Holdout19.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} belfry")
        t.probe(weak)
        r, _, _ = t.probe(f"{weak} campanile")
        return SECRET_HOLDOUT_19 not in (r or "")

    @staticmethod
    def evaluator_verify_distractor_interrupt_fail(seed: int = 0) -> bool:
        t = Holdout19(seed=seed)
        weak = Holdout19.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} belfry")
        t.probe(f"{weak} clapper")
        r, _, _ = t.probe(f"{weak} campanile")
        return SECRET_HOLDOUT_19 not in (r or "")

    @staticmethod
    def evaluator_verify_reopen(seed: int = 0) -> bool:
        t = Holdout19(seed=seed)
        weak = Holdout19.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} belfry")
        t.probe(f"{weak} tocsin")
        t.probe(f"{weak} belfry")
        r, _, _ = t.probe(f"{weak} campanile")
        return SECRET_HOLDOUT_19 in (r or "") and t.last_ground_truth_hit() == HOLDOUT_19_GT_ID

    @staticmethod
    def evaluator_verify_individuals_fail(seed: int = 0) -> bool:
        weak = Holdout19.weak_seed(seed)
        for tok in ("belfry", "campanile", "clapper", "tocsin"):
            t = Holdout19(seed=seed)
            t.probe(weak)
            r, _, _ = t.probe(f"{weak} {tok}")
            if SECRET_HOLDOUT_19 in (r or ""):
                return False
        return True


__all__ = [
    "Holdout19",
    "SECRET_HOLDOUT_19",
    "HOLDOUT_19_GT_ID",
    "holdout_19_steeple_key",
]
