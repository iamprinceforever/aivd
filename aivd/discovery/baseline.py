"""Bounded baseline sampling and variance estimates per region."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from aivd.discovery.features import BehavioralFeatures, extract_features


@dataclass
class BaselineEstimate:
    region_id: str
    n_samples: int = 0
    mean_security: float = 0.0
    var_security: float = 0.0
    mean_cue: float = 0.0
    var_cue: float = 0.0
    mean_behavioral: list[float] = field(default_factory=list)
    var_behavioral: float = 0.0
    samples: list[float] = field(default_factory=list)


@dataclass
class BaselineSampler:
    """Collect cheap baselines; never fabricate variance from n=1."""

    max_samples_per_region: int = 6
    _baselines: dict[str, BaselineEstimate] = field(default_factory=dict)

    def record(
        self,
        region_id: str,
        features: BehavioralFeatures,
    ) -> BaselineEstimate:
        rid = str(region_id)
        est = self._baselines.get(rid) or BaselineEstimate(region_id=rid)
        if est.n_samples >= self.max_samples_per_region:
            return est
        est.samples.append(float(features.security_score))
        est.n_samples = len(est.samples)
        arr = np.asarray(est.samples, dtype=np.float64)
        est.mean_security = float(np.mean(arr))
        est.var_security = float(np.var(arr)) if est.n_samples >= 2 else 0.0
        # cue running stats
        cue = float(features.security_cue_strength)
        prev_n = est.n_samples - 1
        if prev_n <= 0:
            est.mean_cue = cue
            est.var_cue = 0.0
        else:
            old_mean = est.mean_cue
            est.mean_cue = old_mean + (cue - old_mean) / est.n_samples
            # Welford-ish cue var (approx from security samples length)
            est.var_cue = max(0.0, 0.5 * est.var_cue + 0.5 * (cue - old_mean) ** 2) if est.n_samples >= 2 else 0.0
        vec = features.behavioral_only()
        if not est.mean_behavioral:
            est.mean_behavioral = list(vec)
            est.var_behavioral = 0.0
        else:
            mb = np.asarray(est.mean_behavioral, dtype=np.float64)
            v = np.asarray(vec, dtype=np.float64)
            mb = mb + (v - mb) / est.n_samples
            est.mean_behavioral = mb.tolist()
            est.var_behavioral = float(np.mean((v - mb) ** 2)) if est.n_samples >= 2 else 0.0
        self._baselines[rid] = est
        return est

    def get(self, region_id: str) -> BaselineEstimate | None:
        return self._baselines.get(str(region_id))

    def sample_region(
        self,
        region_id: str,
        prompts: list[str],
        probe_fn: Callable[[str], tuple[str, float, str | None]],
        evaluator: Any,
        *,
        budget_charge: Callable[[], bool] | None = None,
        max_n: int = 3,
    ) -> BaselineEstimate:
        """Bounded baseline probes (charges budget if provided)."""
        for p in prompts[:max_n]:
            if budget_charge is not None and not budget_charge():
                break
            resp, lat, err = probe_fn(p)
            score = float(evaluator.evaluate(p, resp, err).score) if evaluator else 0.0
            sigs = list(getattr(evaluator.evaluate(p, resp, err), "signals", []) or []) if evaluator else []
            feats = extract_features(p, resp or "", latency_ms=lat or 0.0, security_score=score, signals=sigs)
            self.record(region_id, feats)
        return self.get(region_id) or BaselineEstimate(region_id=str(region_id))
