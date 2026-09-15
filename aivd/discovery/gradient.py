"""Behavioral gradients and perturbation distance (security tracked separately)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from aivd.discovery.features import BehavioralFeatures


@dataclass
class BehavioralDelta:
    behavioral_distance: float
    security_delta: float
    cue_delta: float
    composite: float  # behavioral + separate security term


def behavioral_delta(a: BehavioralFeatures, b: BehavioralFeatures) -> BehavioralDelta:
    va = np.asarray(a.behavioral_only(), dtype=np.float64)
    vb = np.asarray(b.behavioral_only(), dtype=np.float64)
    n = min(len(va), len(vb))
    dist = float(np.linalg.norm(va[:n] - vb[:n]) / max(1.0, np.sqrt(n)))
    sec = float(b.security_score - a.security_score)
    cue = float(b.security_cue_strength - a.security_cue_strength)
    # Composite: prefer behavioral change that also moves security/cue — but don't let novelty alone dominate
    composite = dist + 0.5 * abs(sec) + 0.4 * abs(cue)
    return BehavioralDelta(behavioral_distance=dist, security_delta=sec, cue_delta=cue, composite=composite)


def perturbation_distance(prompt_a: str, prompt_b: str) -> float:
    """Cheap lexical perturbation distance in [0,1]."""
    ta = set(prompt_a.lower().split())
    tb = set(prompt_b.lower().split())
    if not ta and not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb) or 1
    jaccard = inter / union
    len_ratio = abs(len(prompt_a) - len(prompt_b)) / max(1, max(len(prompt_a), len(prompt_b)))
    return float(min(1.0, (1.0 - jaccard) * 0.7 + len_ratio * 0.3))


def gradient_direction(
    history: Sequence[tuple[BehavioralFeatures, float]],
) -> dict[str, float]:
    """Estimate which dims correlate with rising security/cue along a trajectory."""
    if len(history) < 2:
        return {}
    dims = [
        "input_length", "input_token_diversity", "input_encoding_hint",
        "output_length", "output_novelty", "security_cue_strength",
    ]
    out: dict[str, float] = {}
    for d in dims:
        xs, ys = [], []
        for feats, y in history:
            xs.append(float(getattr(feats, d, 0.0)))
            ys.append(float(y))
        if len(set(xs)) < 2:
            out[d] = 0.0
            continue
        x = np.asarray(xs, dtype=np.float64)
        yarr = np.asarray(ys, dtype=np.float64)
        x = (x - x.mean()) / (x.std() + 1e-8)
        yarr = (yarr - yarr.mean()) / (yarr.std() + 1e-8)
        out[d] = float(np.clip(np.mean(x * yarr), -1.0, 1.0))
    return out
