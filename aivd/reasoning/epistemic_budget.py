"""Adaptive epistemic budget — ensure experiments can run (3.16).

Addresses FIRST BOTTLENECK: invent-without-experiment under budget starvation.
When reasoning is on, reallocate toward probes that produce information.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EpistemicBudgetPolicy:
    """Policy for protecting experimental budget from invent-spam."""
    min_experiment_share: float = 0.35
    release_reserve_on_dead_end: bool = True
    stop_invent_if_no_test: bool = True
    max_gen_without_test: int = 48

    def as_dict(self) -> dict[str, Any]:
        return {
            "min_experiment_share": self.min_experiment_share,
            "release_reserve_on_dead_end": self.release_reserve_on_dead_end,
            "stop_invent_if_no_test": self.stop_invent_if_no_test,
            "max_gen_without_test": self.max_gen_without_test,
        }


def reallocate_for_experiments(
    *,
    total: int,
    used: int,
    reserved: int,
    tested: int,
    generated: int,
    policy: EpistemicBudgetPolicy | None = None,
) -> dict[str, Any]:
    """Decide whether to release reserve / halt invent / protect probe slots."""
    pol = policy or EpistemicBudgetPolicy()
    remaining = max(0, total - used - reserved)
    available = max(0, total - used)
    actions: list[str] = []
    release_n = 0
    halt_invent = False

    # If never tested but generating a lot — dead invent loop
    if tested == 0 and generated >= pol.max_gen_without_test:
        halt_invent = True
        actions.append("halt_invent_spam")
        if pol.release_reserve_on_dead_end and reserved > 0:
            release_n = reserved
            actions.append("release_all_reserve_for_experiment")

    # Protect experiment share
    target_exp = int(total * pol.min_experiment_share)
    if tested < target_exp and reserved > 0 and remaining == 0 and available > 0:
        # reserved is blocking experiments
        release_n = max(release_n, min(reserved, max(1, target_exp - tested)))
        actions.append("release_reserve_to_meet_experiment_share")

    if tested == 0 and available > 0 and remaining == 0 and reserved > 0:
        release_n = max(release_n, reserved)
        actions.append("release_reserve_zero_tests")

    return {
        "release_n": int(release_n),
        "halt_invent": bool(halt_invent or (pol.stop_invent_if_no_test and tested == 0 and generated > 2 * max(1, available))),
        "actions": actions,
        "remaining": remaining,
        "available": available,
        "target_experiment_probes": target_exp,
    }


__all__ = ["EpistemicBudgetPolicy", "reallocate_for_experiments"]
