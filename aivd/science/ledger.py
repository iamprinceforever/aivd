"""Evidence ledger. One experiment is one experiment.

Records what was observed so a later stage can reuse already-paid
evidence without inventing independent trials. Reuse is allowed only
when independence_class permits it. Discovery cannot substitute for
reproduction. Search negatives can satisfy an invariant control.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evidence:
    evidence_id: str
    source_experiment: int
    question: str
    hypothesis: str
    observation: str
    interpretation: str
    independence_class: str
    supports: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    confidence: float = 0.5
    reusable_for: tuple[str, ...] = ()
    cannot_substitute_for: tuple[str, ...] = ()
    prompt: str = ""
    secret: bool = False
    ops: tuple[str, ...] = ()
    remaining: int = 0
    stage: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_experiment": self.source_experiment,
            "question": self.question,
            "hypothesis": self.hypothesis,
            "observation": self.observation,
            "interpretation": self.interpretation,
            "independence_class": self.independence_class,
            "supports": list(self.supports),
            "contradicts": list(self.contradicts),
            "confidence": self.confidence,
            "reusable_for": list(self.reusable_for),
            "cannot_substitute_for": list(self.cannot_substitute_for),
            "secret": self.secret,
            "stage": self.stage,
            "remaining": self.remaining,
        }


class EvidenceLedger:
    """In-episode ledger. Does not read evaluator ground truth."""

    def __init__(self) -> None:
        self.items: list[Evidence] = []
        self.seq = 0
        self.reused = 0
        self.released = 0
        self.stranded = 0
        self.profile: list[dict[str, Any]] = []

    def record(
        self,
        *,
        prompt: str,
        secret: bool,
        ops: list[str] | None,
        remaining: int,
        stage: str,
        metric: float = 0.0,
        informative: bool = False,
    ) -> Evidence:
        self.seq += 1
        used_ops = tuple(ops or ())
        stage_n = stage or _stage_of(used_ops)
        if secret:
            independence = "discovery"
            reusable: tuple[str, ...] = ()
            cannot = ("reproduction", "invariant", "falsify")
            interpretation = "security_effect_observed"
            supports = ("discovery",)
        elif not used_ops:
            independence = "control"
            reusable = ("invariant",)
            cannot = ("reproduction", "discovery")
            interpretation = "unrelated_prompt_no_secret"
            supports = ("invariant",)
        elif not informative:
            independence = "search_negative"
            reusable = ("invariant",)
            cannot = ("reproduction", "discovery")
            interpretation = "candidate_noninformative"
            supports = ("reject_class", "invariant")
        else:
            independence = "search_positive"
            reusable = ()
            cannot = ("reproduction", "invariant")
            interpretation = "informative_without_secret"
            supports = ("localization",)
        ev = Evidence(
            evidence_id=f"e{self.seq}",
            source_experiment=self.seq,
            question=stage_n,
            hypothesis="+".join(used_ops) or "control",
            observation="secret" if secret else ("informative" if informative else "negative"),
            interpretation=interpretation,
            independence_class=independence,
            supports=supports,
            contradicts=("secret_on_control",) if (not secret and not used_ops) else (),
            confidence=0.9 if secret else 0.6,
            reusable_for=reusable,
            cannot_substitute_for=cannot,
            prompt=(prompt or "")[:240],
            secret=bool(secret),
            ops=used_ops,
            remaining=int(remaining),
            stage=stage_n,
        )
        self.items.append(ev)
        self.profile.append({
            "experiment_number": self.seq,
            "stage": stage_n,
            "question": stage_n,
            "candidate": ev.hypothesis,
            "remaining_budget": remaining,
            "result": ev.observation,
            "metric": round(float(metric), 4),
        })
        return ev

    def invariant_ready(self) -> bool:
        """True iff an already-paid independent negative can serve as a control."""
        for ev in self.items:
            if ev.secret:
                continue
            if "invariant" in ev.reusable_for:
                return True
        return False

    def mark_reused(self, purpose: str) -> None:
        self.reused += 1
        self.profile.append({
            "event": "evidence_reuse",
            "purpose": purpose,
            "independence": "reuse_observation_not_new_experiment",
        })

    def mark_release(self, n: int) -> None:
        if n > 0:
            self.released += n

    def as_dict(self) -> dict[str, Any]:
        return {
            "n": len(self.items),
            "reused": self.reused,
            "released": self.released,
            "stranded": self.stranded,
            "invariant_ready": self.invariant_ready(),
            "items": [e.as_dict() for e in self.items[-16:]],
            "profile": list(self.profile[-24:]),
        }


def _stage_of(ops: tuple[str, ...]) -> str:
    if not ops:
        return "control"
    op = ops[0]
    if op.startswith("atom_"):
        return "atom"
    if op.startswith("ext_"):
        return "ext"
    if op.startswith("p_"):
        return "prim"
    if op.startswith("syn_"):
        return "ir"
    return "search"


__all__ = ["Evidence", "EvidenceLedger"]
