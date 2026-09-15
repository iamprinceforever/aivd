"""Generative experiments from harvested primitives + grammar (3.17).

Sandbox ops only (insert/wrap/reorder/repeat via Intervention).
Provenance: OBSERVATION → FEATURE → HYP → OPERATOR → EXPERIMENT.
Open ≠ random: every candidate has why + source primitives.
"""
from __future__ import annotations

from typing import Any

from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.openworld.grammar import GrammarExpr, expressions_from_representation
from aivd.openworld.representation import OpenWorldRepresentation


def _inv(seq: list[str], *, kind: str, why: str, provenance: str = "openworld") -> Intervention:
    ops = [InterventionOp(kind="insert", token=t) for t in seq]
    inv = Intervention(
        ops=ops,
        sequence=list(seq),
        provenance=provenance,
        strategy="openworld",
        cost=1.0 + 0.1 * max(0, len(seq) - 1),
    )
    inv.meta = {
        "why": why,
        "grammar_kind": kind,
        "openworld": True,
        "abstract_op": kind.lower(),
        "info_acquisition": kind in ("ATOM", "INFO"),
        "source_primitives": list(seq),
    }
    return inv


def _uniq(cands: list[Intervention], limit: int) -> list[Intervention]:
    seen: set[str] = set()
    out: list[Intervention] = []
    for c in cands:
        key = "|".join(c.sequence) + "|" + str((c.meta or {}).get("grammar_kind"))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= limit:
            break
    return out


def generate_from_representation(
    rep: OpenWorldRepresentation,
    *,
    ablation: str | None = None,
    max_new: int = 24,
    extra_state_repeats: list[str] | None = None,
    extra_transitions: list[tuple[str, str]] | None = None,
) -> list[Intervention]:
    """Compose generative experiments. Does NOT dump ACTION_STEMS."""
    abl = (ablation or "").lower()
    exprs = expressions_from_representation(rep, ablation=ablation)
    out: list[Intervention] = []
    for expr in exprs:
        for seq in expr.render_sequences():
            if not seq:
                continue
            out.append(_inv(seq, kind=expr.kind, why=expr.why))
            if len(out) >= max_new * 2:
                break
        if len(out) >= max_new * 2:
            break
    # First-class STATE follow-up: re-apply a primitive that already changed state
    if extra_state_repeats and "no_state" not in abl and "no_grammar" not in abl:
        for tok in extra_state_repeats:
            out.append(_inv(
                [tok], kind="STATE",
                why=f"state hypothesis: re-apply '{tok}' after observed state change",
            ))
    # First-class TRANSITION follow-up: B after A had an effect
    if extra_transitions and "no_transition" not in abl and "no_grammar" not in abl:
        for a, b in extra_transitions:
            out.append(_inv(
                [b], kind="TRANSITION",
                why=f"transition: after '{a}' effect, apply '{b}'",
            ))
    if abl == "invent_spam":
        # Explicit anti-pattern (ablation only): mix closed stems — must not be default
        from aivd.invention.intervention_space import ACTION_STEMS
        for s in ACTION_STEMS[:8]:
            out.append(_inv([s], kind="SPAM", why="ablation invent_spam"))
    return _uniq(out, max_new)


def info_acquisition_from_rep(
    rep: OpenWorldRepresentation,
    residual_context: dict[str, Any] | None = None,
    *,
    max_new: int = 4,
) -> list[Intervention]:
    """When REPRESENTATION_INSUFFICIENT, acquire info — not mutate the lexicon."""
    from aivd.openworld.primitives import harvest_tokens
    toks = [t for t, _ in harvest_tokens(residual_context=residual_context)]
    have = set(rep.tokens())
    out: list[Intervention] = []
    for t in toks:
        if t in have:
            continue
        out.append(_inv([t], kind="INFO", why=f"I seek info: probe unseen residual token '{t}'"))
        if len(out) >= max_new:
            break
    if not out and rep.tokens():
        t = rep.tokens()[0]
        out.append(_inv([t], kind="INFO", why="I seek info: re-observe primary primitive"))
    return out[:max_new]


__all__ = ["generate_from_representation", "info_acquisition_from_rep"]
