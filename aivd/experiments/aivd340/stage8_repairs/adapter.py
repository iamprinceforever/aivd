"""Live _keep step-6 equivalence adapter (integration_spec §3–§5).

ONLY the pool-filter decision differs by family. Uses Stage-7 Phase-B
classifiers as source of truth. Ambiguous → retain (provisional novelty).
R-B is never wired.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from aivd.experiments.aivd340.stage6_repairs import ApplyCache, Budget
from aivd.experiments.aivd340.stage7_freeze import core_from_freeze, reserve_from_freeze
from aivd.experiments.aivd340.stage7_repairs.classifiers import (
    classify_baseline,
    classify_r_a,
    classify_r_c,
    classify_r_d,
)
from aivd.experiments.aivd340.stage8_constants import (
    S8_MAX_APPLY_MICRO_PER_PAIR,
    S8_MAX_EXPANSION_CALLS,
    S8_MAX_TOTAL_APPLY_MICRO_EPISODE,
    STAGE7_FREEZE_PATH,
)
from aivd.science.micro import Micro


FAMILY_CLASSIFY: dict[str, Callable] = {
    "BASELINE": classify_baseline,
    "R-A": classify_r_a,
    "R-C": classify_r_c,
    "R-D": classify_r_d,
    # R-B intentionally absent
}


@dataclass
class PoolDecision:
    action: str  # "reject" | "keep"
    label: str  # duplicate | distinct | ambiguous | retain
    fate_hint: str | None = None  # D if reject-by-equiv
    compared_keys: list[str] = field(default_factory=list)
    comparisons: list[dict[str, Any]] = field(default_factory=list)
    apply_micro_calls: int = 0
    ambiguity_state: str | None = None
    family: str = "BASELINE"


def load_stage7_banks(freeze_path: Path | None = None) -> tuple[list, list, dict]:
    p = freeze_path or STAGE7_FREEZE_PATH
    freeze = json.loads(Path(p).read_text())
    return core_from_freeze(freeze), reserve_from_freeze(freeze), freeze


def make_episode_budget(global_used: int = 0) -> Budget:
    b = Budget()
    b.pair_cap = S8_MAX_APPLY_MICRO_PER_PAIR
    b.global_cap = S8_MAX_TOTAL_APPLY_MICRO_EPISODE
    b.expansion_cap = S8_MAX_EXPANSION_CALLS
    b.global_used = global_used
    return b


def step6_equivalence(
    body2: Micro,
    got: str,
    behaviors: dict[str, str],
    body_map: dict[str, Micro],
    *,
    family: str,
    identity: str,
    core,
    reserve,
    budget: Budget,
    cache: ApplyCache,
    recorder: Any | None = None,
) -> PoolDecision:
    """integration_spec §5 pool policy.

    BASELINE: unmodified singleton identity rule (got in behaviors.values()).
    Repair families: classify candidate vs each existing body; reject only on
    duplicate; ambiguous retains.
    """
    if family == "BASELINE":
        if got in behaviors.values():
            dec = PoolDecision(
                action="reject",
                label="duplicate",
                fate_hint="D",
                family="BASELINE",
                compared_keys=list(behaviors.keys()),
            )
            if recorder is not None:
                recorder.equiv_decision(
                    family="BASELINE",
                    candidate_key=body2.key(),
                    label="duplicate",
                    action="reject",
                    apply_micro_calls=0,
                    ambiguity_state=None,
                    compared_keys=dec.compared_keys,
                    comparisons=[],
                )
            return dec
        dec = PoolDecision(action="keep", label="retain", family="BASELINE")
        if recorder is not None:
            recorder.equiv_decision(
                family="BASELINE",
                candidate_key=body2.key(),
                label="retain",
                action="keep",
                apply_micro_calls=0,
                ambiguity_state=None,
                compared_keys=[],
                comparisons=[],
            )
        return dec

    if family not in FAMILY_CLASSIFY:
        raise RuntimeError(f"family not wired for Stage-8: {family}")
    if family == "R-B":
        raise RuntimeError("R-B EXCLUDED (COST_IMPRACTICAL)")

    clf = FAMILY_CLASSIFY[family]
    comparisons: list[dict[str, Any]] = []
    compared: list[str] = []
    calls_total = 0
    any_ambiguous = False
    amb_state = None

    for key, prev_got in list(behaviors.items()):
        prev_body = body_map.get(key)
        if prev_body is None:
            # Cannot classify without body — treat as ambiguous retain for this entry
            comparisons.append(
                {
                    "key": key,
                    "label": "ambiguous",
                    "reason": "missing_prev_body",
                    "apply_micro_calls": 0,
                }
            )
            compared.append(key)
            any_ambiguous = True
            amb_state = "missing_prev_body"
            continue

        budget.reset_pair()
        before = budget.pair_used
        kwargs: dict[str, Any] = {
            "identity": identity,
            "core": core,
            "reserve": reserve,
            "cache": cache,
            "budget": budget,
        }
        out = clf(body2, prev_body, **kwargs)
        label = out["label"] if isinstance(out, dict) else out.label
        calls = (
            out.get("apply_micro_calls", 0)
            if isinstance(out, dict)
            else getattr(out, "apply_micro_calls", 0)
        )
        calls_total += int(calls or 0)
        amb = None
        if isinstance(out, dict):
            amb = out.get("ambiguity_state")
        compared.append(key)
        comparisons.append(
            {
                "key": key,
                "label": label,
                "apply_micro_calls": calls,
                "ambiguity_state": amb,
                "prev_got": prev_got,
            }
        )
        if label == "duplicate":
            dec = PoolDecision(
                action="reject",
                label="duplicate",
                fate_hint="D",
                family=family,
                compared_keys=compared,
                comparisons=comparisons,
                apply_micro_calls=calls_total,
                ambiguity_state=amb,
            )
            if recorder is not None:
                recorder.equiv_decision(
                    family=family,
                    candidate_key=body2.key(),
                    label="duplicate",
                    action="reject",
                    apply_micro_calls=calls_total,
                    ambiguity_state=amb,
                    compared_keys=compared,
                    comparisons=comparisons,
                )
                recorder.repair_ledger_add(calls_total)
            return dec
        if label == "ambiguous":
            any_ambiguous = True
            amb_state = amb or "ambiguous"

    # all distinct or only ambiguous → keep (ambiguous retains)
    final_label = "ambiguous" if any_ambiguous and not any(
        c["label"] == "distinct" for c in comparisons
    ) else ("retain" if not any_ambiguous else "ambiguous")
    # If any distinct and rest ambiguous/distinct → keep as retain/distinct
    if any(c["label"] == "distinct" for c in comparisons) or not comparisons:
        final_label = "distinct" if not any_ambiguous else "ambiguous"

    dec = PoolDecision(
        action="keep",
        label=final_label if final_label != "retain" else "distinct",
        family=family,
        compared_keys=compared,
        comparisons=comparisons,
        apply_micro_calls=calls_total,
        ambiguity_state=amb_state,
    )
    if recorder is not None:
        recorder.equiv_decision(
            family=family,
            candidate_key=body2.key(),
            label=dec.label,
            action="keep",
            apply_micro_calls=calls_total,
            ambiguity_state=amb_state,
            compared_keys=compared,
            comparisons=comparisons,
        )
        recorder.repair_ledger_add(calls_total)
    return dec


def classify_pair_for_replay(body_a, body_b, *, family: str, identity, core, reserve, cache, budget):
    """Live-wired classifier call matching Stage-7 Phase-B API (for P1 replay)."""
    if family not in FAMILY_CLASSIFY:
        raise RuntimeError(f"unwired family: {family}")
    clf = FAMILY_CLASSIFY[family]
    return clf(
        body_a,
        body_b,
        identity=identity,
        core=core,
        reserve=reserve,
        cache=cache,
        budget=budget,
    )
