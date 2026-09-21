"""Stage-6 offline repair classifiers — BASELINE + R-A..R-D (classification-only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.experiments.aivd340.stage6_constants import (
    IDENTITY_DEFAULT,
    IDENTITY_FAMILY,
    RB_AGREE_FAMILIES,
    RB_MIN_AGREE_FAMILIES,
    RC_PROBE_P0,
    RD_SEMANTIC_FAMILIES,
    S6_AMBIGUOUS_AT_BUDGET_EXHAUSTION,
    S6_MAX_APPLY_MICRO_PER_PAIR,
    S6_MAX_EXPANSION_CALLS,
    S6_MAX_TOTAL_APPLY_MICRO_RUN,
)
from aivd.science.micro import Micro, apply_micro


@dataclass
class Budget:
    pair_used: int = 0
    pair_cap: int = S6_MAX_APPLY_MICRO_PER_PAIR
    global_used: int = 0
    global_cap: int = S6_MAX_TOTAL_APPLY_MICRO_RUN
    expansion_used: int = 0
    expansion_cap: int = S6_MAX_EXPANSION_CALLS
    exhausted_pair: bool = False
    exhausted_global: bool = False

    def can_spend(self, n: int = 1, *, expansion: bool = False) -> bool:
        if self.exhausted_pair or self.exhausted_global:
            return False
        if self.pair_used + n > self.pair_cap:
            return False
        if self.global_used + n > self.global_cap:
            return False
        if expansion and self.expansion_used + n > self.expansion_cap:
            return False
        return True

    def spend(self, n: int = 1, *, expansion: bool = False) -> bool:
        if not self.can_spend(n, expansion=expansion):
            if self.global_used + n > self.global_cap:
                self.exhausted_global = True
            else:
                self.exhausted_pair = True
            return False
        self.pair_used += n
        self.global_used += n
        if expansion:
            self.expansion_used += n
        return True

    def reset_pair(self) -> None:
        self.pair_used = 0
        self.expansion_used = 0
        self.exhausted_pair = False


@dataclass
class ApplyCache:
    store: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)

    def get(self, prompt: str, body: Micro, budget: Budget, *, expansion: bool = False):
        key = (prompt, body.key())
        if key in self.store:
            return self.store[key], self.errors.get(key)
        if not budget.spend(1, expansion=expansion):
            return None, "BUDGET"
        try:
            out = apply_micro(prompt, body)
            self.store[key] = out
            return out, None
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}:{e}"
            self.store[key] = None
            self.errors[key] = err
            return None, err


@dataclass
class ClassifyResult:
    label: str
    mechanism: str
    apply_micro_calls: int
    expansion_calls: int
    evidence: dict
    claim_label: str = "OFFLINE_REPAIR_BENCH"
    autonomous_discovery_credit: bool = False


def _compare(body_a, body_b, contexts, cache, budget, *, expansion=False, early_exit_on_diff=True):
    per = []
    for cid, fam, prompt in contexts:
        ga, ea = cache.get(prompt, body_a, budget, expansion=expansion)
        if ea == "BUDGET" or budget.exhausted_pair or budget.exhausted_global:
            return "ambiguous_budget", {"contexts": per, "stop": cid}
        gb, eb = cache.get(prompt, body_b, budget, expansion=expansion)
        if eb == "BUDGET" or budget.exhausted_pair or budget.exhausted_global:
            return "ambiguous_budget", {"contexts": per, "stop": cid}
        if ea or eb or ga is None or gb is None:
            per.append({"context_id": cid, "family": fam, "equal": "UNKNOWN"})
            return "ambiguous_error", {"contexts": per}
        eq = ga == gb
        per.append({"context_id": cid, "family": fam, "equal": eq})
        if early_exit_on_diff and not eq:
            return "differ", {"contexts": per}
    if per and all(x["equal"] is True for x in per):
        return "equal", {"contexts": per}
    if any(x["equal"] is False for x in per):
        return "differ", {"contexts": per}
    return "ambiguous_error", {"contexts": per}


def classify_baseline(body_a, body_b, *, identity=IDENTITY_DEFAULT, cache=None, budget=None, **_):
    assert cache is not None and budget is not None
    start = budget.pair_used
    if body_a.key() == body_b.key():
        return ClassifyResult("duplicate", "BASELINE", 0, 0, {"reason": "identical_canonical_key"})
    ga, ea = cache.get(identity, body_a, budget)
    gb, eb = cache.get(identity, body_b, budget)
    if ea == "BUDGET" or eb == "BUDGET":
        label = "ambiguous" if S6_AMBIGUOUS_AT_BUDGET_EXHAUSTION else "distinct"
        return ClassifyResult(label, "BASELINE", budget.pair_used - start, 0, {"reason": "budget"})
    if ea or eb or ga is None or gb is None:
        return ClassifyResult("distinct", "BASELINE", budget.pair_used - start, 0, {"reason": "apply_error"})
    return ClassifyResult(
        "duplicate" if ga == gb else "distinct",
        "BASELINE", budget.pair_used - start, 0,
        {"identity": identity, "got_a": ga, "got_b": gb},
    )


def classify_r_a(body_a, body_b, *, core, cache=None, budget=None, **_):
    assert cache is not None and budget is not None
    start = budget.pair_used
    if body_a.key() == body_b.key():
        return ClassifyResult("duplicate", "R-A", 0, 0, {"reason": "identical_canonical_key"})
    status, ev = _compare(body_a, body_b, core, cache, budget, early_exit_on_diff=True)
    label = {"equal": "duplicate", "differ": "distinct"}.get(status, "ambiguous")
    return ClassifyResult(label, "R-A", budget.pair_used - start, 0, ev)


def classify_r_b(body_a, body_b, *, core, cache=None, budget=None, **_):
    assert cache is not None and budget is not None
    start = budget.pair_used
    if body_a.key() == body_b.key():
        return ClassifyResult("duplicate", "R-B", 0, 0, {"reason": "identical_canonical_key"})
    fam_order, fam_ctx = [], {}
    for cid, fam, prompt in core:
        if fam not in fam_ctx:
            fam_order.append(fam)
            fam_ctx[fam] = []
        fam_ctx[fam].append((cid, fam, prompt))
    by_fam = {}
    per = []

    def fam_status(fam):
        vals = by_fam.get(fam) or []
        if not vals:
            return "UNKNOWN"
        if any(v == "UNKNOWN" for v in vals):
            return "UNKNOWN"
        if all(v is True for v in vals):
            return "AGREE"
        if any(v is False for v in vals):
            return "DISAGREE"
        return "UNKNOWN"

    for fam in fam_order:
        for cid, f, prompt in fam_ctx[fam]:
            ga, ea = cache.get(prompt, body_a, budget)
            if ea == "BUDGET" or budget.exhausted_pair or budget.exhausted_global:
                flags = {ff: fam_status(ff) for ff in RB_AGREE_FAMILIES}
                if any(flags[ff] == "DISAGREE" for ff in RB_AGREE_FAMILIES):
                    return ClassifyResult("distinct", "R-B", budget.pair_used - start, 0, {"family_status": flags, "contexts": per})
                return ClassifyResult("ambiguous", "R-B", budget.pair_used - start, 0, {"contexts": per, "stop": cid})
            gb, eb = cache.get(prompt, body_b, budget)
            if eb == "BUDGET" or budget.exhausted_pair or budget.exhausted_global:
                flags = {ff: fam_status(ff) for ff in RB_AGREE_FAMILIES}
                if any(flags[ff] == "DISAGREE" for ff in RB_AGREE_FAMILIES):
                    return ClassifyResult("distinct", "R-B", budget.pair_used - start, 0, {"family_status": flags, "contexts": per})
                return ClassifyResult("ambiguous", "R-B", budget.pair_used - start, 0, {"contexts": per, "stop": cid})
            if ea or eb or ga is None or gb is None:
                by_fam.setdefault(f, []).append("UNKNOWN")
                per.append({"context_id": cid, "family": f, "equal": "UNKNOWN"})
            else:
                eq = ga == gb
                by_fam.setdefault(f, []).append(eq)
                per.append({"context_id": cid, "family": f, "equal": eq})
        if fam_status(fam) == "DISAGREE":
            flags = {ff: fam_status(ff) for ff in RB_AGREE_FAMILIES}
            return ClassifyResult(
                "distinct", "R-B", budget.pair_used - start, 0,
                {"family_status": {IDENTITY_FAMILY: fam_status(IDENTITY_FAMILY), **flags},
                 "early_family": fam, "contexts": per},
            )

    id_st = fam_status(IDENTITY_FAMILY)
    flags = {f: fam_status(f) for f in RB_AGREE_FAMILIES}
    n_agree = sum(1 for f in RB_AGREE_FAMILIES if flags[f] == "AGREE")
    n_disagree = sum(1 for f in RB_AGREE_FAMILIES if flags[f] == "DISAGREE")
    if n_disagree >= 1:
        label = "distinct"
    elif id_st == "AGREE" and n_agree >= RB_MIN_AGREE_FAMILIES and n_disagree == 0:
        label = "duplicate"
    else:
        label = "ambiguous"
    return ClassifyResult(
        label, "R-B", budget.pair_used - start, 0,
        {"family_status": {IDENTITY_FAMILY: id_st, **flags}, "n_agree": n_agree, "contexts": per},
    )


def classify_r_c(body_a, body_b, *, identity=IDENTITY_DEFAULT, core=None, reserve=None, cache=None, budget=None, **_):
    assert cache is not None and budget is not None and core is not None and reserve is not None
    start = budget.pair_used
    exp0 = budget.expansion_used
    if body_a.key() == body_b.key():
        return ClassifyResult("duplicate", "R-C", 0, 0, {"reason": "identical_canonical_key"})
    ga, ea = cache.get(identity, body_a, budget)
    gb, eb = cache.get(identity, body_b, budget)
    if ea == "BUDGET" or eb == "BUDGET":
        return ClassifyResult("ambiguous", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "identity_budget"})
    if ea or eb or ga is None or gb is None:
        return ClassifyResult("distinct", "R-C", budget.pair_used - start, 0, {"stage": "identity_error"})
    if ga != gb:
        return ClassifyResult("distinct", "R-C", budget.pair_used - start, 0, {"stage": "identity_differ"})
    core_by_id = {c[0]: c for c in core}
    p0 = [core_by_id[i] for i in RC_PROBE_P0]
    status, ev = _compare(body_a, body_b, p0, cache, budget, early_exit_on_diff=True)
    if status == "differ":
        return ClassifyResult("distinct", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "P0", **ev})
    if status != "equal":
        return ClassifyResult("ambiguous", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "P0", **ev})
    for cid, fam, prompt in reserve:
        ga, ea = cache.get(prompt, body_a, budget, expansion=True)
        if ea == "BUDGET" or budget.exhausted_pair or budget.exhausted_global:
            return ClassifyResult("ambiguous", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "reserve_budget", "stop": cid})
        gb, eb = cache.get(prompt, body_b, budget, expansion=True)
        if eb == "BUDGET" or budget.exhausted_pair or budget.exhausted_global:
            return ClassifyResult("ambiguous", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "reserve_budget", "stop": cid})
        if ea or eb or ga is None or gb is None:
            return ClassifyResult("ambiguous", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "reserve_error", "stop": cid})
        if ga != gb:
            return ClassifyResult("distinct", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "reserve_differ", "stop": cid})
    return ClassifyResult("duplicate", "R-C", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "reserve_exhausted_equal"})


def classify_r_d(body_a, body_b, *, identity=IDENTITY_DEFAULT, core=None, cache=None, budget=None, **_):
    assert cache is not None and budget is not None and core is not None
    start = budget.pair_used
    exp0 = budget.expansion_used
    if body_a.key() == body_b.key():
        return ClassifyResult("duplicate", "R-D", 0, 0, {"reason": "identical_canonical_key"})
    ga, ea = cache.get(identity, body_a, budget)
    gb, eb = cache.get(identity, body_b, budget)
    if ea == "BUDGET" or eb == "BUDGET":
        return ClassifyResult("ambiguous", "R-D", budget.pair_used - start, 0, {"stage": "identity_budget"})
    if ea or eb or ga is None or gb is None:
        return ClassifyResult("distinct", "R-D", budget.pair_used - start, 0, {"stage": "identity_error"})
    if ga != gb:
        return ClassifyResult("distinct", "R-D", budget.pair_used - start, 0, {"stage": "identity_differ"})
    semantic = [c for c in core if c[1] in RD_SEMANTIC_FAMILIES]
    status, ev = _compare(body_a, body_b, semantic, cache, budget, expansion=True, early_exit_on_diff=True)
    label = {"equal": "duplicate", "differ": "distinct"}.get(status, "ambiguous")
    return ClassifyResult(label, "R-D", budget.pair_used - start, budget.expansion_used - exp0, {"stage": "semantic", **ev})


CLASSIFIERS = {
    "BASELINE": classify_baseline,
    "R-A": classify_r_a,
    "R-B": classify_r_b,
    "R-C": classify_r_c,
    "R-D": classify_r_d,
}
