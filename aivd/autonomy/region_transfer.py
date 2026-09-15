"""Residual→region transfer and cue-conditioned priors (3.15).

Learned from evidence: P(region|residual_features, context) ranking.
NO token→region hardcode. Priors revisable; weak cues moderate;
contradictory evidence reduces.
"""
from __future__ import annotations

import math
import re
from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState, BehavioralRegion


def extract_residual_features(residual_context: dict[str, Any] | None) -> dict[str, float]:
    """Opaque numeric features from residual context — not vocabulary maps."""
    ctx = residual_context or {}
    feats: dict[str, float] = {}
    text = str(ctx.get("error") or ctx.get("error_text") or ctx.get("residual_text") or "")
    feats["has_error"] = 1.0 if text else 0.0
    feats["error_len"] = min(1.0, len(text) / 40.0)
    feats["unexplained"] = float(ctx.get("unexplained") or 0.0)
    # Character-class stats (evidence properties, not token→region)
    lower = text.lower()
    feats["dot_density"] = min(1.0, lower.count(".") / max(1, len(lower)))
    feats["alpha_ratio"] = (
        sum(1 for c in lower if c.isalpha()) / max(1, len(lower))
    )
    feats["digit_ratio"] = (
        sum(1 for c in lower if c.isdigit()) / max(1, len(lower))
    )
    # Token-count buckets as abstract shape features
    toks = [t for t in re.split(r"[^a-zA-Z]+", lower) if len(t) >= 3]
    feats["n_tokens_norm"] = min(1.0, len(toks) / 8.0)
    feats["mean_tok_len"] = min(1.0, (sum(len(t) for t in toks) / max(1, len(toks))) / 12.0)
    # Security-shaped residual flag from upstream (generic)
    secs = ctx.get("security_shaped_residuals") or []
    feats["n_sec_channels"] = min(1.0, len(secs) / 4.0)
    return feats


def _feature_affinity(feats: dict[str, float], region: BehavioralRegion) -> float:
    """Soft affinity between residual features and region property vector."""
    if not region.properties:
        # Unvisited region: mild prior from residual strength alone
        return 0.15 + 0.25 * float(feats.get("unexplained") or 0.0)
    score = 0.0
    n = 0
    for k, v in feats.items():
        if k in region.properties:
            # Similarity: 1 - |diff|
            score += 1.0 - min(1.0, abs(float(v) - float(region.properties[k])))
            n += 1
        else:
            # Mild boost if region has related effect under residual pressure
            score += 0.05 * float(v)
            n += 1
    if n == 0:
        return 0.1
    # Blend with observed effect / inverse uncertainty
    base = score / n
    base += 0.2 * min(1.0, abs(region.effect_mean))
    base += 0.15 * (1.0 - region.uncertainty)
    return max(0.0, min(1.0, base))


def rank_regions_given_residual(
    state: AutonomousDiscoveryState,
    *,
    residual_features: dict[str, float] | None = None,
    top_k: int = 8,
) -> list[tuple[str, float]]:
    """P(region|residual_features, context)-style ranking from evidence."""
    feats = residual_features or state.residual_features or {}
    ranked: list[tuple[str, float]] = []
    for rid, region in state.regions.items():
        aff = _feature_affinity(feats, region)
        prior = float(state.region_priors.get(rid, 0.5))
        # Cue-conditioned: prior * affinity, moderated by uncertainty
        p = prior * (0.4 + 0.6 * aff)
        p *= 0.5 + 0.5 * (1.0 - region.uncertainty) if region.visit_count else 1.0
        ranked.append((rid, float(p)))
    # Also propose abstract unseen region slots from feature shape (not token names)
    if feats.get("has_error", 0) > 0 and len(ranked) < top_k:
        for slot in ("R0", "R1", "R2", "A0", "A1"):
            if slot not in state.regions:
                # Abstract slot prior from residual strength
                p = 0.2 + 0.3 * float(feats.get("unexplained") or 0.0)
                ranked.append((slot, p))
    ranked.sort(key=lambda x: -x[1])
    return ranked[:top_k]


def update_cue_conditioned_priors(
    state: AutonomousDiscoveryState,
    *,
    observed_region: str,
    effect: float,
    expected: float | None = None,
) -> dict[str, float]:
    """Revise region priors: weak cue moderate; contradictory evidence reduces."""
    rid = observed_region
    prior = float(state.region_priors.get(rid, 0.5))
    e = float(effect)
    exp = float(expected) if expected is not None else prior
    # Prediction error
    err = e - exp
    if abs(err) < 0.05:
        # Confirm softly
        prior = prior + 0.08 * (1.0 - prior)
    elif err > 0:
        # Positive surprise — strengthen
        prior = prior + 0.15 * (1.0 - prior)
    else:
        # Contradiction — reduce
        prior = prior * 0.7
    # Weak cue moderation: never jump to 0/1 in one step
    prior = max(0.05, min(0.95, prior))
    state.region_priors[rid] = prior
    # Mild competition: reduce other high priors slightly on strong evidence
    if e > 0.2:
        for other, p in list(state.region_priors.items()):
            if other != rid and p > 0.6:
                state.region_priors[other] = p * 0.92
    return dict(state.region_priors)


def seed_regions_from_individuals(
    state: AutonomousDiscoveryState,
    individuals: list[Any],
    *,
    residual_context: dict[str, Any] | None = None,
) -> list[str]:
    """Create abstract regions from intervention families (evidence properties)."""
    feats = extract_residual_features(residual_context)
    state.residual_features = feats
    created: list[str] = []
    by_fam: dict[str, list[Any]] = {}
    for inv in individuals or []:
        fam = (getattr(inv, "meta", None) or {}).get("family_id") or "unknown"
        by_fam.setdefault(str(fam), []).append(inv)
    for i, (fam, invs) in enumerate(by_fam.items()):
        # Abstract region id from family hash bucket — not token vocabulary
        rid = f"reg_{i % 8}_{len(fam) % 5}"
        props = {
            "fam_len_norm": min(1.0, len(fam) / 16.0),
            "n_members_norm": min(1.0, len(invs) / 6.0),
            **{f"r_{k}": v for k, v in list(feats.items())[:4]},
        }
        r = state.upsert_region(rid, **props)
        if fam not in r.family_ids:
            r.family_ids.append(fam)
        if rid not in state.region_priors:
            # Weak cue from residual unexplained
            state.region_priors[rid] = 0.35 + 0.2 * float(feats.get("unexplained") or 0.0)
        created.append(rid)
    state.log("ABSTRACT", n_regions=len(state.regions), n_new=len(created))
    return created


__all__ = [
    "extract_residual_features",
    "rank_regions_given_residual",
    "update_cue_conditioned_priors",
    "seed_regions_from_individuals",
]
