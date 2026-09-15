"""Priority history — decay (not blacklist) and revival for adaptive ordering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PriorityRecord:
    """Per-candidate or per-family priority trajectory."""
    key: str
    priority: float = 0.5
    n_updates: int = 0
    n_tests: int = 0
    n_success: int = 0
    sum_effect: float = 0.0
    decayed: bool = False
    revived: bool = False
    last_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "priority": self.priority,
            "n_updates": self.n_updates,
            "n_tests": self.n_tests,
            "n_success": self.n_success,
            "mean_effect": self.sum_effect / max(1, self.n_tests),
            "decayed": self.decayed,
            "revived": self.revived,
            "last_reason": self.last_reason,
        }


@dataclass
class PriorityHistory:
    """Tracks priority with decay (revisitable) — never hard-blacklist."""
    records: dict[str, PriorityRecord] = field(default_factory=dict)
    # Decay toward prior; never clamps to permanent zero
    decay_rate: float = 0.18
    floor: float = 0.05
    revival_boost: float = 0.35
    success_boost: float = 0.25
    failure_penalty: float = 0.12

    def ensure(self, key: str, *, initial: float = 0.5) -> PriorityRecord:
        if key not in self.records:
            self.records[key] = PriorityRecord(key=key, priority=float(initial))
        return self.records[key]

    def get_priority(self, key: str, default: float = 0.5) -> float:
        r = self.records.get(key)
        return float(r.priority) if r else float(default)

    def decay(self, key: str, *, reason: str = "idle_decay") -> float:
        """Soft decay toward floor — revisitable, not blacklist."""
        r = self.ensure(key)
        r.priority = max(self.floor, r.priority * (1.0 - self.decay_rate))
        r.decayed = True
        r.n_updates += 1
        r.last_reason = reason
        return r.priority

    def decay_all_except(self, keep: set[str] | None = None, *, reason: str = "step_decay") -> None:
        keep = keep or set()
        for key in list(self.records.keys()):
            if key not in keep:
                self.decay(key, reason=reason)

    def observe(
        self,
        key: str,
        *,
        effect: float,
        success: bool,
        reason: str = "observe",
    ) -> float:
        r = self.ensure(key)
        r.n_tests += 1
        r.n_updates += 1
        r.sum_effect += float(effect)
        if success or effect >= 0.25:
            r.n_success += 1
            # Mild echoes (e.g. 0.25–0.45) must not lock search — scale boost by effect
            boost_scale = float(effect) if effect >= 0.5 else 0.35 * float(effect)
            r.priority = min(1.0, r.priority + self.success_boost * max(0.05, boost_scale))
            r.decayed = False
        else:
            # penalty with floor — still revisitable
            r.priority = max(self.floor, r.priority - self.failure_penalty)
            r.decayed = r.priority <= self.floor + 1e-9
        r.last_reason = reason
        return r.priority

    def revive(self, key: str, *, reason: str = "evidence_revival") -> float:
        """Revive a decayed priority on new residual evidence — not a blacklist clear."""
        r = self.ensure(key)
        r.priority = min(1.0, max(r.priority, self.floor) + self.revival_boost)
        r.revived = True
        r.decayed = False
        r.n_updates += 1
        r.last_reason = reason
        return r.priority

    def revive_matching(self, tokens: list[str] | None, key_features: dict[str, dict[str, Any]]) -> list[str]:
        """Revive keys whose features overlap evidence tokens (structural, not GT)."""
        if not tokens:
            return []
        toks = {str(t).lower() for t in tokens if t}
        revived: list[str] = []
        for key, feats in key_features.items():
            stem = str((feats or {}).get("stem_bucket") or "").lower()
            surface = str((feats or {}).get("surface") or "")
            r = self.records.get(key)
            if r is None:
                continue
            if not r.decayed and r.priority > self.floor + 0.1:
                continue
            hit = False
            if stem and (stem in toks or any(t in stem for t in toks if len(t) >= 3)):
                hit = True
            elif surface.startswith("compound") and toks:
                hit = True
            if hit:
                self.revive(key, reason="evidence_overlap")
                revived.append(key)
        return revived

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_records": len(self.records),
            "decay_rate": self.decay_rate,
            "floor": self.floor,
            "records": {k: v.as_dict() for k, v in self.records.items()},
            "note": "Priority decay is revisitable; never a hard blacklist.",
        }
