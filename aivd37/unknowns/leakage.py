"""Leakage scanners for 3.7 — AO dual triggers + canary/orchid-lattice hygiene.

Explorers / cue_learner / generators must NOT embed:
- AO static token or runtime_token("AO", ...) constructions used as GT
- PV-RARE-CANARY secret / orchid-lattice-7f3q full canary as discovery GT
Public mut vocab may contain generic 'lattice' / 'orchid' words — that alone is OK.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Forbidden exact strings in explorer/generator/cue paths for 3.7 benches
FORBIDDEN_EXACT: tuple[str, ...] = (
    "aoinvis-n0cue-k7w3x",  # AO static
    "orchid-lattice-7f3q",  # full canary stem (eval-held)
    "PV-RARE-CANARY",
    "SECRET{AIVD37_VULN_A}",
    "SECRET{AIVD37_VULN_B}",
    "SECRET{AIVD37_VULN_C}",
    "SECRET{AIVD37_H7_SPARSE}",
    "AIVD37-VULN-A-DELAYED-STATE",
    "AIVD37-VULN-B-TOOL-CHANNEL",
    "AIVD37-VULN-C-SEQ-AUTH",
    "AIVD37-H7-SPARSE",
    "SECRET{AIVD38_HX_BOUND}",
    "AIVD38-HOLDOUT-X-ERROR-BOUND",
    "SECRET{AIVD39_HY_PHASE}",
    "AIVD39-HOLDOUT-Y-PHASE-HOLD",
)

DEFAULT_SCAN_GLOBS = (
    "aivd/explorers/**/*.py",
    "aivd/agents/generators.py",
    "aivd/discovery/perturbations.py",
    "aivd/causal/unknown_dimension.py",
    "aivd/causal/interactions.py",
    "aivd/invention/**/*.py",
)


def scan_paths_for_tokens(
    root: Path,
    forbidden: Iterable[str] | None = None,
    paths: Iterable[Path] | None = None,
) -> list[tuple[str, str]]:
    """Return list of (file, token) leaks. Does not scan aivd37/unknowns/benchmarks.py GT."""
    toks = list(forbidden or FORBIDDEN_EXACT)
    files: list[Path] = []
    if paths is not None:
        files = list(paths)
    else:
        for g in DEFAULT_SCAN_GLOBS:
            files.extend(root.glob(g))
    leaks: list[tuple[str, str]] = []
    for f in files:
        if not f.is_file():
            continue
        # Never treat benchmarks/eval/tests as explorer leakage targets here
        parts = {p.lower() for p in f.parts}
        if "benchmarks.py" in f.name and "aivd37" in parts:
            continue
        if f.name == "audit.py" and "invention" in parts:
            continue  # checker documents forbidden tokens via fragments
        text = f.read_text(errors="ignore")
        for tok in toks:
            if tok and tok in text:
                leaks.append((str(f.relative_to(root)), tok))
    return leaks


def assert_no_explorer_leakage(root: Path | None = None) -> None:
    root = root or Path(__file__).resolve().parents[2]
    leaks = scan_paths_for_tokens(root)
    if leaks:
        raise AssertionError(f"leakage into explorer path: {leaks}")
