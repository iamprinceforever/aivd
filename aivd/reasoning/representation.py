"""Representation sufficiency → info-acquisition experiments (3.16).

If state cannot distinguish hypotheses, seek information — not more random
ACTION_STEMS×residual spam.
"""
from __future__ import annotations

from typing import Any

from aivd.invention.intervention_space import Intervention, InterventionOp


def representation_sufficient(
    *,
    hypotheses: list[dict[str, Any]] | None,
    residual_features: dict[str, float] | None,
    n_distinct_effects: int = 0,
    n_regions: int = 0,
) -> dict[str, Any]:
    """Return whether current state can discriminate open hypotheses."""
    hyps = [h for h in (hypotheses or []) if h.get("state") in ("open", "active", None)]
    feats = residual_features or {}
    # Insufficient if multiple open hyps but flat effects / few features
    ok = True
    reasons: list[str] = []
    if len(hyps) >= 2 and n_distinct_effects <= 1:
        ok = False
        reasons.append("competing_hyps_but_effects_unseparated")
    if len(hyps) >= 1 and len(feats) < 2 and n_regions <= 1:
        ok = False
        reasons.append("sparse_features_for_hypotheses")
    if not feats and n_regions == 0:
        ok = False
        reasons.append("empty_representation")
    return {"sufficient": ok, "reasons": reasons, "n_open_hyps": len(hyps), "n_features": len(feats)}


def _tok_inv(token: str) -> Intervention:
    ops = [InterventionOp(kind="insert", token=token)]
    inv = Intervention(ops=ops, sequence=[token], strategy="info_acquisition")
    inv.meta = {"info_acquisition": True, "abstract_op": "probe_token", "why": "info_acquisition"}
    return inv


def info_acquisition_candidates(
    residual_context: dict[str, Any] | None,
    *,
    observation_tokens: list[str] | None = None,
    max_new: int = 8,
) -> list[Intervention]:
    """Generate probes that acquire representation — residual parts, observed toks.

    General: harvest tokens from residual error text and prior observations.
    Does NOT inject holdout-specific vocabularies.
    """
    ctx = residual_context or {}
    toks: list[str] = []
    for key in ("error", "error_text", "residual_text"):
        val = ctx.get(key)
        if val:
            # split on non-alnum
            import re
            toks.extend(re.findall(r"[A-Za-z]{3,}", str(val)))
    for ch in list(ctx.get("residual_channels") or []) + list(ctx.get("security_shaped_residuals") or []):
        import re
        toks.extend(re.findall(r"[A-Za-z]{3,}", str(ch)))
    for t in observation_tokens or []:
        if t and len(t) >= 3:
            toks.append(str(t))

    # Unique, lower, drop ultra-common stop-ish
    stop = {"the", "and", "for", "with", "from", "this", "that", "error", "metric", "authorized", "research"}
    seen: set[str] = set()
    ordered: list[str] = []
    for t in toks:
        tl = t.lower()
        if tl in stop or tl in seen:
            continue
        seen.add(tl)
        ordered.append(tl)

    out: list[Intervention] = []
    # Single residual tokens
    for t in ordered[: max_new // 2 + 1]:
        inv = _tok_inv(t)
        inv.meta["why"] = f"I seek info: probe residual/obs token '{t}' to enrich representation"
        out.append(inv)
    # Pair consecutive residual fragments (structure, not ACTION_STEMS)
    for i in range(len(ordered) - 1):
        if len(out) >= max_new:
            break
        a, b = ordered[i], ordered[i + 1]
        for form in (f"{a}-{b}", f"{b}-{a}"):
            if len(out) >= max_new:
                break
            inv = _tok_inv(form)
            inv.meta["why"] = f"I seek info: residual-internal compound '{form}'"
            inv.meta["abstract_op"] = "pair"
            out.append(inv)
    return out[:max_new]


__all__ = ["representation_sufficient", "info_acquisition_candidates"]
