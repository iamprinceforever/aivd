"""Boundary detection: boundary_score ≈ effect / perturbation_size."""
from __future__ import annotations

from typing import Callable, Sequence

from aivd.investigation.types import BoundaryRecord, new_inv_id

EffectFn = Callable[[str], float]


def boundary_score(effect: float, perturbation_size: float) -> float:
    """High gradient = large effect for small perturbation."""
    size = max(1e-6, float(perturbation_size))
    return float(abs(effect) / size)


def detect_length_boundary(
    template: str,
    effect_fn: EffectFn,
    *,
    lengths: Sequence[int] | None = None,
    region_id: str = "",
    pad_token: str = "x",
) -> BoundaryRecord | None:
    """Scan length cliff: find adjacent lengths where effect jumps."""
    lens = list(lengths or [4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 24, 32])
    scores: list[tuple[int, float, str]] = []
    for n in lens:
        # Replace {n} or append padding
        if "{n}" in template:
            prompt = template.replace("{n}", str(n))
        elif "{pad}" in template:
            prompt = template.replace("{pad}", pad_token * n)
        else:
            prompt = f"{template} " + (pad_token * n)
        scores.append((n, float(effect_fn(prompt)), prompt))

    best: BoundaryRecord | None = None
    best_s = -1.0
    for i in range(len(scores) - 1):
        n0, e0, p0 = scores[i]
        n1, e1, p1 = scores[i + 1]
        pert = abs(n1 - n0) / max(1.0, float(max(lens)))
        eff = e1 - e0
        bs = boundary_score(eff, pert)
        if bs > best_s and abs(eff) >= 0.15:
            best_s = bs
            best = BoundaryRecord(
                id=new_inv_id("bnd_"),
                region_id=region_id,
                dimension="length",
                below_prompt=p0 if e0 <= e1 else p1,
                above_prompt=p1 if e0 <= e1 else p0,
                below_effect=float(min(e0, e1)),
                above_effect=float(max(e0, e1)),
                perturbation_size=float(pert),
                boundary_score=float(bs),
                meta={"n_below": n0, "n_above": n1},
            )
    return best


def detect_token_boundary(
    below_prompt: str,
    above_prompt: str,
    effect_fn: EffectFn,
    *,
    region_id: str = "",
    dimension: str = "token",
    perturbation_size: float | None = None,
) -> BoundaryRecord:
    """Compare two adjacent prompts (e.g. missing vs present critical token)."""
    e0 = float(effect_fn(below_prompt))
    e1 = float(effect_fn(above_prompt))
    # Perturbation size ≈ normalized edit distance proxy
    if perturbation_size is None:
        t0, t1 = set(below_prompt.split()), set(above_prompt.split())
        union = t0 | t1
        pert = 1.0 - (len(t0 & t1) / max(1, len(union)))
        pert = max(0.05, pert)
    else:
        pert = float(perturbation_size)
    eff = e1 - e0
    return BoundaryRecord(
        id=new_inv_id("bnd_"),
        region_id=region_id,
        dimension=dimension,
        below_prompt=below_prompt,
        above_prompt=above_prompt,
        below_effect=e0,
        above_effect=e1,
        perturbation_size=pert,
        boundary_score=boundary_score(eff, pert),
        meta={},
    )


def prioritize_boundaries(records: Sequence[BoundaryRecord]) -> list[BoundaryRecord]:
    """High-gradient first."""
    return sorted(records, key=lambda r: r.boundary_score, reverse=True)
