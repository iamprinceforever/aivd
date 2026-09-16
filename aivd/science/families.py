"""Lazy intervention-family inventory.

Hypothesis space is stored at family granularity. Concrete instances occupy
the executable registry only when materialized. Rejected instances release
those slots. Remaining parameterizations stay symbolic — not enumerated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


def _canon(param: Any) -> str:
    if isinstance(param, str):
        return param
    return repr(param)


@dataclass
class InterventionFamily:
    family_id: str
    question_id: str = ""
    remaining: list[Any] = field(default_factory=list)
    tested: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    materialized_ops: list[str] = field(default_factory=list)
    generated: int = 0
    materialized: int = 0
    executed: int = 0
    continuation: int = 0
    max_generated: int = 4
    state: str = "DORMANT"
    why: str = ""
    param_of: dict[str, str] = field(default_factory=dict)


@dataclass
class FamilyInventory:
    families: dict[str, InterventionFamily] = field(default_factory=dict)
    events: list[dict[str, str]] = field(default_factory=list)
    duplicate_events: int = 0
    wakeups: int = 0
    capacity_releases: int = 0
    deferred: int = 0
    generation_events: int = 0
    occupancy_peak: int = 0

    def remember(
        self,
        family_id: str,
        remaining: list[Any],
        *,
        question_id: str = "",
        why: str = "",
        max_generated: int = 4,
    ) -> InterventionFamily:
        if family_id in self.families:
            return self.families[family_id]
        fam = InterventionFamily(
            family_id=family_id,
            question_id=question_id,
            remaining=list(remaining),
            state="DORMANT",
            why=why,
            max_generated=int(max_generated),
        )
        self.families[family_id] = fam
        self.deferred += 1
        self.events.append({
            "event": "family_remember",
            "family": family_id,
            "remaining": str(len(remaining)),
            "why": why,
        })
        return fam

    def next_param(self, family_id: str) -> Any | None:
        fam = self.families.get(family_id)
        if fam is None:
            return None
        if fam.generated >= fam.max_generated:
            fam.state = "EXHAUSTED"
            return None
        while fam.remaining:
            param = fam.remaining.pop(0)
            key = _canon(param)
            if key in fam.tested or key in fam.rejected:
                self.duplicate_events += 1
                continue
            fam.generated += 1
            self.generation_events += 1
            fam.state = "ACTIVE"
            return param
        fam.state = "EXHAUSTED"
        return None

    def mark_materialized(self, family_id: str, param: Any, op: str) -> None:
        fam = self.families.get(family_id)
        if fam is None:
            return
        fam.materialized += 1
        fam.materialized_ops.append(op)
        fam.tested.append(_canon(param))
        fam.param_of[op] = _canon(param)
        self.events.append({
            "event": "lazy_materialize",
            "family": family_id,
            "op": op,
            "param": _canon(param),
        })

    def mark_executed(self, op: str, *, rejected: bool) -> None:
        for fam in self.families.values():
            if op not in fam.materialized_ops and op not in fam.param_of:
                continue
            fam.executed += 1
            key = fam.param_of.get(op, op)
            if rejected:
                if key not in fam.rejected:
                    fam.rejected.append(key)
                if fam.remaining and fam.generated < fam.max_generated:
                    fam.continuation += 1
                    fam.state = "DORMANT"
            else:
                fam.state = "ACTIVE"
            return

    def note_occupancy(self, n: int) -> None:
        if n > self.occupancy_peak:
            self.occupancy_peak = n

    def telemetry(self) -> dict[str, Any]:
        fams = list(self.families.values())
        return {
            "candidate_family_count": len(fams),
            "candidate_instance_count": sum(len(f.tested) + len(f.remaining) for f in fams),
            "materialized_candidate_count": sum(f.materialized for f in fams),
            "deferred_candidate_count": self.deferred,
            "rejected_candidate_count": sum(len(f.rejected) for f in fams),
            "family_continuation_count": sum(f.continuation for f in fams),
            "candidate_generation_events": self.generation_events,
            "duplicate_candidate_events": self.duplicate_events,
            "deferred_family_wakeups": self.wakeups,
            "capacity_releases": self.capacity_releases,
            "candidate_registry_peak": self.occupancy_peak,
            "families": {
                f.family_id: {
                    "state": f.state,
                    "remaining": len(f.remaining),
                    "tested": list(f.tested),
                    "rejected": list(f.rejected),
                    "generated": f.generated,
                    "materialized": f.materialized,
                    "executed": f.executed,
                    "continuation": f.continuation,
                }
                for f in fams
            },
        }


__all__ = ["InterventionFamily", "FamilyInventory"]
