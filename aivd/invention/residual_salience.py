"""Residual salience — security-shaped preferred, not equated with vulnerability.

Salience ranks residual channels for search ordering. High salience means
"worth discriminating," never "is a vuln." No Holdout-named boosts.
"""
from __future__ import annotations

from typing import Any


# Security-shaped channel prefixes / names (structural, not vuln GT)
_SECURITY_SHAPED = (
    "error",
    "state",
    "tool",
    "out.refusal",
    "refusal",
    "auth",
    "gate",
    "session",
)

# Low-salience novelty-alone channels
_LOW_SALIENT = ("out.hash", "out.len", "latency", "metric")


def _channel_name(ch: Any) -> str:
    if ch is None:
        return ""
    if isinstance(ch, str):
        return ch.lower().strip()
    if isinstance(ch, dict):
        return str(ch.get("name") or ch.get("channel") or ch.get("kind") or "").lower()
    return str(ch).lower()


def channel_salience(channel: Any) -> float:
    """Salience in [0, 1]. Security-shaped preferred; novelty-alone demoted."""
    name = _channel_name(channel)
    if not name:
        return 0.0
    for pref in _SECURITY_SHAPED:
        if name == pref or name.startswith(pref + ".") or pref in name.split("."):
            # error.* gets highest structural weight among security-shaped
            if pref == "error" or name.startswith("error"):
                return 0.95
            if pref in ("state", "tool"):
                return 0.85
            if pref in ("out.refusal", "refusal"):
                return 0.75
            return 0.70
    for low in _LOW_SALIENT:
        if name == low or name.startswith(low):
            return 0.15
    return 0.35


def residual_salience(residual_context: dict[str, Any] | None) -> dict[str, Any]:
    """Aggregate residual salience from context (not GT inspection)."""
    ctx = residual_context or {}
    channels = list(ctx.get("security_shaped_residuals") or []) + list(
        ctx.get("residual_channels") or []
    )
    # also treat error text as a synthetic error channel
    err = ctx.get("error") or ctx.get("error_text")
    if err:
        channels = ["error"] + list(channels)

    per_channel: dict[str, float] = {}
    for ch in channels:
        name = _channel_name(ch) or "unknown"
        per_channel[name] = max(per_channel.get(name, 0.0), channel_salience(ch))

    if not per_channel:
        unexplained = float(ctx.get("unexplained") or 0.0)
        aggregate = min(1.0, 0.4 * unexplained)
    else:
        aggregate = max(per_channel.values())
        # mild boost when multiple security-shaped channels disagree (discrimination value)
        if len([v for v in per_channel.values() if v >= 0.7]) >= 2:
            aggregate = min(1.0, aggregate + 0.05)

    unexplained = float(ctx.get("unexplained") or 0.0)
    return {
        "aggregate": float(aggregate),
        "per_channel": per_channel,
        "unexplained": unexplained,
        "security_shaped_preferred": aggregate >= 0.5,
        "note": "Salience ranks search priority; never equals vulnerability.",
    }


def salience_linked_stems(
    residual_context: dict[str, Any] | None,
    *,
    known_stems: list[str] | None = None,
) -> list[str]:
    """Order stems by residual-token overlap (GENERAL evidence ordering, not GT stems).

    Extracts tokens from error/residual text and ranks known stems by overlap.
    Does NOT hardcode Holdout trigger stems.
    """
    from aivd.invention.intervention_space import extract_residual_tokens, ACTION_STEMS

    ctx = residual_context or {}
    rtoks = [t.lower() for t in extract_residual_tokens(ctx) if t]
    stems = list(known_stems) if known_stems is not None else list(ACTION_STEMS)

    # Tie-break by ACTION_STEMS lexicon order (coverage), NOT alphabetical —
    # alphabetical would starve early lexicon stems (e.g. accept before ack).
    lexicon_idx = {s: i for i, s in enumerate(ACTION_STEMS)}

    def stem_score(stem: str) -> tuple:
        s = stem.lower()
        score = 0.0
        for rt in rtoks:
            if s == rt:
                score += 1.0
            elif len(s) >= 4 and (s in rt or rt in s):
                # require len>=4 to avoid spurious 3-char collisions (stage/stall)
                score += 0.6
        return (-score, lexicon_idx.get(s, 10_000), s)

    return sorted(stems, key=stem_score)
