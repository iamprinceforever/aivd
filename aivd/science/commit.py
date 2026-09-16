"""Epistemic commitment: a temporary lease to test a gap-addressing experiment.

Not a novelty bonus. Not a named-operator boost. The lease exists because
an unresolved question cannot be answered by the current ontology, and this
experiment was compiled to ask that question.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UnresolvedQuestion:
    question_id: str
    origin: str
    hypothesis: str
    uncertainty: float = 0.7
    completion_state: str = "open"
    postponement_count: int = 0
    debt: float = 0.0


@dataclass
class ExperimentLease:
    lease_id: str
    question_id: str
    op: str
    created_at: int = 0
    remaining: int = 1
    state: str = "COMMITTED"
    evidence: float = 0.0
    executed: int = 0


@dataclass
class CommitmentBoard:
    questions: list[UnresolvedQuestion] = field(default_factory=list)
    leases: list[ExperimentLease] = field(default_factory=list)
    executed_novel: int = 0
    revoked: int = 0
    informative: int = 0
    max_leases_executed: int = 3
    waves: int = 0

    def first_wave_exhausted(self) -> bool:
        if any(L.state == "UNLOCKED" for L in self.leases):
            return False
        pending = [
            L for L in self.leases
            if L.state in ("COMMITTED", "TESTING", "INFORMATIVE") and L.remaining > 0
        ]
        return (not pending) and self.revoked >= 1 and self.waves < 2

    def open_gap(self, *, probe: int) -> UnresolvedQuestion:
        q = UnresolvedQuestion(
            question_id=f"q.gap.{len(self.questions)}",
            origin="KNOWN_INTERVENTIONS_INSUFFICIENT",
            hypothesis="identity-preserving residual is not expressed by the current grammar",
        )
        self.questions.append(q)
        return q

    def commit_ops(self, ops: list[str], *, question_id: str, probe: int) -> None:
        for op in ops:
            if any(L.op == op for L in self.leases):
                continue
            self.leases.append(ExperimentLease(
                lease_id=f"lease.{len(self.leases)}",
                question_id=question_id,
                op=op,
                created_at=probe,
                remaining=1,
                state="COMMITTED",
            ))

    def due(self) -> ExperimentLease | None:
        if self.executed_novel >= self.max_leases_executed:
            return None
        for L in self.leases:
            if L.state in ("COMMITTED", "TESTING", "INFORMATIVE") and L.remaining > 0:
                return L
        return None

    def postpone(self) -> None:
        for q in self.questions:
            if q.completion_state == "open":
                q.postponement_count += 1
                q.debt = min(8.0, q.debt + 1.0)

    def on_result(self, op: str, *, informative: bool, secret: bool) -> None:
        for L in self.leases:
            if L.op != op:
                continue
            L.executed += 1
            L.remaining = max(0, L.remaining - 1)
            self.executed_novel += 1
            if secret or informative:
                L.state = "INFORMATIVE"
                L.evidence += 1.0
                self.informative += 1
                if secret:
                    L.remaining = 0
                    L.state = "UNLOCKED"
                elif L.executed < 2:
                    L.remaining = 1  # one renewal on evidence
            else:
                L.state = "REVOKED"
                L.remaining = 0
                self.revoked += 1
            return


__all__ = ["UnresolvedQuestion", "ExperimentLease", "CommitmentBoard"]
