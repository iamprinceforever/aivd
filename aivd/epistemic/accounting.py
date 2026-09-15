"""Global experiment accounting. ONE budget of 32. No hidden execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.epistemic.types import ExperimentTraceRecord


@dataclass
class GlobalLedger:
    """Single global experiment counter. Every environment interaction charges here."""
    total: int = 32
    used: int = 0
    reserved: int = 0
    released: int = 0
    revoked: int = 0
    reallocation_count: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    traces: list[ExperimentTraceRecord] = field(default_factory=list)
    by_subsystem: dict[str, int] = field(default_factory=dict)
    by_branch: dict[str, int] = field(default_factory=dict)

    def remaining_free(self) -> int:
        return max(0, self.total - self.used - self.reserved)

    def remaining(self) -> int:
        """Slots not yet executed (includes reserved, which can be revoked)."""
        return max(0, self.total - self.used)

    def can_spend(self, n: int = 1) -> bool:
        return self.remaining() >= int(n)

    def charge(
        self,
        n: int = 1,
        *,
        subsystem: str = "",
        branch_id: str = "",
        proposal_id: str = "",
        locally_reserved: bool = False,
    ) -> bool:
        n = int(n)
        if n <= 0:
            return True
        if not self.can_spend(n):
            self.history.append({
                "op": "charge_fail", "n": n, "used": self.used, "reserved": self.reserved,
                "subsystem": subsystem, "branch_id": branch_id,
            })
            return False
        self.used += n
        if locally_reserved and self.reserved > 0:
            take = min(n, self.reserved)
            self.reserved -= take
        self.by_subsystem[subsystem] = self.by_subsystem.get(subsystem, 0) + n
        self.by_branch[branch_id] = self.by_branch.get(branch_id, 0) + n
        self.history.append({
            "op": "charge", "n": n, "used": self.used, "reserved": self.reserved,
            "subsystem": subsystem, "branch_id": branch_id, "proposal_id": proposal_id,
            "remaining": self.remaining(),
        })
        return True

    def record_trace(self, rec: ExperimentTraceRecord) -> None:
        self.traces.append(rec)

    def invariant_ok(self) -> bool:
        if self.used < 0 or self.reserved < 0:
            return False
        if self.used > self.total:
            return False
        if self.used + self.reserved > self.total:
            return False
        costs = sum(float(t.experiment_cost) for t in self.traces)
        return costs <= float(self.total) + 1e-9

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "used": self.used,
            "reserved": self.reserved,
            "released": self.released,
            "revoked": self.revoked,
            "remaining": self.remaining(),
            "remaining_free": self.remaining_free(),
            "reallocation_count": self.reallocation_count,
            "by_subsystem": dict(self.by_subsystem),
            "by_branch": dict(self.by_branch),
            "invariant_ok": self.invariant_ok(),
            "n_traces": len(self.traces),
        }


__all__ = ["GlobalLedger"]
