"""End-to-end lifecycle costing. Not a holdout schedule.

3.34 reserved a static invent+repro+verify floor of 3. 3.35 updates
those estimates from in-episode evidence and ranks atom candidates by
expected verified value, not syntactic novelty alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LifecycleCost:
    invent: float = 1.0
    validate: float = 0.0
    discover: float = 1.0
    reproduce: float = 1.0
    verify: float = 1.0
    extra_atom: float = 0.0

    @property
    def chain(self) -> int:
        return max(1, int(round(self.invent + self.reproduce + self.verify)))

    @property
    def expected_atoms(self) -> int:
        return max(1, int(round(self.invent + self.extra_atom)))

    def as_dict(self) -> dict[str, float]:
        return {
            "invent": self.invent,
            "validate": self.validate,
            "discover": self.discover,
            "reproduce": self.reproduce,
            "verify": self.verify,
            "extra_atom": self.extra_atom,
            "chain": float(self.chain),
        }


def expected_verified_value(
    *,
    p_discovery: float,
    p_reproduction: float = 0.85,
    p_verification: float = 0.8,
    causal_value: float = 1.0,
    reuse_value: float = 1.0,
    cost: float = 1.0,
) -> float:
    """Internal allocation score. Not an evaluator ranking."""
    num = (
        max(0.0, p_discovery)
        * max(0.0, p_reproduction)
        * max(0.0, p_verification)
        * max(0.0, causal_value)
        * max(0.0, reuse_value)
    )
    den = max(0.25, float(cost))
    return num / den


def rank_atoms(
    atoms: list[Any],
    *,
    rejected_classes: set[str],
    leftover: int,
    invariant_ready: bool,
    greedy: bool = False,
) -> list[Any]:
    """Stable rank. Untried semantic class beats a class that already failed.

    Does not consult evaluator GT. Original order is the tie-break.
    """
    if greedy or not atoms:
        return list(atoms)

    def key(a: Any) -> tuple[float, int]:
        cls = str(getattr(a, "semantic_class", "") or "")
        same = cls in rejected_classes
        p_disc = 0.12 if same else 0.35
        if leftover >= 3:
            p_ver = 0.85
        elif leftover >= 2 and invariant_ready:
            p_ver = 0.7
        else:
            p_ver = 0.05
        ev = expected_verified_value(
            p_discovery=p_disc,
            p_verification=p_ver,
            causal_value=0.55 if same else 1.0,
            reuse_value=1.1 if not same else 0.8,
            cost=1.0,
        )
        return (-ev, int(getattr(a, "proposal_index", 0)))

    return sorted(atoms, key=key)


def dynamic_floor(
    *,
    base: int,
    atom_rejected: int,
    dynamic: bool,
) -> int:
    """Expected remaining cost of a complete verified chain.

    Caps extra atom tries at 2 so this is not 'reserve 5 for invention'.
    """
    if not dynamic:
        return max(0, int(base))
    extra = min(2, max(0, int(atom_rejected)))
    if atom_rejected == 0:
        # Untried atom prior 0.35 → about three tries in expectation, cap +2.
        extra = 2
    return max(3, int(base) + extra)


__all__ = [
    "LifecycleCost",
    "expected_verified_value",
    "rank_atoms",
    "dynamic_floor",
]
