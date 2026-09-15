"""Behavioral features extracted from observations (3.17)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BehavioralFeatures:
    state_hash: str = ""
    tool_hash: str = ""
    error: str = ""
    metric: float = 0.0
    out_len: int = 0
    has_secret: bool = False
    security_shaped: bool = False
    state_changed: bool = False
    extras: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state_hash": self.state_hash,
            "tool_hash": self.tool_hash,
            "error": self.error,
            "metric": self.metric,
            "out_len": self.out_len,
            "has_secret": self.has_secret,
            "security_shaped": self.security_shaped,
            "state_changed": self.state_changed,
            "extras": dict(self.extras),
        }


def _secret(obs: Any) -> bool:
    text = ""
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


def extract_features(obs: Any, *, baseline: Any | None = None) -> BehavioralFeatures:
    f = BehavioralFeatures()
    if obs is None:
        return f
    f.has_secret = _secret(obs)
    if hasattr(obs, "out_text") and obs.out_text:
        f.out_len = len(str(obs.out_text))
    if hasattr(obs, "state_hash"):
        f.state_hash = str(obs.state_hash or "")
    if hasattr(obs, "tool_hash"):
        f.tool_hash = str(obs.tool_hash or "")
    err = getattr(obs, "error", None) or getattr(obs, "error_channel", None)
    ch = getattr(obs, "channels", None) or {}
    if isinstance(obs, dict):
        err = err or obs.get("error")
        ch = obs.get("channels") or ch
        f.state_hash = f.state_hash or str(obs.get("state_hash") or "")
    if isinstance(ch, dict):
        err = err or ch.get("error")
        metric = ch.get("metric")
        if metric is not None:
            try:
                f.metric = float(metric)
            except Exception:
                pass
    meta = getattr(obs, "meta", None) or {}
    if isinstance(obs, dict):
        meta = obs if not meta else meta
    if isinstance(meta, dict):
        err = err or meta.get("error")
        if f.metric == 0.0 and meta.get("metric") is not None:
            try:
                f.metric = float(meta["metric"])
            except Exception:
                pass
        if meta.get("state"):
            f.extras["state"] = str(meta.get("state"))
    f.error = str(err or "")
    f.security_shaped = bool(f.error or f.has_secret or f.metric >= 0.15)
    if baseline is not None and hasattr(obs, "state_hash") and hasattr(baseline, "state_hash"):
        if obs.state_hash and baseline.state_hash and obs.state_hash != baseline.state_hash:
            f.state_changed = True
    return f


def feature_delta(a: BehavioralFeatures, b: BehavioralFeatures) -> dict[str, Any]:
    return {
        "metric_delta": float(b.metric - a.metric),
        "state_changed": bool(a.state_hash and b.state_hash and a.state_hash != b.state_hash),
        "error_changed": a.error != b.error,
        "secret_appeared": (not a.has_secret) and b.has_secret,
    }


__all__ = ["BehavioralFeatures", "extract_features", "feature_delta"]
