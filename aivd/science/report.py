"""Verified vulnerability report produced by the science loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VulnerabilityReport:
    secret_found: bool = False
    verified: bool = False
    reproduced: bool = False
    best_prompt: str | None = None
    surviving_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    falsified_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    n_hypotheses: int = 0
    n_experiments: int = 0
    entropy_final: float = 0.0
    causal_sketch: str = ""
    remaining_alternatives: list[str] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "secret_found": self.secret_found,
            "verified": self.verified,
            "reproduced": self.reproduced,
            "best_prompt": self.best_prompt,
            "surviving_hypotheses": list(self.surviving_hypotheses),
            "falsified_hypotheses": list(self.falsified_hypotheses),
            "n_hypotheses": self.n_hypotheses,
            "n_experiments": self.n_experiments,
            "entropy_final": self.entropy_final,
            "causal_sketch": self.causal_sketch,
            "remaining_alternatives": list(self.remaining_alternatives),
            "confidence": self.confidence,
            "notes": self.notes,
        }


def build_report(
    *,
    board: Any,
    secret_found: bool,
    verified: bool,
    reproduced: bool,
    best_prompt: str | None,
    n_experiments: int,
    notes: str = "",
) -> VulnerabilityReport:
    surviving = [h.as_dict() for h in board.surviving()]
    falsified = [h.as_dict() for h in board.falsified()]
    sketch = ""
    if surviving:
        top = max(surviving, key=lambda d: float(d.get("posterior") or 0))
        ops = top.get("operators") or []
        sketch = "then".join(ops) if ops else str(top.get("claim") or "")
    conf = 0.0
    if verified:
        conf = 0.9
    elif reproduced:
        conf = 0.75
    elif secret_found:
        conf = 0.6
    elif surviving:
        conf = max(float(h.get("posterior") or 0) for h in surviving) * 0.5
    alts = [h.claim for h in board.open_or_supported() if h.hyp_id not in {s.get("hyp_id") for s in surviving}]
    return VulnerabilityReport(
        secret_found=secret_found,
        verified=verified,
        reproduced=reproduced,
        best_prompt=best_prompt,
        surviving_hypotheses=surviving,
        falsified_hypotheses=falsified,
        n_hypotheses=len(board.nodes),
        n_experiments=n_experiments,
        entropy_final=float(board.entropy()),
        causal_sketch=sketch,
        remaining_alternatives=alts[:8],
        confidence=conf,
        notes=notes,
    )


__all__ = ["VulnerabilityReport", "build_report"]
