"""Invention budget tracker — cheap tests within episode probe budget."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InventionBudget:
    max_inventions: int = 16
    max_cheap_tests: int = 16
    used_inventions: int = 0
    used_tests: int = 0

    def can_invent(self) -> bool:
        return self.used_inventions < self.max_inventions

    def can_test(self) -> bool:
        return self.used_tests < self.max_cheap_tests

    def charge_invent(self, n: int = 1) -> bool:
        if self.used_inventions + n > self.max_inventions:
            return False
        self.used_inventions += n
        return True

    def charge_test(self, n: int = 1) -> bool:
        if self.used_tests + n > self.max_cheap_tests:
            return False
        self.used_tests += n
        return True

    def remaining_tests(self) -> int:
        return max(0, self.max_cheap_tests - self.used_tests)

    def as_dict(self) -> dict:
        return {
            "max_inventions": self.max_inventions,
            "max_cheap_tests": self.max_cheap_tests,
            "used_inventions": self.used_inventions,
            "used_tests": self.used_tests,
        }
