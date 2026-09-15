"""Discovery policies: random / heuristic / small learned."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Literal

from aivd.discovery.perturbations import PerturbationCandidate, generate_perturbations, score_candidate
from aivd.discovery.weak_signal import SignalStrength


DiscoveryAction = Literal[
    "explore",
    "map_baseline",
    "perturb",
    "amplify",
    "frontier_walk",
    "discriminate",
    "handoff_investigate",
    "abandon",
]


@dataclass
class PolicyDecision:
    action: DiscoveryAction
    prompt: str | None = None
    score: float = 0.0
    reason: str = ""
    meta: dict[str, Any] | None = None


class RandomDiscoveryPolicy:
    name = "random"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def decide(self, obs: dict[str, Any]) -> PolicyDecision:
        actions: list[DiscoveryAction] = ["explore", "perturb", "amplify", "frontier_walk", "abandon"]
        strength = obs.get("signal_strength", "none")
        if strength in ("medium", "strong"):
            actions.append("handoff_investigate")
        a = self.rng.choice(actions)
        return PolicyDecision(action=a, reason="random", score=0.0)


class HeuristicDiscoveryPolicy:
    name = "heuristic"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def decide(self, obs: dict[str, Any]) -> PolicyDecision:
        strength = str(obs.get("signal_strength") or "none")
        sec = float(obs.get("security") or 0.0)
        cue = float(obs.get("cue") or 0.0)
        unc = float(obs.get("uncertainty") or 0.5)
        novelty = float(obs.get("novelty") or 0.0)
        disappearing = bool(obs.get("disappearing"))
        amplify_steps = int(obs.get("amplify_steps") or 0)
        frontiers = list(obs.get("frontiers") or [])
        budget_left = int(obs.get("budget_remaining") or 0)

        if budget_left < 1:
            return PolicyDecision("abandon", reason="no_budget")
        if disappearing:
            return PolicyDecision("abandon", reason="disappearing_signal")
        if strength == "strong" or sec >= 0.45:
            return PolicyDecision("handoff_investigate", reason="strong_signal", score=sec)
        if strength == "medium" and sec >= 0.22:
            if amplify_steps < 2:
                return PolicyDecision("amplify", reason="medium_pre_handoff", score=0.6)
            return PolicyDecision("handoff_investigate", reason="medium_ready", score=0.7)
        if strength == "weak" and amplify_steps < 6:
            return PolicyDecision("amplify", reason="weak_amplify", score=0.5 + 0.2 * cue)
        if frontiers and unc > 0.35:
            return PolicyDecision("frontier_walk", reason="frontier_uncertainty", score=0.4 + 0.2 * unc)
        if novelty > 0.4 and unc > 0.3:
            return PolicyDecision("perturb", reason="novel_uncertain", score=0.35)
        if int(obs.get("baseline_n") or 0) < 2:
            return PolicyDecision("map_baseline", reason="need_baseline", score=0.3)
        return PolicyDecision("explore", reason="default_explore", score=0.2)


class LearnedDiscoveryPolicy:
    """Tiny logistic over handcrafted features — not a giant NN."""

    name = "learned"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        # weights for [sec, cue, unc, novelty, strength_ord, amplify_steps_norm, frontier]
        self.w_handoff = [2.5, 1.5, 0.2, 0.1, 1.8, -0.2, 0.1]
        self.w_amplify = [0.8, 2.0, 0.5, 0.2, 1.2, -1.0, 0.2]
        self.w_frontier = [0.2, 0.2, 1.5, 0.8, 0.0, 0.0, 1.5]
        self.b = {"handoff": -1.2, "amplify": -0.4, "frontier": -0.6}

    def _feat(self, obs: dict[str, Any]) -> list[float]:
        strength = str(obs.get("signal_strength") or "none")
        ord_map = {"none": 0.0, "weak": 0.33, "medium": 0.66, "strong": 1.0}
        return [
            float(obs.get("security") or 0.0),
            float(obs.get("cue") or 0.0),
            float(obs.get("uncertainty") or 0.5),
            float(obs.get("novelty") or 0.0),
            ord_map.get(strength, 0.0),
            min(1.0, int(obs.get("amplify_steps") or 0) / 6.0),
            1.0 if obs.get("frontiers") else 0.0,
        ]

    @staticmethod
    def _dot(w: list[float], x: list[float], b: float) -> float:
        return sum(a * b_ for a, b_ in zip(w, x)) + b

    def decide(self, obs: dict[str, Any]) -> PolicyDecision:
        if bool(obs.get("disappearing")) or int(obs.get("budget_remaining") or 0) < 1:
            return PolicyDecision("abandon", reason="learned_stop")
        x = self._feat(obs)
        scores = {
            "handoff_investigate": self._dot(self.w_handoff, x, self.b["handoff"]),
            "amplify": self._dot(self.w_amplify, x, self.b["amplify"]),
            "frontier_walk": self._dot(self.w_frontier, x, self.b["frontier"]),
            "explore": 0.1,
            "perturb": 0.15 + 0.2 * x[3],
        }
        # Softmax sample with temperature for exploration
        items = list(scores.items())
        mx = max(v for _, v in items)
        exps = [math.exp(min(20.0, v - mx)) for _, v in items]
        z = sum(exps) or 1.0
        probs = [e / z for e in exps]
        r = self.rng.random()
        cum = 0.0
        choice = items[-1][0]
        for (name, _), p in zip(items, probs):
            cum += p
            if r <= cum:
                choice = name
                break
        return PolicyDecision(action=choice, score=float(scores[choice]), reason="learned")  # type: ignore[arg-type]


def make_policy(name: str, seed: int = 42):
    n = (name or "heuristic").lower()
    if n == "random":
        return RandomDiscoveryPolicy(seed=seed)
    if n == "learned":
        return LearnedDiscoveryPolicy(seed=seed)
    return HeuristicDiscoveryPolicy(seed=seed)
