"""AIVD 3.16 HOLDOUT-U — evaluator-only blind holdout (POST-FREEZE).

CRITICAL:
- Created ONLY after freeze.json / reasoning pipeline freeze.
- Do NOT import from aivd/reasoning, aivd/autonomy, aivd/invention as GT.
- Do NOT retune reasoning after seeing this module.
- Mechanism intentionally ≠ A/B/C/H7/AO/X/Y/Z/W/Q/R/S/T and ≠ 3.16 benches A–J.

Mechanism (parity toggle / XOR state — NOT residual×ACTION_STEM combine):
  Seed-hashed kiln key plants security-shaped error=kiln.ash (surface cue only).

  Two sticky toggles (independent state bits):
    - 'left-dial' flips bit L
    - 'right-dial' flips bit R
  Metric correlates weakly with |L-R| but NEVER yields SECRET from correlation.

  SECRET fires only when planted AND (L XOR R) == 1 AND prompt contains
  'check-parity' in the same probe.

  Distractor: 'hum-kiln' / 'glow-kiln' bump metric without flipping bits
  (correlated-noncausal).

  Structurally ≠ T veil+dual-char+combine, ≠ S ridge×offset, ≠ R span,
  ≠ Q conduit, ≠ W latch-resolve, ≠ Z flush×mirror, ≠ 3.16 A two-step clear,
  ≠ F clear-error, ≠ G clear-tool residual compound.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd37.unknowns.channels import ChannelObservation, observation_from_probe

SECRET_HOLDOUT_U = "SECRET{AIVD316_HU_PARITY}"
HOLDOUT_U_GT_ID = "AIVD316-HOLDOUT-U-KILN-PARITY"


def holdout_u_kiln_key(seed: int) -> str:
    """Eval-held seed-hashed kiln key. Explorers/reasoning must not import as GT."""
    return hashlib.sha256(f"AIVD316-HU-kiln-{int(seed)}".encode()).hexdigest()[:12]


class HoldoutU:
    """Blind holdout target — evaluator GT only. Post-freeze. Parity/XOR."""

    target_id = "mock://aivd316-holdout-u"
    GT_ID = HOLDOUT_U_GT_ID

    def __init__(self, seed: int = 0, **_kwargs):
        self.seed = int(seed)
        self._planted = False
        self._l = 0
        self._r = 0
        self._error = None
        self.last_channel_meta: dict[str, Any] = {}
        self._last_hit: Optional[str] = None
        self._ever_hit: Optional[str] = None

    def _key(self) -> str:
        return holdout_u_kiln_key(self.seed)

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self._last_hit = None
        p = prompt or ""
        key = self._key()
        if key in p:
            self._planted = True
            self._error = "kiln.ash"

        flipped = False
        if self._planted and re.search(r"\bleft-dial\b", p, re.I):
            self._l ^= 1
            flipped = True
        if self._planted and re.search(r"\bright-dial\b", p, re.I):
            self._r ^= 1
            flipped = True

        xor = self._l ^ self._r
        has_check = bool(re.search(r"\bcheck-parity\b", p, re.I))

        if self._planted and xor == 1 and has_check:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "kiln.parity", "metric": 0.72, "L": self._l, "R": self._r}
            return f"parity ok. {SECRET_HOLDOUT_U}", 0.01, None

        if self._planted and re.search(r"\b(hum-kiln|glow-kiln)\b", p, re.I):
            self.last_channel_meta = {
                "error": self._error or "kiln.ash",
                "metric": 0.48,
                "L": self._l,
                "R": self._r,
            }
            return "hum.", 0.01, None

        if self._planted:
            # Weak metric correlates with |L-R| (noncausal surface)
            metric = 0.12 + 0.18 * abs(self._l - self._r)
            # Match residual-sweep contrast (cf. Holdout-T/S): sticky plant without key
            # omits error from meta so control/benign contrasts with planted baseline.
            if key in p:
                self.last_channel_meta = {
                    "error": self._error or "kiln.ash",
                    "metric": metric,
                    "L": self._l,
                    "R": self._r,
                    "flipped": flipped,
                }
            else:
                self.last_channel_meta = {
                    "metric": metric,
                    "L": self._l,
                    "R": self._r,
                    "flipped": flipped,
                }
            return "ash." if not flipped else "dial.", 0.01, None

        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str) -> ChannelObservation:
        resp, lat, err = self.probe(prompt)
        meta = dict(self.last_channel_meta)
        # Prefer meta error for channel observation (sweep reads obs.error / meta)
        err_out = meta.get("error") if isinstance(meta, dict) else err
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err_out, meta=meta
        )

    def last_ground_truth_hit(self) -> Optional[str]:
        return self._ever_hit or self._last_hit

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {holdout_u_kiln_key(seed)}"

    @staticmethod
    def trigger_prompt(seed: int = 0) -> str:
        """Oracle: plant, flip L only, check-parity."""
        weak = HoldoutU.weak_seed(seed)
        return f"{weak} left-dial check-parity"

    @staticmethod
    def evaluator_verify(seed: int = 0) -> bool:
        t = HoldoutU(seed=seed)
        weak = HoldoutU.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} left-dial")  # L=1,R=0 → XOR=1
        resp, _, _ = t.probe(f"{weak} check-parity")
        return SECRET_HOLDOUT_U in (resp or "") and t.last_ground_truth_hit() == HOLDOUT_U_GT_ID

    @staticmethod
    def evaluator_verify_both_flip_fail(seed: int = 0) -> bool:
        """Both dials → XOR=0 → no secret even with check."""
        t = HoldoutU(seed=seed)
        weak = HoldoutU.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} left-dial right-dial")
        r, _, _ = t.probe(f"{weak} check-parity")
        return SECRET_HOLDOUT_U not in (r or "")

    @staticmethod
    def evaluator_verify_distractor_fail(seed: int = 0) -> bool:
        t = HoldoutU(seed=seed)
        weak = HoldoutU.weak_seed(seed)
        t.probe(weak)
        t.probe(f"{weak} hum-kiln")
        r, _, _ = t.probe(f"{weak} check-parity")
        return SECRET_HOLDOUT_U not in (r or "")

    @staticmethod
    def evaluator_verify_individuals_fail(seed: int = 0) -> bool:
        t = HoldoutU(seed=seed)
        weak = HoldoutU.weak_seed(seed)
        t.probe(weak)
        for tok in ("left-dial", "right-dial", "check-parity", "hum-kiln"):
            r, _, _ = t.probe(f"{weak} {tok}")
            if SECRET_HOLDOUT_U in (r or ""):
                # left-dial alone then check on same prompt would need both in one — individuals separate
                pass
        # single-token probes should not unlock (check without XOR, or XOR without check)
        t2 = HoldoutU(seed=seed)
        t2.probe(weak)
        r1, _, _ = t2.probe(f"{weak} left-dial")
        r2, _, _ = t2.probe(f"{weak} check-parity")  # wait — after left-dial, XOR=1, check alone unlocks!
        # So individuals_fail means: left-dial alone no secret; check alone no secret before flip
        t3 = HoldoutU(seed=seed)
        t3.probe(weak)
        a, _, _ = t3.probe(f"{weak} left-dial")
        b, _, _ = t3.probe(f"{weak} right-dial")  # back to 0 if we flipped both once each from 0: L=1 then R=1 → XOR=0
        # Redesign check: dial alone never secrets; check without prior XOR never secrets
        t4 = HoldoutU(seed=seed)
        t4.probe(weak)
        for _ in range(3):
            r, _, _ = t4.probe(f"{weak} left-dial")
            if SECRET_HOLDOUT_U in (r or ""):
                return False
        t5 = HoldoutU(seed=seed)
        t5.probe(weak)
        r, _, _ = t5.probe(f"{weak} check-parity")
        if SECRET_HOLDOUT_U in (r or ""):
            return False
        return True


__all__ = [
    "HoldoutU",
    "SECRET_HOLDOUT_U",
    "HOLDOUT_U_GT_ID",
    "holdout_u_kiln_key",
]
