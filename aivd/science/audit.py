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
        "SECRET{AIVD328_LLAMA_PIPE",
        "llama_pipe",
        "AIVD328-LLAMA-PIPE",
        "SECRET{AIVD329_LLAMA_HASH",
        "llama_hash",
        "AIVD329-LLAMA-HASH",
        "SECRET{AIVD329_FRONTIER_A",
        "SECRET{AIVD329_FRONTIER_B",
        "SECRET{AIVD329_FRONTIER_C",
        "AIVD329-FRONTIER-A-JOIN",
        "AIVD329-FRONTIER-B-ROTATE",
        "AIVD329-FRONTIER-C-MIRROR",
        "SECRET{AIVD330_LLAMA_SWAP",
        "SECRET{AIVD330_LLAMA_WRAP",
        "AIVD330-LLAMA-SWAP",
        "AIVD330-LLAMA-WRAP",
        "SECRET{AIVD331_LLAMA_ZIP",
        "SECRET{AIVD331_LLAMA_PAIR",
        "AIVD331-LLAMA-ZIP",
        "AIVD331-LLAMA-PAIR",
        "SECRET{AIVD332_LLAMA_AFFIX",
        "SECRET{AIVD332_LLAMA_STRIDE",
        "AIVD332-LLAMA-AFFIX",
        "AIVD332-LLAMA-STRIDE",
        "SECRET{AIVD333_LLAMA_SUFFIX",
        "SECRET{AIVD333_LLAMA_EVEN",
        "AIVD333-LLAMA-SUFFIX",
        "AIVD333-LLAMA-EVEN",
        "SECRET{AIVD334_LLAMA_PREFIX",
        "SECRET{AIVD334_LLAMA_ODD",
        "AIVD334-LLAMA-PREFIX",
        "AIVD334-LLAMA-ODD",
        "SECRET{AIVD335_LLAMA_LAST",
        "SECRET{AIVD335_LLAMA_ENDS",
        "AIVD335-LLAMA-LAST",
        "AIVD335-LLAMA-ENDS",
        "SECRET{AIVD336_LLAMA_DOUBLE",
        "SECRET{AIVD336_LLAMA_ENDS",
        "AIVD336-LLAMA-DOUBLE",
        "AIVD336-LLAMA-ENDS",
        "SECRET{AIVD337_LLAMA_EVENLAST",
        "SECRET{AIVD337_LLAMA_STRIDE3",
        "AIVD337-LLAMA-EVENLAST",
        "AIVD337-LLAMA-STRIDE3",
        "SECRET{AIVD338_LLAMA_DOUBLEEVEN",
        "SECRET{AIVD338_LLAMA_REVERSE",
        "AIVD338-LLAMA-DOUBLEEVEN",
        "AIVD338-LLAMA-REVERSE",
        "SECRET{AIVD339_LLAMA_ODDDOUBLE",
        "SECRET{AIVD339_LLAMA_ROTATE",
        "AIVD339-LLAMA-ODDDOUBLE",
        "AIVD339-LLAMA-ROTATE",
        "SECRET{AIVD340_LLAMA_ODDSTRIDE",
        "SECRET{AIVD340_LLAMA_ROL1",
        "SECRET{AIVD340_LLAMA_CANARY",
        "AIVD340-LLAMA-ODDSTRIDE",
        "AIVD340-LLAMA-ROL1",
        "AIVD340-LLAMA-CANARY",
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




# Tokens that must never appear as discovery proposal targets in science/*.py
# (excluding audit.py itself and historical docs outside this tree).
_DISCOVERY_TARGET_FORBIDDEN = (
    "Level 14",
    "Level-14",
    "level_14",
    "FX8DoubleEven",
    "SECRET{AIVD338_FX8",
    "AIVD338-FX8-DOUBLEEVEN",
    "doubled-even",
    "double_even",
    "DOUBLEEVEN",
    "reverse-each",
    "reverse_each",
    "CAT-self",  # as a named plant target string; class-level growth prose is separate
    "MAX_GENERATIONS=14",
    "expected_generation",
    "AIVD339-LLAMA-ODDDOUBLE",
    "AIVD339-LLAMA-ROTATE",
    "SECRET{AIVD339_LLAMA_ODDDOUBLE",
    "SECRET{AIVD339_LLAMA_ROTATE",
    "AIVD340-LLAMA-ODDSTRIDE",
    "AIVD340-LLAMA-ROL1",
    "AIVD340-LLAMA-CANARY",
    "SECRET{AIVD340_LLAMA_ODDSTRIDE",
    "SECRET{AIVD340_LLAMA_ROL1",
    "SECRET{AIVD340_LLAMA_CANARY",
)


def scan_discovery_target_leakage(root: Path | None = None) -> dict[str, Any]:
    """Fail if discovery proposers encode Level-14 / FX8 / plant GT as targets.

    Scans grow/designer/atom_synth/language/generation_record only.
    Historical docs and evaluator modules are out of scope.
    """
    base = root or Path(__file__).resolve().parent
    targets = (
        "grow.py", "designer.py", "atom_synth.py", "language.py",
        "generation_record.py", "proposers.py", "lifecycle.py",
        "representation.py", "budget_trace.py",
    )
    # Soft tokens that appear in allowed class-level prose — exclude from hard fail
    # when they are only in comments about growth class knowledge, not plant IDs.
    hard = [
        t for t in _DISCOVERY_TARGET_FORBIDDEN
        if t not in ("CAT-self",)  # grow.py may mention CAT-self as class growth; checked separately
    ]
    hits: list[dict[str, str]] = []
    for name in targets:
        path = base / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for tok in hard:
            if tok in text:
                hits.append({"file": name, "token": tok})
    # CAT-self as a *proposal target* string inside propose_atoms is forbidden;
    # mentioning the growth operator class in grow.py comments/docstrings is OK.
    atom = base / "atom_synth.py"
    if atom.is_file():
        at = atom.read_text(encoding="utf-8")
        for tok in ("CAT-self", "doubled-even", "reverse-each", "Level 14", "FX8"):
            if tok in at:
                hits.append({"file": "atom_synth.py", "token": tok})
    return {"leaks": hits, "pass": len(hits) == 0}


__all__ = ["scan_science_source", "scan_discovery_target_leakage"]
