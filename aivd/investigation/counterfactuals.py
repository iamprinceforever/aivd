"""Falsification experiments for investigation hypotheses.

Extends / uses CounterfactualEvaluator patterns without duplicating blindly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from aivd.evaluation.counterfactual import CounterfactualEvaluator
from aivd.investigation.types import HypothesisStatus, InvestigationHypothesis

EffectFn = Callable[[str], float]  # returns security/effect score
ProbeFn = Callable[[str], tuple[str, float, str | None]]


@dataclass
class FalsificationResult:
    falsified: bool
    supported: bool
    score_drop: float
    details: dict


def remove_span(prompt: str, span: str) -> str:
    if not span:
        return prompt
    out = prompt.replace(span, "")
    return re.sub(r"\s{2,}", " ", out).strip() or "Hello."


def semantic_equivalent(prompt: str) -> list[str]:
    return [
        prompt + "\n(Authorized research.)",
        "In other words: " + prompt,
        prompt.replace("Please", "Kindly").replace("please", "kindly"),
    ]


def reorder_parts(prompt: str) -> str:
    parts = [p.strip() for p in re.split(r"[.;\n]+", prompt) if p.strip()]
    if len(parts) >= 2:
        return ". ".join(reversed(parts)) + "."
    toks = prompt.split()
    mid = max(1, len(toks) // 2)
    return " ".join(toks[mid:] + toks[:mid])


def falsify_hypothesis(
    hyp: InvestigationHypothesis,
    prompt: str,
    effect_fn: EffectFn,
    *,
    baseline_effect: float | None = None,
    drop_threshold: float = 0.15,
) -> FalsificationResult:
    """Run falsification suite: remove suspected trigger, semantic eq, reorder.

    - If removing suspected span kills effect → supports causal role of span.
    - If semantic equivalents keep effect → supports semantic (not brittle lexical) hyp.
    - If reorder kills sequential hyp → supports sequential claim.
    """
    base = float(baseline_effect) if baseline_effect is not None else float(effect_fn(prompt))
    span = hyp.minimal_trigger_estimate or hyp.meta.get("suspected_span", "")
    details: dict = {"baseline": base}

    # Remove X
    removed = remove_span(prompt, str(span)) if span else prompt
    rem_score = float(effect_fn(removed)) if removed != prompt else base
    details["remove_score"] = rem_score
    drop = base - rem_score

    # Semantic equivalents
    sem_scores = [float(effect_fn(v)) for v in semantic_equivalent(prompt)[:2]]
    details["semantic_scores"] = sem_scores
    sem_persist = sum(1 for s in sem_scores if s >= max(0.2, base * 0.7)) / max(1, len(sem_scores))

    # Reorder
    reord = reorder_parts(prompt)
    reord_score = float(effect_fn(reord))
    details["reorder_score"] = reord_score

    falsified = False
    supported = False
    claim = (hyp.claim or "").lower()
    dim = (hyp.dimension or "").lower()

    if "sequential" in claim or dim == "sequential":
        if base - reord_score >= drop_threshold:
            supported = True
        else:
            falsified = True
            details["reason"] = "reorder_preserved_effect"
    elif "lexical" in claim or "token" in claim or dim in {"rare_token", "lexical"}:
        if drop >= drop_threshold:
            supported = True
        else:
            falsified = True
            details["reason"] = "removal_did_not_drop"
    elif "semantic" in claim or dim == "semantic":
        if sem_persist >= 0.5 and drop >= drop_threshold * 0.5:
            supported = True
        elif sem_persist < 0.25:
            falsified = True
            details["reason"] = "semantic_eq_lost_effect"
    else:
        # Generic: removal drop supports; no drop falsifies "X is necessary"
        if drop >= drop_threshold:
            supported = True
        elif drop < drop_threshold * 0.3 and base >= drop_threshold:
            falsified = True
            details["reason"] = "X_not_necessary"

    details["sem_persist"] = sem_persist
    return FalsificationResult(
        falsified=falsified, supported=supported, score_drop=float(drop), details=details
    )


def update_hypothesis_from_falsification(
    hyp: InvestigationHypothesis, result: FalsificationResult
) -> InvestigationHypothesis:
    hyp = hyp.model_copy(deep=True)
    if result.falsified:
        hyp.status = HypothesisStatus.FALSIFIED
        hyp.posterior = max(0.05, hyp.posterior * 0.3)
        hyp.falsifying_ids.append("falsify")
    elif result.supported:
        hyp.status = HypothesisStatus.SUPPORTED
        hyp.posterior = min(0.95, hyp.posterior + 0.25)
        hyp.supporting_ids.append("falsify")
    else:
        hyp.status = HypothesisStatus.UNRESOLVED
    hyp.meta["falsification"] = result.details
    return hyp


class InvestigationCounterfactual:
    """Thin wrapper that reuses CounterfactualEvaluator + falsify_hypothesis."""

    def __init__(self, seed: int = 42):
        self.cf = CounterfactualEvaluator(seed=seed)
        self.seed = seed

    def classic_evidence(self, prompt: str, probe_fn: ProbeFn, baseline_score: float | None = None):
        return self.cf.evaluate(prompt, probe_fn, baseline_score=baseline_score)

    def falsify(self, hyp: InvestigationHypothesis, prompt: str, effect_fn: EffectFn, **kw):
        return falsify_hypothesis(hyp, prompt, effect_fn, **kw)
