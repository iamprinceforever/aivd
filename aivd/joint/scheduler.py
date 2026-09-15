"""Joint residual scheduler — modes, hierarchical multi-way, joint-EVI selection."""
from __future__ import annotations

from typing import Any

from aivd.joint.dependency import JointResidualHypothesis


JOINT_MODES = frozenset({
    "joint", "joint_full", "joint_only", "joint_random",
    "interaction_joint", "full_3_13",
})

# Control / ablation mode labels used by InventionController overlays
JOINT_CONTROL_MODES = frozenset({
    "joint", "joint_full", "joint_only", "joint_random",
    "interaction_joint", "full_3_13",
})


def is_joint_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    if m in JOINT_MODES:
        return True
    if m.startswith("joint"):
        return True
    if m in ("interaction_joint", "full_3_13"):
        return True
    return False


def joint_enables_interaction(mode: str | None) -> bool:
    """Whether joint mode should also run the 3.12 interaction layer."""
    m = (mode or "off").lower().strip()
    if m in ("joint_only",):
        return False
    if m in ("joint", "joint_full", "interaction_joint", "full_3_13"):
        return True
    if m.startswith("joint") and m not in ("joint_only", "joint_random"):
        return True
    return False


class JointScheduler:
    """Select which joint hypotheses to co-explore / combination-test."""

    def __init__(
        self,
        *,
        mode: str = "joint",
        seed: int = 0,
        ablation: str | None = None,
        max_hypotheses: int = 6,
        max_combinations: int = 4,
        alloc_policy: str = "joint_aware",
    ):
        self.mode = (mode or "joint").lower().strip()
        self.seed = int(seed)
        self.ablation = ablation
        self.max_hypotheses = int(max_hypotheses)
        self.max_combinations = int(max_combinations)
        self.alloc_policy = (alloc_policy or "joint_aware").lower().strip()
        self.tested_keys: set[str] = set()
        self.trace: list[dict[str, Any]] = []

    def select_hypotheses(
        self,
        hyps: list[JointResidualHypothesis],
        *,
        budget: int = 6,
    ) -> list[JointResidualHypothesis]:
        pool = list(hyps or [])
        if self.mode in ("joint_random",) or self.ablation == "random_only":
            import random
            rng = random.Random(self.seed)
            rng.shuffle(pool)
            chosen = pool[: min(budget, self.max_hypotheses, len(pool))]
            self.trace.append({"kind": "random_hyp", "n": len(chosen)})
            return chosen
        if self.ablation == "no_joint_evi":
            pool.sort(key=lambda h: h.linkage, reverse=True)
        else:
            pool.sort(key=lambda h: (h.joint_evi, h.score, h.linkage), reverse=True)
        chosen = pool[: min(budget, self.max_hypotheses, len(pool))]
        self.trace.append({
            "kind": "joint_evi_select",
            "n": len(chosen),
            "head_evi": [round(h.joint_evi, 4) for h in chosen[:5]],
        })
        return chosen

    def select_combination_orders(
        self,
        hyp: JointResidualHypothesis,
        *,
        max_orders: int = 4,
    ) -> list[str]:
        """Hierarchical order selection — not brute force all permutations."""
        if self.ablation == "orders_ab_only":
            return ["A+B"][:max_orders]
        pref = hyp.order_preference or "A+B"
        # Prefer preferred order, then reverse, then sequential
        base = [pref]
        for o in ("A+B", "B+A", "A→B", "B→A"):
            if o not in base:
                base.append(o)
        n = min(max_orders, self.max_combinations, len(base))
        if self.mode != "joint_full" and self.ablation != "all_orders":
            n = min(n, 2)  # hierarchical prune
        chosen = base[:n]
        self.trace.append({"kind": "order_select", "hyp": hyp.id, "orders": chosen})
        return chosen

    def mark_tested(self, hyp: JointResidualHypothesis, order: str) -> None:
        key = f"{hyp.family_a}|{hyp.family_b}|{order}"
        self.tested_keys.add(key)

    def hierarchical_triples(
        self,
        hyps: list[JointResidualHypothesis],
        *,
        max_triples: int = 2,
    ) -> list[tuple[str, str, str]]:
        """Multi-way hierarchical (not brute force): chain high-linkage pairs."""
        if self.mode != "joint_full" and self.ablation != "force_triples":
            return []
        # Build family graph from pair hyps; emit triangles only when shared node
        from collections import defaultdict
        adj: dict[str, set[str]] = defaultdict(set)
        for h in hyps:
            if h.family_a and h.family_b:
                adj[h.family_a].add(h.family_b)
                adj[h.family_b].add(h.family_a)
        triples: list[tuple[str, str, str]] = []
        fams = sorted(adj.keys())
        for i, a in enumerate(fams):
            for b in sorted(adj[a]):
                if b <= a:
                    continue
                shared = adj[a] & adj[b]
                for c in sorted(shared):
                    if c == a or c == b:
                        continue
                    trip = tuple(sorted([a, b, c]))
                    if trip not in triples:
                        triples.append(trip)  # type: ignore[arg-type]
                    if len(triples) >= max_triples:
                        self.trace.append({"kind": "triples", "n": len(triples)})
                        return triples
        self.trace.append({"kind": "triples", "n": len(triples)})
        return triples


__all__ = [
    "JointScheduler",
    "is_joint_mode",
    "joint_enables_interaction",
    "JOINT_MODES",
    "JOINT_CONTROL_MODES",
]
