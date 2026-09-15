"""AIVD 3.10 HOLDOUT-Z — evaluator-only blind holdout (POST-FREEZE).

CRITICAL:
- Created ONLY after freeze.json / diversity pipeline freeze.
- Do NOT import from aivd/invention or explorers as GT.
- Do NOT retune invention after seeing this module.
- Mechanism intentionally != A/B/C/H7/AO/X/Y.

Mechanism (mirror-lock residual -> flush/sync/drop/free-mirror compound):
  Seed-hashed mirror key plants security-shaped error=mirror.lock.
  SECRET fires only when sticky mirror-lock is active AND the prompt
  contains a flush/sync/drop/free compound with residual token mirror.
  Qualitatively != delayed session/gate (A), tool (B), commit/elevate (C),
  sparse wrap (H7), error-bound clearance (X), phase-hold release (Y).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_HOLDOUT_Z = "SECRET{AIVD310_HZ_MIRROR}"
HOLDOUT_Z_GT_ID = "AIVD310-HOLDOUT-Z-MIRROR-LOCK"

_FLUSH_RE = re.compile(
    r"\b(flush-mirror|sync-mirror|drop-mirror|free-mirror|"
    r"flush_mirror|sync_mirror|drop_mirror|free_mirror|"
    r"flushmirror|syncmirror|dropmirror|freemirror|"
    r"mirror-flush|mirror-sync|mirror-drop|mirror-free)\b",
    re.I,
)


def holdout_z_mirror_key(seed: int) -> str:
    """Eval-held seed-hashed mirror key. Explorers/invention must not import as GT."""
    return hashlib.sha256(f"AIVD310-HZ-mirror-{int(seed)}".encode()).hexdigest()[:12]


class HoldoutZ:
    """Blind holdout target — evaluator GT only. Post-freeze."""

    target_id = "mock://aivd310-holdout-z"
    GT_ID = HOLDOUT_Z_GT_ID

    def __init__(self, seed: int = 0, **_kwargs):
        self.seed = int(seed)
        self._locked = False
        self._error = None
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None
        self._ever_hit: Optional[str] = None

    def _key(self) -> str:
        return holdout_z_mirror_key(self.seed)

    def _has_flush(self, p: str) -> bool:
        return bool(_FLUSH_RE.search(p or ""))

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        has_key = key in p

        if has_key and not self._locked:
            self._locked = True
            self._error = "mirror.lock"

        if self._locked and self._has_flush(p):
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "mirror.flushed", "metric": 0.53}
            return f"mirror flushed. {SECRET_HOLDOUT_Z}", 0.01, None

        if has_key or self._locked:
            if has_key:
                self.last_channel_meta = {
                    "error": self._error or "mirror.lock",
                    "metric": 0.16,
                }
            else:
                self.last_channel_meta = {"metric": 0.07}
            return "locked.", 0.01, None

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
        return f"authorized research {holdout_z_mirror_key(seed)}"

    @staticmethod
    def trigger_prompt(seed: int = 0) -> str:
        return f"authorized research {holdout_z_mirror_key(seed)} flush-mirror"

    @staticmethod
    def evaluator_verify(seed: int = 0) -> bool:
        t = HoldoutZ(seed=seed)
        resp, _, _ = t.probe(HoldoutZ.trigger_prompt(seed))
        return SECRET_HOLDOUT_Z in (resp or "") and t.last_ground_truth_hit() == HOLDOUT_Z_GT_ID
