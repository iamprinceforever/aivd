"""Generate limited interaction hypotheses — NOT Cartesian brute force.

Strategies: residual-linked, cross-family, counterfactual, sequential,
state-aware, context-aware, random baseline, novel cross-family.
"""
from __future__ import annotations

import itertools
import random
from typing import Any

from aivd.invention.intervention_space import Intervention, extract_residual_tokens
from aivd.interaction.representation import InteractionCandidate, GENERATION_STRATEGIES


def _family_of(inv: Intervention) -> str:
    return (inv.meta or {}).get("family_id") or "unknown"


def _stem_bucket(inv: Intervention) -> str:
    feats = (inv.meta or {}).get("family_features") or {}
    if feats.get("stem_bucket"):
        return str(feats["stem_bucket"])
    seq = inv.sequence or []
    if not seq:
        return "empty"
    tok = str(seq[0]).lower().replace("_", "-")
    return tok.split("-")[0] if "-" in tok else tok[:8]


def _residual_linked(inv: Intervention, residual_toks: list[str]) -> bool:
    blob = " ".join(str(x).lower() for x in inv.sequence)
    return any(rt and rt in blob for rt in residual_toks)


def _pair_key(a: Intervention, b: Intervention, order: str) -> str:
    if order == "unordered":
        ids = tuple(sorted([a.id, b.id]))
    else:
        ids = (a.id, b.id)
    return f"{order}|{ids[0]}|{ids[1]}"


