"""Revisable budget reservation for combination testing."""
from __future__ import annotations

from typing import Any

from aivd.joint.dependency import JointResidualHypothesis
from aivd.joint.readiness import pair_interaction_ready


class BudgetReserve:
    """Hold combination slots; revise when readiness / evidence changes."""

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

    def reserve(
        self,
        hyp: JointResidualHypothesis,
        *,
        reason: str = "joint_evi",
    ) -> bool:
        if self.slots_remaining <= 0:
            return False
        # Prefer interaction-ready; allow soft reserve for high joint EVI
        soft = float(hyp.joint_evi) >= 0.35 or float(hyp.linkage) >= 0.5
        ready = hyp.interaction_ready or pair_interaction_ready(
            hyp.readiness_a, hyp.readiness_b
        )
        if not (ready or soft):
            return False
        self.slots_remaining -= 1
        rec = {
            "hyp_id": hyp.id,
            "family_a": hyp.family_a,
            "family_b": hyp.family_b,
            "reason": reason,
            "ready": ready,
            "soft": soft and not ready,
            "joint_evi": hyp.joint_evi,
            "order": hyp.order_preference,
        }
        self.reservations.append(rec)
        hyp.meta["reserved"] = True
        return True

    def revise(self, hyp: JointResidualHypothesis, *, drop: bool = False) -> None:
        """Revise reservation: drop if disqualified / low EVI; keep if stronger."""
        kept: list[dict[str, Any]] = []
        for r in self.reservations:
            if r.get("hyp_id") != hyp.id:
                kept.append(r)
                continue
            if drop or hyp.readiness_a == "DISQUALIFIED" or hyp.readiness_b == "DISQUALIFIED":
                self.released.append({**r, "revise": "drop"})
                self.slots_remaining += 1
                hyp.meta["reserved"] = False
            else:
                r["joint_evi"] = hyp.joint_evi
                r["ready"] = hyp.interaction_ready
                r["revise"] = "update"
                kept.append(r)
        self.reservations = kept

    def consume(self, hyp_id: str) -> bool:
        """Spend a reserved slot on an actual combination test."""
        for i, r in enumerate(self.reservations):
            if r.get("hyp_id") == hyp_id:
                self.consumed.append(self.reservations.pop(i))
                return True
        # Allow consume from unallocated remaining reserve
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


__all__ = ["BudgetReserve"]
