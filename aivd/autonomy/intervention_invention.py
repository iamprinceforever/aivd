"""Evidence-guided intervention family invention from abstract operators (3.15).

Operators: modify / reorder / delay / context-switch / pair / compose / …
Reason logged (“I am testing this because…”). EIG-guided, not infinite random.
Integrates invention mutator/composer — does not duplicate.
"""
from __future__ import annotations

from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState
from aivd.invention.intervention_space import Intervention, InterventionOp, PRIMITIVE_OPS
from aivd.invention.intervention_mutator import mutate_after_delta
from aivd.invention.intervention_composer import compose_kept


ABSTRACT_OPERATORS: tuple[str, ...] = (
    "modify",
    "reorder",
    "delay",
    "repeat",
    "context_switch",
    "pair",
    "compose",
    "omit",
    "wrap",
    "prefix",
    "suffix",
    "stage_commit",
)


def invent_from_evidence(
    state: AutonomousDiscoveryState,
    base: list[Intervention],
    *,
    seed: int = 0,
    max_new: int = 8,
    eig_by_op: dict[str, float] | None = None,
) -> list[Intervention]:
    """Invent new interventions guided by EIG over abstract operators."""
    import random
    rng = random.Random(int(seed) + state.step)
    eig = dict(eig_by_op or state.eig_estimates or {})
    for op in ABSTRACT_OPERATORS:
        eig.setdefault(op, 0.35)
    ranked_ops = sorted(ABSTRACT_OPERATORS, key=lambda o: -(eig.get(o, 0.2) + rng.random() * 0.05))
    invented: list[Intervention] = []
    pool = list(base or [])
    if not pool:
        return invented

    for op in ranked_ops:
        if len(invented) >= max_new:
            break
        src = rng.choice(pool)
        why = (
            f"I am testing this because operator={op} has EIG={eig.get(op, 0):.3f} "
            f"and region_prior_focus={_top_prior(state)}"
        )
        new = _apply_abstract_op(src, op, rng=rng, why=why)
        if new is not None:
            invented.append(new)
            state.invention_history.append({
                "op": op,
                "why": why,
                "src_id": src.id,
                "new_id": new.id,
                "step": state.step,
            })
            state.eig_estimates[op] = float(eig.get(op, 0.35))

    # Integrate mutator on best parent
    try:
        parent = pool[0]
        mutated = mutate_after_delta(
            parent, delta_positive=True, seed=seed, n=max(1, min(3, max_new - len(invented))),
        )
        for m in mutated:
            m.meta = dict(m.meta or {})
            m.meta["why"] = m.meta.get("why") or (
                "I am testing this because mutator suggested delta follow-up"
            )
            invented.append(m)
            if len(invented) >= max_new:
                break
    except Exception:
        pass
    try:
        composed = compose_kept(pool[:4], seed=seed, n=max(1, min(3, max_new - len(invented))))
        for c in (composed or []):
            c.meta = dict(c.meta or {})
            c.meta["why"] = c.meta.get("why") or (
                "I am testing this because composition may reveal interaction"
            )
            invented.append(c)
            if len(invented) >= max_new:
                break
    except Exception:
        pass

    state.generated_candidates += len(invented)
    state.log("INVENT", n=len(invented), ops=ranked_ops[:4])
    return invented[:max_new]


def _top_prior(state: AutonomousDiscoveryState) -> str:
    if not state.region_priors:
        return "none"
    return max(state.region_priors.items(), key=lambda kv: kv[1])[0]


def _apply_abstract_op(
    src: Intervention,
    op: str,
    *,
    rng: Any,
    why: str,
) -> Intervention | None:
    seq = list(src.sequence or [])
    if not seq:
        return None
    new_seq = list(seq)
    if op == "modify" and seq:
        tok = str(seq[-1])
        new_seq = seq + [tok]
    elif op == "reorder" and len(seq) >= 2:
        new_seq = list(reversed(seq))
    elif op == "delay":
        new_seq = seq + ["delay"]
    elif op == "repeat" and seq:
        new_seq = seq + [seq[-1]]
    elif op == "context_switch":
        new_seq = ["context_switch"] + seq
    elif op == "pair" and len(seq) >= 1:
        new_seq = seq + ["pair"]
    elif op == "compose" and len(seq) >= 2:
        new_seq = seq[:2] + seq[2:]
    elif op == "omit" and len(seq) >= 2:
        new_seq = seq[:-1]
    elif op == "wrap":
        new_seq = ["wrap"] + seq + ["wrap"]
    elif op == "prefix":
        new_seq = ["prefix"] + seq
    elif op == "suffix":
        new_seq = seq + ["suffix"]
    elif op == "stage_commit":
        new_seq = seq + ["stage", "commit"]
    else:
        return None
    new_seq = [str(t) for t in new_seq if t]
    if not new_seq or new_seq == seq:
        new_seq = seq + [rng.choice(list(PRIMITIVE_OPS)[:6])]
    ops = [InterventionOp(kind="insert", token=t) for t in new_seq]
    inv = Intervention(ops=ops, sequence=new_seq, strategy=f"autonomy_{op}")
    inv.meta = {
        "family_id": (src.meta or {}).get("family_id") or "autonomy",
        "abstract_op": op,
        "why": why,
        "parent_id": src.id,
    }
    return inv


def update_operator_eig(
    state: AutonomousDiscoveryState,
    op: str,
    *,
    information_gain: float,
    effect: float,
) -> None:
    cur = float(state.eig_estimates.get(op, 0.35))
    target = float(information_gain)
    if abs(effect) < 0.01:
        target *= 0.5
    state.eig_estimates[op] = max(0.05, min(0.95, 0.7 * cur + 0.3 * target))


__all__ = [
    "ABSTRACT_OPERATORS",
    "invent_from_evidence",
    "update_operator_eig",
]
