"""Budget-aware adaptive escalation. Not a holdout schedule.

3.33 invented atoms after 3.32 exhausted, then skipped if leftover < 3.
That skip is post-hoc. 3.34 plans backward from verification and
compares expected value of continuing the current layer against
escalating, using only in-episode evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CONTINUE = "CONTINUE_CURRENT_LANGUAGE"
ESC_IR = "ESCALATE_TO_PROGRAM_SYNTHESIS"
ESC_PRIM = "ESCALATE_TO_PRIMITIVE_SYNTHESIS"
ESC_EXT = "ESCALATE_TO_SUBSTRATE_SYNTHESIS"
ESC_ATOM = "ESCALATE_TO_ATOM_INVENTION"
STOP = "STOP_AND_PRESERVE_VERIFICATION_BUDGET"

LAYERS = ("ir", "prim", "ext", "atom")


@dataclass
class LayerValue:
    name: str
    tried: int = 0
    rejected: int = 0
    succeeded: int = 0
    streak: int = 0
    metric_sum: float = 0.0
    cost_sum: int = 0

    @property
    def fail_rate(self) -> float:
        if self.tried <= 0:
            return 0.0
        return self.rejected / max(1, self.tried)

    @property
    def p_continue(self) -> float:
        if self.succeeded:
            return 0.65
        if self.tried == 0:
            return 0.35
        return max(0.03, 0.35 * (0.5 ** self.rejected))

    @property
    def eig(self) -> float:
        if self.succeeded:
            return 0.05
        if self.tried == 0:
            return 0.28
        return 0.12 * self.p_continue + 0.04 * (1.0 / (1 + self.streak))

    def observe(self, *, informative: bool, secret: bool, metric: float = 0.0) -> None:
        self.tried += 1
        self.cost_sum += 1
        self.metric_sum += float(metric)
        if secret:
            self.succeeded += 1
            self.streak = 0
        elif not informative:
            self.rejected += 1
            self.streak += 1
        else:
            self.streak = 0


@dataclass
class QuestionValue:
    uncertainty: float = 0.7
    anomaly: float = 0.0
    relevance: float = 0.4
    eig: float = 0.2
    feasible: float = 1.0

    def score(self) -> float:
        return (
            self.uncertainty
            * max(0.05, self.anomaly)
            * self.relevance
            * self.eig
            * self.feasible
        )


@dataclass
class BudgetPlan:
    remaining: int
    verify_cost: int
    repro_cost: int
    invent_cost: int
    floor: int
    available: int

    def as_dict(self) -> dict[str, int]:
        return {
            "remaining": self.remaining,
            "verify_cost": self.verify_cost,
            "repro_cost": self.repro_cost,
            "invent_cost": self.invent_cost,
            "floor": self.floor,
            "available": self.available,
        }


class EscalationPlanner:
    """In-episode planner. Estimates, does not read evaluator GT."""

    def __init__(
        self,
        *,
        reserve: bool = True,
        plan: bool = True,
        ev: bool = True,
        qval: bool = True,
        lval: bool = True,
        portfolio: bool = True,
        always_late: bool = False,
        always_early: bool = False,
        dynamic: bool = False,
    ) -> None:
        self.reserve = bool(reserve)
        self.plan = bool(plan)
        self.ev = bool(ev)
        self.qval = bool(qval)
        self.lval = bool(lval)
        self.portfolio = bool(portfolio)
        self.always_late = bool(always_late)
        self.always_early = bool(always_early)
        self.dynamic = bool(dynamic)
        self.layers: dict[str, LayerValue] = {n: LayerValue(name=n) for n in LAYERS}
        self.question = QuestionValue()
        self.events: list[dict[str, str]] = []
        self.held = 0
        self.escalations = 0
        self.stops = 0
        self.false_esc = 0
        self.decisions: list[str] = []

    def observe_layer(self, layer: str, *, informative: bool, secret: bool, metric: float = 0.0) -> None:
        if layer not in self.layers:
            return
        self.layers[layer].observe(informative=informative, secret=secret, metric=metric)
        if self.qval:
            if secret:
                self.question.uncertainty = 0.05
                self.question.anomaly = 1.0
            elif not informative:
                self.question.uncertainty = min(0.95, self.question.uncertainty + 0.06)
                self.question.anomaly = max(0.05, self.question.anomaly * 0.85)
            else:
                self.question.anomaly = min(1.0, self.question.anomaly + 0.08)
                self.question.eig = min(0.5, self.question.eig + 0.02)

    def estimate(self, remaining: int) -> BudgetPlan:
        remaining = max(0, int(remaining))
        # In-episode: each lease is 1. Repro+verify observed as 2 charges
        # on standalone science; pipeline sometimes spends 3. Use 2 unless
        # this episode's uninformative streak made leftover historically tight.
        repro = 1
        verify = 1
        if self.plan:
            # Backward: discovery 1 + repro 1 + verify 1.
            invent = 1
        else:
            invent = 1
            repro = 1
            verify = 1
        if not self.reserve:
            floor = 0
        else:
            floor = invent + repro + verify
            if self.dynamic:
                from aivd.science.lifecycle import dynamic_floor
                floor = dynamic_floor(
                    base=floor,
                    atom_rejected=self.layers["atom"].rejected,
                    dynamic=True,
                )
        # Dynamic bump: if two synthesis layers already failed, another
        # invention try is likely; keep the same floor (one complete chain).
        available = max(0, remaining - floor) if self.reserve else remaining
        self.held = floor if self.reserve else 0
        if self.qval:
            self.question.feasible = 1.0 if remaining >= floor else 0.0
        return BudgetPlan(
            remaining=remaining,
            verify_cost=verify,
            repro_cost=repro,
            invent_cost=invent,
            floor=floor,
            available=available,
        )

    def decide(self, *, remaining: int, current: str) -> str:
        """Decide whether to continue `current` or escalate.

        `current` is the layer about to materialize another candidate.
        """
        plan = self.estimate(remaining)
        if self.always_early:
            self.escalations += 1
            self.decisions.append(ESC_ATOM)
            self.events.append({"event": "escalate", "to": ESC_ATOM, "why": "always_early"})
            return ESC_ATOM
        if self.always_late:
            self.decisions.append(CONTINUE)
            return CONTINUE
        floor = plan.floor
        layer = self.layers.get(current, LayerValue(name=current))
        nxt = {"ir": "prim", "prim": "ext", "ext": "atom", "atom": "atom"}.get(current, "atom")

        if remaining < floor and current != "atom":
            self.stops += 1
            self.decisions.append(STOP)
            self.events.append({
                "event": "stop",
                "why": "INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION",
                "remaining": str(remaining),
                "floor": str(floor),
            })
            return STOP

        # Untried layer gets one shot if another try would still leave a chain.
        if layer.tried == 0 and remaining > floor:
            self.decisions.append(CONTINUE)
            return CONTINUE

        extra = 1
        starve = remaining - extra < floor
        exhausted = layer.rejected >= 2
        tight = layer.rejected >= 1 and remaining < floor + 2
        ev_esc = False
        if self.ev and layer.tried >= 1:
            nxt_layer = self.layers.get(nxt, LayerValue(name=nxt))
            # Prefer escalate when current eig is dominated and leftover is not ample.
            if nxt_layer.eig > layer.eig * 1.4 and remaining <= floor + 3:
                ev_esc = True

        if current == "atom":
            if remaining < 3:
                self.stops += 1
                self.decisions.append(STOP)
                self.events.append({
                    "event": "stop",
                    "why": "ATOM_INVENTION_SKIPPED_BY_PLANNING",
                    "remaining": str(remaining),
                })
                return STOP
            self.decisions.append(CONTINUE)
            return CONTINUE

        if starve or exhausted or tight or ev_esc:
            act = {
                "ir": ESC_PRIM,
                "prim": ESC_EXT,
                "ext": ESC_ATOM,
            }.get(current, ESC_ATOM)
            # If escalating to ext would itself starve atom, skip to atom.
            if act == ESC_EXT and remaining <= floor:
                act = ESC_ATOM
            if act == ESC_PRIM and remaining <= floor + 1:
                act = ESC_ATOM if remaining >= floor else ESC_EXT
            self.escalations += 1
            self.decisions.append(act)
            self.events.append({
                "event": "escalate",
                "from": current,
                "to": act,
                "why": "starve" if starve else ("exhausted" if exhausted else ("tight" if tight else "ev")),
                "remaining": str(remaining),
                "floor": str(floor),
                "rejected": str(layer.rejected),
            })
            return act
        self.decisions.append(CONTINUE)
        return CONTINUE

    def telemetry(self) -> dict[str, Any]:
        return {
            "held": self.held,
            "escalations": self.escalations,
            "stops": self.stops,
            "decisions": list(self.decisions[-12:]),
            "layers": {
                n: {
                    "tried": L.tried,
                    "rejected": L.rejected,
                    "succeeded": L.succeeded,
                    "eig": round(L.eig, 3),
                    "p_continue": round(L.p_continue, 3),
                }
                for n, L in self.layers.items()
            },
            "question_value": round(self.question.score(), 4) if self.qval else None,
            "events": list(self.events[-16:]),
        }


__all__ = [
    "CONTINUE",
    "ESC_IR",
    "ESC_PRIM",
    "ESC_EXT",
    "ESC_ATOM",
    "STOP",
    "LayerValue",
    "QuestionValue",
    "BudgetPlan",
    "EscalationPlanner",
]
