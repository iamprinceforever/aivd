"""Stage-4 H2a–H2f interpretation from observational trails (prereg rules)."""
from __future__ import annotations

from collections import Counter
from typing import Any


def evidence_for_leaf(episodes: list[dict[str, Any]], leaf: str) -> dict[str, Any]:
    """Aggregate FOR / AGAINST / UNKNOWN counts for one H2 leaf."""
    for_ = []
    against = []
    unknown = []
    for ep in episodes:
        trail = ep.get("trail") or {}
        hint = trail.get("h2_leaf_hint") or ep.get("h2_leaf_hint")
        stop = trail.get("stop_stage")
        offline = ep.get("offline_ir")
        if leaf == "H2a":
            tests = trail.get("compatibility_tests") or []
            core_ids = {"PROMOTED_STATE", "LEFTOVER_GE_3", "TOKENS_SHORTER", "CAT_SELF_SHAPE", "SEMANTIC_CLASS_ELIGIBLE"}
            core_fails = [t for t in tests if t.get("gate_id") in core_ids and t.get("passed") is False]
            if trail.get("admissible") is False and "leftover" not in str(trail.get("admissibility_reason") or ""):
                for_.append(ep.get("cell_id"))
            elif core_fails and hint == "H2a":
                for_.append(ep.get("cell_id"))
            elif trail.get("admissible") and not core_fails:
                against.append(ep.get("cell_id"))
            elif hint == "H2c":
                against.append(ep.get("cell_id"))
            else:
                unknown.append(ep.get("cell_id"))
        elif leaf == "H2b":
            if offline and offline.get("single_step_cat_self") is True:
                against.append(ep.get("cell_id") or f"ir-{ep.get('seed')}")
            elif offline and offline.get("path_found") is False:
                for_.append(ep.get("cell_id") or f"ir-{ep.get('seed')}")
            elif hint == "H2b":
                for_.append(ep.get("cell_id"))
            elif hint in ("H2c", "POST_POOL", "H2a"):
                against.append(ep.get("cell_id"))
            else:
                unknown.append(ep.get("cell_id"))
        elif leaf == "H2c":
            filters = trail.get("structural_filter_results") or []
            if any(
                f.get("rejection_category", "").startswith("FILTER_") for f in filters
            ) and hint == "H2c":
                for_.append(ep.get("cell_id"))
            elif hint == "H2c":
                for_.append(ep.get("cell_id"))
            elif trail.get("in_candidate_pool") is True:
                against.append(ep.get("cell_id"))
            elif hint in ("H2a", "H2b") and not filters:
                against.append(ep.get("cell_id"))
            else:
                unknown.append(ep.get("cell_id"))
        elif leaf == "H2d":
            # narrow: only if offline path exists, compatible, but online never attempts due to utility
            if offline and offline.get("path_found") and hint == "H2d":
                for_.append(ep.get("cell_id"))
            elif hint == "H2c":
                # behavioral dup is structural, not pure utility — against H2d as earliest
                against.append(ep.get("cell_id"))
            else:
                unknown.append(ep.get("cell_id"))
        elif leaf == "H2e":
            if offline and offline.get("single_step_cat_self") is True:
                against.append(ep.get("cell_id") or f"ir-{ep.get('seed')}")
            elif offline and offline.get("path_found") is False and offline.get("single_step_cat_self") is False:
                # could be H2e or H2b
                unknown.append(ep.get("cell_id") or f"ir-{ep.get('seed')}")
            else:
                unknown.append(ep.get("cell_id"))
        elif leaf == "H2f":
            if hint == "H2f":
                for_.append(ep.get("cell_id"))
            elif trail.get("admissible") is True and int(trail.get("remaining_budget") or 0) >= 3:
                against.append(ep.get("cell_id"))
            else:
                unknown.append(ep.get("cell_id"))
        elif leaf == "POST_POOL":
            if trail.get("in_candidate_pool") is True:
                for_.append(ep.get("cell_id"))
            elif trail.get("in_candidate_pool") is False:
                against.append(ep.get("cell_id"))
            else:
                unknown.append(ep.get("cell_id"))
    def _verdict(f, a, u):
        if f and not a:
            return "FOR"
        if a and not f:
            return "AGAINST"
        if f and a:
            return "MIXED"
        return "UNKNOWN"

    return {
        "leaf": leaf,
        "FOR": for_,
        "AGAINST": against,
        "UNKNOWN": unknown,
        "verdict": _verdict(for_, against, unknown),
        "n_for": len(for_),
        "n_against": len(against),
        "n_unknown": len(unknown),
    }


def aggregate_h2(episodes_b: list[dict[str, Any]], offline_b: list[dict[str, Any]]) -> dict[str, Any]:
    combined = list(episodes_b) + [{"offline_ir": o, "seed": o.get("seed"), "cell_id": o.get("condition_id")} for o in offline_b]
    leaves = ["H2a", "H2b", "H2c", "H2d", "H2e", "H2f", "POST_POOL"]
    matrix = {leaf: evidence_for_leaf(combined if leaf in ("H2b", "H2e") else episodes_b, leaf) for leaf in leaves}
    # H2b/H2e need offline; recompute properly
    matrix["H2b"] = evidence_for_leaf(combined, "H2b")
    matrix["H2e"] = evidence_for_leaf(combined, "H2e")

    hints = Counter(
        (ep.get("trail") or {}).get("h2_leaf_hint")
        for ep in episodes_b
        if (ep.get("trail") or {}).get("h2_leaf_hint")
    )
    # Final conclusion rule
    conclusion = "INCONCLUSIVE"
    if hints.get("H2c") and hints.get("H2c") == len(episodes_b) and matrix["H2c"]["verdict"] == "FOR":
        # check offline rejects pure H2b
        if matrix["H2b"]["verdict"] == "AGAINST" and matrix["H2e"]["verdict"] == "AGAINST":
            conclusion = "H2c SUPPORTED"
        elif matrix["H2b"]["verdict"] == "AGAINST":
            conclusion = "H2c SUPPORTED"
        else:
            conclusion = "MULTIPLE H2 MECHANISMS"
    elif hints.get("POST_POOL"):
        conclusion = "POST-POOL BOTTLENECK"
    elif len(hints) > 1:
        conclusion = "MULTIPLE H2 MECHANISMS"
    elif len(hints) == 1:
        only = next(iter(hints))
        if only and only.startswith("H2"):
            conclusion = f"{only} SUPPORTED"
        elif only == "POST_POOL":
            conclusion = "POST-POOL BOTTLENECK"
        else:
            conclusion = "INCONCLUSIVE"
    return {
        "hint_counts": dict(hints),
        "leaf_matrix": matrix,
        "conclusion": conclusion,
    }


__all__ = ["evidence_for_leaf", "aggregate_h2"]
