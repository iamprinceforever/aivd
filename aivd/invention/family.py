"""Structural intervention families — derived from ops/sequence shape, not vuln categories.

Families cluster by intervention STRUCTURE (op kinds, surface form, stem bucket,
arity, strategy class). Never keyed by Holdout / vuln names.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from aivd.invention.intervention_space import Intervention

_STEM_RE = re.compile(r"[a-z]+", re.I)


def _primary_stem(sequence: list[str]) -> str:
    """First alphabetic stem of the first token (pre-hyphen / pre-suffix core)."""
    if not sequence:
        return "empty"
    tok = str(sequence[0] or "").lower().strip()
    # split hyphen/underscore compounds → first part
    part = re.split(r"[-_]", tok)[0] if tok else ""
    m = _STEM_RE.match(part) if part else None
    stem = (m.group(0) if m else part) or "empty"
    # strip common morph suffixes for bucket stability (structure, not GT)
    for suf in ("ance", "ment", "ion", "ing", "ed", "er", "al"):
        if stem.endswith(suf) and len(stem) > len(suf) + 2:
            stem = stem[: -len(suf)]
            break
    return stem[:16] or "empty"


def _surface_form(sequence: list[str], ops: list) -> str:
    """Structural surface class of the intervention."""
    if not sequence:
        return "empty"
    joined = " ".join(sequence)
    if any("-" in str(t) for t in sequence):
        return "compound_hyphen"
    if any("_" in str(t) for t in sequence):
        return "compound_underscore"
    kinds = {getattr(o, "kind", "") for o in (ops or [])}
    if "wrap" in kinds:
        return "wrap"
    if "pair" in kinds or "combine" in kinds:
        return "pair_combine"
    if "repeat" in kinds:
        return "repeat"
    if "reorder" in kinds:
        return "reorder"
    if len(sequence) >= 2:
        return "multi_token"
    # single token: morph-like if longer than common stems
    tok = str(sequence[0])
    if len(tok) >= 7 and any(tok.endswith(s) for s in ("ance", "ment", "ion", "ing")):
        return "morph"
    # concat compound heuristic (two stems jammed)
    if len(tok) >= 8 and "-" not in tok and "_" not in tok:
        return "compound_concat"
    return "primitive"


def _op_signature(ops: list) -> str:
    kinds = sorted({getattr(o, "kind", "unknown") or "unknown" for o in (ops or [])})
    return ",".join(kinds) if kinds else "none"


def _strategy_class(strategy: str) -> str:
    s = (strategy or "primitive").lower()
    if s in ("counterfactual", "primitive", "mutation", "composition",
             "novelty", "history", "random", "diversity"):
        return s
    return "other"


@dataclass
class FamilyFeatures:
    """Structural features used for family identity / clustering."""
    stem_bucket: str = "empty"
    surface: str = "primitive"
    op_signature: str = "none"
    arity: int = 0
    strategy_class: str = "primitive"
    residual_linked: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "stem_bucket": self.stem_bucket,
            "surface": self.surface,
            "op_signature": self.op_signature,
            "arity": self.arity,
            "strategy_class": self.strategy_class,
            "residual_linked": self.residual_linked,
        }

    def family_key(self, *, coarse: bool = False) -> str:
        """Stable family key. coarse=True collapses arity/strategy/compound form."""
        surface = self.surface
        if coarse:
            # Collapse compound hyphen/underscore/concat into one structural class
            if surface.startswith("compound"):
                surface = "compound"
            raw = f"{self.stem_bucket}|{surface}"
        else:
            raw = (
                f"{self.stem_bucket}|{self.surface}|{self.op_signature}|"
                f"{min(self.arity, 3)}|{self.strategy_class}"
            )
        return hashlib.sha256(raw.encode()).hexdigest()[:10]


def extract_family_features(
    inv: Intervention,
    *,
    residual_tokens: Iterable[str] | None = None,
) -> FamilyFeatures:
    """Derive structural family features from an intervention (not vuln labels)."""
    seq = list(inv.sequence or [])
    ops = list(inv.ops or [])
    rtoks = {str(t).lower() for t in (residual_tokens or []) if t}
    residual_linked = False
    if rtoks:
        blob = " ".join(seq).lower()
        residual_linked = any(rt in blob for rt in rtoks)
    return FamilyFeatures(
        stem_bucket=_primary_stem(seq),
        surface=_surface_form(seq, ops),
        op_signature=_op_signature(ops),
        arity=len(seq),
        strategy_class=_strategy_class(inv.strategy),
        residual_linked=residual_linked,
    )


def assign_family(
    inv: Intervention,
    *,
    residual_tokens: Iterable[str] | None = None,
    coarse: bool = False,
) -> str:
    """Assign / stamp family_id on intervention; return family_id."""
    feats = extract_family_features(inv, residual_tokens=residual_tokens)
    fid = feats.family_key(coarse=coarse)
    inv.meta = dict(inv.meta or {})
    inv.meta["family_id"] = fid
    inv.meta["family_features"] = feats.as_dict()
    return fid


def cluster_interventions(
    interventions: list[Intervention],
    *,
    residual_tokens: Iterable[str] | None = None,
    coarse: bool = False,
) -> dict[str, list[Intervention]]:
    """Cluster interventions into structural families."""
    buckets: dict[str, list[Intervention]] = {}
    for inv in interventions:
        fid = assign_family(inv, residual_tokens=residual_tokens, coarse=coarse)
        buckets.setdefault(fid, []).append(inv)
    return buckets


@dataclass
class FamilyBelief:
    """Posterior belief over a structural family (Beta-Bernoulli style)."""
    family_id: str
    features: dict[str, Any] = field(default_factory=dict)
    alpha: float = 1.0  # successes prior
    beta: float = 1.0   # failures prior
    n_tested: int = 0
    n_success: int = 0
    sum_effect: float = 0.0
    saturated: bool = False
    revived: bool = False
    last_evidence: str = ""

    @property
    def mean(self) -> float:
        return self.alpha / max(1e-9, self.alpha + self.beta)

    @property
    def uncertainty(self) -> float:
        """Normalized Beta variance proxy in ~[0,1]."""
        a, b = self.alpha, self.beta
        var = (a * b) / (((a + b) ** 2) * max(1e-9, a + b + 1))
        # max variance at a=b=1 is 1/12
        return float(min(1.0, var / (1.0 / 12.0)))

    def update(self, *, effect: float, success: bool, evidence: str = "") -> None:
        self.n_tested += 1
        self.sum_effect += float(effect)
        if success or effect >= 0.25:
            self.alpha += 1.0
            self.n_success += 1
        else:
            self.beta += 1.0
        if evidence:
            self.last_evidence = evidence

    def as_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "features": dict(self.features),
            "alpha": self.alpha,
            "beta": self.beta,
            "mean": self.mean,
            "uncertainty": self.uncertainty,
            "n_tested": self.n_tested,
            "n_success": self.n_success,
            "mean_effect": self.sum_effect / max(1, self.n_tested),
            "saturated": self.saturated,
            "revived": self.revived,
            "last_evidence": self.last_evidence,
        }
