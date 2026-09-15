"""Ensure explorer/generator sources do not contain investigation-bench GT tokens."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.targets.investigation_bench import InvestigationBenchTarget

ROOT = Path(__file__).resolve().parents[1]
GT = InvestigationBenchTarget.offline_ground_truth()

# Collect exact GT tokens that must not appear in explorer-facing code
FORBIDDEN = set()
FORBIDDEN.add(GT["A"]["token"])
FORBIDDEN.add(GT["B"]["token"])
FORBIDDEN.add(GT["C"]["parts"][0])
FORBIDDEN.add(GT["C"]["parts"][1])
FORBIDDEN.add(GT["D"]["first"])
FORBIDDEN.add(GT["D"]["second"])
FORBIDDEN.add(GT["E"]["context"])
FORBIDDEN.add(GT["E"]["payload"])
FORBIDDEN.add(GT["F"]["plaintext"])
FORBIDDEN.add(GT["F"]["b64"])
FORBIDDEN.add(GT["G"]["token"])
FORBIDDEN.add(GT["J"]["token"])
for v in GT["I"]["vulns"]:
    FORBIDDEN.add(v["token"])

if "AO" in GT and isinstance(GT["AO"], dict) and GT["AO"].get("token"):
    FORBIDDEN.add(GT["AO"]["token"])
if "Z" in GT and isinstance(GT["Z"], dict) and GT["Z"].get("token"):
    FORBIDDEN.add(GT["Z"]["token"])

SCAN_DIRS = [
    ROOT / "aivd" / "explorers",
    ROOT / "aivd" / "agents" / "generators.py",
    ROOT / "aivd" / "causal" / "unknown_dimension.py",
    ROOT / "aivd" / "causal" / "interactions.py",
]


def _iter_files():
    for p in SCAN_DIRS:
        if p.is_file():
            yield p
        else:
            yield from p.rglob("*.py")


def test_no_gt_leakage_in_explorers_generators():
    leaks = []
    for path in _iter_files():
        text = path.read_text(errors="ignore")
        for tok in FORBIDDEN:
            if tok and tok in text:
                leaks.append((str(path.relative_to(ROOT)), tok))
    assert leaks == [], f"GT leakage into explorer-facing code: {leaks}"


def test_offline_gt_file_marked():
    p = ROOT / "reports" / "investigation_bench" / "ground_truth_OFFLINE_ONLY.json"
    assert p.exists()
    data = p.read_text()
    assert "OFFLINE" in data
