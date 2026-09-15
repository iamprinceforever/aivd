"""Investigation-branch lifecycle for the global arbiter (3.18)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.epistemic.scoring import completion_probability, expected_terminal_value
from aivd.epistemic.types import BranchState, TERMINAL_BRANCH_STATES, VIABLE_BRANCH_STATES


@dataclass
class Branch:
    branch_id: str
    subsystem: str
    hypothesis_id: str = ""
    state: BranchState = BranchState.FORMING
    evidence_strength: float = 0.2
    dead_end_score: float = 0.0
    uncertainty: float = 0.8
    security_relevance: float = 0.0
    verification_value: float = 0.0
    discrimination_value: float = 0.0
    estimated_remaining_steps: int = 4
    experiments_used: int = 0
    wait_time: int = 0
    starvation_time: int = 0
    last_ig: float = 0.0
    mean_ig: float = 0.0
    repeating_failed: bool = False
    causal_evidence: bool = False
    protected: bool = False
    completion_p: float = 0.0
    expected_terminal: float = 0.0
    seen_actions: set[str] = field(default_factory=set)
    history: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def viable(self) -> bool:
        return self.state in VIABLE_BRANCH_STATES

    def terminal(self) -> bool:
        return self.state in TERMINAL_BRANCH_STATES

    def recompute(self, remaining_budget: int) -> None:
        self.completion_p = completion_probability(
            evidence_strength=self.evidence_strength,
            dead_end_score=self.dead_end_score,
            estimated_remaining_steps=self.estimated_remaining_steps,
            remaining_budget=remaining_budget,
            plausible_path=0.0 if self.repeating_failed else 1.0,
        )
        self.expected_terminal = expected_terminal_value(
            security_relevance=self.security_relevance,
            verification_value=self.verification_value,
        )

    def observe_result(
        self,
        *,
        actual_ig: float,
        effect: float,
        secret: bool,
        falsified: bool,
        redundant: bool,
        remaining_budget: int,
    ) -> None:
        self.experiments_used += 1
        self.wait_time = 0
        self.last_ig = float(actual_ig)
        n = self.experiments_used
        self.mean_ig = self.mean_ig + (float(actual_ig) - self.mean_ig) / n
        self.uncertainty = max(0.05, min(1.0, self.uncertainty * (1.0 - 0.08 - 0.25 * abs(effect) * 0.5)))
        if secret:
            self.evidence_strength = 1.0
            self.security_relevance = 1.0
            self.verification_value = max(self.verification_value, 0.7)
            self.estimated_remaining_steps = 0
            self.state = BranchState.COMPLETED
        elif falsified:
            self.dead_end_score = 1.0
            self.evidence_strength = min(self.evidence_strength, 0.05)
            self.state = BranchState.FALSIFIED
        else:
            self.evidence_strength = min(1.0, self.evidence_strength + 0.35 * float(actual_ig) + 0.2 * float(effect))
            if effect > 0.15:
                self.causal_evidence = True
                self.discrimination_value = min(1.0, self.discrimination_value + 0.15)
                self.estimated_remaining_steps = max(1, self.estimated_remaining_steps - 1)
            if actual_ig < 0.01:
                self.dead_end_score = min(1.0, self.dead_end_score + 0.2)
            else:
                self.dead_end_score = max(0.0, self.dead_end_score - 0.1)
            if redundant:
                self.repeating_failed = True
                self.dead_end_score = min(1.0, self.dead_end_score + 0.25)
            self._refresh_state(remaining_budget)
        self.recompute(remaining_budget)
        self.history.append({
            "ig": actual_ig, "effect": effect, "secret": secret,
            "falsified": falsified, "state": self.state.value,
        })

    def tick_wait(self) -> None:
        if self.viable():
            self.wait_time += 1
            if self.wait_time >= 4:
                self.starvation_time += 1

    def maybe_starve(self, remaining_budget: int) -> None:
        if self.terminal():
            return
        if remaining_budget <= 0 and self.state not in (
            BranchState.COMPLETED, BranchState.FALSIFIED, BranchState.ABANDONED,
        ):
            if self.completion_p > 0.2 and self.estimated_remaining_steps > 0:
                self.state = BranchState.STARVED
            elif self.dead_end_score > 0.7:
                self.state = BranchState.ABANDONED

    def abandon(self, reason: str = "") -> None:
        self.state = BranchState.ABANDONED
        if reason:
            self.meta["abandon_reason"] = reason

    def _refresh_state(self, remaining_budget: int) -> None:
        if self.state in (BranchState.COMPLETED, BranchState.FALSIFIED):
            return
        if self.dead_end_score >= 0.85:
            self.state = BranchState.ABANDONED
            return
        if self.verification_value >= 0.6 and self.security_relevance >= 0.5:
            self.state = BranchState.VERIFYING
            return
        if self.causal_evidence and self.evidence_strength >= 0.55:
            self.state = BranchState.HIGH_VALUE
            return
        if self.evidence_strength >= 0.35:
            self.state = BranchState.PROMISING
            return
        if self.experiments_used > 0:
            self.state = BranchState.ACTIVE
            return
        self.state = BranchState.FORMING

    def stats(self) -> dict[str, Any]:
        return {
            "evidence_strength": self.evidence_strength,
            "dead_end_score": self.dead_end_score,
            "uncertainty": self.uncertainty,
            "security_relevance": self.security_relevance,
            "verification_value": self.verification_value,
            "discrimination_value": self.discrimination_value,
            "estimated_remaining_steps": self.estimated_remaining_steps,
            "completion_p": self.completion_p,
            "expected_terminal": self.expected_terminal,
            "repeating_failed": self.repeating_failed,
            "causal_evidence": self.causal_evidence,
            "protected": self.protected,
            "state": self.state.value,
        }

    def as_dict(self) -> dict[str, Any]:
        d = self.stats()
        d.update({
            "branch_id": self.branch_id,
            "subsystem": self.subsystem,
            "hypothesis_id": self.hypothesis_id,
            "experiments_used": self.experiments_used,
            "wait_time": self.wait_time,
            "starvation_time": self.starvation_time,
            "mean_ig": self.mean_ig,
        })
        return d


class BranchRegistry:
    def __init__(self) -> None:
        self.branches: dict[str, Branch] = {}

    def get(self, branch_id: str) -> Branch | None:
        return self.branches.get(branch_id)

    def register(self, branch: Branch) -> Branch:
        self.branches[branch.branch_id] = branch
        return branch

    def ensure(
        self,
        branch_id: str,
        *,
        subsystem: str,
        hypothesis_id: str = "",
        remaining_steps: int = 4,
    ) -> Branch:
        b = self.branches.get(branch_id)
        if b is None:
            b = Branch(
                branch_id=branch_id,
                subsystem=subsystem,
                hypothesis_id=hypothesis_id,
                estimated_remaining_steps=remaining_steps,
            )
            self.branches[branch_id] = b
        return b

    def viable(self) -> list[Branch]:
        return [b for b in self.branches.values() if b.viable()]

    def tick_unselected(self, selected_id: str | None, remaining_budget: int) -> None:
        for b in self.branches.values():
            if selected_id is None or b.branch_id != selected_id:
                b.tick_wait()
            b.maybe_starve(remaining_budget)

    def as_dict(self) -> dict[str, Any]:
        return {k: v.as_dict() for k, v in self.branches.items()}


__all__ = ["Branch", "BranchRegistry"]
