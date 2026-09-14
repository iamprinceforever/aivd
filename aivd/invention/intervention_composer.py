"""Compose interventions from kept building blocks."""
from __future__ import annotations

from aivd.invention.candidate_generator import generate_compositions
from aivd.invention.intervention_space import Intervention, InterventionOp


def compose_kept(kept: list[Intervention], *, seed: int = 0, n: int = 4) -> list[Intervention]:
    if len(kept) < 1:
        return []
    comps = generate_compositions(kept, seed=seed, n=n)
    # also ordered stage→confirm style generic compose
    extra: list[Intervention] = []
    if kept:
        a = kept[0]
        seq = ["stage"] + list(a.sequence) + ["confirm"]
        extra.append(Intervention(
            ops=[InterventionOp(kind="insert", token=t) for t in seq],
            sequence=seq,
            compose_of=[a.id],
            provenance="compose_stage_confirm",
            strategy="composition",
            cost=float(a.cost) + 1.0,
        ))
    return (comps + extra)[:n]
