"""Investigation action candidates + EIG-based selection (AIVD 3.4)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class InvestigationAction(str, Enum):
    REMOVE = "remove"
    MUTATE = "mutate"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    ENCODING = "encoding"
    CONTEXT = "context"
    ORDER = "order"
    REPEAT = "repeat"
    SPLIT = "split"
    BOUNDARY = "boundary"
    SECURITY = "security"
    LOCALIZE = "localize"
    FALSIFY = "falsify"
    VARIANT = "variant"
    VERIFY = "verify"
    ABANDON = "abandon"
    BASELINE = "baseline"
    PROBE = "probe"


@dataclass
class ActionScore:
    action: InvestigationAction
    score: float
    eig: float = 0.0
    security: float = 0.0
    localization: float = 0.0
    discrimination: float = 0.0
    cost: float = 1.0
    redundancy: float = 0.0
    reasoning: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "score": self.score,
            "eig": self.eig,
            "security": self.security,
            "localization": self.localization,
            "discrimination": self.discrimination,
            "cost": self.cost,
            "redundancy": self.redundancy,
            "reasoning": self.reasoning,
            "meta": dict(self.meta),
        }


def default_candidates(
    *,
    state: str = "probing",
    has_trigger: bool = False,
    localized: bool = False,
    cf_done: bool = False,
) -> list[InvestigationAction]:
    """State-aware candidate set (adaptive, not fixed order)."""
    s = (state or "").lower()
    if s in {"signal_detected", "triage"}:
        return [InvestigationAction.ABANDON]  # triage decides elsewhere
    if s in {"hypothesis_formed", "baseline_check"}:
        return [InvestigationAction.BASELINE, InvestigationAction.PROBE, InvestigationAction.ABANDON]
    if s == "probing":
        return [
            InvestigationAction.PROBE,
            InvestigationAction.REMOVE,
            InvestigationAction.MUTATE,
            InvestigationAction.SPLIT,
            InvestigationAction.LOCALIZE,
            InvestigationAction.ABANDON,
        ]
    if s == "localizing":
        return [
            InvestigationAction.LOCALIZE,
            InvestigationAction.SPLIT,
            InvestigationAction.REMOVE,
            InvestigationAction.FALSIFY,
            InvestigationAction.ABANDON,
        ]
    if s == "variant_testing":
        return [
            InvestigationAction.SEMANTIC,
            InvestigationAction.STRUCTURAL,
            InvestigationAction.ENCODING,
            InvestigationAction.CONTEXT,
            InvestigationAction.ORDER,
            InvestigationAction.VARIANT,
            InvestigationAction.ABANDON,
        ]
    if s == "boundary_search":
        return [InvestigationAction.BOUNDARY, InvestigationAction.MUTATE, InvestigationAction.ABANDON]
    if s == "counterfactual_test":
        return [InvestigationAction.FALSIFY, InvestigationAction.REMOVE, InvestigationAction.SEMANTIC, InvestigationAction.ABANDON]
    if s == "stochasticity_check":
        return [InvestigationAction.REPEAT, InvestigationAction.ABANDON]
    if s == "security_assessment":
        return [InvestigationAction.SECURITY, InvestigationAction.VERIFY, InvestigationAction.ABANDON]
    if s == "verification":
        return [InvestigationAction.VERIFY, InvestigationAction.REPEAT, InvestigationAction.ABANDON]
    # Default broad set
    out = [
        InvestigationAction.PROBE,
        InvestigationAction.LOCALIZE,
        InvestigationAction.FALSIFY,
        InvestigationAction.BOUNDARY,
        InvestigationAction.VARIANT,
        InvestigationAction.REPEAT,
        InvestigationAction.SECURITY,
        InvestigationAction.ABANDON,
    ]
    if has_trigger and not localized:
        out.insert(0, InvestigationAction.LOCALIZE)
    if localized and not cf_done:
        out.insert(0, InvestigationAction.FALSIFY)
    return out


def score_action(
    action: InvestigationAction,
    *,
    eig: float = 0.4,
    security: float = 0.3,
    localization_need: float = 0.3,
    discrimination_need: float = 0.3,
    cost: float = 1.0,
    redundancy: float = 0.0,
    history: Sequence[str] | None = None,
) -> ActionScore:
    """score = EIG + security + localization + discrimination − cost − redundancy."""
    hist = list(history or [])
    red = float(redundancy)
    if hist:
        # Penalize repeating the same action many times
        same = sum(1 for h in hist[-8:] if h == action.value)
        red = max(red, min(1.0, same * 0.25))

    # Action-type priors
    priors = {
        InvestigationAction.LOCALIZE: (0.55, 0.35, 0.8, 0.4, 1.5),
        InvestigationAction.FALSIFY: (0.5, 0.4, 0.2, 0.85, 1.2),
        InvestigationAction.BOUNDARY: (0.45, 0.35, 0.3, 0.5, 1.3),
        InvestigationAction.ENCODING: (0.4, 0.25, 0.45, 0.4, 1.0),
        InvestigationAction.SEMANTIC: (0.35, 0.25, 0.35, 0.45, 1.0),
        InvestigationAction.STRUCTURAL: (0.35, 0.2, 0.3, 0.4, 1.0),
        InvestigationAction.CONTEXT: (0.3, 0.25, 0.25, 0.35, 1.0),
        InvestigationAction.ORDER: (0.3, 0.2, 0.35, 0.4, 1.0),
        InvestigationAction.REMOVE: (0.45, 0.3, 0.6, 0.55, 1.0),
        InvestigationAction.MUTATE: (0.35, 0.25, 0.4, 0.35, 1.0),
        InvestigationAction.SPLIT: (0.5, 0.25, 0.7, 0.4, 1.2),
        InvestigationAction.REPEAT: (0.25, 0.2, 0.1, 0.3, 1.0),
        InvestigationAction.PROBE: (0.4, 0.3, 0.2, 0.3, 1.0),
        InvestigationAction.SECURITY: (0.2, 0.9, 0.1, 0.3, 0.8),
        InvestigationAction.VERIFY: (0.3, 0.7, 0.1, 0.5, 1.5),
        InvestigationAction.BASELINE: (0.2, 0.1, 0.05, 0.1, 1.0),
        InvestigationAction.VARIANT: (0.35, 0.25, 0.35, 0.45, 1.0),
        InvestigationAction.ABANDON: (0.0, 0.0, 0.0, 0.0, 0.0),
    }
    pe, ps, pl, pd, pc = priors.get(action, (0.3, 0.3, 0.3, 0.3, 1.0))
    e = 0.5 * float(eig) + 0.5 * pe
    sec = 0.5 * float(security) + 0.5 * ps
    loc = float(localization_need) * pl
    disc = float(discrimination_need) * pd
    c = float(cost) * pc * 0.15
    total = e + sec + loc + disc - c - 0.35 * red

    if action == InvestigationAction.ABANDON:
        # Abandon useful when EIG low / budget tight — scored externally; keep low base
        total = 0.15 - 0.1 * float(eig) - 0.1 * float(security)

    reasoning = (
        f"action={action.value} eig={e:.2f} sec={sec:.2f} loc={loc:.2f} "
        f"disc={disc:.2f} cost={c:.2f} red={red:.2f} → {total:.2f}"
    )
    return ActionScore(
        action=action,
        score=float(total),
        eig=float(e),
        security=float(sec),
        localization=float(loc),
        discrimination=float(disc),
        cost=float(c),
        redundancy=float(red),
        reasoning=reasoning,
        meta={"prior": {"eig": pe, "sec": ps, "loc": pl, "disc": pd, "cost": pc}},
    )


def select_action(
    candidates: Sequence[InvestigationAction] | None = None,
    *,
    state: str = "probing",
    eig: float = 0.4,
    security: float = 0.3,
    localization_need: float = 0.3,
    discrimination_need: float = 0.3,
    history: Sequence[str] | None = None,
    force_abandon_if_budget_zero: bool = False,
) -> ActionScore:
    if force_abandon_if_budget_zero:
        return score_action(InvestigationAction.ABANDON, eig=0.0, security=0.0, history=history)
    cands = list(candidates) if candidates is not None else default_candidates(state=state)
    if not cands:
        cands = [InvestigationAction.ABANDON]
    scored = [
        score_action(
            a,
            eig=eig,
            security=security,
            localization_need=localization_need,
            discrimination_need=discrimination_need,
            history=history,
        )
        for a in cands
    ]
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[0]


__all__ = [
    "InvestigationAction",
    "ActionScore",
    "default_candidates",
    "score_action",
    "select_action",
]
