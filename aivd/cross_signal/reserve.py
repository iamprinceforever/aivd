"""Revisable budget reserve for cross-signal combination testing."""
from __future__ import annotations

from typing import Any

from aivd.cross_signal.relation import CrossSignalHypothesis, RelationState


class CrossSignalReserve:
    """Hold combo slots; release when confidence collapses."""

    def __init__(self, slots: int = 0):
        self.slots_total = max(0, int(slots))
        self.slots_remaining = self.slots_total
        self.reservations: list[dict[str, Any]] = []
        self.released: list[dict[str, Any]] = []
        self.consumed: list[dict[str, Any]] = []

    def configure(self, slots: int) -> None:
        used = self.slots_total - self.slots_remaining
        self.slots_total = max(0, int(slots))
        self.slots_remaining = max(0, self.slots_total - used)

    def reserve(self, hyp: CrossSignalHypothesis, *, reason: str = "cross_evi") -> bool:
        if self.slots_remaining <= 0:
            return False
        soft = float(hyp.cross_evi) >= 0.30 or float(hyp.link_score) >= 0.35
        ready = hyp.interaction_ready or hyp.state in (
            RelationState.SUPPORTED.value,
            RelationState.PLAUSIBLE.value,
        )
        if not (ready or soft):
            return False
        self.slots_remaining -= 1
        rec = {
            "hyp_id": hyp.id,
            "residual_id": hyp.residual_id,
            "action_id": hyp.action_id,
            "reason": reason,
            "state": hyp.state,
            "cross_evi": hyp.cross_evi,
            "link_score": hyp.link_score,
        }
        self.reservations.append(rec)
        hyp.reserved = True
        return True

    def release_on_collapse(self, hyp: CrossSignalHypothesis) -> bool:
        """Release reserved slot if confidence collapsed."""
        collapsed = hyp.state in (
            RelationState.FALSIFIED.value,
            RelationState.REJECTED.value,
        ) or float(hyp.link_score) < 0.15
        if not collapsed:
            return False
        kept: list[dict[str, Any]] = []
        released_any = False
        for r in self.reservations:
            if r.get("hyp_id") != hyp.id:
                kept.append(r)
                continue
            self.released.append({**r, "revise": "collapse"})
            self.slots_remaining += 1
            hyp.reserved = False
            released_any = True
        self.reservations = kept
        return released_any

    def revise(self, hyp: CrossSignalHypothesis) -> None:
        if self.release_on_collapse(hyp):
            return
        for r in self.reservations:
            if r.get("hyp_id") == hyp.id:
                r["cross_evi"] = hyp.cross_evi
                r["link_score"] = hyp.link_score
                r["state"] = hyp.state
                r["revise"] = "update"

    def consume(self, hyp_id: str) -> bool:
        for i, r in enumerate(self.reservations):
            if r.get("hyp_id") == hyp_id:
                self.consumed.append(self.reservations.pop(i))
                return True
        if self.slots_remaining > 0:
            self.slots_remaining -= 1
            self.consumed.append({"hyp_id": hyp_id, "ad_hoc": True})
            return True
        return False

    def can_test_combination(self) -> bool:
        return bool(self.reservations) or self.slots_remaining > 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "slots_total": self.slots_total,
            "slots_remaining": self.slots_remaining,
            "n_reserved": len(self.reservations),
            "n_released": len(self.released),
            "n_consumed": len(self.consumed),
            "reservations": list(self.reservations),
            "released": list(self.released),
            "consumed": list(self.consumed),
        }


__all__ = ["CrossSignalReserve"]
