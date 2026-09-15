"""Behavioral contrast vs baseline. No lexical answer extraction."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


def _text(obs: Any) -> str:
    if obs is None:
        return ""
    if hasattr(obs, "out_text"):
        return str(obs.out_text or "")
    if isinstance(obs, dict):
        return str(obs.get("out_text") or obs.get("text") or "")
    if isinstance(obs, tuple) and obs:
        return str(obs[0] or "")
    return str(obs)


def _error(obs: Any) -> str:
    if obs is None:
        return ""
    err = getattr(obs, "error", None)
    if err:
        return str(err)
    meta = getattr(obs, "meta", None) or {}
    if isinstance(meta, dict) and meta.get("error"):
        return str(meta.get("error"))
    ch = getattr(obs, "channels", None) or {}
    if isinstance(ch, dict) and ch.get("error"):
        return str(ch.get("error"))
    return ""


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


def _secret(obs: Any) -> bool:
    t = _text(obs).lower()
    return "secret{" in t or "disallowed:" in t


@dataclass
class Contrast:
    secret: bool
    metric: float
    metric_delta: float
    error: str
    error_appeared: bool
    text_changed: bool
    security_shaped: bool
    greedy_metric: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def contrast(obs: Any, baseline: Any | None = None) -> Contrast:
    m = _metric(obs)
    mb = _metric(baseline) if baseline is not None else 0.0
    err = _error(obs)
    err_b = _error(baseline) if baseline is not None else ""
    secret = _secret(obs)
    text_changed = _text(obs) != (_text(baseline) if baseline is not None else _text(obs))
    error_appeared = bool(err) and err != err_b
    security_shaped = bool(secret or error_appeared or (err and m >= 0.2))
    greedy = bool(m >= 0.55 and not secret and not error_appeared)
    return Contrast(
        secret=secret,
        metric=m,
        metric_delta=m - mb,
        error=err,
        error_appeared=error_appeared,
        text_changed=text_changed,
        security_shaped=security_shaped,
        greedy_metric=greedy,
    )


__all__ = ["Contrast", "contrast", "_text", "_error", "_metric", "_secret"]
