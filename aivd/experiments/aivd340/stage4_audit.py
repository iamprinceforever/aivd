"""Observational growth-path audit for a controlled parent atom.

Does NOT alter propose_growth / scores / filters / selection. Probes the same
gates that propose_growth uses and records OBSERVED / CONTROLLED / UNKNOWN /
NOT_APPLICABLE statuses. Never invents missing transitions.
"""
from __future__ import annotations

from typing import Any

from aivd.experiments.aivd340.stage4_constants import (
    GATE_CAT_SELF_SHAPE,
    GATE_COMPOSE_DISTINCT_CLASS,
    GATE_LEFTOVER_GE_3,
    GATE_PROMOTED_STATE,
    GATE_SEMANTIC_CLASS_ELIGIBLE,
    GATE_TOKENS_SHORTER,
    ODD_CAT_SELF_BODY_KEY,
    PROV_CONTROLLED_INPUT,
    PROV_UNKNOWN,
    STATUS_CONTROLLED,
    STATUS_NOT_APPLICABLE,
    STATUS_OBSERVED,
    STATUS_UNKNOWN,
    TRANSITION_CHAIN,
    U_GOOD_CAT_SELF_BODY_KEY,
)
from aivd.science.grow import (
    cat_self_body,
    pick_compose_pair,
    pick_generation_action,
    tokens_shorter,
)
from aivd.science.micro import apply_micro, canonicalize_micro, validate_micro
from aivd.science.operators import split_prompt
from aivd.science.representation import propose_growth_candidates


def _find_atom(language: Any, body_key: str) -> Any | None:
    for a in getattr(language, "invented", []) or []:
        if a.key() == body_key:
            return a
    return None


def _gate(gate_id: str, passed: bool | str, detail: str | None = None) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": passed, "detail": detail}


