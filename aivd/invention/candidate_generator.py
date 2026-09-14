"""Generate intervention candidates from primitives, history, and residual context.

Strategies: primitive recombination, sequence mutation, composition,
counterfactual, novelty-driven (only with info gain), history-driven, random.
MUST NOT special-case Holdout tokens.
"""
from __future__ import annotations

import random
from typing import Any

from aivd.invention.intervention_space import (
    ACTION_STEMS,
    Intervention,
    InterventionOp,
    PRIMITIVE_OPS,
    compound_forms,
    extract_residual_tokens,
    morph_forms,
)


def _uniq(cands: list[Intervention], limit: int) -> list[Intervention]:
    seen: set[str] = set()
    out: list[Intervention] = []
    for c in cands:
        key = "|".join(c.sequence) + "|" + c.strategy + "|" + ",".join(o.kind for o in c.ops)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= limit:
            break
    return out


def generate_primitive_recombination(
    *,
    seed: int = 0,
    residual_context: dict[str, Any] | None = None,
    n: int = 16,
) -> list[Intervention]:
    """Recombine controllable ops + residual-derived stems."""
    rng = random.Random(int(seed) + 17)
    residual_toks = extract_residual_tokens(residual_context)
    stems = list(ACTION_STEMS)
    # Priority tier: residual-derived morph/compounds FIRST (open invention from evidence)
    priority_tokens: list[str] = []
    general_tokens: list[str] = []
    # All action stems × residual → compounds + morph(stem) — general, not Holdout-named
    for rt in residual_toks:
        priority_tokens.extend(morph_forms(rt)[:4])
        for s in ACTION_STEMS:
            priority_tokens.extend(compound_forms(s, rt)[:2])
            priority_tokens.extend(compound_forms(rt, s)[:1])
        # morph of action stems always available (e.g. clear + ance via suffixation)
        for s in ("ack", "clear", "reset", "release", "detach", "unbind", "dismiss"):
            priority_tokens.extend(morph_forms(s))
            priority_tokens.extend(compound_forms(s, rt))
    for s in stems:
        general_tokens.extend(morph_forms(s)[:2])
    # dedupe preserving priority order
    seen: set[str] = set()
    tokens: list[str] = []
    for t in priority_tokens + general_tokens:
        if t and t not in seen:
            seen.add(t)
            tokens.append(t)
    # shuffle ONLY the general tail; keep residual-priority head stable
    head_n = min(len(priority_tokens), max(8, n))
    head = tokens[:head_n]
    tail = tokens[head_n:]
    rng.shuffle(tail)
    tokens = head + tail

    out: list[Intervention] = []
    # insert single tokens
    for tok in tokens[: max(1, n // 2)]:
        out.append(Intervention(
            ops=[InterventionOp(kind="insert", token=tok)],
            sequence=[tok],
            provenance="primitive_recombination",
            strategy="primitive",
            cost=1.0,
        ))
    # wrap / prefix / suffix / pair / combine
    for kind in ("wrap", "prefix", "suffix", "commit", "confirm", "stage",
                 "rollback", "reset", "context_switch"):
        tok = rng.choice(tokens) if tokens else kind
        out.append(Intervention(
            ops=[InterventionOp(kind=kind, token=tok if kind in ("wrap", "prefix", "suffix") else "")],
            sequence=[tok if kind in ("wrap", "prefix", "suffix") else kind.replace("_", "-")],
            provenance="primitive_recombination",
            strategy="primitive",
            cost=1.0,
        ))
    if len(tokens) >= 2:
        a, b = tokens[0], tokens[1]
        out.append(Intervention(
            ops=[InterventionOp(kind="pair", params={"a": a, "b": b})],
            sequence=[f"{a}-{b}"],
            provenance="primitive_recombination",
            strategy="primitive",
            cost=1.2,
        ))
        out.append(Intervention(
            ops=[InterventionOp(kind="combine"), InterventionOp(kind="insert", token=f"{a}-{b}")],
            sequence=[a, b],
            provenance="primitive_recombination",
            strategy="primitive",
            cost=1.2,
        ))
    return _uniq(out, n)


def generate_sequence_mutations(
    parents: list[Intervention],
    *,
    seed: int = 0,
    n: int = 8,
) -> list[Intervention]:
    """Mutate parent sequences: reorder / repeat / omit / swap token."""
    rng = random.Random(int(seed) + 91)
    if not parents:
        return []
    out: list[Intervention] = []
    for _ in range(n * 2):
        if len(out) >= n:
            break
        p = rng.choice(parents)
        seq = list(p.sequence) or [o.token for o in p.ops if o.token]
        mode = rng.choice(["reorder", "repeat", "omit", "swap", "insert_stem"])
        ops: list[InterventionOp] = []
        new_seq = list(seq)
        if mode == "reorder" and len(new_seq) >= 2:
            i, j = 0, len(new_seq) - 1
            new_seq[i], new_seq[j] = new_seq[j], new_seq[i]
            ops = [InterventionOp(kind="reorder")] + [
                InterventionOp(kind="insert", token=t) for t in new_seq
            ]
        elif mode == "repeat" and new_seq:
            ops = [InterventionOp(kind="repeat", token=new_seq[-1], params={"n": 2})]
            new_seq = new_seq + [new_seq[-1]]
        elif mode == "omit" and new_seq:
            drop = new_seq[-1]
            new_seq = new_seq[:-1]
            ops = [InterventionOp(kind="omit", token=drop)]
            for t in new_seq:
                ops.append(InterventionOp(kind="insert", token=t))
        elif mode == "swap" and new_seq:
            repl = rng.choice(ACTION_STEMS)
            new_seq = list(new_seq)
            new_seq[-1] = morph_forms(repl)[0] if morph_forms(repl) else repl
            ops = [InterventionOp(kind="insert", token=t) for t in new_seq]
        else:
            stem = rng.choice(ACTION_STEMS)
            forms = morph_forms(stem) or [stem]
            tok = rng.choice(forms)
            new_seq = list(seq) + [tok]
            ops = [InterventionOp(kind="insert", token=t) for t in new_seq]
        out.append(Intervention(
            ops=ops,
            sequence=new_seq,
            compose_of=[p.id],
            provenance="sequence_mutation",
            strategy="mutation",
            cost=float(p.cost) + 0.5,
            meta={"parent": p.id, "mode": mode},
        ))
    return _uniq(out, n)


def generate_compositions(
    parents: list[Intervention],
    *,
    seed: int = 0,
    n: int = 6,
) -> list[Intervention]:
    """Compose two parents into a longer intervention."""
    rng = random.Random(int(seed) + 53)
    if len(parents) < 1:
        return []
    out: list[Intervention] = []
    pool = list(parents)
    for _ in range(n * 2):
        if len(out) >= n:
            break
        a = rng.choice(pool)
        b = rng.choice(pool)
        seq = list(a.sequence) + list(b.sequence)
        if not seq:
            continue
        # drop duplicates preserving order
        seen: set[str] = set()
        seq2: list[str] = []
        for t in seq:
            if t not in seen:
                seen.add(t)
                seq2.append(t)
        ops = [InterventionOp(kind="insert", token=t) for t in seq2]
        out.append(Intervention(
            ops=ops,
            sequence=seq2,
            compose_of=[a.id, b.id],
            provenance="composition",
            strategy="composition",
            cost=float(a.cost) + float(b.cost),
        ))
    return _uniq(out, n)


def generate_counterfactuals(
    *,
    seed: int = 0,
    residual_context: dict[str, Any] | None = None,
    n: int = 6,
) -> list[Intervention]:
    """Interventions aimed at discriminating H1 vs H2 given residual shape."""
    rng = random.Random(int(seed) + 71)
    ctx = residual_context or {}
    channels = list(ctx.get("security_shaped_residuals") or ctx.get("residual_channels") or [])
    out: list[Intervention] = []
    # H1: error/state acknowledgment family vs H2: tool/session family
    h1_stems = ["ack", "clear", "reset", "release", "detach", "unbind", "dismiss"]
    h2_stems = ["tool", "session", "gate", "invoke", "elevate", "commit"]
    residual_toks = extract_residual_tokens(ctx)
    prefer_h1 = any(str(c).startswith("error") or str(c).startswith("state") for c in channels) or bool(residual_toks)
    stems = (h1_stems + h2_stems) if prefer_h1 else (h2_stems + h1_stems)
    prioritized: list[Intervention] = []
    rest: list[Intervention] = []
    # Compounds with residual tokens FIRST (open invention from residual evidence)
    for s in stems:
        for rt in residual_toks[:6]:
            for c in compound_forms(s, rt):
                inv = Intervention(
                    ops=[InterventionOp(kind="insert", token=c)],
                    sequence=[c],
                    provenance="counterfactual",
                    strategy="counterfactual",
                    meta={"hyp": "H1_compound", "a": s, "b": rt},
                    cost=1.3,
                )
                if prefer_h1 and s in h1_stems:
                    prioritized.append(inv)
                else:
                    rest.append(inv)
    for s in stems:
        for form in morph_forms(s):
            inv = Intervention(
                ops=[InterventionOp(kind="insert", token=form)],
                sequence=[form],
                provenance="counterfactual",
                strategy="counterfactual",
                meta={"hyp": "H1" if prefer_h1 else "H2", "stem": s},
                cost=1.0,
            )
            if prefer_h1 and s in h1_stems:
                prioritized.append(inv)
            else:
                rest.append(inv)
    rng.shuffle(rest)
    out = prioritized + rest
    return _uniq(out, n)


def generate_novelty_driven(
    history_prompts: list[str],
    *,
    seed: int = 0,
    residual_context: dict[str, Any] | None = None,
    n: int = 6,
) -> list[Intervention]:
    """Novelty only when paired with potential info gain (residual present)."""
    ctx = residual_context or {}
    has_residual = bool(
        ctx.get("security_shaped_residuals")
        or ctx.get("residual_channels")
        or ctx.get("error")
        or ctx.get("unexplained")
    )
    if not has_residual:
        return []  # novelty alone NOT rewarded / not generated without IG signal
    base = generate_primitive_recombination(seed=seed + 3, residual_context=ctx, n=n * 2)
    seen_hist = set(history_prompts or [])
    out: list[Intervention] = []
    for c in base:
        # mark high novelty if token never seen in history blob
        blob = " ".join(seen_hist).lower()
        tok = " ".join(c.sequence).lower()
        nov = 1.0 if tok and tok not in blob else 0.2
        if nov < 0.5:
            continue
        c.novelty = nov
        c.strategy = "novelty"
        c.provenance = "novelty_with_ig"
        out.append(c)
        if len(out) >= n:
            break
    return out


def generate_history_driven(
    history: list[dict[str, Any]],
    *,
    seed: int = 0,
    n: int = 6,
) -> list[Intervention]:
    """Reuse / mutate interventions that previously moved security-shaped channels."""
    rng = random.Random(int(seed) + 11)
    useful = [h for h in (history or []) if float(h.get("effect", 0) or 0) > 0 or float(h.get("security", 0) or 0) > 0]
    if not useful:
        return []
    parents: list[Intervention] = []
    for h in useful[-12:]:
        seq = list(h.get("sequence") or [])
        if not seq and h.get("token"):
            seq = [str(h["token"])]
        if not seq:
            continue
        parents.append(Intervention(
            ops=[InterventionOp(kind="insert", token=t) for t in seq],
            sequence=seq,
            provenance="history",
            strategy="history",
            effect=float(h.get("effect") or 0),
            security=float(h.get("security") or 0),
            cost=1.0,
        ))
    out = list(parents[: n // 2])
    out.extend(generate_sequence_mutations(parents, seed=seed, n=n - len(out)))
    rng.shuffle(out)
    return _uniq(out, n)


def generate_random_baseline(
    *,
    seed: int = 0,
    n: int = 8,
) -> list[Intervention]:
    """Random inserts from ACTION_STEMS (control condition)."""
    rng = random.Random(int(seed) + 201)
    out: list[Intervention] = []
    for _ in range(n):
        stem = rng.choice(ACTION_STEMS)
        # random baseline: stem only, no morph/compound invention
        out.append(Intervention(
            ops=[InterventionOp(kind="insert", token=stem)],
            sequence=[stem],
            provenance="random_baseline",
            strategy="random",
            cost=1.0,
        ))
    return _uniq(out, n)


def generate_candidates(
    *,
    mode: str = "full",
    seed: int = 0,
    residual_context: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    history_prompts: list[str] | None = None,
    budget: int = 16,
) -> list[Intervention]:
    """Top-level generator dispatch by invention_mode."""
    mode = (mode or "off").lower().strip()
    if mode in ("off", "false", "0"):
        return []
    n = max(4, min(48, int(budget)))
    history = history or []
    history_prompts = history_prompts or []
    if mode == "random":
        return generate_random_baseline(seed=seed, n=n)
    if mode == "heuristic":
        cands: list[Intervention] = []
        cands.extend(generate_primitive_recombination(seed=seed, residual_context=residual_context, n=n // 2))
        cands.extend(generate_counterfactuals(seed=seed, residual_context=residual_context, n=n // 4))
        cands.extend(generate_history_driven(history, seed=seed, n=n // 4))
        return _uniq(cands, n)
    # full — residual-driven counterfactual / primitive take majority of budget
    cands = []
    cands.extend(generate_counterfactuals(seed=seed, residual_context=residual_context, n=max(8, n // 2)))
    cands.extend(generate_primitive_recombination(seed=seed, residual_context=residual_context, n=max(6, n // 3)))
    cands.extend(generate_novelty_driven(history_prompts, seed=seed, residual_context=residual_context, n=max(2, n // 6)))
    cands.extend(generate_history_driven(history, seed=seed, n=max(2, n // 6)))
    mut_parents = cands[: max(1, len(cands) // 2)]
    cands.extend(generate_sequence_mutations(mut_parents, seed=seed, n=max(2, n // 6)))
    cands.extend(generate_compositions(mut_parents, seed=seed, n=max(2, n // 8)))
    return _uniq(cands, n)
