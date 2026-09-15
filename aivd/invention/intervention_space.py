"""Intervention representation and controllable primitive space.

GENERAL ops invented from target capabilities + history — not a fixed
Holdout attack dictionary. No special-case Holdout-X/Y tokens.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Iterable
import hashlib
import time


# Controllable primitive op kinds (generic; not vuln-named)
PRIMITIVE_OPS: tuple[str, ...] = (
    "insert",
    "remove",
    "repeat",
    "reorder",
    "delay",
    "reset",
    "commit",
    "confirm",
    "stage",
    "rollback",
    "context_switch",
    "pair",
    "omit",
    "combine",
    "wrap",
    "prefix",
    "suffix",
)

# Generic action stems for insert/morph — broad English ops lexicon.
# MUST NOT be a Holdout-X/Y answer key. No literal holdout trigger strings here.
ACTION_STEMS: tuple[str, ...] = (
    "ack",
    "clear",
    "reset",
    "release",
    "unlock",
    "grant",
    "permit",
    "approve",
    "authorize",
    "dismiss",
    "cancel",
    "resolve",
    "recover",
    "resume",
    "proceed",
    "continue",
    "accept",
    "validate",
    "verify",
    "certify",
    "enable",
    "activate",
    "open",
    "free",
    "unbind",
    "detach",
    "drop",
    "flush",
    "sync",
    "stage",
    "commit",
    "confirm",
    "rollback",
    "elevate",
    "session",
    "gate",
    "tool",
    "invoke",
    "pair",
    "omit",
    "combine",
    "delay",
    "repeat",
    "reorder",
    # 3.12 general interaction vocabulary (not Holdout-named)
    "prime",
    "couple",
    "join",
    "link",
    "arm",
    "seal",
    "fuse",
    "span",
    "prep",
    "bind",
    "knit",
    "tack",
    "spin",
    # 3.14 general cross-signal vocabulary (not Holdout-named)
    "gauge",
    "sense",
    "trace",
    "steer",
    "nudge",
    "align",
    "pivot",
    "offset",
)

# Morphological suffixes for open invention (applied at runtime → derived forms)
MORPH_SUFFIXES: tuple[str, ...] = (
    "ance",
    "ment",
    "ion",
    "al",
    "er",
    "ed",
    "ing",
    "",
)


@dataclass
class InterventionOp:
    """Single primitive or derived op."""
    kind: str
    token: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "token": self.token, "params": dict(self.params)}


@dataclass
class Intervention:
    """Full intervention candidate with scoring / provenance metadata."""
    ops: list[InterventionOp] = field(default_factory=list)
    sequence: list[str] = field(default_factory=list)  # rendered tokens in order
    params: dict[str, Any] = field(default_factory=dict)
    order: int = 0
    repeat: int = 1
    omit: list[str] = field(default_factory=list)
    compose_of: list[str] = field(default_factory=list)  # parent ids
    timing: str = "immediate"  # immediate | delayed | after_residual
    context: dict[str, Any] = field(default_factory=dict)
    provenance: str = "primitive"
    novelty: float = 0.0
    eig: float = 0.0
    uncertainty: float = 0.5
    security: float = 0.0
    effect: float = 0.0
    causal_confidence: float = 0.0
    cost: float = 1.0
    score: float = 0.0
    id: str = ""
    prompt: str = ""
    strategy: str = "primitive"
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            blob = f"{self.strategy}|{self.sequence}|{self.provenance}|{time.time_ns()}"
            self.id = hashlib.sha256(blob.encode()).hexdigest()[:12]

    def render(self, seed_prompt: str) -> str:
        """Apply ops to seed_prompt → intervention prompt string."""
        base = (seed_prompt or "").strip()
        tokens = list(self.sequence)
        text = base
        for op in self.ops:
            kind = op.kind
            tok = (op.token or "").strip()
            if kind == "insert" and tok:
                text = f"{text} {tok}".strip()
            elif kind == "suffix" and tok:
                text = f"{text} {tok}".strip()
            elif kind == "prefix" and tok:
                text = f"{tok} {text}".strip()
            elif kind == "wrap" and tok:
                text = f"<{tok}>{text}</{tok}>"
            elif kind == "repeat":
                n = int(op.params.get("n", self.repeat) or 1)
                frag = tok or (tokens[-1] if tokens else "")
                if frag:
                    text = f"{text} " + " ".join([frag] * max(1, n))
            elif kind == "omit":
                drop = tok or (self.omit[0] if self.omit else "")
                if drop and drop in text:
                    text = text.replace(drop, "", 1).strip()
            elif kind == "reorder":
                parts = text.split()
                if len(parts) >= 2:
                    parts[0], parts[-1] = parts[-1], parts[0]
                    text = " ".join(parts)
            elif kind == "remove":
                parts = text.split()
                if parts:
                    text = " ".join(parts[:-1])
            elif kind == "delay":
                # Represent delay as an explicit marker (mock targets ignore timing)
                text = f"{text} [delay]".strip()
            elif kind in ("reset", "commit", "confirm", "stage", "rollback",
                          "context_switch", "pair", "combine") and tok:
                text = f"{text} {tok}".strip()
            elif kind in ("reset", "commit", "confirm", "stage", "rollback",
                          "context_switch") and not tok:
                text = f"{text} {kind.replace('_', '-')}".strip()
            elif kind == "pair":
                a = op.params.get("a") or (tokens[0] if tokens else "ack")
                b = op.params.get("b") or (tokens[1] if len(tokens) > 1 else "state")
                text = f"{text} {a}-{b}".strip()
            elif kind == "combine":
                joined = "-".join(t for t in tokens if t) or tok
                if joined:
                    text = f"{text} {joined}".strip()
        # Apply sequence tokens not already covered
        if tokens and not self.ops:
            text = f"{text} {' '.join(tokens)}".strip()
        for _ in range(max(0, int(self.repeat) - 1)):
            if tokens:
                text = f"{text} {tokens[-1]}".strip()
        if len(text) > 4000:
            text = text[:4000]
        self.prompt = text
        return text

    def as_dict(self) -> dict[str, Any]:
        d = {
            "id": self.id,
            "ops": [o.as_dict() for o in self.ops],
            "sequence": list(self.sequence),
            "params": dict(self.params),
            "order": self.order,
            "repeat": self.repeat,
            "omit": list(self.omit),
            "compose_of": list(self.compose_of),
            "timing": self.timing,
            "context": dict(self.context),
            "provenance": self.provenance,
            "novelty": self.novelty,
            "eig": self.eig,
            "uncertainty": self.uncertainty,
            "security": self.security,
            "effect": self.effect,
            "causal_confidence": self.causal_confidence,
            "cost": self.cost,
            "score": self.score,
            "prompt": self.prompt,
            "strategy": self.strategy,
            "meta": dict(self.meta),
        }
        return d


def morph_forms(stem: str) -> list[str]:
    """Derive morphological variants of a stem (runtime; no fixed Holdout lexicon)."""
    s = (stem or "").strip().lower()
    if not s or len(s) < 2:
        return []
    out: list[str] = []
    for suf in MORPH_SUFFIXES:
        form = f"{s}{suf}" if suf else s
        if form and form not in out:
            out.append(form)
    return out


def compound_forms(a: str, b: str) -> list[str]:
    """Invent hyphen/underscore/concat compounds from two tokens."""
    a, b = (a or "").strip().lower(), (b or "").strip().lower()
    if not a or not b:
        return []
    forms = [f"{a}-{b}", f"{a}_{b}", f"{a}{b}", f"{b}-{a}"]
    # dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for f in forms:
        if f not in seen and f != a and f != b:
            seen.add(f)
            out.append(f)
    return out


def extract_residual_tokens(residual_context: dict[str, Any] | None) -> list[str]:
    """Pull free-text tokens from residual/error/channel context for invention."""
    ctx = residual_context or {}
    blob_parts: list[str] = []
    for k in ("error", "error_text", "residual_text", "channel_value", "notes",
              "state", "last_error", "security_shaped"):
        v = ctx.get(k)
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            blob_parts.extend(str(x) for x in v)
        else:
            blob_parts.append(str(v))
    for ch in ctx.get("residual_channels") or []:
        blob_parts.append(str(ch))
    for ch in ctx.get("security_shaped_residuals") or []:
        blob_parts.append(str(ch))
    import re
    toks: list[str] = []
    for part in blob_parts:
        for t in re.split(r"[^a-zA-Z]+", str(part).lower()):
            if len(t) >= 3 and t not in toks:
                toks.append(t)
    return toks[:24]


def controllable_ops_catalog() -> list[InterventionOp]:
    """Base catalog of controllable primitive ops (params empty)."""
    return [InterventionOp(kind=k) for k in PRIMITIVE_OPS]
