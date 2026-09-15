"""Cross-signal modes + bidirectional co-exploration scheduler."""
from __future__ import annotations

from typing import Any

from aivd.cross_signal.relation import CrossSignalHypothesis


CROSS_SIGNAL_MODES = frozenset({
    "cross_signal", "cross_signal_full", "cross_signal_only", "cross_signal_random",
    "cross_joint", "full_3_14",
})


def is_cross_signal_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in CROSS_SIGNAL_MODES:
        return True
    if m.startswith("cross_signal") or m.startswith("cross_"):
        return True
    if m in ("full_3_14", "cross_joint"):
        return True
    return False


def cross_enables_joint(mode: str | None) -> bool:
    """Whether cross-signal mode should also run 3.13 joint layer."""
    m = (mode or "off").lower().strip()
    if m in ("cross_signal_only",):
        return False
    if m in ("cross_signal", "cross_signal_full", "cross_joint", "full_3_14"):
        return True
    if m.startswith("cross") and m not in ("cross_signal_only", "cross_signal_random"):
        return True
    return False


def cross_enables_interaction(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in ("cross_signal_only",):
        return False
    if m in ("cross_signal", "cross_signal_full", "cross_joint", "full_3_14"):
        return True
    return False


class CrossSignalScheduler:
    """Select which cross-signal hypotheses to co-explore / combination-test."""

    def __init__(
        self,
        *,
        mode: str = "cross_signal",
        seed: int = 0,
        ablation: str | None = None,
        max_hypotheses: int = 6,
        max_combinations: int = 4,
    ):
        self.mode = (mode or "cross_signal").lower().strip()
        self.seed = int(seed)
        self.ablation = ablation
        self.max_hypotheses = int(max_hypotheses)
        self.max_combinations = int(max_combinations)
        self.tested_keys: set[str] = set()
        self.trace: list[dict[str, Any]] = []

    def select_hypotheses(
        self,
        hyps: list[CrossSignalHypothesis],
        *,
        budget: int = 6,
    ) -> list[CrossSignalHypothesis]:
        pool = list(hyps or [])
        if self.mode in ("cross_signal_random",) or self.ablation == "random_only":
            import random
            rng = random.Random(self.seed)
            rng.shuffle(pool)
            chosen = pool[: min(budget, self.max_hypotheses, len(pool))]
            self.trace.append({"kind": "random_hyp", "n": len(chosen)})
            return chosen
        if self.ablation == "no_cross_evi":
            pool.sort(key=lambda h: h.link_score, reverse=True)
        elif self.ablation == "correlation_only":
            # ablation: use only delta_similarity (raw-ish) — should underperform
            pool.sort(key=lambda h: h.delta_similarity, reverse=True)
        else:
            pool.sort(key=lambda h: (h.cross_evi, h.score, h.link_score), reverse=True)
        chosen = pool[: min(budget, self.max_hypotheses, len(pool))]
        self.trace.append({
            "kind": "cross_evi_select",
            "n": len(chosen),
            "head_evi": [round(h.cross_evi, 4) for h in chosen[:5]],
        })
        return chosen

    def select_orders(
        self,
        hyp: CrossSignalHypothesis,
        *,
        max_orders: int = 4,
    ) -> list[str]:
        if self.ablation == "orders_ra_only":
            return ["R+A"][:max_orders]
        base = ["R+A", "A+R", "R→A", "A→R"]
        n = min(max_orders, self.max_combinations, len(base))
        if self.mode != "cross_signal_full" and self.ablation != "all_orders":
            n = min(n, 2)
        chosen = base[:n]
        self.trace.append({"kind": "order_select", "hyp": hyp.id, "orders": chosen})
        return chosen

    def mark_tested(self, hyp: CrossSignalHypothesis, order: str) -> None:
        self.tested_keys.add(f"{hyp.residual_id}|{hyp.action_id}|{order}")


__all__ = [
    "CROSS_SIGNAL_MODES",
    "is_cross_signal_mode",
    "cross_enables_joint",
    "cross_enables_interaction",
    "CrossSignalScheduler",
]
