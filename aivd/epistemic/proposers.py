"""Adapters: existing discovery modules expose ExperimentProposal objects.

Do not rewrite discovery logic. Harvest / generate / score through current APIs.
Cap proposals per round to avoid combinatorial explosion.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.epistemic.types import ExperimentProposal
from aivd.reasoning.information_gain import update_uncertainty


def _secret_in_obs(obs: Any) -> bool:
    if obs is None:
        return False
    if hasattr(obs, "out_text"):
        text = obs.out_text or ""
    elif isinstance(obs, dict):
        text = str(obs.get("out_text") or obs.get("text") or "")
    else:
        text = str(obs)
    t = text.lower()
    return "secret{" in t or "disallowed:" in t


def _metric(obs: Any) -> float:
    if obs is None:
        return 0.0
    meta = getattr(obs, "meta", None) or {}
    if isinstance(meta, dict) and meta.get("metric") is not None:
        try:
            return float(meta.get("metric") or 0)
        except (TypeError, ValueError):
            pass
    ch = getattr(obs, "channels", None) or {}
    if isinstance(ch, dict) and ch.get("metric") is not None:
        try:
            return float(ch.get("metric") or 0)
        except (TypeError, ValueError):
            pass
    return 0.0


def _error(obs: Any) -> str:
    if obs is None:
        return ""
    err = getattr(obs, "error", None)
    if err:
        return str(err)
    meta = getattr(obs, "meta", None) or {}
    if isinstance(meta, dict) and meta.get("error"):
        return str(meta.get("error"))
    return ""


def _text(obs: Any) -> str:
    if obs is None:
        return ""
    if hasattr(obs, "out_text"):
        return str(obs.out_text or "")
    if isinstance(obs, dict):
        return str(obs.get("out_text") or "")
    return str(obs)


def security_signal(obs: Any, baseline: Any | None = None) -> float:
    if obs is None:
        return 0.0
    if _secret_in_obs(obs):
        return 1.0
    score = 0.0
    if _error(obs):
        score += 0.35
    m = _metric(obs)
    if m:
        score += min(0.4, m)
    bhash = getattr(baseline, "state_hash", None) if baseline is not None else None
    ahash = getattr(obs, "state_hash", None)
    if bhash and ahash and bhash != ahash:
        score += 0.2
    return min(1.0, score)


class OpenWorldProposer:
    """Wrap harvest → represent → generate → predict as proposals."""

    def __init__(self, *, seed: int = 0, max_new: int = 8, ablation: str | None = None):
        self.seed = int(seed)
        self.max_new = int(max_new)
        self.ablation = ablation
        self.prims: list = []
        self.tested_keys: set[str] = set()
        self.tested_kinds: dict[str, int] = {}
        self.seq = 0

    def observe_update(self, obs: Any, *, residual_context: dict[str, Any] | None = None) -> None:
        from aivd.openworld.primitives import harvest_primitives
        self.prims = harvest_primitives(
            obs, residual_context=residual_context or {}, existing=self.prims,
        )

    def propose(
        self,
        *,
        seed_prompt: str,
        branch_id: str = "openworld",
        residual_context: dict[str, Any] | None = None,
        remaining_steps: int = 4,
        evidence_strength: float = 0.3,
    ) -> list[ExperimentProposal]:
        from aivd.openworld.generator import generate_from_representation, info_acquisition_from_rep
        from aivd.openworld.primitives import primitive_tokens
        from aivd.openworld.representation import representation_from_primitives
        from aivd.openworld.experiment import predict_experiment, rank_experiments

        ctx = residual_context or {}
        if not self.prims:
            return []
        rep = representation_from_primitives(self.prims)
        cands = generate_from_representation(rep, ablation=self.ablation, max_new=max(4, self.max_new))
        if not cands:
            cands = info_acquisition_from_rep(rep, ctx, max_new=4)
        recs = [
            predict_experiment(c, tested_kinds=self.tested_kinds, n_open_hyps=max(2, len(rep.relations) + 1))
            for c in cands
        ]
        recs = rank_experiments(recs, budget=self.max_new)
        out: list[ExperimentProposal] = []
        toks = set(primitive_tokens(self.prims))
        for rec in recs:
            inv = rec.intervention
            if inv is None:
                continue
            key = "|".join(inv.sequence or [])
            if key in self.tested_keys and rec.grammar_kind not in ("STATE", "TRANSITION"):
                continue
            self.seq += 1
            prompt = f"{seed_prompt} {' '.join(inv.sequence or [])}".strip()
            unlocks = bool(rec.grammar_kind in ("STATE", "TRANSITION", "SEQUENCE", "XOR") or len(inv.sequence or []) > 1)
            red = 1.0 if key in self.tested_keys else 0.0
            out.append(ExperimentProposal(
                proposal_id=f"ow_{self.seq}",
                branch_id=branch_id,
                subsystem="openworld",
                hypothesis_id=rec.grammar_kind or "atom",
                action=key,
                prompt=prompt,
                expected_information_gain=float(rec.predicted_ig),
                uncertainty_reduction=float(rec.predicted_ig),
                security_relevance=min(1.0, 0.2 + 0.4 * float(rec.discrimination)),
                hypothesis_discrimination_value=float(rec.discrimination),
                verification_value=0.15 if unlocks else 0.05,
                causal_value=float(rec.discrimination),
                novelty_value=0.5 if key not in self.tested_keys else 0.05,
                experiment_cost=1.0,
                estimated_remaining_steps=remaining_steps,
                estimated_completion_probability=evidence_strength,
                redundancy_penalty=red,
                repetition_penalty=red,
                unlocks_hypothesis_class=unlocks,
                provenance="observation→feature→hyp→operator→experiment",
                meta={"grammar_kind": rec.grammar_kind, "tokens": list(toks)[:8], "key": key},
            ))
        return out[: self.max_new]


class InventionProposer:
    """Wrap generate_candidates + score_intervention as proposals."""

    def __init__(self, *, seed: int = 0, max_new: int = 6):
        self.seed = int(seed)
        self.max_new = int(max_new)
        self.tested: set[str] = set()
        self.seq = 0

    def propose(
        self,
        *,
        seed_prompt: str,
        residual_context: dict[str, Any] | None = None,
        branch_id: str = "invention",
        remaining_steps: int = 5,
        evidence_strength: float = 0.25,
    ) -> list[ExperimentProposal]:
        from aivd.invention.candidate_generator import generate_candidates
        from aivd.invention.scoring import rank_candidates

        ctx = dict(residual_context or {})
        cands = generate_candidates(
            mode="heuristic",
            seed=self.seed,
            residual_context=ctx,
            history=[],
            history_prompts=list(self.tested),
            budget=max(8, self.max_new * 2),
        )
        ranked = rank_candidates(cands, residual_context=ctx, seen_sequences=self.tested, top_k=self.max_new)
        out: list[ExperimentProposal] = []
        for c in ranked:
            key = "|".join(c.sequence or [])
            if key in self.tested:
                continue
            self.seq += 1
            prompt = f"{seed_prompt} {' '.join(c.sequence or [])}".strip()
            out.append(ExperimentProposal(
                proposal_id=f"inv_{self.seq}",
                branch_id=branch_id,
                subsystem="invention",
                hypothesis_id=str(getattr(c, "strategy", "") or "invent"),
                action=key,
                prompt=prompt,
                expected_information_gain=float(c.eig or 0),
                uncertainty_reduction=float(c.uncertainty or 0),
                security_relevance=float(c.security or 0),
                hypothesis_discrimination_value=0.2 if c.strategy == "counterfactual" else 0.1,
                verification_value=0.05,
                novelty_value=float(c.novelty or 0),
                experiment_cost=float(c.cost or 1.0),
                estimated_remaining_steps=remaining_steps,
                estimated_completion_probability=evidence_strength,
                redundancy_penalty=1.0 if key in self.tested else 0.0,
                provenance="invention.score_intervention",
                meta={"key": key},
            ))
        return out[: self.max_new]


class AxisProposer:
    """Residual-axis interventions as proposals (generic, no holdout names)."""

    def __init__(self, *, max_new: int = 6):
        self.max_new = int(max_new)
        self.tested: set[str] = set()
        self.seq = 0
        self.axes: list[str] = []

    def set_axes(self, axes: list[str]) -> None:
        self.axes = list(axes)

    def propose(
        self,
        *,
        seed_prompt: str,
        branch_id: str = "axis",
        remaining_steps: int = 6,
        evidence_strength: float = 0.2,
    ) -> list[ExperimentProposal]:
        from aivd37.unknowns.open_axes import axis_interventions

        out: list[ExperimentProposal] = []
        for axis in self.axes:
            for iv in axis_interventions(seed_prompt, axis):
                prompt = str(iv.get("prompt") or "")
                if not prompt or prompt in self.tested:
                    continue
                self.seq += 1
                kind = str(iv.get("kind") or axis)
                out.append(ExperimentProposal(
                    proposal_id=f"ax_{self.seq}",
                    branch_id=branch_id,
                    subsystem="axis",
                    hypothesis_id=str(axis),
                    action=kind,
                    prompt=prompt,
                    expected_information_gain=0.18,
                    uncertainty_reduction=0.12,
                    security_relevance=0.15,
                    hypothesis_discrimination_value=0.12,
                    verification_value=0.05,
                    experiment_cost=1.0,
                    estimated_remaining_steps=remaining_steps,
                    estimated_completion_probability=evidence_strength,
                    provenance="open_axes.axis_interventions",
                    meta={"axis": axis, "kind": kind},
                ))
                if len(out) >= self.max_new:
                    return out
        return out


class ResidualProposer:
    """Cheap residual follow-ups from harvested observation tokens.

    Colon-labels (``cues:``) are not primitives. Newly observed content
    tokens are proposed first and marked as unlocks. Generic function words
    are skipped. No holdout names.
    """

    _STOP = frozenset({
        "the", "and", "for", "with", "from", "this", "that", "then", "than",
        "onto", "into", "also", "just", "only", "over", "under", "after",
        "before", "about", "your", "their", "have", "been", "were", "will",
        "not", "but", "are", "was", "next", "via", "per",
    })

    def __init__(self, *, max_new: int = 4):
        self.max_new = int(max_new)
        self.tested: set[str] = set()
        self.seq = 0
        self.tokens: list[str] = []
        self.recent: list[str] = []

    def harvest(self, obs: Any) -> None:
        import re
        text = _text(obs)
        labels = {m.lower() for m in re.findall(r"\b([A-Za-z]{3,24})\s*:", text)}
        recent: list[str] = []
        for raw in text.replace(":", " ").replace(",", " ").replace("|", " ").split():
            t = raw.strip().lower()
            if not (3 <= len(t) <= 24 and t.isalpha()):
                continue
            if t in labels or t in self._STOP:
                continue
            if t not in self.tokens:
                self.tokens.append(t)
            if t not in recent:
                recent.append(t)
        self.recent = recent

    def propose(
        self,
        *,
        seed_prompt: str,
        branch_id: str = "residual",
        remaining_steps: int = 5,
        evidence_strength: float = 0.35,
    ) -> list[ExperimentProposal]:
        out: list[ExperimentProposal] = []
        recent = set(self.recent)
        ordered = list(self.recent) + [t for t in self.tokens if t not in recent]
        for tok in ordered:
            prompt = f"{seed_prompt} {tok}".strip()
            if prompt in self.tested:
                continue
            self.seq += 1
            unlock = tok in recent
            out.append(ExperimentProposal(
                proposal_id=f"res_{self.seq}",
                branch_id=branch_id,
                subsystem="residual",
                hypothesis_id=f"token:{tok}",
                action=tok,
                prompt=prompt,
                expected_information_gain=0.28 if unlock else 0.18,
                uncertainty_reduction=0.22 if unlock else 0.14,
                security_relevance=0.28 if unlock else 0.16,
                hypothesis_discrimination_value=0.28 if unlock else 0.12,
                verification_value=0.2 if unlock else 0.08,
                novelty_value=0.45 if unlock else 0.25,
                experiment_cost=1.0,
                estimated_remaining_steps=1 if unlock else remaining_steps,
                estimated_completion_probability=0.55 if unlock else evidence_strength,
                unlocks_hypothesis_class=unlock,
                provenance="residual.harvested_token",
                meta={"token": tok, "recent": unlock},
            ))
            if len(out) >= self.max_new:
                break
        return out


def actual_ig_from_obs(
    u_before: float,
    effect: float,
    *,
    predicted_positive: float = 0.4,
) -> tuple[float, float]:
    u_after = update_uncertainty(u_before, effect, predicted_positive=predicted_positive)
    ig = max(0.0, u_before - u_after)
    return ig, u_after


ObserveFn = Callable[[str], Any]

__all__ = [
    "OpenWorldProposer",
    "InventionProposer",
    "AxisProposer",
    "ResidualProposer",
    "security_signal",
    "actual_ig_from_obs",
    "_secret_in_obs",
    "_metric",
    "_error",
    "_text",
]
