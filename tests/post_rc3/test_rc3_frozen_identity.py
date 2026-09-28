"""RC3 implementation files are byte-identical to AIVD-RC3 (7b2ada3). POST-RC3 layer only adds files."""

import hashlib
import subprocess
from pathlib import Path

from aivd_post_rc3.rc3_freeze_blobs import RC3_FREEZE_BLOBS, RC3_FREEZE_COMMIT
from aivd_post_rc3.stop import StopCondition, check_rc3_source_unmodified


def _blob(p):
    d = Path(p).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(d) + d).hexdigest()


def test_freeze_commit_is_rc3_tag():
    assert RC3_FREEZE_COMMIT == "7b2ada344cbaa830d787e2fe7ad48910125d4046"
    try:
        got = subprocess.check_output(["git", "rev-parse", "AIVD-RC3^{commit}"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return
    assert got == RC3_FREEZE_COMMIT


def test_every_rc3_implementation_file_byte_identical():
    changed = [p for p, sha in RC3_FREEZE_BLOBS.items() if not Path(p).exists() or _blob(p) != sha]
    assert changed == []


def test_pins_cover_all_rc3_stages_and_frozen_deps():
    for p in ("aivd_rc3/discover.py", "aivd_rc3/investigate.py", "aivd_rc3/verifier.py", "aivd_rc3/provenance.py",
              "aivd_rc3/driver.py", "aivd_rc3/session.py", "aivd_rc3/authorize.py", "aivd_rc3/publish.py",
              "aivd_rc3/labeler.py", "aivd_rc3/wire.py", "aivd_rc3/provider.py", "aivd_rc3/represent.py",
              "aivd_stateful/model.py", "aivd_investigation/probes.py", "scripts/rc3_run_pass.py"):
        assert p in RC3_FREEZE_BLOBS, p


def test_pins_match_git_tree_at_freeze_when_available():
    try:
        out = subprocess.check_output(["git", "ls-tree", "-r", RC3_FREEZE_COMMIT, "--", "aivd_rc3/"],
                                      stderr=subprocess.DEVNULL).decode()
    except Exception:
        return
    tree = {l.split("\t", 1)[1]: l.split()[2] for l in out.splitlines() if l.endswith(".py")}
    for p, sha in tree.items():
        assert RC3_FREEZE_BLOBS[p] == sha


def test_rc3_tree_unchanged_vs_freeze_in_git():
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", RC3_FREEZE_COMMIT, "--", "aivd_rc3/",
                                       "aivd_stateful/", "aivd_investigation/"], stderr=subprocess.DEVNULL).decode()
    except Exception:
        return
    assert out.strip() == ""


def test_stop_check_detects_modification(tmp_path, monkeypatch):
    check_rc3_source_unmodified()  # clean tree passes
    import aivd_post_rc3.stop as stop
    fake = tmp_path / "x.py"
    fake.write_text("changed")
    monkeypatch.setattr(stop, "RC3_FREEZE_BLOBS", {str(fake): "0" * 40})
    try:
        stop.check_rc3_source_unmodified()
    except StopCondition as exc:
        assert "RC3_SOURCE_MODIFICATION" in str(exc)
    else:
        raise AssertionError("modification not detected")
