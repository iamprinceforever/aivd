"""Budget-capped search for A+B and A+B+C interactions.

Does not assume the answer is an interaction; just proposes pairwise/triple
combinations of *observed fragments* with generic public modifiers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from aivd.causal.unknown_dimension import GENERIC_MODIFIERS


@dataclass
class InteractionCandidate:
    factors: tuple[str, ...]
    prompt: str
    arity: int


def observed_fragments(prompt: str, *, max_n: int = 6) -> list[str]:
    parts = [p for p in (prompt or "").replace("<", " ").replace(">", " ").split() if 3 <= len(p) <= 40]
    # Keep distinctive fragments, drop ultra-generic stopwords
    stop = {"authorized", "research", "please", "probe", "the", "and", "for", "with"}
    out = []
    for p in parts:
        if p.lower() in stop:
            continue
        if p not in out:
            out.append(p)
        if len(out) >= max_n:
            break
    return out


def generate_interactions(
    seed_prompt: str,
    *,
    history_prompts: Sequence[str] | None = None,
    max_pairs: int = 6,
    max_triples: int = 3,
) -> list[InteractionCandidate]:
    base = (seed_prompt or "").strip()
    frags = observed_fragments(base)
    for hp in history_prompts or []:
        for f in observed_fragments(hp, max_n=3):
            if f not in frags:
                frags.append(f)
    mods = list(GENERIC_MODIFIERS)
    out: list[InteractionCandidate] = []
    # Prefer the most common two- and three-way public modifiers first (budget-capped later)
    if frags or base:
        out.append(InteractionCandidate(("obs", "gate"), f"{base} gate".strip(), 2))
        out.append(InteractionCandidate(("obs", "gate", "channel"), f"{base} gate channel".strip(), 3))
        out.append(InteractionCandidate(("obs", "channel"), f"{base} channel".strip(), 2))
    # A+B: each observed fragment + generic modifier (and fragment pairs)
    for f in frags[:4]:
        for m in mods:
            if len(out) >= max_pairs:
                break
            if m.lower() in base.lower() and f in base:
                continue
            out.append(InteractionCandidate((f, m), f"{base} {m}".strip() if f in base else f"{base} {f} {m}", 2))
        if len(out) >= max_pairs:
            break
    # Fragment-fragment pairs from history
    if len(frags) >= 2:
        a, b = frags[0], frags[1]
        out.append(InteractionCandidate((a, b), f"{base} {b}" if b not in base else f"{a} {b}", 2))
    # A+B+C triples (hard cap)
    triples = 0
    if frags:
        f0 = frags[0]
        for i, m1 in enumerate(mods[:4]):
            for m2 in mods[i + 1 : 5]:
                if triples >= max_triples:
                    break
                out.append(InteractionCandidate((f0, m1, m2), f"{base} {m1} {m2}", 3))
                triples += 1
            if triples >= max_triples:
                break
    # Dedup
    seen = set()
    uniq: list[InteractionCandidate] = []
    for c in out:
        if c.prompt in seen:
            continue
        seen.add(c.prompt)
        uniq.append(c)
    return uniq


def search_interactions(
    seed_prompt: str,
    *,
    probe_fn: Callable[[str], tuple[str, float, str | None]],
    effect_fn: Callable[[str, str], float],
    budget_charge: Callable[[], bool],
    baseline_effect: float,
    max_probes: int = 6,
    history_prompts: Sequence[str] | None = None,
    threshold: float = 0.18,
) -> dict:
    cands = generate_interactions(seed_prompt, history_prompts=history_prompts)
    used = 0
    hits: list[dict] = []
    best = None
    for c in cands:
        if used >= max_probes:
            break
        if not budget_charge():
            break
        resp, _, err = probe_fn(c.prompt)
        used += 1
        if err == "budget_exhausted":
            break
        eff = float(effect_fn(c.prompt, resp or ""))
        rec = {"factors": list(c.factors), "arity": c.arity, "effect": eff, "delta": eff - baseline_effect}
        if eff >= baseline_effect + threshold:
            hits.append(rec)
            if best is None or rec["delta"] > best["delta"]:
                best = rec
    return {
        "probes_used": used,
        "hits": hits,
        "best": best,
        "discovered": bool(hits),
        "arity": (best or {}).get("arity"),
    }
