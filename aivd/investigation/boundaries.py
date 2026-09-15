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


def adaptive_boundary_search(
    seed_prompt: str,
    effect_fn: EffectFn,
    *,
    budget: int = 8,
    region_id: str = "",
    dimension: str = "adaptive",
) -> list[BoundaryRecord]:
    """Coarse → detect → binary refine → local confirm.

    Budget-capped. Returns zero or more BoundaryRecords (high-gradient first).
    """
    if budget < 2 or not seed_prompt:
        return []
    toks = seed_prompt.split()
    records: list[BoundaryRecord] = []
    used = 0

    # Coarse: compare full vs empty-ish control
    control = "Hello."
    if used + 2 > budget:
        return []
    e_full = float(effect_fn(seed_prompt))
    used += 1
    e_ctrl = float(effect_fn(control))
    used += 1
    if abs(e_full - e_ctrl) < 0.15:
        return []

    # Detect: try removing halves / critical tokens (coarse grid)
    candidates: list[tuple[str, str, float]] = []  # below, above, pert
    if len(toks) >= 2:
        mid = len(toks) // 2
        left, right = " ".join(toks[:mid]), " ".join(toks[mid:])
        for below, above, pert in (
            (left, seed_prompt, 0.5),
            (right, seed_prompt, 0.5),
            (control, seed_prompt, 1.0),
        ):
            if used >= budget:
                break
            e_b = float(effect_fn(below))
            used += 1
            # above already measured as e_full for seed
            e_a = e_full if above == seed_prompt else float(effect_fn(above))
            if above != seed_prompt:
                used += 1
            if abs(e_a - e_b) >= 0.15:
                candidates.append((below, above, pert))

    # Length-style: if prompt has lencliff prefix, binary search pad length
    if "lencliff:" in seed_prompt and used + 2 <= budget:
        lo, hi = 0, 16
        best_pair = None
        while hi - lo > 1 and used + 2 <= budget:
            mid = (lo + hi) // 2
            p_lo = f"lencliff:{'x' * lo}"
            p_mid = f"lencliff:{'x' * mid}"
            e_lo = float(effect_fn(p_lo))
            used += 1
            if used >= budget:
                break
            e_mid = float(effect_fn(p_mid))
            used += 1
            if abs(e_mid - e_lo) >= 0.15:
                best_pair = (p_lo, p_mid, e_lo, e_mid, abs(mid - lo) / 16.0)
                hi = mid
            else:
                lo = mid
        if best_pair:
            p0, p1, e0, e1, pert = best_pair
            # Local confirm
            if used < budget:
                e1c = float(effect_fn(p1))
                used += 1
                e1 = e1c
            rec = BoundaryRecord(
                id=new_inv_id("bnd_"),
                region_id=region_id,
                dimension="length",
                below_prompt=p0,
                above_prompt=p1,
                below_effect=float(e0),
                above_effect=float(e1),
                perturbation_size=float(max(0.05, pert)),
                boundary_score=boundary_score(e1 - e0, max(0.05, pert)),
                meta={"method": "adaptive_binary_length", "used": used},
            )
            records.append(rec)

    # Binary refine on token presence: drop one token at a time near gradient
    if not records and toks and used < budget:
        # Find a token whose removal drops effect most
        best_drop = None
        best_eff = 0.0
        for i, tok in enumerate(toks):
            if used >= budget:
                break
            trial = " ".join(toks[:i] + toks[i + 1 :]) or control
            e_t = float(effect_fn(trial))
            used += 1
            drop = e_full - e_t
            if drop > best_eff and drop >= 0.15:
                best_eff = drop
                best_drop = (trial, seed_prompt, e_t, e_full, tok)
        if best_drop:
            below, above, e0, e1, tok = best_drop
            pert = 1.0 / max(1, len(toks))
            # Local confirm above
            if used < budget:
                e1 = float(effect_fn(above))
                used += 1
            records.append(
                BoundaryRecord(
                    id=new_inv_id("bnd_"),
                    region_id=region_id,
                    dimension=dimension or "token",
                    below_prompt=below,
                    above_prompt=above,
                    below_effect=float(e0),
                    above_effect=float(e1),
                    perturbation_size=float(pert),
                    boundary_score=boundary_score(e1 - e0, pert),
                    meta={"method": "adaptive_token_drop", "token": tok, "used": used},
                )
            )

    # From coarse candidates
    for below, above, pert in candidates[:2]:
        if used >= budget + 2:
            break
        rec = detect_token_boundary(
            below, above, effect_fn, region_id=region_id, dimension=dimension, perturbation_size=pert
        )
        used += 2
        if abs(rec.above_effect - rec.below_effect) >= 0.15:
            records.append(rec)

    return prioritize_boundaries(records)
