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
        "SECRET{AIVD322_H23",
        "holdout_23_",
        "AIVD322-HOLDOUT-23",
        "SECRET{AIVD323_H24",
        "holdout_24_",
        "AIVD323-HOLDOUT-24",
        "SECRET{AIVD323_H25",
        "holdout_25_",
        "AIVD323-HOLDOUT-25",
        "SECRET{AIVD323_LLAMA_ORPHAN",
        "llama_orphan",
        "AIVD323-LLAMA-ORPHAN",
        "orphan-compaction",
        "SECRET{AIVD324_LLAMA_ORTHO",
        "llama_orthography",
        "AIVD324-LLAMA-ORTHO",
        "SECRET{AIVD325_LLAMA_DISC",
        "llama_discourse",
        "AIVD325-LLAMA-DISC",
        "SECRET{AIVD326_LLAMA_FIELD",
        "llama_field",
        "AIVD326-LLAMA-FIELD",
        "SECRET{AIVD327_LLAMA_EQ",
        "llama_equals",
        "AIVD327-LLAMA-EQUALS",
        "SECRET{AIVD327_LLAMA_QUOTE",
        "llama_quote",
        "AIVD327-LLAMA-QUOTE",
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
