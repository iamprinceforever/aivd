"""Joint residual dependency estimation — hypothesize A×B residual coupling."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import time

from aivd.invention.intervention_space import Intervention
from aivd.joint.joint_uncertainty import (
    component_uncertainty,
    joint_evi,
    joint_uncertainty,
)
from aivd.joint.readiness import ComponentState, readiness_score


@dataclass
class JointResidualHypothesis:
    """Hypothesis that a residual depends jointly on underexplored components A, B.

    Goal: manage joint uncertainty — NOT 'make a specific holdout pass.'
    """

    residual: str = ""
    component_a: Intervention | None = None
    component_b: Intervention | None = None
    family_a: str = ""
    family_b: str = ""
    component_ids: list[str] = field(default_factory=list)
    families: list[str] = field(default_factory=list)
    u_a: float = 0.9
    u_b: float = 0.9
    u_ab: float = 0.9
    linkage: float = 0.5
    eig: float = 0.0
    joint_evi: float = 0.0
    readiness_a: str = ComponentState.UNEXAMINED.value
    readiness_b: str = ComponentState.UNEXAMINED.value
    interaction_ready: bool = False
    budget_required: float = 4.0
    evidence_quality: float = 0.0
    interaction_confidence: float = 0.0
    order_preference: str = "A+B"  # A+B | B+A | A→B | B→A
    id: str = ""
    score: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.component_a is not None and not self.family_a:
            self.family_a = (self.component_a.meta or {}).get("family_id") or "unknown"
        if self.component_b is not None and not self.family_b:
            self.family_b = (self.component_b.meta or {}).get("family_id") or "unknown"
        if not self.families:
            self.families = [self.family_a, self.family_b]
        if not self.component_ids:
            ids = []
            if self.component_a is not None:
                ids.append(self.component_a.id)
            if self.component_b is not None:
                ids.append(self.component_b.id)
            self.component_ids = ids
        if not self.id:
            blob = f"{self.residual}|{self.family_a}|{self.family_b}|{time.time_ns()}"
            self.id = hashlib.sha256(blob.encode()).hexdigest()[:14]

    def refresh_uncertainty(
        self,
        *,
        n_a: int = 0,
        n_b: int = 0,
        var_a: int = 0,
        var_b: int = 0,
        effect_a: float = 0.0,
        effect_b: float = 0.0,
        interaction_tested: bool = False,
    ) -> None:
        self.u_a = component_uncertainty(
            n_probes=n_a, n_variants=var_a, effect_mean=effect_a,
            characterized=self.readiness_a in (
                ComponentState.CHARACTERIZED.value,
                ComponentState.INTERACTION_READY.value,
            ),
        )
        self.u_b = component_uncertainty(
            n_probes=n_b, n_variants=var_b, effect_mean=effect_b,
            characterized=self.readiness_b in (
                ComponentState.CHARACTERIZED.value,
                ComponentState.INTERACTION_READY.value,
            ),
        )
        self.interaction_ready = (
            self.readiness_a in (
                ComponentState.CHARACTERIZED.value,
                ComponentState.INTERACTION_READY.value,
            )
            and self.readiness_b in (
                ComponentState.CHARACTERIZED.value,
                ComponentState.INTERACTION_READY.value,
            )
        )
        self.u_ab = joint_uncertainty(
            self.u_a, self.u_b,
            linkage=self.linkage,
            interaction_tested=interaction_tested,
            interaction_ready=self.interaction_ready,
        )
        self.joint_evi = joint_evi(
            self.u_a, self.u_b, self.u_ab,
            readiness=0.5 * (
                readiness_score(self.readiness_a) + readiness_score(self.readiness_b)
            ),
            reserved=bool(self.meta.get("reserved")),
            standalone_value_a=effect_a,
            standalone_value_b=effect_b,
        )
        self.eig = self.joint_evi
        self.score = (
            0.35 * self.joint_evi
            + 0.25 * self.linkage
            + 0.20 * self.evidence_quality
            + 0.20 * (1.0 if self.interaction_ready else 0.3)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "residual": self.residual,
            "family_a": self.family_a,
            "family_b": self.family_b,
            "component_ids": list(self.component_ids),
            "families": list(self.families),
            "u_a": self.u_a,
            "u_b": self.u_b,
            "u_ab": self.u_ab,
            "linkage": self.linkage,
            "eig": self.eig,
            "joint_evi": self.joint_evi,
            "readiness_a": self.readiness_a,
            "readiness_b": self.readiness_b,
            "interaction_ready": self.interaction_ready,
            "budget_required": self.budget_required,
            "evidence_quality": self.evidence_quality,
            "interaction_confidence": self.interaction_confidence,
            "order_preference": self.order_preference,
            "score": self.score,
            "meta": dict(self.meta),
        }


def estimate_linkage(
    a: Intervention,
    b: Intervention,
    *,
    residual_context: dict[str, Any] | None = None,
) -> float:
    """Estimate residual-linked dependency between two families (0..1).

    General heuristics only — no Holdout-named rules.
    """
    ctx = residual_context or {}
    fa = (a.meta or {}).get("family_id") or "unknown"
    fb = (b.meta or {}).get("family_id") or "unknown"
    if fa == fb:
        return 0.15  # same family → low joint residual dependency
    link = 0.35
    # Cross-family boost
    link += 0.20
    # Shared residual token presence in sequences
    toks_a = set(str(t).split("-")[-1] for t in (a.sequence or []) if t)
    toks_b = set(str(t).split("-")[-1] for t in (b.sequence or []) if t)
    shared = toks_a & toks_b
    if shared:
        link += 0.20
    # Residual context unexplained
    unexplained = float(ctx.get("unexplained") or 0.0)
    link += 0.15 * min(1.0, unexplained)
    # Both weak individually → higher joint mystery
    ea = float(a.effect or a.security or 0.0)
    eb = float(b.effect or b.security or 0.0)
    if ea < 0.15 and eb < 0.15:
        link += 0.12
    return float(max(0.05, min(0.98, link)))


def hypothesize_joint_residuals(
    individuals: list[Intervention],
    *,
    residual_context: dict[str, Any] | None = None,
    max_hypotheses: int = 12,
    family_stats: dict[str, dict[str, Any]] | None = None,
) -> list[JointResidualHypothesis]:
    """Build joint residual hypotheses across underexplored component families.

    Hierarchical: prefer cross-family pairs with shared residual tokens;
    do not enumerate Cartesian product of all individuals.
    """
    ctx = residual_context or {}
    stats = family_stats or {}
    residual = str(
        ctx.get("error") or ctx.get("error_text") or ctx.get("residual_text") or "residual"
    )
    # Group by family
    by_fam: dict[str, list[Intervention]] = {}
    for inv in individuals or []:
        fid = (inv.meta or {}).get("family_id") or "unknown"
        by_fam.setdefault(fid, []).append(inv)
    fams = list(by_fam.keys())
    hyps: list[JointResidualHypothesis] = []
    # Hierarchical: only cross-family pairs (not brute force all individuals)
    for i, fa in enumerate(fams):
        for fb in fams[i + 1 :]:
            # Pick representative (highest effect or first)
            reps_a = sorted(
                by_fam[fa],
                key=lambda x: float(x.effect or x.security or 0.0),
                reverse=True,
            )
            reps_b = sorted(
                by_fam[fb],
                key=lambda x: float(x.effect or x.security or 0.0),
                reverse=True,
            )
            a, b = reps_a[0], reps_b[0]
            link = estimate_linkage(a, b, residual_context=ctx)
            sa = stats.get(fa) or {}
            sb = stats.get(fb) or {}
            hyp = JointResidualHypothesis(
                residual=residual,
                component_a=a,
                component_b=b,
                family_a=fa,
                family_b=fb,
                linkage=link,
                evidence_quality=0.3 + 0.2 * link,
                budget_required=4.0,
                order_preference="A+B",
            )
            hyp.readiness_a = str(sa.get("state") or ComponentState.UNEXAMINED.value)
            hyp.readiness_b = str(sb.get("state") or ComponentState.UNEXAMINED.value)
            hyp.refresh_uncertainty(
                n_a=int(sa.get("n_probes") or 0),
                n_b=int(sb.get("n_probes") or 0),
                var_a=int(sa.get("n_variants") or 0),
                var_b=int(sb.get("n_variants") or 0),
                effect_a=float(sa.get("effect_mean") or a.effect or 0.0),
                effect_b=float(sb.get("effect_mean") or b.effect or 0.0),
            )
            hyps.append(hyp)
    hyps.sort(key=lambda h: h.score, reverse=True)
    return hyps[: max_hypotheses]


__all__ = [
    "JointResidualHypothesis",
    "estimate_linkage",
    "hypothesize_joint_residuals",
]
