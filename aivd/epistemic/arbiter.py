"""Global Epistemic Arbiter — every subsystem proposes; none owns the next slot."""
from __future__ import annotations

from typing import Any

from aivd.epistemic.accounting import GlobalLedger
from aivd.epistemic.allocation import select_next, legacy_choice
from aivd.epistemic.branch import BranchRegistry
from aivd.epistemic.reservation import (
    Reservation,
    ReservationBook,
    earns_protected_floor,
    protected_slots,
)
from aivd.epistemic.shadow import ShadowLog, compare_choices
from aivd.epistemic.types import (
    AllocationDecision,
    ExperimentProposal,
    ExperimentTraceRecord,
)


class GlobalEpistemicArbiter:
    """Allocate a shared experiment budget across branches.

    Default policy is completion-value scoring (not greedy EIG).
    Reservations are suggestions; the arbiter may revoke them.
    """

    def __init__(
        self,
        *,
        total: int = 32,
        seed: int = 0,
        shadow: bool = False,
        policy: str = "completion_value",
    ):
        self.seed = int(seed)
        self.shadow = bool(shadow)
        self.policy = str(policy or "completion_value")
        self.ledger = GlobalLedger(total=int(total))
        self.registry = BranchRegistry()
        self.book = ReservationBook()
        self.shadow_log = ShadowLog()
        self.step = 0
        self.last_decision: AllocationDecision | None = None

    def register_branch(self, branch) -> None:
        self.registry.register(branch)

    def refresh_floors(self) -> None:
        """Evidence-driven protected continuation. Subsystem-agnostic. Revocable."""
        remaining = self.ledger.remaining()
        for b in self.registry.viable():
            b.recompute(remaining)
            ok = earns_protected_floor(
                evidence_causal=b.causal_evidence,
                unresolved_uncertainty=b.uncertainty,
                completion_probability=b.completion_p,
                discrimination_value=b.discrimination_value,
                repeating_failed=b.repeating_failed,
                remaining_steps=b.estimated_remaining_steps,
                remaining_budget=remaining,
            )
            existing = [r for r in self.book.active if r.owner == b.branch_id and r.protected]
            if ok:
                n = protected_slots(
                    remaining_steps=b.estimated_remaining_steps,
                    remaining_budget=remaining,
                    completion_probability=b.completion_p,
                )
                if n > 0 and not existing:
                    room = self.ledger.remaining_free()
                    take = min(n, room)
                    if take > 0:
                        self.ledger.reserved += take
                        self.book.add(Reservation(
                            reservation_id="",
                            owner=b.branch_id,
                            purpose="protected_continuation",
                            slots=take,
                            expected_value=b.completion_p * b.expected_terminal,
                            protected=True,
                            created_step=self.step,
                            expiry_step=self.step + max(4, take + 2),
                        ))
                        b.protected = True
            else:
                if existing:
                    n = self.book.revoke_owner(b.branch_id, reason="evidence_collapse")
                    self.ledger.reserved = max(0, self.ledger.reserved - n)
                    self.ledger.revoked += n
                    self.ledger.reallocation_count += 1
                    b.protected = False
        expired = self.book.expire(self.step)
        if expired:
            self.ledger.reserved = max(0, self.ledger.reserved - expired)
            self.ledger.revoked += expired
            self.ledger.reallocation_count += 1

    def decide(self, proposals: list[ExperimentProposal]) -> AllocationDecision:
        self.refresh_floors()
        remaining = self.ledger.remaining()
        stats = {b.branch_id: b.stats() for b in self.registry.branches.values()}
        prot = {b.branch_id for b in self.registry.viable() if b.protected}
        if self.shadow:
            dec = compare_choices(
                proposals,
                remaining_budget=remaining,
                step=self.step,
                branch_stats=stats,
                protected_owners=prot,
                execute_legacy=True,
            )
        else:
            selected, ranked = select_next(
                proposals,
                remaining_budget=remaining,
                branch_stats=stats,
                protected_owners=prot,
                policy=self.policy,
            )
            leg = legacy_choice(ranked or proposals)
            agree = True
            if selected is not None and leg is not None:
                agree = selected.proposal_id == leg.proposal_id
            dec = AllocationDecision(
                step=self.step,
                selected=selected,
                legacy_selected=leg,
                proposals=ranked or proposals,
                remaining_budget=remaining,
                reason=self.policy,
                shadow=False,
                agreement=agree,
            )
        self.shadow_log.record(dec)
        self.last_decision = dec
        return dec

    def commit_execution(
        self,
        proposal: ExperimentProposal,
        *,
        actual_ig: float,
        uncertainty_before: float,
        uncertainty_after: float,
        effect: float,
        secret: bool,
        falsified: bool,
        redundant: bool,
        cost: float = 1.0,
    ) -> bool:
        """Charge the global ledger and update the branch. One env interaction."""
        locally = any(r.owner == proposal.branch_id for r in self.book.active)
        ok = self.ledger.charge(
            int(max(1, round(cost))),
            subsystem=proposal.subsystem,
            branch_id=proposal.branch_id,
            proposal_id=proposal.proposal_id,
            locally_reserved=locally,
        )
        if not ok:
            return False
        if locally:
            self.book.consume(proposal.branch_id, int(max(1, round(cost))))
        b = self.registry.ensure(
            proposal.branch_id,
            subsystem=proposal.subsystem,
            hypothesis_id=proposal.hypothesis_id,
            remaining_steps=proposal.estimated_remaining_steps,
        )
        b.security_relevance = max(b.security_relevance, proposal.security_relevance)
        b.verification_value = max(b.verification_value, proposal.verification_value)
        b.discrimination_value = max(b.discrimination_value, proposal.hypothesis_discrimination_value)
        b.seen_actions.add(proposal.action or proposal.prompt)
        b.observe_result(
            actual_ig=actual_ig,
            effect=effect,
            secret=secret,
            falsified=falsified,
            redundant=redundant,
            remaining_budget=self.ledger.remaining(),
        )
        self.registry.tick_unselected(proposal.branch_id, self.ledger.remaining())
        rec = ExperimentTraceRecord(
            global_index=self.ledger.used,
            subsystem=proposal.subsystem,
            branch_id=proposal.branch_id,
            hypothesis_id=proposal.hypothesis_id,
            candidate_id=proposal.proposal_id,
            expected_ig=float(proposal.expected_information_gain),
            actual_ig=float(actual_ig),
            uncertainty_before=float(uncertainty_before),
            uncertainty_after=float(uncertainty_after),
            security_relevance=float(max(proposal.security_relevance, effect)),
            verification_relevance=float(proposal.verification_value),
            experiment_cost=float(cost),
            branch_state=b.state.value,
            remaining_global_budget=self.ledger.remaining(),
            locally_reserved=locally,
            later_redundant=redundant,
            branch_completed=secret or b.state.value == "COMPLETED",
            starved_other=any(x.starvation_time > 0 for x in self.registry.branches.values()),
            proposal_id=proposal.proposal_id,
            action=proposal.action,
        )
        self.ledger.record_trace(rec)
        self.step += 1
        return True

    def checkpoint(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "shadow": self.shadow,
            "policy": self.policy,
            "step": self.step,
            "ledger": self.ledger.as_dict(),
            "branches": self.registry.as_dict(),
            "reservations": self.book.as_dict(),
            "shadow_log": self.shadow_log.as_dict(),
        }


__all__ = ["GlobalEpistemicArbiter"]
