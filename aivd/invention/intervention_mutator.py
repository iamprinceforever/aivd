"""Mutate kept interventions after observed deltas."""
from __future__ import annotations

import random
from typing import Any

from aivd.invention.candidate_generator import generate_sequence_mutations
from aivd.invention.intervention_space import (
    ACTION_STEMS,
    Intervention,
    InterventionOp,
    compound_forms,
    morph_forms,
)


def mutate_after_delta(
    parent: Intervention,
    *,
    delta_positive: bool,
    residual_tokens: list[str] | None = None,
    seed: int = 0,
    n: int = 4,
) -> list[Intervention]:
    """If delta positive: local morph/compound intensify; else: diversify."""
    rng = random.Random(int(seed) + hash(parent.id) % 10007)
    out: list[Intervention] = []
    seq = list(parent.sequence) or [o.token for o in parent.ops if o.token]
    residual_tokens = residual_tokens or []
    if delta_positive:
        # intensify around working tokens
        for tok in seq[:3]:
            for form in morph_forms(tok)[:2]:
                if form == tok:
                    continue
                out.append(Intervention(
                    ops=[InterventionOp(kind="insert", token=form)],
                    sequence=[form],
                    compose_of=[parent.id],
                    provenance="mutate_intensify",
                    strategy="mutation",
                    cost=float(parent.cost) + 0.3,
                ))
            for rt in residual_tokens[:3]:
                for c in compound_forms(tok, rt)[:2]:
                    out.append(Intervention(
                        ops=[InterventionOp(kind="insert", token=c)],
                        sequence=[c],
                        compose_of=[parent.id],
                        provenance="mutate_compound",
                        strategy="mutation",
                        cost=float(parent.cost) + 0.4,
                    ))
    else:
        out.extend(generate_sequence_mutations([parent], seed=seed, n=n))
        # diversify with distant stem
        stem = rng.choice(ACTION_STEMS)
        form = rng.choice(morph_forms(stem) or [stem])
        out.append(Intervention(
            ops=[InterventionOp(kind="insert", token=form)],
            sequence=[form],
            compose_of=[parent.id],
            provenance="mutate_diversify",
            strategy="mutation",
            cost=1.0,
        ))
    # dedupe
    seen: set[str] = set()
    uniq: list[Intervention] = []
    for c in out:
        k = "|".join(c.sequence)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
        if len(uniq) >= n:
            break
    return uniq
