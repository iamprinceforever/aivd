"""Composition via 3.12/3.13 joint machinery (3.15).

Uses joint-EVI, readiness, CF, reserve, asymmetric, hierarchical —
no brute-force Cartesian composition.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.autonomy.state import AutonomousDiscoveryState
from aivd.invention.intervention_space import Intervention


ObserveFn = Callable[[str], Any]


def assess_composition_readiness(
    state: AutonomousDiscoveryState,
    *,
    relation_supported: bool = False,
) -> dict[str, Any]:
    """Readiness from characterized regions + optional cross-signal support."""
    regions = list(state.regions.values())
    characterized = [r for r in regions if r.characterized]
    score = 0.0
    if len(characterized) >= 2:
        score += 0.4
    if len(characterized) >= 1:
        score += 0.15
    if relation_supported:
        score += 0.35
    if state.cross_signal.get("n_hypotheses", 0) >= 1:
        score += 0.1
    score = min(1.0, score)
    for r in characterized:
        state.readiness[r.region_id] = max(float(state.readiness.get(r.region_id, 0.0)), score)
    return {
        "score": score,
        "n_characterized": len(characterized),
        "relation_supported": relation_supported,
        "ready": score >= 0.55 and (relation_supported or len(characterized) >= 2),
    }


def compose_via_joint(
    seed_prompt: str,
    individuals: list[Intervention],
    state: AutonomousDiscoveryState,
    *,
    observe_fn: ObserveFn,
    charge: Callable[[], bool] | None = None,
    residual_context: dict[str, Any] | None = None,
    budget: int = 8,
    seed: int = 0,
    ablation: str | None = None,
) -> dict[str, Any]:
    """Delegate combination testing to JointResidualController (3.13)."""
    from aivd.joint.controller import JointResidualController

    if len(individuals) < 2:
        state.mark_broken("COMPOSE")
        return {"enabled": False, "reason": "insufficient_individuals"}
    if budget <= 0:
        return {"enabled": False, "reason": "budget_exhausted"}

    ready = assess_composition_readiness(
        state,
        relation_supported=bool(state.cross_signal.get("n_supported") or state.cross_signal.get("relation_supported")),
    )
    if not ready.get("ready") and ablation != "force_compose":
        return {"enabled": True, "ready": False, "readiness": ready, "n_combinations_tested": 0}

    jrc = JointResidualController(
        mode="joint",
        seed=seed,
        max_hypotheses=min(6, max(2, len(individuals) // 2)),
        max_combinations=min(4, budget),
        alloc_policy="joint_aware",
        reserve_fraction=0.25,
        ablation=ablation,
        total_budget=budget,
    )
    effects = {
        inv.id: float(inv.effect or inv.security or 0.0)
        for inv in individuals if inv.id
    }
    result = jrc.run(
        seed_prompt,
        individuals=individuals,
        observe_fn=observe_fn,
        residual_context=residual_context or {"unexplained": state.unexplained},
        charge=charge,
        individual_effects=effects,
        budget=budget,
    )
    state.meta["composed"] = True
    state.log(
        "COMPOSE",
        n_combinations=result.get("n_combinations_tested"),
        secret=result.get("secret_found"),
        readiness=ready,
    )
    return {**result, "readiness": ready}


def compose_via_cross_signal(
    seed_prompt: str,
    individuals: list[Intervention],
    state: AutonomousDiscoveryState,
    *,
    observe_fn: ObserveFn,
    charge: Callable[[], bool] | None = None,
    residual_context: dict[str, Any] | None = None,
    budget: int = 8,
    seed: int = 0,
    ablation: str | None = None,
) -> dict[str, Any]:
    """Delegate to CrossSignalController (3.14) for residual↔action composition."""
    from aivd.cross_signal.controller import CrossSignalController

    if len(individuals) < 2 or budget <= 0:
        return {"enabled": False, "reason": "insufficient"}

    csc = CrossSignalController(
        mode="cross_signal",
        seed=seed,
        max_hypotheses=6,
        max_combinations=min(4, budget),
        reserve_fraction=0.25,
        ablation=ablation,
        total_budget=budget,
    )
    effects = {
        inv.id: float(inv.effect or inv.security or 0.0)
        for inv in individuals if inv.id
    }
    result = csc.run(
        seed_prompt,
        individuals=individuals,
        observe_fn=observe_fn,
        residual_context=residual_context or {"unexplained": state.unexplained},
        charge=charge,
        individual_effects=effects,
        budget=budget,
    )
    state.cross_signal = {
        "n_hypotheses": result.get("n_hypotheses"),
        "n_supported": result.get("n_supported"),
        "secret_found": result.get("secret_found"),
        "relation_supported": bool(result.get("n_supported")),
        "complexity": result.get("complexity"),
    }
    state.meta["composed"] = True
    state.log(
        "COMPOSE_CROSS",
        n_hypotheses=result.get("n_hypotheses"),
        secret=result.get("secret_found"),
        brute=(result.get("complexity") or {}).get("brute_force"),
    )
    return result


__all__ = [
    "assess_composition_readiness",
    "compose_via_joint",
    "compose_via_cross_signal",
]
