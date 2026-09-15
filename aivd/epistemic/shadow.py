"""Shadow mode: record LEGACY vs ARBITER choice without changing execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.epistemic.allocation import legacy_choice, select_next
from aivd.epistemic.types import AllocationDecision, ExperimentProposal


@dataclass
class ShadowLog:
    decisions: list[AllocationDecision] = field(default_factory=list)

    def record(self, dec: AllocationDecision) -> None:
        self.decisions.append(dec)

    @property
    def n(self) -> int:
        return len(self.decisions)

    def agreement_rate(self) -> float:
        if not self.decisions:
            return 1.0
        return sum(1 for d in self.decisions if d.agreement) / len(self.decisions)

    def n_disagree(self) -> int:
        return sum(1 for d in self.decisions if not d.agreement)

    def legacy_regret(self) -> float:
        """mean(best_available - legacy_selected) over disagreements+agreements."""
        vals: list[float] = []
        for d in self.decisions:
            if not d.proposals:
                continue
            best = max(p.score.total for p in d.proposals)
            leg = d.legacy_selected.score.total if d.legacy_selected else 0.0
            vals.append(best - leg)
        return sum(vals) / len(vals) if vals else 0.0

    def arbiter_regret(self) -> float:
        vals: list[float] = []
        for d in self.decisions:
            if not d.proposals:
                continue
            best = max(p.score.total for p in d.proposals)
            arb = d.selected.score.total if d.selected else 0.0
            vals.append(best - arb)
        return sum(vals) / len(vals) if vals else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_decisions": self.n,
            "agreement_rate": self.agreement_rate(),
            "n_disagree": self.n_disagree(),
            "legacy_regret": self.legacy_regret(),
            "arbiter_regret": self.arbiter_regret(),
            "decisions": [d.as_dict() for d in self.decisions[-64:]],
        }


def compare_choices(
    proposals: list[ExperimentProposal],
    *,
    remaining_budget: int,
    step: int,
    branch_stats: dict[str, dict[str, Any]] | None = None,
    protected_owners: set[str] | None = None,
    execute_legacy: bool = True,
) -> AllocationDecision:
    """Compare policies. If execute_legacy, selected=legacy (shadow does not change execution)."""
    arb, ranked = select_next(
        proposals,
        remaining_budget=remaining_budget,
        branch_stats=branch_stats,
        protected_owners=protected_owners,
    )
    # Attach ranked scores onto the original list for regret
    scored = ranked or proposals
    leg = legacy_choice(scored)
    agree = True
    if arb is not None and leg is not None:
        agree = arb.proposal_id == leg.proposal_id
    chosen = leg if execute_legacy else arb
    return AllocationDecision(
        step=step,
        selected=chosen,
        legacy_selected=leg,
        proposals=scored,
        remaining_budget=remaining_budget,
        reason="shadow_legacy_exec" if execute_legacy else "authoritative",
        shadow=execute_legacy,
        agreement=agree,
    )


__all__ = ["ShadowLog", "compare_choices"]
