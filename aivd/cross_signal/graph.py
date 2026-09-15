"""Bidirectional residual↔action relation graph."""
from __future__ import annotations

from typing import Any

from aivd.cross_signal.relation import CrossSignalHypothesis, RelationState
from aivd.cross_signal.signals import ActionSignal, ResidualSignal


class RelationGraph:
    """Undirected conceptual bipartite graph residual ↔ action with scored edges."""

    def __init__(self) -> None:
        self.residuals: dict[str, ResidualSignal] = {}
        self.actions: dict[str, ActionSignal] = {}
        self.hypotheses: dict[str, CrossSignalHypothesis] = {}
        # adjacency: residual_id -> set(hyp_ids), action_id -> set(hyp_ids)
        self._from_residual: dict[str, set[str]] = {}
        self._from_action: dict[str, set[str]] = {}
        self.pairs_considered: int = 0
        self.pairs_pruned: int = 0
        self.pairs_tested: int = 0

    def add_residual(self, sig: ResidualSignal) -> ResidualSignal:
        self.residuals[sig.signal_id] = sig
        return sig

    def add_action(self, sig: ActionSignal) -> ActionSignal:
        self.actions[sig.signal_id] = sig
        return sig

    def add_hypothesis(self, hyp: CrossSignalHypothesis) -> CrossSignalHypothesis:
        self.hypotheses[hyp.id] = hyp
        self._from_residual.setdefault(hyp.residual_id, set()).add(hyp.id)
        self._from_action.setdefault(hyp.action_id, set()).add(hyp.id)
        self.pairs_considered += 1
        return hyp

    def neighbors_of_residual(self, residual_id: str) -> list[CrossSignalHypothesis]:
        ids = self._from_residual.get(residual_id) or set()
        return [self.hypotheses[i] for i in ids if i in self.hypotheses]

    def neighbors_of_action(self, action_id: str) -> list[CrossSignalHypothesis]:
        ids = self._from_action.get(action_id) or set()
        return [self.hypotheses[i] for i in ids if i in self.hypotheses]

    def prune(self, hyp_id: str, *, reason: str = "low_score") -> None:
        hyp = self.hypotheses.get(hyp_id)
        if hyp is None:
            return
        hyp.state = RelationState.REJECTED.value
        hyp.meta["prune_reason"] = reason
        self.pairs_pruned += 1

    def mark_tested(self, hyp_id: str) -> None:
        if hyp_id in self.hypotheses:
            self.pairs_tested += 1
            self.hypotheses[hyp_id].meta["tested"] = True

    def supported(self) -> list[CrossSignalHypothesis]:
        return [
            h for h in self.hypotheses.values()
            if h.state == RelationState.SUPPORTED.value
        ]

    def interaction_ready_pairs(self) -> list[CrossSignalHypothesis]:
        """Ready only with relation support — not mere visits."""
        return [h for h in self.hypotheses.values() if h.interaction_ready]

    def complexity(self) -> dict[str, Any]:
        n_r = len(self.residuals)
        n_a = len(self.actions)
        possible = n_r * n_a
        generated = len(self.hypotheses)
        prune_ratio = 1.0 - (generated / max(1, possible)) if possible else 1.0
        # Also credit explicit prunes
        if self.pairs_considered > 0:
            prune_ratio = max(
                prune_ratio,
                self.pairs_pruned / max(1, self.pairs_considered),
            )
        brute = bool(possible >= 8 and generated >= possible * 0.85 and self.pairs_tested >= possible * 0.7)
        return {
            "n_residuals": n_r,
            "n_actions": n_a,
            "possible_pairs": possible,
            "pairs_considered": self.pairs_considered,
            "pairs_generated": generated,
            "pairs_tested": self.pairs_tested,
            "pairs_pruned": self.pairs_pruned,
            "pruning_ratio": round(max(0.0, min(1.0, prune_ratio)), 4),
            "brute_force": brute,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "residuals": {k: v.as_dict() for k, v in self.residuals.items()},
            "actions": {k: v.as_dict() for k, v in self.actions.items()},
            "hypotheses": {k: v.as_dict() for k, v in self.hypotheses.items()},
            "complexity": self.complexity(),
        }


__all__ = ["RelationGraph"]