def generate_pairs(
    individuals: list[Intervention],
    *,
    seed: int = 0,
    residual_context: dict[str, Any] | None = None,
    max_pairs: int = 24,
    strategies: list[str] | None = None,
    ablation: str | None = None,
    mode: str = "interaction",
) -> tuple[list[InteractionCandidate], dict[str, Any]]:
    """Hierarchical, budget-aware pair generation with pruning stats."""
    rng = random.Random(int(seed) + 312)
    ctx = residual_context or {}
    rtoks = extract_residual_tokens(ctx)
    strat_list = list(strategies or GENERATION_STRATEGIES)
    if ablation == "no_cross_family":
        strat_list = [s for s in strat_list if s not in ("cross_family", "novel_cross_family")]
    if ablation == "no_residual":
        strat_list = [s for s in strat_list if s != "residual_linked"]
    if ablation == "novelty_only" or ablation == "random_only" or mode in ("random", "interaction_random"):
        strat_list = ["random"]
    if mode == "static":
        strat_list = ["cross_family", "residual_linked"]

    n = len(individuals)
    possible_pairs = n * (n - 1) // 2 if n >= 2 else 0
    possible_ordered = n * (n - 1) if n >= 2 else 0

    by_family: dict[str, list[Intervention]] = {}
    for inv in individuals:
        by_family.setdefault(_family_of(inv), []).append(inv)

    seen: set[str] = set()
    out: list[InteractionCandidate] = []
    pruned = 0
    strategy_counts: dict[str, int] = {}

    def _add(a: Intervention, b: Intervention, *, strategy: str, order: str = "unordered",
             composition: str = "concat", timing: str = "immediate",
             context: dict | None = None, state: dict | None = None) -> bool:
        nonlocal pruned
        if a.id == b.id:
            pruned += 1
            return False
        key = _pair_key(a, b, order)
        if key in seen:
            pruned += 1
            return False
        # Same exact sequence → redundant
        if list(a.sequence) == list(b.sequence):
            pruned += 1
            return False
        seen.add(key)
        fa, fb = _family_of(a), _family_of(b)
        cand = InteractionCandidate(
            components=[a, b],
            families=[fa, fb],
            order=order,
            composition=composition,
            timing=timing,
            context=dict(context or {}),
            state=dict(state or {}),
            strategy=strategy,
            predicted_individual=[float(a.effect or a.security or 0.0),
                                  float(b.effect or b.security or 0.0)],
            provenance=f"pair_generator:{strategy}",
        )
        out.append(cand)
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        return True

    # Cap per strategy so we don't explode
    per = max(2, max_pairs // max(1, len(strat_list)))

    # A residual-linked: both touch residual evidence
    if "residual_linked" in strat_list and rtoks:
        linked = [i for i in individuals if _residual_linked(i, rtoks)]
        rng.shuffle(linked)
        added = 0
        for a, b in itertools.combinations(linked[:12], 2):
            if added >= per:
                break
            if _family_of(a) != _family_of(b) or True:
                if _add(a, b, strategy="residual_linked"):
                    added += 1

    # B cross-family
    if "cross_family" in strat_list:
        fams = list(by_family.keys())
        rng.shuffle(fams)
        added = 0
        for i, fa in enumerate(fams):
            for fb in fams[i + 1 :]:
                if added >= per:
                    break
                pool_a = by_family[fa][:3]
                pool_b = by_family[fb][:3]
                for a in pool_a:
                    for b in pool_b:
                        if added >= per:
                            break
                        if _add(a, b, strategy="cross_family"):
                            added += 1
            if added >= per:
                break

    # C counterfactual: omit-style + positive / residual
    if "counterfactual" in strat_list:
        cfs = [i for i in individuals if i.strategy == "counterfactual" or "omit" in (i.sequence or [])]
        others = [i for i in individuals if i not in cfs]
        rng.shuffle(cfs)
        rng.shuffle(others)
        added = 0
        for a in cfs[:6]:
            for b in others[:4]:
                if added >= per:
                    break
                if _add(a, b, strategy="counterfactual", order="ordered"):
                    added += 1

    # D sequential / ordered
    if "sequential" in strat_list:
        ranked = sorted(
            individuals,
            key=lambda x: float(x.effect or x.security or 0.0),
            reverse=True,
        )
        added = 0
        for a, b in itertools.permutations(ranked[:8], 2):
            if added >= per:
                break
            if _family_of(a) != _family_of(b):
                if _add(a, b, strategy="sequential", order="sequential", timing="sequential"):
                    added += 1

    # E state-aware
    if "state_aware" in strat_list:
        soft = [i for i in individuals if float(i.effect or i.security or 0.0) >= 0.15]
        hard = [i for i in individuals if float(i.effect or i.security or 0.0) < 0.15]
        rng.shuffle(soft)
        rng.shuffle(hard)
        added = 0
        for a in soft[:6]:
            for b in (hard[:4] or soft[6:10]):
                if added >= per:
                    break
                if _add(
                    a, b, strategy="state_aware", order="ordered",
                    state={"gate": "after_soft_positive"}, timing="after_residual",
                ):
                    added += 1

    # F context-aware
    if "context_aware" in strat_list:
        ctx_tag = str(ctx.get("error") or ctx.get("chosen_axis") or "")
        added = 0
        pool = list(individuals)
        rng.shuffle(pool)
        for a, b in itertools.combinations(pool[:10], 2):
            if added >= per:
                break
            if _add(
                a, b, strategy="context_aware",
                context={"residual_error": ctx_tag, "axis": ctx.get("chosen_axis")},
                composition="contextual",
            ):
                added += 1

    # H novel cross-family (underexplored families)
    if "novel_cross_family" in strat_list:
        fam_sizes = {f: len(v) for f, v in by_family.items()}
        rare = sorted(fam_sizes, key=lambda f: fam_sizes[f])[:6]
        added = 0
        for i, fa in enumerate(rare):
            for fb in rare[i + 1 :]:
                if added >= per:
                    break
                for a in by_family[fa][:2]:
                    for b in by_family[fb][:2]:
                        if added >= per:
                            break
                        if _add(a, b, strategy="novel_cross_family"):
                            added += 1

    # G random baseline
    if "random" in strat_list or mode in ("random", "interaction_random"):
        added = 0
        pool = list(individuals)
        attempts = 0
        target = per if "random" in strat_list else max_pairs
        while added < target and attempts < max_pairs * 8 and len(pool) >= 2:
            attempts += 1
            a, b = rng.sample(pool, 2)
            if _add(a, b, strategy="random"):
                added += 1

    # Truncate to budget
    if len(out) > max_pairs:
        if mode == "static":
            out = out[:max_pairs]
        else:
            rng.shuffle(out)
            # Prefer non-random when truncating under interaction modes
            non_rand = [c for c in out if c.strategy != "random"]
            rand = [c for c in out if c.strategy == "random"]
            out = (non_rand + rand)[:max_pairs]

    complexity = {
        "n_individuals": n,
        "possible_unordered_pairs": possible_pairs,
        "possible_ordered_pairs": possible_ordered,
        "generated_pairs": len(out),
        "pruned": pruned,
        "strategy_counts": strategy_counts,
        "strategies_used": strat_list,
        "max_pairs_budget": max_pairs,
        "brute_force": False,
        "pruning_ratio": round(1.0 - (len(out) / max(1, possible_pairs)), 4) if possible_pairs else 1.0,
    }
    return out, complexity


def generate_triples(
    individuals: list[Intervention],
    *,
    seed: int = 0,
    residual_context: dict[str, Any] | None = None,
    max_triples: int = 4,
    parent_pairs: list[InteractionCandidate] | None = None,
) -> tuple[list[InteractionCandidate], dict[str, Any]]:
    """Hierarchical multi-way: only extend promising pairs — not Cartesian."""
    rng = random.Random(int(seed) + 713)
    n = len(individuals)
    possible = n * (n - 1) * (n - 2) // 6 if n >= 3 else 0
    out: list[InteractionCandidate] = []
    if max_triples <= 0 or n < 3:
        return out, {
            "possible_triples": possible,
            "generated_triples": 0,
            "tested_note": "hierarchical_extension_only",
        }

    # Prefer extending screened synergistic / residual-linked pairs
    bases = list(parent_pairs or [])
    if not bases:
        # Fall back to top residual-linked individuals
        rtoks = extract_residual_tokens(residual_context)
        linked = [i for i in individuals if _residual_linked(i, rtoks)] if rtoks else list(individuals)
        bases_inds = linked[:6] if linked else individuals[:6]
        for a, b in itertools.combinations(bases_inds[:5], 2):
            bases.append(InteractionCandidate(components=[a, b], strategy="residual_linked"))

    pool = list(individuals)
    rng.shuffle(pool)
    seen: set[str] = set()
    for base in bases[:8]:
        if len(out) >= max_triples:
            break
        ids = set(base.component_ids or [c.id for c in base.components])
        for c in pool:
            if len(out) >= max_triples:
                break
            if c.id in ids:
                continue
            # Prefer different family
            fams = set(base.families or [])
            if _family_of(c) in fams and rng.random() < 0.7:
                continue
            key = "|".join(sorted(list(ids) + [c.id]))
            if key in seen:
                continue
            seen.add(key)
            comps = list(base.components) + [c]
            out.append(InteractionCandidate(
                components=comps,
                order="ordered",
                strategy="multi_way_extend",
                provenance="triple_hierarchical",
                meta={"extended_from": base.id},
            ))

    return out, {
        "possible_triples": possible,
        "generated_triples": len(out),
        "hierarchical": True,
        "brute_force": False,
    }
