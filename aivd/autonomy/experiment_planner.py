"""Unified experiment planner — EVI-like scoring (3.15).

Factors: IG, uncertainty, discrimination, transfer, cross-signal, readiness,
security − redundancy/repetition/invalidity/budget_risk.
Integrates cross_signal scoring + joint EVI — does not duplicate logic blindly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState
from aivd.invention.intervention_space import Intervention


@dataclass
class PlanItem:
    intervention: Intervention
    score: float
    components: dict[str, float] = field(default_factory=dict)
    why: str = ""
    region_id: str | None = None


def _redundancy_penalty(inv: Intervention, tested_keys: set[str]) -> float:
    key = "|".join(inv.sequence or []) or inv.id
    if key in tested_keys:
        return 0.8
    # Soft overlap
    toks = set(str(t).lower() for t in (inv.sequence or []))
    for tk in tested_keys:
        other = set(tk.lower().split("|"))
        if toks and other and len(toks & other) / max(1, len(toks | other)) > 0.7:
            return 0.35
    return 0.0


def score_candidate(
    inv: Intervention,
    state: AutonomousDiscoveryState,
    *,
    tested_keys: set[str] | None = None,
    cross_signal_bonus: float = 0.0,
    readiness_bonus: float = 0.0,
) -> PlanItem:
    """EVI-like multi-factor score."""
    tested = tested_keys or set()
    region_id = (inv.meta or {}).get("routed_region")
    u = float(state.uncertainties.get(region_id, 0.7)) if region_id else 0.6
    transfer_p = float(state.region_priors.get(region_id, 0.4)) if region_id else 0.35
    # Information gain proxy: high uncertainty + transfer
    ig = 0.45 * u + 0.35 * transfer_p
    # Discrimination: prefer hyps needing evidence
    disc = 0.25
    if state.hypotheses:
        disc = 0.2 + 0.15 * min(1.0, len([h for h in state.hypotheses if h.get("state") in ("open", "active")]) / 4.0)
    # Security relevance (no GT) from residual unexplained + prior security map
    sec = float(state.security_relevance.get(region_id or "", 0.0))
    sec = max(sec, 0.15 * float(state.unexplained))
    # Cross-signal / readiness from planner integration
    xs = float(cross_signal_bonus)
    ready = float(readiness_bonus)
    # Penalties
    red = _redundancy_penalty(inv, tested)
    invalid = 0.0 if (inv.sequence and len(inv.sequence) <= 12) else 0.4
    budget_risk = 0.15 if state.reserve_budget > 0 and state.step > 0 else 0.0
    # Operator EIG if annotated
    op = (inv.meta or {}).get("abstract_op")
    op_eig = float(state.eig_estimates.get(op, 0.3)) if op else 0.25

    score = (
        0.22 * ig
        + 0.14 * u
        + 0.12 * disc
        + 0.12 * transfer_p
        + 0.10 * xs
        + 0.08 * ready
        + 0.12 * sec
        + 0.10 * op_eig
        - 0.25 * red
        - 0.20 * invalid
        - 0.10 * budget_risk
    )
    comps = {
        "ig": ig,
        "uncertainty": u,
        "discrimination": disc,
        "transfer": transfer_p,
        "cross_signal": xs,
        "readiness": ready,
        "security": sec,
        "op_eig": op_eig,
        "redundancy": red,
        "invalidity": invalid,
        "budget_risk": budget_risk,
    }
    why = (
        f"I am planning this because ig={ig:.2f} u={u:.2f} transfer={transfer_p:.2f} "
        f"xs={xs:.2f} sec={sec:.2f} − red={red:.2f}"
    )
    return PlanItem(
        intervention=inv,
        score=float(score),
        components=comps,
        why=why,
        region_id=region_id,
    )


def plan_experiments(
    candidates: list[Intervention],
    state: AutonomousDiscoveryState,
    *,
    budget: int = 8,
    tested_keys: set[str] | None = None,
    cross_signal_scores: dict[str, float] | None = None,
    diversity: bool = True,
) -> list[PlanItem]:
    """Select a diverse, high-EVI batch under budget."""
    xs_map = cross_signal_scores or {}
    items = [
        score_candidate(
            inv,
            state,
            tested_keys=tested_keys,
            cross_signal_bonus=float(xs_map.get((inv.meta or {}).get("routed_region") or "", 0.0)),
            readiness_bonus=float(state.readiness.get((inv.meta or {}).get("routed_region") or "", 0.0)),
        )
        for inv in candidates
    ]
    items.sort(key=lambda p: -p.score)
    if not diversity:
        chosen = items[:budget]
    else:
        # Diversity across regions / families / ops
        chosen = []
        seen_regions: set[str] = set()
        seen_fams: set[str] = set()
        seen_ops: set[str] = set()
        for it in items:
            if len(chosen) >= budget:
                break
            rid = it.region_id or "?"
            fam = (it.intervention.meta or {}).get("family_id") or "?"
            op = (it.intervention.meta or {}).get("abstract_op") or "?"
            # Soft diversity: allow repeats after coverage
            penalty = 0
            if rid in seen_regions:
                penalty += 1
            if fam in seen_fams:
                penalty += 1
            if op in seen_ops:
                penalty += 1
            if penalty >= 3 and len(chosen) < budget // 2:
                continue
            if penalty >= 2 and len(seen_regions) < 3 and len(chosen) < budget:
                # Prefer unseen region
                continue
            chosen.append(it)
            seen_regions.add(rid)
            seen_fams.add(str(fam))
            seen_ops.add(str(op))
        # Fill remaining by score
        if len(chosen) < budget:
            ids = {id(c.intervention) for c in chosen}
            for it in items:
                if len(chosen) >= budget:
                    break
                if id(it.intervention) not in ids:
                    chosen.append(it)
    state.log("EXPERIMENT_PLAN", n=len(chosen), budget=budget, head_scores=[round(c.score, 3) for c in chosen[:5]])
    # Store EIG estimates per planned region
    for it in chosen:
        if it.region_id:
            state.eig_estimates[it.region_id] = max(
                float(state.eig_estimates.get(it.region_id, 0.0)),
                float(it.components.get("ig", 0.0)),
            )
    return chosen


def integrate_cross_signal_scores(
    state: AutonomousDiscoveryState,
    cross_summary: dict[str, Any] | None,
) -> dict[str, float]:
    """Bidirectional: pull cross-signal link scores into planner region bonuses."""
    out: dict[str, float] = {}
    if not cross_summary:
        return out
    hyps = cross_summary.get("hypotheses") or cross_summary.get("hypotheses_summary") or []
    if isinstance(hyps, list):
        for h in hyps:
            if not isinstance(h, dict):
                continue
            rid = str(h.get("action_id") or h.get("region") or h.get("action_family") or "")
            score = float(h.get("cross_evi") or h.get("link_score") or h.get("score") or 0.0)
            if rid:
                out[rid] = max(out.get(rid, 0.0), score)
    # Also map generic residual strength
    if cross_summary.get("n_hypotheses"):
        state.cross_signal = {
            "n_hypotheses": cross_summary.get("n_hypotheses"),
            "n_supported": cross_summary.get("n_supported"),
            "secret_found": cross_summary.get("secret_found"),
        }
    return out


__all__ = [
    "PlanItem",
    "score_candidate",
    "plan_experiments",
    "integrate_cross_signal_scores",
]
