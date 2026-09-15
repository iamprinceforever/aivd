"""Allocate residual budget across underexplored component families.

Policies: static | equal | greedy | joint_aware (default adaptive).
Asymmetric: do not blindly equalize when U(A) ≠ U(B).
"""
from __future__ import annotations

from typing import Any

from aivd.joint.dependency import JointResidualHypothesis
from aivd.joint.readiness import ComponentState, readiness_score


ALLOC_POLICIES = frozenset({
    "static", "equal", "greedy", "joint_aware", "adaptive", "random",
})


def _need(state: str, u: float) -> float:
    """How much characterization budget a component still needs."""
    s = str(state or ComponentState.UNEXAMINED.value)
    if s == ComponentState.DISQUALIFIED.value:
        return 0.0
    if s == ComponentState.INTERACTION_READY.value:
        return 0.15
    if s == ComponentState.CHARACTERIZED.value:
        return 0.35
    if s == ComponentState.PARTIALLY_CHARACTERIZED.value:
        return 0.7 + 0.3 * float(u)
    return 0.95 + 0.2 * float(u)


def allocate_budget(
    hypotheses: list[JointResidualHypothesis],
    *,
    total_budget: int,
    policy: str = "joint_aware",
    reserve_fraction: float = 0.25,
    ablation: str | None = None,
) -> dict[str, Any]:
    """Allocate probes across families + reserved combination slots.

    Returns allocation dict with per-family budgets, reserve, and audit trail.
    """
    policy = (ablation or policy or "joint_aware").lower().strip()
    if policy == "adaptive":
        policy = "joint_aware"
    total = max(0, int(total_budget))
    reserve_n = int(round(total * float(reserve_fraction))) if total else 0
    if policy == "static":
        reserve_n = 0
    elif policy == "equal":
        reserve_n = max(1, total // 4) if total >= 4 else 0
    elif policy == "greedy":
        reserve_n = max(0, min(2, total // 8))
    elif policy == "random":
        import random
        reserve_n = random.Random(total + len(hypotheses)).randint(0, max(0, total // 3))

    char_budget = max(0, total - reserve_n)
    families: dict[str, dict[str, Any]] = {}
    for h in hypotheses or []:
        for fam, state, u in (
            (h.family_a, h.readiness_a, h.u_a),
            (h.family_b, h.readiness_b, h.u_b),
        ):
            if not fam:
                continue
            entry = families.get(fam) or {
                "family_id": fam,
                "state": state,
                "u": u,
                "need": _need(state, u),
                "linkage_max": 0.0,
                "joint_evi_max": 0.0,
            }
            entry["need"] = max(float(entry["need"]), _need(state, u))
            entry["u"] = max(float(entry["u"]), float(u))
            entry["linkage_max"] = max(float(entry["linkage_max"]), float(h.linkage))
            entry["joint_evi_max"] = max(float(entry["joint_evi_max"]), float(h.joint_evi))
            # Prefer more advanced readiness label
            if readiness_score(state) > readiness_score(entry["state"]):
                entry["state"] = state
            families[fam] = entry

    fam_list = list(families.values())
    alloc: dict[str, int] = {f["family_id"]: 0 for f in fam_list}

    if not fam_list or char_budget <= 0:
        return {
            "policy": policy,
            "total_budget": total,
            "characterization_budget": char_budget,
            "reserve": reserve_n,
            "per_family": alloc,
            "family_details": families,
            "asymmetric": False,
            "audit": [{"kind": "empty_or_zero"}],
        }

    audit: list[dict[str, Any]] = []

    if policy == "equal":
        # Blind equal split — control (NOT recommended scientifically)
        per = char_budget // max(1, len(fam_list))
        rem = char_budget - per * len(fam_list)
        for i, f in enumerate(fam_list):
            alloc[f["family_id"]] = per + (1 if i < rem else 0)
        audit.append({"kind": "equal_split", "per": per})
        asymmetric = False
    elif policy == "static":
        # Fixed priority by family_id sort
        ordered = sorted(fam_list, key=lambda x: x["family_id"])
        i = 0
        left = char_budget
        while left > 0 and ordered:
            alloc[ordered[i % len(ordered)]["family_id"]] += 1
            left -= 1
            i += 1
        audit.append({"kind": "static_round_robin"})
        asymmetric = False
    elif policy == "greedy":
        # Always feed the currently neediest single family
        ordered = sorted(fam_list, key=lambda x: x["need"], reverse=True)
        left = char_budget
        for f in ordered:
            take = min(left, max(1, int(round(f["need"] * char_budget))))
            alloc[f["family_id"]] = take
            left -= take
            if left <= 0:
                break
        if left > 0 and ordered:
            alloc[ordered[0]["family_id"]] += left
        audit.append({"kind": "greedy_need", "head": ordered[0]["family_id"] if ordered else None})
        asymmetric = True
    elif policy == "random":
        import random
        rng = random.Random(17 + total)
        left = char_budget
        while left > 0 and fam_list:
            f = rng.choice(fam_list)
            alloc[f["family_id"]] += 1
            left -= 1
        audit.append({"kind": "random_alloc"})
        asymmetric = True
    else:
        # joint_aware / adaptive: weight by need × linkage × joint_evi; asymmetric
        weights = []
        for f in fam_list:
            w = (
                0.45 * float(f["need"])
                + 0.25 * float(f["linkage_max"])
                + 0.30 * min(1.0, float(f["joint_evi_max"]))
            )
            # Boost underexplored
            if f["state"] in (
                ComponentState.UNEXAMINED.value,
                ComponentState.PARTIALLY_CHARACTERIZED.value,
                ComponentState.REOPENED.value,
            ):
                w *= 1.25
            weights.append(max(0.05, w))
        s = sum(weights)
        raw = [char_budget * (w / s) for w in weights]
        # Floor then distribute remainder by fractional part
        floors = [int(x) for x in raw]
        for i, f in enumerate(fam_list):
            alloc[f["family_id"]] = floors[i]
        rem = char_budget - sum(floors)
        order_frac = sorted(
            range(len(fam_list)),
            key=lambda i: raw[i] - floors[i],
            reverse=True,
        )
        for i in order_frac:
            if rem <= 0:
                break
            alloc[fam_list[i]["family_id"]] += 1
            rem -= 1
        audit.append({
            "kind": "joint_aware",
            "weights": {fam_list[i]["family_id"]: round(weights[i], 4) for i in range(len(fam_list))},
            "raw": {fam_list[i]["family_id"]: round(raw[i], 4) for i in range(len(fam_list))},
        })
        asymmetric = len(set(alloc.values())) > 1 or (
            len(fam_list) >= 2 and abs(fam_list[0]["need"] - fam_list[1]["need"]) > 0.05
        )

    return {
        "policy": policy,
        "total_budget": total,
        "characterization_budget": char_budget,
        "reserve": reserve_n,
        "per_family": alloc,
        "family_details": families,
        "asymmetric": asymmetric,
        "audit": audit,
        "sum_allocated": sum(alloc.values()) + reserve_n,
    }


__all__ = ["allocate_budget", "ALLOC_POLICIES"]