def simulate_keep_checks(
    *,
    language: Any,
    identity: str,
    candidate_body: Any,
    behaviors: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Mirror propose_growth._keep checks observationally (no mutation)."""
    known_keys = {a.key() for a in getattr(language, "invented", []) or []}
    known_keys.update(getattr(language, "program_keys", lambda: set())())
    if behaviors is None:
        behaviors = {}
        promoted = [
            a
            for a in getattr(language, "invented", []) or []
            if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
        ]
        try:
            for a in promoted:
                behaviors[a.key()] = apply_micro(identity, a.body)
        except Exception:
            pass

    body2 = canonicalize_micro(candidate_body)
    if body2 is None:
        return {
            "status": "rejected",
            "rejection_category": "FILTER_OTHER",
            "rejection_reason": "canonicalize_micro returned None",
            "result_body_key": None,
        }
    k = body2.key()
    if k in known_keys:
        return {
            "status": "rejected",
            "rejection_category": "FILTER_KNOWN_KEY",
            "rejection_reason": "body key already in known_keys",
            "result_body_key": k,
        }
    vm = validate_micro(body2, n_tokens=max(2, len(split_prompt(identity))))
    if vm is not None:
        return {
            "status": "rejected",
            "rejection_category": "FILTER_VALIDATE_MICRO",
            "rejection_reason": str(vm),
            "result_body_key": k,
        }
    try:
        got = apply_micro(identity, body2)
    except Exception as e:
        return {
            "status": "rejected",
            "rejection_category": "FILTER_OTHER",
            "rejection_reason": f"apply_micro exception: {e}",
            "result_body_key": k,
        }
    if got == identity or not got:
        return {
            "status": "rejected",
            "rejection_category": "FILTER_IDENTITY_NOOP",
            "rejection_reason": "got == identity or empty",
            "result_body_key": k,
        }
    if got in behaviors.values():
        dup_of = [kk for kk, vv in behaviors.items() if vv == got]
        return {
            "status": "rejected",
            "rejection_category": "FILTER_BEHAVIORAL_DUP",
            "rejection_reason": f"behavioral duplicate of {dup_of}",
            "result_body_key": k,
            "behavior": got,
            "duplicate_of": dup_of,
        }
    return {
        "status": "constructed",
        "rejection_category": None,
        "rejection_reason": None,
        "result_body_key": k,
        "behavior": got,
    }


def audit_controlled_parent(
    *,
    language: Any,
    identity: str,
    leftover: int,
    parent_body_key: str,
    relevant_product_body_key: str,
    policy: str = "R1",
    provenance: str = PROV_CONTROLLED_INPUT,
    max_cands_observed: int | None = None,
) -> dict[str, Any]:
    """Full observational trail for one parent body key through the growth path."""
    transitions: dict[str, dict[str, Any]] = {
        name: {"status": STATUS_UNKNOWN, "detail": None} for name in TRANSITION_CHAIN
    }

    atom = _find_atom(language, parent_body_key)
    transitions["INPUT"] = {
        "status": STATUS_CONTROLLED if provenance == PROV_CONTROLLED_INPUT else STATUS_OBSERVED,
        "detail": {
            "body_key": parent_body_key,
            "present_in_language": atom is not None,
            "provenance": provenance,
            "origin": getattr(atom, "origin", None) if atom else None,
            "semantic_class": getattr(atom, "semantic_class", None) if atom else None,
        },
    }

    if atom is None:
        transitions["ADMISSIBILITY"] = {
            "status": STATUS_OBSERVED,
            "detail": {"admissible": False, "reason": "atom_absent_from_language"},
        }
        for later in TRANSITION_CHAIN[TRANSITION_CHAIN.index("COMPATIBILITY") :]:
            transitions[later] = {
                "status": STATUS_NOT_APPLICABLE,
                "detail": "upstream_atom_absent",
            }
        return _finalize(
            transitions,
            atom=None,
            parent_body_key=parent_body_key,
            relevant_product_body_key=relevant_product_body_key,
            growth_cands=[],
            action=None,
            leftover=leftover,
            compositions=[],
            filters=[],
            compatibility_tests=[],
            applicable_operators=[],
            stop_stage="ADMISSIBILITY",
            h2_leaf_hint="H2a",
        )

    name = atom.name()
    state = getattr(language, "state_of", lambda _n: STATUS_UNKNOWN)(name)
    promoted_ok = state == "PROMOTED"
    leftover_ok = int(leftover) >= 3
    admissible = bool(promoted_ok and leftover_ok)
    admissibility_reason = None
    if not promoted_ok:
        admissibility_reason = f"state={state} (need PROMOTED)"
    elif not leftover_ok:
        admissibility_reason = f"leftover={leftover} < 3"

    transitions["ADMISSIBILITY"] = {
        "status": STATUS_OBSERVED,
        "detail": {
            "admissible": admissible,
            "reason": admissibility_reason,
            "gates": [
                _gate(GATE_PROMOTED_STATE, promoted_ok, state),
                _gate(GATE_LEFTOVER_GE_3, leftover_ok, str(leftover)),
            ],
        },
    }

    # Compatibility
    try:
        got_parent = apply_micro(identity, atom.body)
        shorter = tokens_shorter(identity, got_parent)
        shorter_detail = repr(got_parent)
    except Exception as e:
        got_parent = None
        shorter = False
        shorter_detail = f"apply_micro exception: {e}"

    cat_body = cat_self_body(atom.body)
    cat_ok = cat_body is not None
    cat_key = cat_body.key() if cat_body is not None else None
    # SEMANTIC_CLASS_ELIGIBLE: under R1 any_class=True, non-char_project still eligible
    # if tokens_shorter; char_project always in first loop.
    cls = getattr(atom, "semantic_class", None) or ""
    if policy in ("R1", "R1b") or True:
        # R1 forces any_class=True in propose_growth_candidates
        class_eligible = bool(shorter and cat_ok)  # any class with shortening + shape
        class_detail = f"semantic_class={cls}; R1 any_class path"
    else:
        class_eligible = bool(cls == "char_project" and shorter and cat_ok)
        class_detail = f"semantic_class={cls}; R0 char_project-only"

    compose_pair = pick_compose_pair(language)
    compose_eligible = False
    compose_detail = "no distinct-class pair involving this parent"
    if compose_pair is not None:
        a, b = compose_pair
        if atom.name() in (a.name(), b.name()):
            compose_eligible = True
            compose_detail = f"pair=({a.key()}|{b.key()})"
        else:
            compose_detail = f"pair_exists_elsewhere=({a.key()}|{b.key()})"

    compatibility_tests = [
        _gate(GATE_PROMOTED_STATE, promoted_ok, state),
        _gate(GATE_LEFTOVER_GE_3, leftover_ok, str(leftover)),
        _gate(GATE_TOKENS_SHORTER, shorter if got_parent is not None else STATUS_UNKNOWN, shorter_detail),
        _gate(GATE_CAT_SELF_SHAPE, cat_ok, cat_key),
        _gate(GATE_SEMANTIC_CLASS_ELIGIBLE, class_eligible, class_detail),
        _gate(GATE_COMPOSE_DISTINCT_CLASS, compose_eligible, compose_detail),
    ]
    compat_pass = bool(promoted_ok and leftover_ok and shorter and cat_ok and class_eligible)
    transitions["COMPATIBILITY"] = {
        "status": STATUS_OBSERVED,
        "detail": {"passed": compat_pass, "tests": compatibility_tests},
    }

    if not admissible:
        for later in (
            "APPLICABLE_OPERATORS",
            "COMPOSITION_ATTEMPTS",
            "SUCCESSFUL_COMPOSITIONS",
            "STRUCTURAL_FILTERS",
            "CANDIDATE_POOL",
            "SCORE",
            "RANK",
            "SELECTION",
            "VERIFICATION",
        ):
            transitions[later] = {
                "status": STATUS_NOT_APPLICABLE,
                "detail": "not_admissible",
            }
        return _finalize(
            transitions,
            atom=atom,
            parent_body_key=parent_body_key,
            relevant_product_body_key=relevant_product_body_key,
            growth_cands=[],
            action=None,
            leftover=leftover,
            compositions=[],
            filters=[],
            compatibility_tests=compatibility_tests,
            applicable_operators=[],
            stop_stage="ADMISSIBILITY",
            h2_leaf_hint="H2f" if (promoted_ok and not leftover_ok) else "H2a",
        )

    # Applicable operators
    applicable: list[str] = []
    if cat_ok and shorter:
        applicable.append("CAT_SELF")
    if compose_eligible:
        applicable.append("COMPOSE")
    if not applicable:
        applicable = ["NONE"]
    transitions["APPLICABLE_OPERATORS"] = {
        "status": STATUS_OBSERVED,
        "detail": {"operators": applicable},
    }

    compositions: list[dict[str, Any]] = []
    filters: list[dict[str, Any]] = []

    # CAT_SELF attempt (observational parallel to propose_growth)
    if "CAT_SELF" in applicable and cat_body is not None:
        # Build behaviors as propose_growth does BEFORE considering this parent,
        # approximating class-order: char_project first, then others.
        behaviors: dict[str, str] = {}
        promoted = [
            a
            for a in getattr(language, "invented", []) or []
            if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
        ]
        try:
            for a in promoted:
                behaviors[a.key()] = apply_micro(identity, a.body)
        except Exception:
            pass
        # Register behaviors of CAT-selves that propose_growth would keep earlier
        # (char_project loop, reversed) — observational reconstruction of filter state.
        pre_kept: list[str] = []
        for a in reversed(promoted):
            if a.semantic_class != "char_project":
                continue
            if a.key() == parent_body_key:
                break  # stop before our parent in char_project path (odd is not char_project)
            try:
                g = apply_micro(identity, a.body)
            except Exception:
                continue
            if not tokens_shorter(identity, g):
                continue
            cb = cat_self_body(a.body)
            if cb is None:
                continue
            chk = simulate_keep_checks(
                language=language, identity=identity, candidate_body=cb, behaviors=behaviors
            )
            if chk["status"] == "constructed" and chk.get("result_body_key"):
                behaviors[chk["result_body_key"]] = chk.get("behavior") or apply_micro(
                    identity, canonicalize_micro(cb)
                )
                pre_kept.append(chk["result_body_key"])
            if a.key() == parent_body_key:
                break

        # Also register earlier any_class parents before ours in chronological order
        for a in promoted:
            if a.key() == parent_body_key:
                break
            if a.semantic_class == "char_project":
                continue
            try:
                g = apply_micro(identity, a.body)
            except Exception:
                continue
            if not tokens_shorter(identity, g):
                continue
            cb = cat_self_body(a.body)
            if cb is None:
                continue
            chk = simulate_keep_checks(
                language=language, identity=identity, candidate_body=cb, behaviors=behaviors
            )
            if chk["status"] == "constructed" and chk.get("result_body_key"):
                behaviors[chk["result_body_key"]] = chk.get("behavior") or apply_micro(
                    identity, canonicalize_micro(cb)
                )
                pre_kept.append(chk["result_body_key"])

        keep = simulate_keep_checks(
            language=language, identity=identity, candidate_body=cat_body, behaviors=behaviors
        )
        compositions.append(
            {
                "op": "CAT_SELF",
                "parent_body_keys": [parent_body_key],
                "result_body_key": keep.get("result_body_key") or cat_key,
                "status": "attempted"
                if keep["status"] == "rejected"
                else ("constructed" if keep["status"] == "constructed" else "UNKNOWN"),
                "rejection_reason": keep.get("rejection_reason"),
                "rejection_category": keep.get("rejection_category"),
                "pre_kept_behaviors_from": pre_kept,
            }
        )
        if keep["status"] == "rejected":
            filters.append(
                {
                    "op": "CAT_SELF",
                    "result_body_key": keep.get("result_body_key"),
                    "rejection_category": keep.get("rejection_category"),
                    "rejection_reason": keep.get("rejection_reason"),
                    "duplicate_of": keep.get("duplicate_of"),
                }
            )
            transitions["COMPOSITION_ATTEMPTS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"attempts": compositions},
            }
            transitions["SUCCESSFUL_COMPOSITIONS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"successful": []},
            }
            transitions["STRUCTURAL_FILTERS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"filters": filters},
            }
        else:
            transitions["COMPOSITION_ATTEMPTS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"attempts": compositions},
            }
            transitions["SUCCESSFUL_COMPOSITIONS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"successful": [keep.get("result_body_key")]},
            }
            transitions["STRUCTURAL_FILTERS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"filters": [], "note": "constructed_passed_keep_checks"},
            }
    elif "NONE" in applicable or not applicable:
        transitions["COMPOSITION_ATTEMPTS"] = {
            "status": STATUS_OBSERVED,
            "detail": {"attempts": [], "reason": "no_applicable_operator"},
        }
        transitions["SUCCESSFUL_COMPOSITIONS"] = {
            "status": STATUS_OBSERVED,
            "detail": {"successful": []},
        }
        transitions["STRUCTURAL_FILTERS"] = {
            "status": STATUS_NOT_APPLICABLE,
            "detail": "no_composition_to_filter",
        }
    else:
        transitions["COMPOSITION_ATTEMPTS"] = {
            "status": STATUS_OBSERVED,
            "detail": {"attempts": compositions},
        }
        transitions["SUCCESSFUL_COMPOSITIONS"] = {
            "status": STATUS_UNKNOWN,
            "detail": "compose_only_path_not_fully_instrumented",
        }
        transitions["STRUCTURAL_FILTERS"] = {
            "status": STATUS_UNKNOWN,
            "detail": "compose_only",
        }

    # Real pool via unchanged propose_growth_candidates
    growth_cands = propose_growth_candidates(
        language, identity=identity, leftover=leftover, policy=policy
    )
    pool_keys = [g.key() for g in growth_cands]
    in_pool = relevant_product_body_key in pool_keys
    parent_products_in_pool = [
        g.key() for g in growth_cands if parent_body_key in (getattr(g, "parent", ()) or ())
        or (hasattr(g, "parent") and parent_body_key in tuple(getattr(g, "parent", ()) or ()))
    ]
    # Also match by key equality to relevant product
    if in_pool and relevant_product_body_key not in parent_products_in_pool:
        parent_products_in_pool.append(relevant_product_body_key)

    # Detect max_cands truncation: constructed by keep but absent from pool
    constructed_keys = [
        c["result_body_key"]
        for c in compositions
        if c.get("status") == "constructed" and c.get("result_body_key")
    ]
    for ck in constructed_keys:
        if ck not in pool_keys:
            filters.append(
                {
                    "op": "CAT_SELF",
                    "result_body_key": ck,
                    "rejection_category": "FILTER_MAX_CANDS_TRUNCATE",
                    "rejection_reason": "constructed by keep semantics but absent from capped growth_cands",
                }
            )
            # refresh structural filter transition
            transitions["STRUCTURAL_FILTERS"] = {
                "status": STATUS_OBSERVED,
                "detail": {"filters": filters},
            }

    transitions["CANDIDATE_POOL"] = {
        "status": STATUS_OBSERVED,
        "detail": {
            "pool_body_keys": pool_keys,
            "relevant_in_pool": in_pool,
            "parent_products_in_pool": parent_products_in_pool,
            "n_growth_cands": len(growth_cands),
        },
    }

    # Score / rank / select via unchanged pick_generation_action (+ observational mirror)
    compose_pair = pick_compose_pair(language)
    promoted_names = [
        a.name()
        for a in getattr(language, "invented", []) or []
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
        and not str(a.name()).startswith("cmp_")
    ]

    def parent_rank(g: Any) -> int:
        parents = getattr(g, "parent", ()) or ()
        idxs = [promoted_names.index(p) if p in promoted_names else 99 for p in parents]
        return min(idxs) if idxs else 99

    ranked = sorted(growth_cands, key=parent_rank)
    score = None
    rank = None
    selected = False
    selected_bk = None
    if in_pool:
        for i, g in enumerate(ranked, start=1):
            if g.key() == relevant_product_body_key:
                rank = i
                score = float(-parent_rank(g))
                break
        transitions["SCORE"] = {"status": STATUS_OBSERVED, "detail": {"score": score}}
        transitions["RANK"] = {"status": STATUS_OBSERVED, "detail": {"rank": rank}}
    else:
        transitions["SCORE"] = {
            "status": STATUS_NOT_APPLICABLE,
            "detail": "relevant_product_absent_from_pool",
        }
        transitions["RANK"] = {
            "status": STATUS_NOT_APPLICABLE,
            "detail": "relevant_product_absent_from_pool",
        }

    action = pick_generation_action(
        language,
        growth_cands=growth_cands,
        compose_pair=compose_pair,
        leftover=leftover,
    )
    if action and action[0] == "grow" and action[1] is not None:
        selected_bk = action[1].key()
        selected = selected_bk == relevant_product_body_key
    elif action and action[0] == "compose":
        selected_bk = "COMPOSE"
        selected = False
    elif action and action[0] == "safety":
        selected_bk = "safety"
        selected = False

    if in_pool:
        transitions["SELECTION"] = {
            "status": STATUS_OBSERVED,
            "detail": {"selected": selected, "action": action[0] if action else None, "selected_body_key": selected_bk},
        }
    else:
        transitions["SELECTION"] = {
            "status": STATUS_NOT_APPLICABLE,
            "detail": "relevant_product_absent_from_pool",
        }

    # Verification not exercised in observational-only (no Sacred) → UNKNOWN or N/A
    transitions["VERIFICATION"] = {
        "status": STATUS_NOT_APPLICABLE,
        "detail": "stage4_observational_audit_no_sacred_verification",
    }

    # Earliest stop + H2 leaf hint
    stop_stage, h2_hint = _earliest_stop(
        transitions=transitions,
        compositions=compositions,
        filters=filters,
        in_pool=in_pool,
        compat_pass=compat_pass,
        applicable=applicable,
        leftover_ok=leftover_ok,
        promoted_ok=promoted_ok,
    )

    return _finalize(
        transitions,
        atom=atom,
        parent_body_key=parent_body_key,
        relevant_product_body_key=relevant_product_body_key,
        growth_cands=growth_cands,
        action=action,
        leftover=leftover,
        compositions=compositions,
        filters=filters,
        compatibility_tests=compatibility_tests,
        applicable_operators=applicable,
        stop_stage=stop_stage,
        h2_leaf_hint=h2_hint,
        score=score,
        rank=rank,
        selected=selected,
        in_pool=in_pool,
    )


def _earliest_stop(
    *,
    transitions: dict,
    compositions: list,
    filters: list,
    in_pool: bool,
    compat_pass: bool,
    applicable: list,
    leftover_ok: bool,
    promoted_ok: bool,
) -> tuple[str, str]:
    if not promoted_ok:
        return "ADMISSIBILITY", "H2a"
    if not leftover_ok:
        return "ADMISSIBILITY", "H2f"
    if not compat_pass:
        # distinguish tokens_shorter / shape vs class
        return "COMPATIBILITY", "H2a"
    if applicable == ["NONE"] or not applicable or applicable == []:
        return "APPLICABLE_OPERATORS", "H2b"
    constructed = [c for c in compositions if c.get("status") == "constructed"]
    rejected = [c for c in compositions if c.get("status") == "attempted" and c.get("rejection_category")]
    if rejected and not constructed:
        cat = rejected[0].get("rejection_category") or ""
        if cat.startswith("FILTER_"):
            return "STRUCTURAL_FILTERS", "H2c"
        return "COMPOSITION_ATTEMPTS", "H2b"
    if constructed and not in_pool:
        # truncated or otherwise dropped
        if any(f.get("rejection_category") == "FILTER_MAX_CANDS_TRUNCATE" for f in filters):
            return "STRUCTURAL_FILTERS", "H2c"
        return "STRUCTURAL_FILTERS", "H2c"
    if in_pool:
        return "CANDIDATE_POOL", "POST_POOL"
    if not compositions:
        return "COMPOSITION_ATTEMPTS", "H2b"
    return "COMPOSITION_ATTEMPTS", "INCONCLUSIVE"


def _finalize(
    transitions: dict,
    *,
    atom: Any,
    parent_body_key: str,
    relevant_product_body_key: str,
    growth_cands: list,
    action: Any,
    leftover: int,
    compositions: list,
    filters: list,
    compatibility_tests: list,
    applicable_operators: list,
    stop_stage: str,
    h2_leaf_hint: str,
    score: Any = None,
    rank: Any = None,
    selected: bool = False,
    in_pool: bool = False,
) -> dict[str, Any]:
    return {
        "atom_id": None if atom is None else atom.name(),
        "origin": PROV_CONTROLLED_INPUT
        if atom is not None and "controlled" in str(getattr(atom, "origin", "")).lower()
        else (getattr(atom, "origin", None) if atom else None),
        "provenance": PROV_CONTROLLED_INPUT
        if atom is not None
        and (
            getattr(atom, "novelty", None) == PROV_CONTROLLED_INPUT
            or "controlled" in str(getattr(atom, "origin", "")).lower()
        )
        else (PROV_UNKNOWN if atom is None else "AUTONOMOUS_OR_OTHER"),
        "generation": None,
        "parent": None if atom is None else (getattr(atom, "parent", None) or None),
        "body_key": parent_body_key,
        "representation": "R1",
        "semantic_class": None if atom is None else getattr(atom, "semantic_class", None),
        "admissible": (transitions.get("ADMISSIBILITY") or {}).get("detail", {}).get("admissible"),
        "admissibility_reason": (transitions.get("ADMISSIBILITY") or {}).get("detail", {}).get("reason"),
        "compatibility_tests": compatibility_tests,
        "applicable_operators": applicable_operators,
        "compositions": compositions,
        "structural_filter_results": filters,
        "in_candidate_pool": in_pool,
        "pool_body_keys": [g.key() for g in growth_cands],
        "relevant_product_body_key": relevant_product_body_key,
        "score": score if score is not None else "UNKNOWN",
        "rank": rank if rank is not None else "UNKNOWN",
        "selected": selected if in_pool else "UNKNOWN",
        "action": None if action is None else (action[0] if isinstance(action, tuple) else action),
        "remaining_budget": leftover,
        "stop_stage": stop_stage,
        "h2_leaf_hint": h2_leaf_hint,
        "transitions": transitions,
        "claim_label": STATUS_OBSERVED,
    }


def causal_trace_compact(trail: dict[str, Any]) -> str:
    """Compact causal trace with status at every arrow."""
    tr = trail.get("transitions") or {}
    parts = []
    for name in TRANSITION_CHAIN:
        st = (tr.get(name) or {}).get("status", STATUS_UNKNOWN)
        parts.append(f"{name}[{st}]")
    return " → ".join(parts)


__all__ = [
    "audit_controlled_parent",
    "simulate_keep_checks",
    "causal_trace_compact",
]
