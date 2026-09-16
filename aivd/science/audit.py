"""Leakage scan for aivd/science — no holdout literals, no vuln signatures."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _forbidden() -> list[str]:
    return [
        "SECRET{AIVD318_H18",
        "SECRET{AIVD319_H19",
        "cistern.silt",
        "steeple.rust",
        "holdout_18_",
        "holdout_19_",
        "sluice",
        "spillway",
        "belfry",
        "campanile",
        "clapper",
        "tocsin",
        "facet-prism",
        "vault.humus",
        "left-dial",
        "right-dial",
        "if this looks like",
        "SECRET{AIVD320_H20",
        "holdout_20_",
        "AIVD320-HOLDOUT-20",
        "SECRET{AIVD321_H21",
        "holdout_21_",
        "AIVD321-HOLDOUT-21",
        "SECRET{AIVD321_H22",
        "holdout_22_",
        "AIVD321-HOLDOUT-22",
    ]


def scan_science_source(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parent
    hits: list[dict[str, str]] = []
    forbid = _forbidden()
    for path in sorted(base.glob("*.py")):
        if path.name == "audit.py":
            continue
        text = path.read_text(encoding="utf-8")
        for tok in forbid:
            if tok in text:
                hits.append({"file": str(path.name), "token": tok})
    return {"leaks": hits, "pass": len(hits) == 0}


__all__ = ["scan_science_source"]
