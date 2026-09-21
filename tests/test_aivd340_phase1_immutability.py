"""Phase-1 must not mutate Stage-2 or import discovery from replay."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE2 = ROOT / "reports/aivd_3_40_stage2"
REPLAY = ROOT / "aivd/experiments/aivd340/phase1_replay.py"
NORMALIZE = ROOT / "aivd/experiments/aivd340/phase1_normalize.py"
REPORT = ROOT / "aivd/experiments/aivd340/phase1_report.py"

FORBIDDEN_IMPORT_ROOTS = (
    "aivd.science.designer",
    "aivd.science.atom_synth",
    "aivd.science.grow",
    "aivd.science.representation",
    "aivd.science.language",
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_phase1_modules_no_discovery_imports():
    for path in (REPLAY, NORMALIZE, REPORT):
        imps = _imports(path)
        for bad in FORBIDDEN_IMPORT_ROOTS:
            assert bad not in imps, (path.name, bad)
            assert not any(i.startswith(bad) for i in imps), (path.name, imps)


def test_stage2_run_count_unchanged():
    runs = list((STAGE2 / "runs").glob("*.json"))
    assert len(runs) == 28


def test_normalize_writes_only_phase1_outputs():
    """normalize may write_text to Phase-1 out_dir, never under stage2."""
    tree = ast.parse(NORMALIZE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            if name in ("write_text", "write_bytes"):
                # ensure call is not constructing a stage2 path in same stmt — soft check via source segment
                seg = ast.get_source_segment(NORMALIZE.read_text(), node) or ""
                assert "aivd_3_40_stage2" not in seg
