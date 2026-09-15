"""Early weak-signal routing into candidate generation (3.15).

Uncertainty-weighted; no single-signal domination. Integrates invention
candidate_generator without duplicating it.
"""
from __future__ import annotations

from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState
from aivd.autonomy.region_transfer import rank_regions_given_residual
from aivd.invention.candidate_generator import generate_candidates
from aivd.invention.intervention_space import Intervention


def _uncertainty_weights(state: AutonomousDiscoveryState) -> dict[str, float]:
    """Normalize uncertainties so no single signal dominates."""
    import math
    u = dict(state.uncertainties) or {rid: r.uncertainty for rid, r in state.regions.items()}
    if not u:
        return {}
    vals = list(u.values())
    mx = max(vals) if vals else 1.0
    exps = {k: math.exp((v / max(1e-6, mx) - 1.0) * 2.0) for k, v in u.items()}
    z = sum(exps.values()) or 1.0
    return {k: v / z for k, v in exps.items()}


def route_weak_signals(
    state: AutonomousDiscoveryState,
    *,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Route weak residual signals into region-targeted candidate slots."""
    ranked = rank_regions_given_residual(state, top_k=top_k)
    weights = _uncertainty_weights(state)
    routes: list[dict[str, Any]] = []
    for rid, p in ranked:
        w = weights.get(rid, 1.0 / max(1, len(ranked)))
        priority = 0.5 * p + 0.5 * w
        routes.append({
            "region_id": rid,
            "transfer_p": p,
            "uncertainty_w": w,
            "priority": priority,
            "why": (
                f"I am routing weak signal to region {rid} because "
                f"transfer_p={p:.3f} and uncertainty_w={w:.3f}"
            ),
        })
    routes.sort(key=lambda r: -r["priority"])
    if routes:
        top = routes[0]["priority"]
        for r in routes[1:]:
            if r["priority"] > 0.85 * top:
                r["priority"] *= 0.9
        routes.sort(key=lambda r: -r["priority"])
    state.log("ROUTE", n_routes=len(routes), head=[r["region_id"] for r in routes[:3]])
    return routes


def generate_routed_candidates(
    seed_prompt: str,
    state: AutonomousDiscoveryState,
    *,
    mode: str = "full",
    seed: int = 0,
    max_candidates: int = 24,
    residual_context: dict[str, Any] | None = None,
) -> list[Intervention]:
    """Generate candidates with early weak-signal routing bias."""
    routes = route_weak_signals(state, top_k=5)
    # Theoretical upper bound (accounting only) — never fully enumerated
    state.theoretical_candidates = max(state.theoretical_candidates, 64 * 16)
    ctx = dict(residual_context or {})
    ctx.setdefault("unexplained", state.unexplained)
    if state.residual_features.get("has_error") and "error" not in ctx:
        # Keep opaque; do not inject Holdout tokens
        ctx.setdefault("error_text", "")
    cands = generate_candidates(
        mode=_base_mode(mode),
        seed=seed,
        budget=max_candidates,
        residual_context=ctx,
        history_prompts=[seed_prompt] if seed_prompt else None,
        stem_coverage=True,
    )
    for i, inv in enumerate(cands):
        route = routes[i % len(routes)] if routes else None
        inv.meta = dict(inv.meta or {})
        if route:
            inv.meta["routed_region"] = route["region_id"]
            inv.meta["route_priority"] = route["priority"]
            inv.meta["route_why"] = route["why"]
    state.generated_candidates += len(cands)
    state.log("CANDIDATE_GEN", n=len(cands), theoretical=state.theoretical_candidates)
    return cands


def _base_mode(mode: str) -> str:
    m = (mode or "full").lower().strip()
    if m in ("off", "random", "heuristic", "full"):
        return m if m != "off" else "full"
    return "full"


__all__ = [
    "route_weak_signals",
    "generate_routed_candidates",
]
