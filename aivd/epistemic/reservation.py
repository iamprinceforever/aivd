"""Revocable, evidence-driven reservations (3.18).

Existing reserve systems remain as *suggestions* visible to the arbiter.
No subsystem silently consumes a reservation without global accounting.

Soft protected floor is GENERIC — not `if subsystem == openworld: reserve N`.
A branch earns protected continuation when evidence supports a completion path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Reservation:
    reservation_id: str
    owner: str  # branch_id
    purpose: str
    slots: int
    expected_value: float = 0.0
    validity: str = "evidence_holds"
    expiry_step: int | None = None
    release_condition: str = "evidence_collapse"
    reallocatable: bool = True
    protected: bool = False
    created_step: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "owner": self.owner,
            "purpose": self.purpose,
            "slots": self.slots,
            "expected_value": self.expected_value,
            "validity": self.validity,
            "expiry_step": self.expiry_step,
            "release_condition": self.release_condition,
            "reallocatable": self.reallocatable,
            "protected": self.protected,
            "created_step": self.created_step,
        }


def earns_protected_floor(
    *,
    evidence_causal: bool,
    unresolved_uncertainty: float,
    completion_probability: float,
    discrimination_value: float,
    repeating_failed: bool,
    remaining_steps: int,
    remaining_budget: int,
) -> bool:
    """Evidence-driven, subsystem-agnostic floor eligibility."""
    if repeating_failed:
        return False
    if remaining_steps <= 0:
        return False
    if remaining_budget <= 0:
        return False
    if completion_probability < 0.18:
        return False
    if unresolved_uncertainty < 0.10 and not evidence_causal:
        return False
    if discrimination_value < 0.04 and not evidence_causal:
        return False
    return True


def protected_slots(
    *,
    remaining_steps: int,
    remaining_budget: int,
    completion_probability: float,
    max_floor: int = 6,
) -> int:
    """Dynamic floor size — revocable, not a permanent quota."""
    if remaining_budget <= 0:
        return 0
    need = max(1, int(remaining_steps))
    # Scale with completion probability so weak branches cannot lock the budget.
    scaled = int(round(need * min(1.0, 0.5 + float(completion_probability))))
    cap = min(int(max_floor), max(0, remaining_budget // 4), remaining_budget)
    return int(max(0, min(scaled, cap, need)))


class ReservationBook:
    def __init__(self) -> None:
        self.active: list[Reservation] = []
        self.released: list[Reservation] = []
        self.revoked: list[Reservation] = []
        self._seq = 0

    def _id(self) -> str:
        self._seq += 1
        return f"rsv_{self._seq}"

    def total_slots(self) -> int:
        return sum(max(0, r.slots) for r in self.active)

    def add(self, res: Reservation) -> Reservation:
        if not res.reservation_id:
            res.reservation_id = self._id()
        self.active.append(res)
        return res

    def release(self, reservation_id: str, *, reason: str = "") -> int:
        kept: list[Reservation] = []
        n = 0
        for r in self.active:
            if r.reservation_id == reservation_id:
                r.meta["release_reason"] = reason
                self.released.append(r)
                n += r.slots
            else:
                kept.append(r)
        self.active = kept
        return n

    def revoke_owner(self, owner: str, *, reason: str = "") -> int:
        kept: list[Reservation] = []
        n = 0
        for r in self.active:
            if r.owner == owner and r.reallocatable:
                r.meta["revoke_reason"] = reason
                self.revoked.append(r)
                n += r.slots
            else:
                kept.append(r)
        self.active = kept
        return n

    def consume(self, owner: str, n: int = 1) -> int:
        left = int(n)
        for r in self.active:
            if left <= 0:
                break
            if r.owner != owner or r.slots <= 0:
                continue
            take = min(left, r.slots)
            r.slots -= take
            left -= take
        self.active = [r for r in self.active if r.slots > 0]
        return int(n) - left

    def expire(self, step: int) -> int:
        kept: list[Reservation] = []
        n = 0
        for r in self.active:
            if r.expiry_step is not None and step >= r.expiry_step:
                r.meta["revoke_reason"] = "expired"
                self.revoked.append(r)
                n += r.slots
            else:
                kept.append(r)
        self.active = kept
        return n

    def as_dict(self) -> dict[str, Any]:
        return {
            "active": [r.as_dict() for r in self.active],
            "released": [r.as_dict() for r in self.released],
            "revoked": [r.as_dict() for r in self.revoked],
            "n_active": len(self.active),
            "n_released": len(self.released),
            "n_revoked": len(self.revoked),
            "slots": self.total_slots(),
        }


__all__ = [
    "Reservation",
    "ReservationBook",
    "earns_protected_floor",
    "protected_slots",
]
