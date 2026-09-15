"""ResidualSignal / ActionSignal — abstract cross-signal evidence units.

IDs are opaque; randomized remapping must preserve behavior (anti-mapping).
No Holdout-named rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import time


@dataclass
class ResidualSignal:
    """Weak residual / behavioral evidence (not a vulnerability claim)."""

    signal_id: str = ""
    channel: str = ""
    residual_text: str = ""
    strength: float = 0.0
    uncertainty: float = 0.9
    n_observations: int = 0
    timestamp: float = 0.0
    features: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.signal_id:
            blob = f"R|{self.channel}|{self.residual_text}|{time.time_ns()}"
            self.signal_id = hashlib.sha256(blob.encode()).hexdigest()[:12]
        if not self.timestamp:
            self.timestamp = time.time()

    def observe(self, *, strength: float | None = None, **feats: float) -> None:
        self.n_observations += 1
        if strength is not None:
            # EMA update
            a = 0.4
            self.strength = a * float(strength) + (1 - a) * self.strength
        for k, v in feats.items():
            prev = float(self.features.get(k) or 0.0)
            self.features[k] = 0.5 * prev + 0.5 * float(v)
        self.uncertainty = max(0.05, 0.9 / (1.0 + 0.35 * self.n_observations))

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "kind": "residual",
            "channel": self.channel,
            "residual_text": self.residual_text,
            "strength": self.strength,
            "uncertainty": self.uncertainty,
            "n_observations": self.n_observations,
            "timestamp": self.timestamp,
            "features": dict(self.features),
            "meta": dict(self.meta),
        }


@dataclass
class ActionSignal:
    """Action / stem region evidence (underexplored controllable side)."""

    signal_id: str = ""
    family_id: str = ""
    stem: str = ""
    region: str = ""
    strength: float = 0.0
    uncertainty: float = 0.9
    n_probes: int = 0
    n_variants: int = 0
    effect_mean: float = 0.0
    timestamp: float = 0.0
    features: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.signal_id:
            blob = f"A|{self.family_id}|{self.stem}|{self.region}|{time.time_ns()}"
            self.signal_id = hashlib.sha256(blob.encode()).hexdigest()[:12]
        if not self.region:
            self.region = self.family_id or self.stem or "unknown"
        if not self.timestamp:
            self.timestamp = time.time()

    def observe(self, *, effect: float = 0.0, variant: str | None = None) -> None:
        self.n_probes += 1
        if variant:
            seen = self.meta.setdefault("variants", [])
            if variant not in seen:
                seen.append(variant)
            self.n_variants = len(seen)
        a = 0.4
        self.effect_mean = a * float(effect) + (1 - a) * self.effect_mean
        self.strength = max(self.strength, min(1.0, abs(self.effect_mean) + 0.05 * self.n_probes))
        self.uncertainty = max(
            0.05,
            0.9 / (1.0 + 0.3 * self.n_probes + 0.2 * self.n_variants),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "kind": "action",
            "family_id": self.family_id,
            "stem": self.stem,
            "region": self.region,
            "strength": self.strength,
            "uncertainty": self.uncertainty,
            "n_probes": self.n_probes,
            "n_variants": self.n_variants,
            "effect_mean": self.effect_mean,
            "timestamp": self.timestamp,
            "features": dict(self.features),
            "meta": dict(self.meta),
        }


def remap_signal_id(sig_id: str, mapping: dict[str, str]) -> str:
    """Apply anti-mapping remapping; unknown IDs pass through."""
    return mapping.get(sig_id, sig_id)


__all__ = [
    "ResidualSignal",
    "ActionSignal",
    "remap_signal_id",
]
