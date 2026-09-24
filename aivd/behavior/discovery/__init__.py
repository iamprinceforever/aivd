"""Isolated behavioral discovery. Not imported by aivd.science.

The measurement primitive is apply_micro. Family labels and observation
metrics are not inputs. The frozen discovery bank is not executed here.
"""

from aivd.behavior.discovery.budget import BehavioralBudget
from aivd.behavior.discovery.constants import (
    DISCOVERY_BANK_HASH,
    PAIR_RESERVE,
    PROTOCOL_VERSION,
    TOTAL_BEHAVIOR_CALLS,
)
from aivd.behavior.discovery.engine import DiscoveryEngine, sealed_receipt
from aivd.behavior.discovery.errors import BudgetExhausted, DiscoveryBankSealed

__all__ = [
    "BehavioralBudget",
    "BudgetExhausted",
    "DISCOVERY_BANK_HASH",
    "DiscoveryBankSealed",
    "DiscoveryEngine",
    "PAIR_RESERVE",
    "PROTOCOL_VERSION",
    "TOTAL_BEHAVIOR_CALLS",
    "sealed_receipt",
]
