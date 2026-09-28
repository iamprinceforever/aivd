"""Protected values must never enter Git or public reports."""

import json
import subprocess
from pathlib import Path

from aivd_rc2.protected import PROTECTED_DIR, protected_values, scan, tracked_files, tracked_protected_paths
from aivd_rc2.provider import draw, public_commitment_view, public_manifest


def test_protected_dir_is_ignored_and_untracked():
    assert tracked_protected_paths() == []
    probe = PROTECTED_DIR / "probe.json"
    try:
        out = subprocess.run(["git", "check-ignore", "-q", str(probe)])
        assert out.returncode == 0
    except FileNotFoundError:
        pass


def test_no_protected_value_in_tracked_files():
    values = protected_values()
    assert scan(tracked_files(), values) == []


def test_scanner_detects_planted_value(tmp_path):
    seal = draw(b"scanner-test")
    protected = tmp_path / "protected"
    protected.mkdir()
    (protected / "seal.json").write_text(json.dumps(seal))
    values = protected_values(protected)
    token = next(r["token"] for r in seal["targets"] if r["family"] == "security")
    assert token in values
    leaked = tmp_path / "public.md"
    leaked.write_text("report " + token)
    assert scan([str(leaked)], values)
    clean = tmp_path / "clean.md"
    clean.write_text(json.dumps(public_commitment_view(seal)) + json.dumps(public_manifest(seal)))
    assert scan([str(clean)], values) == []


def test_public_views_hide_protected_fields():
    seal = draw(b"public-view")
    blob = json.dumps(public_manifest(seal)) + json.dumps(public_commitment_view(seal))
    for row in seal["targets"]:
        if row["token"]:
            assert row["token"] not in blob
        assert row["note"] not in blob
    assert "security" not in json.dumps(public_manifest(seal))
    assert "benign" not in json.dumps(public_manifest(seal))


def test_public_rc1_reports_have_no_protected_value():
    root = Path("reports/aivd_rc2")
    files = [str(p) for p in root.rglob("*") if p.is_file() and "protected" not in p.parts] if root.exists() else []
    assert scan(files, protected_values()) == []
