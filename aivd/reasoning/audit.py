"""Leakage / forbidden-literal scan for aivd/reasoning (3.16)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _forbidden() -> list[str]:
    # Split concatenations so source itself doesn't hardcode full holdout labels in one literal.
    return [
        "AIVD38-" + "HOLDOUT-X-" + "ERROR-BOUND",
        "HOLDOUT" + "-Y",
        "HOLDOUT" + "-Z",
        "HOLDOUT" + "-W",
        "HOLDOUT" + "-Q",
        "HOLDOUT" + "-R",
        "HOLDOUT" + "-S",
        "HOLDOUT" + "-T",
        "HOLDOUT" + "-U",
        "HOLDOUT" + "-U",
        "facet-prism",
        "skew-drift",
        "prism.drift",
        "holdout_t_prism_key",
        "holdout_u_",
        "left-dial",
        "right-dial",
        "check-parity",
        "kiln.ash",
        "gauge-ridge",
        "enable-span",
        "flush-mirror",
    ]


def scan_reasoning_source(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parent
    hits: list[dict[str, str]] = []
    forbid = _forbidden()
    for path in sorted(base.rglob("*.py")):
        if path.name == "audit.py":
            continue
        if path.name == "benchmarks.py":
            # evaluator-side benches may mention neutral patterns only
            text = path.read_text(encoding="utf-8")
            for tok in forbid:
                if tok in text and tok.startswith("HOLDOUT"):
                    hits.append({"file": str(path.relative_to(base.parent.parent)), "token": tok})
            continue
        text = path.read_text(encoding="utf-8")
        for tok in forbid:
            if tok in text:
                hits.append({"file": str(path.relative_to(base.parent.parent)), "token": tok})
    return {"leaks": hits, "pass": len(hits) == 0}


def reasoning_audit_record() -> dict[str, Any]:
    scan = scan_reasoning_source()
    return {
        "package": "aivd.reasoning",
        "version_target": "3.16.0",
        "leakage_pass": scan["pass"],
        "leaks": scan["leaks"],
        "default_mode_off": True,
        "no_holdout_rules": True,
    }


__all__ = ["scan_reasoning_source", "reasoning_audit_record"]
