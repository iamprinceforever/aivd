"""Investigation policies: HeuristicController vs small LearnedController (AIVD 3.4).

Action space (high-level): EXPLORE / INVESTIGATE / LOCALIZE / FALSIFY /
BOUNDARY / VARIANT / REPEAT / VERIFY / ABANDON.

LearnedController is the *smallest* learnable formulation — tabular /
linear weights over hand features — NOT a giant NN.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class PolicyAction(str, Enum):
    EXPLORE = "explore"
    INVESTIGATE = "investigate"
    LOCALIZE = "localize"
    FALSIFY = "falsify"
    BOUNDARY = "boundary"
    VARIANT = "variant"
    REPEAT = "repeat"
    VERIFY = "verify"
    ABANDON = "abandon"


POLICY_ACTIONS: tuple[PolicyAction, ...] = tuple(PolicyAction)


@dataclass
class PolicyObservation:
    security_relevance: float = 0.0
    effect_magnitude: float = 0.0
    uncertainty: float = 0.5
    localization_progress: float = 0.0
    confidence: float = 0.0
    remaining_budget_frac: float = 1.0
    episode_active: bool = False
    has_trigger: bool = False
    cf_done: bool = False
    boundary_found: bool = False
    claim_without_effect: bool = False
    steps_taken: int = 0
    state: str = "explore"


@dataclass
class PolicyDecision:
    action: PolicyAction
    score: float
    reasoning: str
    scores: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


class HeuristicController:
    """Rule + score based multi-step investigation policy."""

    name = "heuristic"

    def __init__(self, seed: int = 42, abandon_budget_frac: float = 0.05):
        self.rng = random.Random(seed)
        self.abandon_budget_frac = abandon_budget_frac

    def act(self, obs: PolicyObservation) -> PolicyDecision:
        if obs.claim_without_effect and obs.security_relevance < 0.15:
            return PolicyDecision(
                PolicyAction.ABANDON,
                1.0,
                "decoy_or_non_security_drama",
                {PolicyAction.ABANDON.value: 1.0},
            )
        if obs.remaining_budget_frac <= self.abandon_budget_frac:
            return PolicyDecision(
                PolicyAction.ABANDON,
                1.0,
                "budget_floor",
                {PolicyAction.ABANDON.value: 1.0},
            )

        scores: dict[str, float] = {a.value: 0.0 for a in POLICY_ACTIONS}

        if not obs.episode_active:
            # When to investigate vs keep exploring
            scores[PolicyAction.INVESTIGATE.value] = (
                0.45 * obs.security_relevance
                + 0.25 * obs.effect_magnitude
                + 0.20 * obs.uncertainty
                - 0.15 * (1.0 - obs.remaining_budget_frac)
            )
            scores[PolicyAction.EXPLORE.value] = 0.35 + 0.2 * (1.0 - obs.security_relevance)
            scores[PolicyAction.ABANDON.value] = 0.1
        else:
            scores[PolicyAction.EXPLORE.value] = 0.05
            # Localization priority when we have a trigger candidate but incomplete shrink
            scores[PolicyAction.LOCALIZE.value] = (
                0.55 * (1.0 - obs.localization_progress) * (0.4 + obs.security_relevance)
                + (0.25 if obs.has_trigger else 0.0)
            )
            scores[PolicyAction.FALSIFY.value] = (
                0.5 * obs.localization_progress * (0.5 + obs.security_relevance)
                + (0.2 if obs.has_trigger and not obs.cf_done else 0.0)
            )
            scores[PolicyAction.BOUNDARY.value] = (
                0.35 * obs.localization_progress
                + 0.2 * obs.security_relevance
                + (0.15 if not obs.boundary_found else -0.2)
            )
            scores[PolicyAction.VARIANT.value] = 0.3 * obs.localization_progress + 0.15 * obs.uncertainty
            scores[PolicyAction.REPEAT.value] = 0.25 * obs.uncertainty * (1.0 - obs.confidence)
            scores[PolicyAction.VERIFY.value] = 0.55 * obs.confidence + 0.25 * obs.localization_progress
            scores[PolicyAction.INVESTIGATE.value] = 0.2 * obs.uncertainty
            scores[PolicyAction.ABANDON.value] = (
                0.15
                + 0.25 * (1.0 - obs.remaining_budget_frac)
                + (0.3 if obs.steps_taken > 12 else 0.0)
                - 0.2 * obs.security_relevance
            )

        best = max(scores.items(), key=lambda kv: kv[1])
        action = PolicyAction(best[0])
        return PolicyDecision(
            action=action,
            score=float(best[1]),
            reasoning=f"heuristic:{action.value}={best[1]:.3f}",
            scores=scores,
        )


class LearnedController:
    """Smallest learnable policy: linear scores over fixed features + online update.

    NOT a deep network. Weight vector W[action, feature] updated by simple
    reward-weighted Perceptron-style rule when `update` is called.
    """

    name = "learned"
    FEATURE_NAMES = (
        "security",
        "effect",
        "uncertainty",
        "loc_prog",
        "confidence",
        "budget_frac",
        "has_trigger",
        "cf_done",
        "boundary",
        "active",
        "bias",
    )

    def __init__(self, seed: int = 42, lr: float = 0.05):
        self.rng = random.Random(seed)
        self.lr = lr
        # Initialize near heuristic priors
        self.weights: dict[str, list[float]] = {
            a.value: [self.rng.uniform(-0.05, 0.05) for _ in self.FEATURE_NAMES]
            for a in POLICY_ACTIONS
        }
        # Mild prior biases
        self.weights[PolicyAction.LOCALIZE.value][3] = -0.4  # prefer when loc_prog low → negate later
        self.weights[PolicyAction.LOCALIZE.value][0] = 0.4
        self.weights[PolicyAction.FALSIFY.value][3] = 0.35
        self.weights[PolicyAction.VERIFY.value][4] = 0.5
        self.weights[PolicyAction.ABANDON.value][5] = -0.4
        self.weights[PolicyAction.INVESTIGATE.value][0] = 0.45
        self.weights[PolicyAction.EXPLORE.value][10] = 0.3
        self._last_obs: PolicyObservation | None = None
        self._last_action: PolicyAction | None = None

    def _features(self, obs: PolicyObservation) -> list[float]:
        return [
            float(obs.security_relevance),
            float(obs.effect_magnitude),
            float(obs.uncertainty),
            float(obs.localization_progress),
            float(obs.confidence),
            float(obs.remaining_budget_frac),
            1.0 if obs.has_trigger else 0.0,
            1.0 if obs.cf_done else 0.0,
            1.0 if obs.boundary_found else 0.0,
            1.0 if obs.episode_active else 0.0,
            1.0,
        ]

    def act(self, obs: PolicyObservation) -> PolicyDecision:
        # Safety overrides (same as heuristic gates)
        if obs.claim_without_effect and obs.security_relevance < 0.15:
            return PolicyDecision(PolicyAction.ABANDON, 1.0, "learned:decoy_gate")
        if obs.remaining_budget_frac <= 0.05:
            return PolicyDecision(PolicyAction.ABANDON, 1.0, "learned:budget_floor")

        feats = self._features(obs)
        scores: dict[str, float] = {}
        for a in POLICY_ACTIONS:
            # Special: LOCALIZE prefers low loc_prog → use (1-loc) via weight on loc_prog negative
            w = self.weights[a.value]
            scores[a.value] = sum(wi * fi for wi, fi in zip(w, feats))
            if a == PolicyAction.LOCALIZE:
                scores[a.value] += 0.35 * (1.0 - obs.localization_progress) * max(0.2, obs.security_relevance)

        # Softmax sample or greedy (greedy for determinism in tests; epsilon from rng)
        best = max(scores.items(), key=lambda kv: kv[1])
        if self.rng.random() < 0.08:
            action = self.rng.choice(list(POLICY_ACTIONS))
        else:
            action = PolicyAction(best[0])
        self._last_obs = obs
        self._last_action = action
        return PolicyDecision(
            action=action,
            score=float(scores[action.value]),
            reasoning=f"learned:{action.value}={scores[action.value]:.3f}",
            scores=scores,
        )

    def update(self, reward: float) -> None:
        """Online linear update toward actions that yielded reward."""
        if self._last_obs is None or self._last_action is None:
            return
        feats = self._features(self._last_obs)
        a = self._last_action.value
        # Reward-weighted: push weights in direction of features * reward
        for i, fi in enumerate(feats):
            self.weights[a][i] += self.lr * float(reward) * fi
            # Mild L2 shrink
            self.weights[a][i] *= 0.999


class RandomPolicy:
    """Ablation baseline."""

    name = "random"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def act(self, obs: PolicyObservation) -> PolicyDecision:
        if not obs.episode_active:
            action = self.rng.choice([PolicyAction.EXPLORE, PolicyAction.INVESTIGATE, PolicyAction.ABANDON])
        else:
            action = self.rng.choice([a for a in POLICY_ACTIONS if a != PolicyAction.EXPLORE])
        return PolicyDecision(action=action, score=0.0, reasoning="random")


def policy_action_to_investigation(action: PolicyAction) -> str:
    """Map high-level policy action to investigation action_select name."""
    mapping = {
        PolicyAction.EXPLORE: "abandon",  # leave episode
        PolicyAction.INVESTIGATE: "probe",
        PolicyAction.LOCALIZE: "localize",
        PolicyAction.FALSIFY: "falsify",
        PolicyAction.BOUNDARY: "boundary",
        PolicyAction.VARIANT: "variant",
        PolicyAction.REPEAT: "repeat",
        PolicyAction.VERIFY: "verify",
        PolicyAction.ABANDON: "abandon",
    }
    return mapping.get(action, "probe")


__all__ = [
    "PolicyAction",
    "POLICY_ACTIONS",
    "PolicyObservation",
    "PolicyDecision",
    "HeuristicController",
    "LearnedController",
    "RandomPolicy",
    "policy_action_to_investigation",
]
