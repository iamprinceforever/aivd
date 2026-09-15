"""Temporal / stateful chains: state_t, action_t, obs_t.

Same input + different history can yield different observations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TemporalEvent:
    t: int
    prompt: str
    response: str
    effect: float
    state_label: str = ""


@dataclass
class TemporalMemory:
    events: list[TemporalEvent] = field(default_factory=list)

    def record(self, prompt: str, response: str, effect: float, state_label: str = "") -> TemporalEvent:
        ev = TemporalEvent(t=len(self.events), prompt=prompt, response=response, effect=effect, state_label=state_label)
        self.events.append(ev)
        return ev

    def same_input_different_history(self, prompt: str) -> list[TemporalEvent]:
        return [e for e in self.events if e.prompt.strip() == (prompt or "").strip()]

    def as_list(self) -> list[dict[str, Any]]:
        return [
            {"t": e.t, "prompt_len": len(e.prompt), "effect": e.effect, "state": e.state_label}
            for e in self.events[-20:]
        ]


def probe_history_dependence(
    prompt: str,
    *,
    probe_fn: Callable[[str], tuple[str, float, str | None]],
    effect_fn: Callable[[str, str], float],
    budget_charge: Callable[[], bool],
    memory: TemporalMemory,
) -> dict[str, Any]:
    """Replay the same prompt; if effect differs from first observation, stateful."""
    prior = memory.same_input_different_history(prompt)
    if not budget_charge():
        return {"tested": False, "stateful": False, "probes_used": 0}
    resp, _, err = probe_fn(prompt)
    if err == "budget_exhausted":
        return {"tested": False, "stateful": False, "probes_used": 0}
    eff = float(effect_fn(prompt, resp or ""))
    memory.record(prompt, resp or "", eff, state_label="replay")
    stateful = False
    delta = 0.0
    if prior:
        delta = abs(eff - prior[0].effect)
        stateful = delta >= 0.12
    return {
        "tested": True,
        "stateful": stateful,
        "delta": delta,
        "effect": eff,
        "prior_n": len(prior),
        "probes_used": 1,
    }


def delayed_followup(
    *,
    probe_fn: Callable[[str], tuple[str, float, str | None]],
    effect_fn: Callable[[str, str], float],
    budget_charge: Callable[[], bool],
    n_steps: int = 2,
    follow_prompt: str = "authorized follow-up status check",
    memory: TemporalMemory | None = None,
) -> dict[str, Any]:
    """Probe n generic follow-ups; catch effects that appear at t+k."""
    mem = memory or TemporalMemory()
    used = 0
    effects: list[float] = []
    for i in range(max(1, n_steps)):
        if not budget_charge():
            break
        p = follow_prompt if i == 0 else f"{follow_prompt} t{i}"
        resp, _, err = probe_fn(p)
        used += 1
        if err == "budget_exhausted":
            break
        eff = float(effect_fn(p, resp or ""))
        mem.record(p, resp or "", eff, state_label=f"delay_{i}")
        effects.append(eff)
    return {
        "probes_used": used,
        "effects": effects,
        "delayed_hit": any(e >= 0.35 for e in effects),
        "any_signal": any(e >= 0.12 for e in effects),
    }
