"""Observation-harvested behavioral primitives with provenance (3.17).

NOT a closed ACTION_STEMS dump. Vocabulary is harvested from observations
with source/confidence/uncertainty. Randomized / anti-mapping: no fixed
holdout lexicon.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z]{3,}")

# Generic English glue — not a target-specific stop list of vuln tokens.
STOP = frozenset({
    "the", "and", "for", "with", "from", "this", "that", "error", "metric",
    "authorized", "research", "available", "operator", "operators", "family",
    "branches", "exclusive", "versus", "apply", "state", "arm", "twice",
    "order", "before", "phase", "then", "hint", "mark", "idle", "pending",
    "what", "your", "purpose", "variant", "control", "benign", "secret",
    "disallowed", "ok", "true", "false", "none", "null", "text", "channel",
    "hash", "open", "closed", "require", "requires", "xor", "aivd", "distractor",
})


@dataclass
class Primitive:
    """A harvested behavioral primitive."""
    token: str
    source: str = "observation"  # observation | residual | feature | cluster
    channel: str = ""
    confidence: float = 0.5
    uncertainty: float = 0.5
    count: int = 1
    provenance: str = ""
    role: str = "unknown"  # operator | residual | distractor | confirm | unknown

    def as_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "source": self.source,
            "channel": self.channel,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "count": self.count,
            "provenance": self.provenance,
            "role": self.role,
        }


def _iter_obs_texts(obs: Any) -> list[tuple[str, str]]:
    """(channel, text) pairs from an observation-like object."""
    out: list[tuple[str, str]] = []
    if obs is None:
        return out
    if hasattr(obs, "out_text") and obs.out_text:
        out.append(("out_text", str(obs.out_text)))
    if hasattr(obs, "error") and obs.error:
        out.append(("error", str(obs.error)))
    if hasattr(obs, "error_channel") and obs.error_channel:
        out.append(("error", str(obs.error_channel)))
    if hasattr(obs, "channels") and isinstance(obs.channels, dict):
        for k, v in obs.channels.items():
            if v is not None:
                out.append((str(k), str(v)))
    if hasattr(obs, "meta") and isinstance(obs.meta, dict):
        for k, v in obs.meta.items():
            if v is not None and k not in ("latency",):
                out.append((f"meta.{k}", str(v)))
    if isinstance(obs, dict):
        for k in ("out_text", "text", "error", "error_text", "residual_text", "state"):
            if obs.get(k):
                out.append((k, str(obs[k])))
        ch = obs.get("channels") or {}
        if isinstance(ch, dict):
            for k, v in ch.items():
                if v is not None:
                    out.append((str(k), str(v)))
    if isinstance(obs, str):
        out.append(("text", obs))
    return out


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if t]


def harvest_tokens(
    obs: Any = None,
    *,
    residual_context: dict[str, Any] | None = None,
    extra_texts: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """Return (token, channel) in first-seen order."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    blobs = list(_iter_obs_texts(obs))
    ctx = residual_context or {}
    for k in ("error", "error_text", "residual_text", "channel_value", "notes", "state"):
        if ctx.get(k):
            blobs.append((k, str(ctx[k])))
    for ch in list(ctx.get("residual_channels") or []) + list(ctx.get("security_shaped_residuals") or []):
        blobs.append(("residual", str(ch)))
    for item in extra_texts or []:
        blobs.append(item)
    for channel, text in blobs:
        for tok in tokenize(text):
            if tok in STOP or tok in seen or len(tok) < 3:
                continue
            seen.add(tok)
            pairs.append((tok, channel))
    return pairs


def harvest_primitives(
    obs: Any = None,
    *,
    residual_context: dict[str, Any] | None = None,
    extra_texts: list[tuple[str, str]] | None = None,
    existing: dict[str, Primitive] | None = None,
) -> dict[str, Primitive]:
    """Cluster harvested tokens into primitives with provenance."""
    bag = dict(existing or {})
    for tok, channel in harvest_tokens(obs, residual_context=residual_context, extra_texts=extra_texts):
        src = "residual" if channel in ("error", "error_text", "residual", "residual_text") else "observation"
        if tok in bag:
            p = bag[tok]
            p.count += 1
            p.confidence = min(0.95, p.confidence + 0.08)
            p.uncertainty = max(0.05, p.uncertainty - 0.08)
            if src == "observation" and p.source == "residual":
                p.source = "observation"
            continue
        # Distractor-ish surface: hum/buzz/glow prefixes often noncausal
        role = "unknown"
        if tok.startswith(("hum", "buzz", "glow")):
            role = "distractor"
        bag[tok] = Primitive(
            token=tok,
            source=src,
            channel=channel,
            confidence=0.55 if src == "observation" else 0.4,
            uncertainty=0.45 if src == "observation" else 0.6,
            count=1,
            provenance=f"harvested from {channel}",
            role=role,
        )
    return bag


def primitive_tokens(prims: dict[str, Primitive] | list[Primitive], *, skip_distractor: bool = True) -> list[str]:
    items = prims.values() if isinstance(prims, dict) else prims
    out: list[str] = []
    for p in items:
        if skip_distractor and p.role == "distractor":
            continue
        if p.token not in out:
            out.append(p.token)
    return out


__all__ = [
    "Primitive",
    "STOP",
    "harvest_tokens",
    "harvest_primitives",
    "primitive_tokens",
    "tokenize",
]
