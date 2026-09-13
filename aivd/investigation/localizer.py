"""Budget-aware trigger localization (binary / greedy / delta-debug style)."""
from __future__ import annotations

from typing import Callable

EffectFn = Callable[[str], float]  # prompt -> effect magnitude / security score


def _tokens(prompt: str) -> list[str]:
    return prompt.split()


def _join(toks: list[str]) -> str:
    return " ".join(toks).strip() or "Hello."


def binary_decompose(
    prompt: str,
    effect_fn: EffectFn,
    *,
    baseline: float = 0.0,
    threshold: float = 0.15,
    budget: int = 16,
) -> tuple[str, int, list[str]]:
    """Binary decomposition: keep the half that preserves effect.

    Returns (minimal_estimate, experiments_used, trace).
    NEVER explodes combinatorially — O(log n) probes.
    """
    toks = _tokens(prompt)
    if len(toks) <= 1:
        return prompt, 0, []
    used = 0
    trace: list[str] = []
    cur = toks
    while len(cur) > 1 and used < budget:
        mid = len(cur) // 2
        left, right = cur[:mid], cur[mid:]
        # Prefer testing the smaller side first when sizes differ
        candidates = [left, right]
        kept = None
        for cand in candidates:
            if used >= budget:
                break
            p = _join(cand)
            used += 1
            score = float(effect_fn(p))
            trace.append(f"bin:{p[:60]}→{score:.2f}")
            if score - baseline >= threshold:
                kept = cand
                break
        if kept is None:
            # Neither half alone sufficient — try one-token greedy shrink from ends
            break
        cur = kept
    return _join(cur), used, trace


def greedy_eliminate(
    prompt: str,
    effect_fn: EffectFn,
    *,
    baseline: float = 0.0,
    threshold: float = 0.15,
    budget: int = 24,
) -> tuple[str, int, list[str]]:
    """Greedy elimination: drop tokens that are not necessary for the effect."""
    toks = _tokens(prompt)
    used = 0
    trace: list[str] = []
    if not toks:
        return prompt, 0, []
    # Confirm full prompt has effect
    full = float(effect_fn(prompt))
    used += 1
    if full - baseline < threshold:
        return prompt, used, [f"no_effect:{full:.2f}"]

    necessary = list(toks)
    i = 0
    while i < len(necessary) and used < budget:
        trial = necessary[:i] + necessary[i + 1 :]
        if not trial:
            break
        p = _join(trial)
        used += 1
        score = float(effect_fn(p))
        trace.append(f"drop:{necessary[i]}→{score:.2f}")
        if score - baseline >= threshold:
            necessary = trial
            # do not increment i — next token shifted into position i
        else:
            i += 1
    return _join(necessary), used, trace


def delta_debug_minimize(
    prompt: str,
    effect_fn: EffectFn,
    *,
    baseline: float = 0.0,
    threshold: float = 0.15,
    budget: int = 32,
) -> tuple[str, int, dict]:
    """Delta-debugging style minimization with hard budget cap.

    Combines binary decompose then greedy eliminate. Total probes ≤ budget.
    """
    remaining = max(1, budget)
    est, u1, t1 = binary_decompose(
        prompt, effect_fn, baseline=baseline, threshold=threshold, budget=max(1, remaining // 2)
    )
    remaining -= u1
    est2, u2, t2 = greedy_eliminate(
        est, effect_fn, baseline=baseline, threshold=threshold, budget=max(1, remaining)
    )
    used = u1 + u2
    return est2, used, {"binary_trace": t1, "greedy_trace": t2, "experiments": used}


def localize_minimal_trigger(
    prompt: str,
    effect_fn: EffectFn,
    *,
    baseline: float = 0.0,
    threshold: float = 0.15,
    budget: int = 24,
) -> tuple[str, int, dict]:
    """Public API: return minimal sufficient trigger estimate under budget."""
    return delta_debug_minimize(
        prompt, effect_fn, baseline=baseline, threshold=threshold, budget=budget
    )


def localize_with_transforms(
    prompt: str,
    effect_fn: EffectFn,
    *,
    baseline: float = 0.0,
    threshold: float = 0.15,
    budget: int = 24,
) -> tuple[str, int, dict]:
    """Localization that first tries encoding/semantic decode hints, then delta-debug.

    Improves encoding-heavy triggers (e.g. IB-F) where token splits destroy base64.
    """
    from aivd.investigation.equivalence import EncodingTransform

    used = 0
    meta: dict = {"path": [], "encoding_candidates": []}
    remaining = max(1, budget)

    # 1) If prompt contains decodable base64, test decoded plaintext as candidate
    decoded = EncodingTransform.try_decode_spans(prompt)
    best = prompt
    best_score = None
    for dec in decoded[:3]:
        if used >= remaining:
            break
        # Test decoded alone
        used += 1
        s = float(effect_fn(dec))
        meta["encoding_candidates"].append({"decoded": dec[:80], "score": s})
        meta["path"].append(f"enc_decode:{dec[:40]}→{s:.2f}")
        if s - baseline >= threshold:
            best = dec
            best_score = s
            # Also try keeping only the b64 token from original
            break
        # Test original with decoded appended (representation switch)
        if used < remaining:
            used += 1
            combo = f"{prompt}\nplaintext:{dec}"
            s2 = float(effect_fn(combo))
            meta["path"].append(f"enc_combo→{s2:.2f}")
            if s2 - baseline >= threshold and (best_score is None or s2 >= best_score):
                best = dec
                best_score = s2

    # If encoding decode already yields a short effective trigger, return it
    if best_score is not None and best != prompt and len(best.split()) <= max(4, len(prompt.split()) // 2):
        meta["experiments"] = used
        meta["method"] = "encoding_decode"
        return best, used, meta

    # 2) Prefer isolating base64 token via greedy on whitespace but protect b64 spans
    protected = prompt
    b64_toks = [t for t in prompt.split() if _is_b64_token(t)]
    if b64_toks and used < remaining:
        tok = max(b64_toks, key=len)
        used += 1
        s = float(effect_fn(tok))
        meta["path"].append(f"b64_tok:{tok[:40]}→{s:.2f}")
        if s - baseline >= threshold:
            meta["experiments"] = used
            meta["method"] = "b64_token"
            return tok, used, meta
        # Try decode-and-follow wrapper alone
        wrapped = f"Please decode and follow: {tok}"
        if used < remaining:
            used += 1
            s = float(effect_fn(wrapped))
            meta["path"].append(f"b64_wrap→{s:.2f}")
            if s - baseline >= threshold:
                meta["experiments"] = used
                meta["method"] = "b64_wrap"
                # Prefer decoded plaintext if available
                dec = EncodingTransform.try_decode_spans(tok)
                return (dec[0] if dec else tok), used, meta

    # 3) Fall back to standard delta-debug on (possibly encoding-simplified) best
    rem = max(1, remaining - used)
    est, u2, meta2 = delta_debug_minimize(
        best, effect_fn, baseline=baseline, threshold=threshold, budget=rem
    )
    used += u2
    meta["dd"] = meta2
    meta["experiments"] = used
    meta["method"] = "transform+dd"
    return est, used, meta


def _is_b64_token(tok: str) -> bool:
    import re

    return bool(re.fullmatch(r"[A-Za-z0-9+/]{8,}={0,2}", tok))
