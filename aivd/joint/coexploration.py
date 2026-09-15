"""Co-exploration — characterize multiple component families under a joint hypothesis."""
from __future__ import annotations

from typing import Any, Callable

from aivd.invention.intervention_space import Intervention
from aivd.joint.dependency import JointResidualHypothesis
from aivd.joint.residual_graph import ResidualGraph


ObserveFn = Callable[[str], Any]


ORDERINGS = ("A+B", "B+A", "A→B", "B→A")


def _apply_prompt(seed: str, inv: Intervention) -> str:
    seq = " ".join(inv.sequence or [])
    return f"{seed} {seq}".strip() if seq else seed


def _family_variants(
    individuals: list[Intervention],
    family_id: str,
) -> list[Intervention]:
    out = []
    for inv in individuals:
        fid = (inv.meta or {}).get("family_id") or "unknown"
        if fid == family_id:
            out.append(inv)
    return out


def coexplore_families(
    seed_prompt: str,
    hyp: JointResidualHypothesis,
    *,
    individuals: list[Intervention],
    observe_fn: ObserveFn,
    graph: ResidualGraph,
    alloc_a: int,
    alloc_b: int,
    charge: Callable[[], bool] | None = None,
    secret_fn: Callable[[Any], bool] | None = None,
) -> dict[str, Any]:
    """Spend characterization budget on A and B families (asymmetric OK)."""
    vars_a = _family_variants(individuals, hyp.family_a)
    vars_b = _family_variants(individuals, hyp.family_b)
    if hyp.component_a and hyp.component_a not in vars_a:
        vars_a = [hyp.component_a] + vars_a
    if hyp.component_b and hyp.component_b not in vars_b:
        vars_b = [hyp.component_b] + vars_b

    results_a: list[dict[str, Any]] = []
    results_b: list[dict[str, Any]] = []
    secret_found = False
    best_prompt = None
    best_obs = None
    probes = 0

    def _probe_family(variants: list[Intervention], fam: str, n: int, sink: list) -> None:
        nonlocal secret_found, best_prompt, best_obs, probes
        if n <= 0 or not variants:
            return
        for i in range(n):
            if charge is not None and not charge():
                break
            inv = variants[i % len(variants)]
            prompt = _apply_prompt(seed_prompt, inv)
            obs = observe_fn(prompt)
            probes += 1
            effect = 1.0 if (secret_fn and secret_fn(obs)) else float(inv.effect or inv.security or 0.0)
            if secret_fn and secret_fn(obs):
                secret_found = True
                best_prompt = prompt
                best_obs = obs
                effect = 1.0
            graph.observe(
                fam,
                variant="|".join(inv.sequence or []) or inv.id,
                effect=effect,
            )
            sink.append({
                "family": fam,
                "prompt": prompt,
                "effect": effect,
                "id": inv.id,
            })
            if secret_found:
                break

    # Asymmetric order: spend larger allocation first (characterize bottleneck)
    if alloc_a >= alloc_b:
        _probe_family(vars_a, hyp.family_a, alloc_a, results_a)
        if not secret_found:
            _probe_family(vars_b, hyp.family_b, alloc_b, results_b)
    else:
        _probe_family(vars_b, hyp.family_b, alloc_b, results_b)
        if not secret_found:
            _probe_family(vars_a, hyp.family_a, alloc_a, results_a)

    graph.refresh_readiness()
    stats = graph.family_stats()
    sa = stats.get(hyp.family_a) or {}
    sb = stats.get(hyp.family_b) or {}
    hyp.readiness_a = str(sa.get("state") or hyp.readiness_a)
    hyp.readiness_b = str(sb.get("state") or hyp.readiness_b)
    hyp.refresh_uncertainty(
        n_a=int(sa.get("n_probes") or 0),
        n_b=int(sb.get("n_probes") or 0),
        var_a=int(sa.get("n_variants") or 0),
        var_b=int(sb.get("n_variants") or 0),
        effect_a=float(sa.get("effect_mean") or 0.0),
        effect_b=float(sb.get("effect_mean") or 0.0),
    )

    return {
        "results_a": results_a,
        "results_b": results_b,
        "probes": probes,
        "secret_found": secret_found,
        "best_prompt": best_prompt,
        "best_obs": best_obs,
        "readiness_a": hyp.readiness_a,
        "readiness_b": hyp.readiness_b,
        "interaction_ready": hyp.interaction_ready,
    }


def compose_ordered_prompts(
    seed_prompt: str,
    hyp: JointResidualHypothesis,
    *,
    orders: tuple[str, ...] = ORDERINGS,
) -> list[dict[str, Any]]:
    """Build ordered combination prompts: A+B, B+A, A→B, B→A."""
    a = hyp.component_a
    b = hyp.component_b
    if a is None or b is None:
        return []
    seq_a = " ".join(a.sequence or [])
    seq_b = " ".join(b.sequence or [])
    out: list[dict[str, Any]] = []
    for order in orders:
        if order == "A+B":
            body = f"{seq_a} {seq_b}".strip()
        elif order == "B+A":
            body = f"{seq_b} {seq_a}".strip()
        elif order == "A→B":
            body = f"{seq_a} then {seq_b}".strip()
        elif order == "B→A":
            body = f"{seq_b} then {seq_a}".strip()
        else:
            body = f"{seq_a} {seq_b}".strip()
        out.append({
            "order": order,
            "prompt": f"{seed_prompt} {body}".strip(),
            "hyp_id": hyp.id,
        })
    return out


__all__ = [
    "coexplore_families",
    "compose_ordered_prompts",
    "ORDERINGS",
]
