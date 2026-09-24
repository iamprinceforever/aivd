"""Isolated apply_micro accounting. Does not touch episode or atom quotas."""

from __future__ import annotations

from aivd.behavior.discovery.constants import CHARACTERIZATION_LIMIT, PAIR_RESERVE, TOTAL_BEHAVIOR_CALLS
from aivd.behavior.discovery.errors import BudgetExhausted


class BehavioralBudget:
    def __init__(self) -> None:
        self.characterization_used = 0
        self.pair_used = 0

    @property
    def total_used(self) -> int:
        return self.characterization_used + self.pair_used

    def charge_characterization(self, calls: int) -> None:
        self._charge("characterization", calls)

    def charge_pair(self, calls: int) -> None:
        self._charge("pair", calls)

    def can_characterize(self, calls: int) -> bool:
        return calls >= 0 and self.characterization_used + calls <= CHARACTERIZATION_LIMIT

    def can_pair(self, calls: int) -> bool:
        return calls >= 0 and self.pair_used + calls <= PAIR_RESERVE

    def _charge(self, pool: str, calls: int) -> None:
        if calls < 0:
            raise BudgetExhausted(pool)
        if pool == "characterization":
            if not self.can_characterize(calls):
                raise BudgetExhausted(pool)
            self.characterization_used += calls
        elif pool == "pair":
            if not self.can_pair(calls):
                raise BudgetExhausted(pool)
            self.pair_used += calls
        else:
            raise BudgetExhausted(pool)
        if self.total_used > TOTAL_BEHAVIOR_CALLS:
            raise BudgetExhausted("total")
