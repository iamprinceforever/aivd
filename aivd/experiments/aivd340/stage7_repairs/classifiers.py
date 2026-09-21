"""Isolated executable classifiers — decision-equivalent to Stage-6 offline family specs."""
from __future__ import annotations

from typing import Any

from aivd.experiments.aivd340.stage6_repairs import (
    ApplyCache,
    Budget,
    ClassifyResult,
    classify_baseline as _baseline,
    classify_r_a as _ra,
    classify_r_b as _rb,
    classify_r_c as _rc,
    classify_r_d as _rd,
)
from aivd.experiments.aivd340.stage7_constants import IDENTITY_DEFAULT


def _enrich(result: ClassifyResult, *, independence: str | None = None) -> dict[str, Any]:
    """Map ClassifyResult → Phase-B contract fields."""
    label = result.label
    ambiguity_state = None
    if label == "ambiguous":
        ambiguity_state = (result.evidence or {}).get("reason") or (result.evidence or {}).get("stage") or "ambiguous"
    budget_exhausted = bool(
        (result.evidence or {}).get("stop")
        and "budget" in str((result.evidence or {})).lower()
    ) or (result.evidence or {}).get("reason") == "budget"
    # Also detect ambiguous_budget path
    if "budget" in str((result.evidence or {}).get("reason", "")).lower():
        budget_exhausted = True
    if (result.evidence or {}).get("stage") in {"identity_budget", "reserve_budget"}:
        budget_exhausted = True

    provenance = {
        "family_id": result.mechanism,
        "contexts_used": [
            c.get("context_id")
            for c in (result.evidence or {}).get("contexts") or []
            if isinstance(c, dict)
        ],
        "expansion_used": result.expansion_calls,
        "independence_label_echo": independence,
        "claim_label": "IMPL_SPEC_EQUIVALENCE",
        "autonomous_discovery_credit": False,
        "sacred": False,
        "live_promote_set_mutation": False,
    }
    return {
        "label": label,
        "ambiguity_state": ambiguity_state,
        "evidence": result.evidence,
        "provenance": provenance,
        "apply_micro_calls": result.apply_micro_calls,
        "family_id": result.mechanism,
        "budget_exhausted": budget_exhausted,
        "expansion_calls": result.expansion_calls,
        # retain raw for offline compare
        "_raw_mechanism": result.mechanism,
    }


def classify_baseline(body_a, body_b, **kwargs):
    r = _baseline(body_a, body_b, **kwargs)
    return _enrich(r, independence=kwargs.get("independence"))


def classify_r_a(body_a, body_b, **kwargs):
    r = _ra(body_a, body_b, **kwargs)
    return _enrich(r, independence=kwargs.get("independence"))


def classify_r_b(body_a, body_b, **kwargs):
    r = _rb(body_a, body_b, **kwargs)
    return _enrich(r, independence=kwargs.get("independence"))


def classify_r_c(body_a, body_b, **kwargs):
    r = _rc(body_a, body_b, **kwargs)
    return _enrich(r, independence=kwargs.get("independence"))


def classify_r_d(body_a, body_b, **kwargs):
    r = _rd(body_a, body_b, **kwargs)
    return _enrich(r, independence=kwargs.get("independence"))


CLASSIFIERS = {
    "BASELINE": classify_baseline,
    "R-A": classify_r_a,
    "R-B": classify_r_b,
    "R-C": classify_r_c,
    "R-D": classify_r_d,
}


def classify_pair(body_a, body_b, *, family_id: str, identity=IDENTITY_DEFAULT,
                  context_bank=None, budget_state=None, core=None, reserve=None,
                  cache=None, independence=None, **kwargs) -> dict[str, Any]:
    """Phase-B / isolation API."""
    clf = CLASSIFIERS[family_id]
    return clf(
        body_a, body_b,
        identity=identity,
        core=core if core is not None else context_bank,
        reserve=reserve,
        cache=cache,
        budget=budget_state,
        independence=independence,
        **kwargs,
    )
