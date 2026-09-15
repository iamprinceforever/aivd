"""Connect an earlier probe to a later effect (indirect / delayed causation)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aivd.causal.causal_graph import CausalGraph
from aivd.causal.temporal import TemporalMemory


@dataclass
class IndirectLink:
    cause_t: int
    effect_t: int
    confidence: float
    note: str = ""


def hypothesize_indirect(
    memory: TemporalMemory,
    *,
    later_effect: float,
    later_prompt: str,
    threshold: float = 0.18,
) -> list[IndirectLink]:
    """If a later obs has an effect not explained by the current prompt, credit earlier probes."""
    if later_effect < threshold:
        return []
    # Crude: current prompt looks unrelated (short / generic) but effect is high
    generic = later_prompt.lower()
    looks_unrelated = any(k in generic for k in ("follow-up", "continuation", "status check", "unrelated"))
    looks_unrelated = looks_unrelated or len(later_prompt.split()) <= 6
    if not looks_unrelated:
        return []
    links = []
    for e in memory.events:
        if e.t >= len(memory.events):
            continue
        if e.effect >= 0.08 or e.state_label in ("seed", "unexplained", ""):
            links.append(IndirectLink(cause_t=e.t, effect_t=len(memory.events), confidence=0.45, note="earlier_probe_candidate"))
    return links[-4:]


def probe_indirect(
    *,
    probe_fn: Callable[[str], tuple[str, float, str | None]],
    effect_fn: Callable[[str, str], float],
    budget_charge: Callable[[], bool],
    memory: TemporalMemory,
    graph: CausalGraph | None = None,
    follow_prompt: str = "authorized unrelated continuation probe",
) -> dict[str, Any]:
    """Intervention: later generic probe. If effect appears, link to earlier events (not mere correlation)."""
    if not budget_charge():
        return {"tested": False, "indirect": False, "probes_used": 0}
    resp, _, err = probe_fn(follow_prompt)
    if err == "budget_exhausted":
        return {"tested": False, "indirect": False, "probes_used": 0}
    eff = float(effect_fn(follow_prompt, resp or ""))
    memory.record(follow_prompt, resp or "", eff, state_label="indirect_followup")
    links = hypothesize_indirect(memory, later_effect=eff, later_prompt=follow_prompt)
    g = graph or CausalGraph()
    if links and eff >= 0.18:
        g.add_node("earlier_probe", "input", "earlier_probe")
        g.add_node("later_obs", "obs", "later_obs")
        g.intervene("earlier_probe", "later_obs", effect_changed=True)
        kind = "causes"
    else:
        g.add_node("earlier_probe", "input", "earlier_probe")
        g.add_node("later_obs", "obs", "later_obs")
        g.observe_correlation("earlier_probe", "later_obs", note="no_later_effect")
        kind = "correlated"
    return {
        "tested": True,
        "indirect": bool(links) and eff >= 0.18,
        "effect": eff,
        "links": [{"cause_t": ln.cause_t, "effect_t": ln.effect_t, "confidence": ln.confidence} for ln in links],
        "edge_kind": kind,
        "probes_used": 1,
    }
