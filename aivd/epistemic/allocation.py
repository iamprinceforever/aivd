"""Select the next experiment from the global proposal frontier (3.18)."""
from __future__ import annotations

from typing import Any

from aivd.epistemic.scoring import apply_opportunity_costs, greedy_eig_select
from aivd.epistemic.types import ExperimentProposal


def select_next(
    proposals: list[ExperimentProposal],
    *,
    remaining_budget: int,
    branch_stats: dict[str, dict[str, Any]] | None = None,
    protected_owners: set[str] | None = None,
    policy: str = "completion_value",
) -> tuple[ExperimentProposal | None, list[ExperimentProposal]]:
    """Return (selected, ranked). Never enumerates the full action space.

    policy:
      completion_value — default 3.18 (EIG + completion + floors)
      greedy_eig — 3.17-like control
      sequential — first proposal in insertion order (legacy tower)
    """
    viable = [p for p in proposals if float(p.experiment_cost) <= remaining_budget]
    if not viable:
        return None, []
    pol = (policy or "completion_value").lower()
    if pol in ("greedy_eig", "greedy", "eig"):
        ranked = sorted(viable, key=lambda p: (-p.expected_information_gain, p.proposal_id))
        return (ranked[0] if ranked else None), ranked
    if pol in ("sequential", "legacy"):
        return viable[0], viable
    ranked = apply_opportunity_costs(
        viable, remaining_budget=remaining_budget, branch_stats=branch_stats,
    )
    prot = protected_owners or set()
    if prot:
        # Soft floor: among protected branches, prefer the highest-scoring
        # protected proposal if its completion value is competitive.
        protected = [p for p in ranked if p.branch_id in prot]
        if protected:
            head = ranked[0]
            best_p = protected[0]
            # If the unprotected head is a high-EIG dead-end relative to a
            # protected multi-step branch, keep investing in the protected one.
            if best_p.score.expected_completion + 1e-9 >= 0.55 * max(0.05, head.score.total):
                if best_p.proposal_id != head.proposal_id:
                    ranked = [best_p] + [p for p in ranked if p.proposal_id != best_p.proposal_id]
    return (ranked[0] if ranked else None), ranked


def legacy_choice(
    proposals: list[ExperimentProposal],
    *,
    preferred_subsystems: list[str] | None = None,
) -> ExperimentProposal | None:
    """Approximate 3.17 sequential ownership: first preferred subsystem, else greedy EIG."""
    if not proposals:
        return None
    order = preferred_subsystems or [
        "residual", "axis", "invention", "openworld", "autonomy", "reasoning", "verify",
    ]
    for sub in order:
        group = [p for p in proposals if p.subsystem == sub]
        if group:
            return greedy_eig_select(group)
    return greedy_eig_select(proposals)


__all__ = ["select_next", "legacy_choice"]
