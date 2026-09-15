"""Small interpretable causal policies — not a giant NN."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Literal

CausalAction = Literal[
    "generate_hypotheses",
    "discriminate",
    "search_interaction",
    "test_temporal",
    "test_indirect",
    "handoff_amplify",
    "handoff_investigate",
    "abandon",
]


@dataclass
class CausalDecision:
    action: CausalAction
    score: float = 0.0
    reason: str = ""
    meta: dict[str, Any] | None = None


class RandomCausalPolicy:
    name = "random"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def decide(self, obs: dict[str, Any]) -> CausalDecision:
        actions: list[CausalAction] = [
            "discriminate", "search_interaction", "test_temporal", "test_indirect", "abandon",
        ]
        if obs.get("dimension_id"):
            actions.append("handoff_amplify")
        if float(obs.get("security") or 0) >= 0.4:
            actions.append("handoff_investigate")
        return CausalDecision(self.rng.choice(actions), reason="random")


class HeuristicCausalPolicy:
    """Default: always discriminate unexplained signals; then specialize."""

    name = "heuristic"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def decide(self, obs: dict[str, Any]) -> CausalDecision:
        budget = int(obs.get("budget_remaining") or 0)
        if budget < 1:
            return CausalDecision("abandon", reason="no_budget")
        if bool(obs.get("disappearing")):
            return CausalDecision("abandon", reason="disappearing")
        sec = float(obs.get("security") or 0.0)
        dim = obs.get("dimension_id")
        unexplained = bool(obs.get("unexplained"))
        n_hyps = int(obs.get("n_hyps") or 0)
        disc_done = bool(obs.get("discriminated"))
        ent = float(obs.get("hypothesis_entropy") or 1.0)
        if sec >= 0.45 and dim:
            return CausalDecision("handoff_investigate", score=sec, reason="strong_after_dim")
        if dim and not obs.get("amplified"):
            return CausalDecision("handoff_amplify", score=0.7, reason="dimension_identified")
        if n_hyps < 2 or (unexplained and not disc_done):
            return CausalDecision("discriminate", score=0.65, reason="nway_default")
        if disc_done and ent > 1.2 and not obs.get("interaction_tried"):
            return CausalDecision("search_interaction", score=0.5, reason="residual_entropy_interaction")
        if not obs.get("temporal_tried") and unexplained:
            return CausalDecision("test_temporal", score=0.4, reason="history_dependence")
        if not obs.get("indirect_tried") and unexplained:
            return CausalDecision("test_indirect", score=0.4, reason="later_effect")
        if disc_done and dim:
            return CausalDecision("handoff_amplify", score=0.55, reason="post_disc_amplify")
        if disc_done:
            return CausalDecision("discriminate", score=0.35, reason="still_uncertain")
        return CausalDecision("discriminate", score=0.3, reason="default_nway")


class LearnedCausalPolicy:
    """Tiny logistic over handcrafted features."""

    name = "learned"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.w = {
            "discriminate": [1.2, 0.4, 1.5, -0.8, 0.2, 0.1],
            "search_interaction": [0.3, 0.2, 0.8, 0.2, 1.6, 0.0],
            "test_temporal": [0.2, 0.1, 0.5, 0.0, 0.2, 1.4],
            "handoff_amplify": [0.5, 2.2, -0.4, 1.8, 0.1, 0.1],
            "handoff_investigate": [2.5, 1.8, -0.2, 1.2, 0.0, 0.0],
        }
        self.b = {
            "discriminate": -0.2,
            "search_interaction": -0.8,
            "test_temporal": -0.9,
            "handoff_amplify": -1.0,
            "handoff_investigate": -1.4,
        }

    def _feat(self, obs: dict[str, Any]) -> list[float]:
        return [
            float(obs.get("security") or 0.0),
            1.0 if obs.get("dimension_id") else 0.0,
            float(obs.get("hypothesis_entropy") or 1.0) / 4.0,
            1.0 if obs.get("discriminated") else 0.0,
            1.0 if obs.get("unexplained") else 0.0,
            1.0 if obs.get("has_history") else 0.0,
        ]

    @staticmethod
    def _dot(w: list[float], x: list[float], b: float) -> float:
        return sum(a * b_ for a, b_ in zip(w, x)) + b

    def decide(self, obs: dict[str, Any]) -> CausalDecision:
        if int(obs.get("budget_remaining") or 0) < 1 or bool(obs.get("disappearing")):
            return CausalDecision("abandon", reason="learned_stop")
        x = self._feat(obs)
        scores = {name: self._dot(w, x, self.b[name]) for name, w in self.w.items()}
        items = list(scores.items())
        mx = max(v for _, v in items)
        exps = [math.exp(min(20.0, v - mx)) for _, v in items]
        z = sum(exps) or 1.0
        probs = [e / z for e in exps]
        r = self.rng.random()
        cum = 0.0
        choice = items[0][0]
        for (name, _), p in zip(items, probs):
            cum += p
            if r <= cum:
                choice = name
                break
        return CausalDecision(action=choice, score=float(scores[choice]), reason="learned")  # type: ignore[arg-type]


class FullCausalPolicy(HeuristicCausalPolicy):
    """Heuristic plus always consider interaction/temporal/indirect before abandon."""

    name = "full"

    def decide(self, obs: dict[str, Any]) -> CausalDecision:
        d = super().decide(obs)
        if d.action == "abandon" and int(obs.get("budget_remaining") or 0) >= 2:
            if not obs.get("interaction_tried"):
                return CausalDecision("search_interaction", reason="full_interaction")
            if not obs.get("indirect_tried"):
                return CausalDecision("test_indirect", reason="full_indirect")
            if not obs.get("temporal_tried"):
                return CausalDecision("test_temporal", reason="full_temporal")
        return d


def make_causal_policy(name: str, seed: int = 42):
    n = (name or "heuristic").lower()
    if n in ("random",):
        return RandomCausalPolicy(seed=seed)
    if n in ("learned", "learned_active"):
        return LearnedCausalPolicy(seed=seed)
    if n in ("full", "full_causal_discovery"):
        return FullCausalPolicy(seed=seed)
    if n in ("hypothesis_discrimination", "heuristic_active", "heuristic"):
        return HeuristicCausalPolicy(seed=seed)
    return HeuristicCausalPolicy(seed=seed)
