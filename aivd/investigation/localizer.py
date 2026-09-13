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
