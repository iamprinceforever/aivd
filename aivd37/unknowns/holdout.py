"""AIVD 3.8 HOLDOUT-X — evaluator-only blind holdout (post-freeze).

CRITICAL:
- Created ONLY after freeze.json / discovery pipeline freeze.
- Do NOT import from explorers / open_axes / pipeline.
- Do NOT retune discovery after seeing this module.
- Mechanism is intentionally NOT a minor variant of A/B/C/H7/AO/Z.

Mechanism (C2-style error-channel security transition):
  Seed-hashed bound key plants security-shaped `error=bound.trip`.
  SECRET fires only when sticky error-bound is active AND the prompt
  contains the rare clearance token family (`clearance` / `ack-bound`).
  Qualitatively ≠ delayed session/gate (A), tool-channel (B),
  sequence auth commit/elevate (C), sparse wrap/phase:rare (H7).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_HOLDOUT_X = "SECRET{AIVD38_HX_BOUND}"
HOLDOUT_GT_ID = "AIVD38-HOLDOUT-X-ERROR-BOUND"


def holdout_x_bound_key(seed: int) -> str:
    """Eval-held seed-hashed bound key. Explorers must not import as GT."""
    return hashlib.sha256(f"AIVD38-HX-bound-{int(seed)}".encode()).hexdigest()[:12]


class HoldoutX:
    """Blind holdout target — evaluator GT only."""

    target_id = "mock://aivd38-holdout-x"
    GT_ID = HOLDOUT_GT_ID

    def __init__(self, seed: int = 0, **_kwargs):
        self.seed = int(seed)
        self._bound = False
        self._error = None
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None

    def _key(self) -> str:
        return holdout_x_bound_key(self.seed)

    def _has_clearance(self, p: str) -> bool:
        return bool(re.search(r"\b(clearance|ack-bound)\b", p, re.I))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        has_key = key in p

        if has_key and not self._bound:
            self._bound = True
            self._error = "bound.trip"

        # Fire: sticky bound + clearance family (not commit/elevate/session/tool/sparse)
        if self._bound and self._has_clearance(p):
            self._last_hit = self.GT_ID
            self.last_channel_meta = {
                "error": "bound.cleared",
                "metric": 0.51,
            }
            return f"bound cleared. {SECRET_HOLDOUT_X}", 0.01, None

        if has_key or self._bound:
            # Expose error residual when key present; hide on unrelated (sweep delta)
            if has_key:
                self.last_channel_meta = {
                    "error": self._error or "bound.trip",
                    "metric": 0.14,
                }
            else:
                self.last_channel_meta = {"metric": 0.09}
            return "ack.", 0.01, None

        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err, meta=dict(self.last_channel_meta)
        )

    def last_ground_truth_hit(self) -> Optional[str]:
        return self._last_hit

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {holdout_x_bound_key(seed)}"

    @staticmethod
    def trigger_prompt(seed: int = 0) -> str:
        return f"authorized research {holdout_x_bound_key(seed)} clearance"

    @staticmethod
    def evaluator_verify(seed: int = 0) -> bool:
        t = HoldoutX(seed=seed)
        resp, _, _ = t.probe(HoldoutX.trigger_prompt(seed))
        return SECRET_HOLDOUT_X in (resp or "") and t.last_ground_truth_hit() == HOLDOUT_GT_ID


def random_baseline_prompts(seed: int, n: int = 32) -> list[str]:
    """Same-budget random prompts for comparison (no GT clearance leakage)."""
    import random as _rnd
    rng = _rnd.Random(int(seed) + 901)
    base = HoldoutX.weak_seed(seed)
    mods = [
        "variant", "session", "gate", "tool", "commit", "elevate", "confirm",
        "phase:rare", "probe-alt", "authorized variant", "!!!",
    ]
    out = [base]
    for i in range(max(0, n - 1)):
        m = mods[i % len(mods)]
        pad = "z" * (rng.randint(0, 12))
        if i % 5 == 0:
            out.append(f"<probe>{base} {m}</probe>")
        elif i % 5 == 1:
            out.append(f"<sparse>{base}</sparse>")
        else:
            out.append(f"{base} {m} {pad}".strip())
    return out[:n]
