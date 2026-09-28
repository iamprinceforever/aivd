"""All historical stages AND all RC1 artifacts are byte-identical to RC1 final commit fa7e10f."""

import hashlib
import subprocess
from pathlib import Path

from aivd_rc2.frozen_manifest import FROZEN_BLOBS, MOVED_RC1_DOCS, RC1_FINAL_COMMIT


def _blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def test_every_historical_and_rc1_file_is_unchanged():
    changed = [p for p, sha in FROZEN_BLOBS.items() if not Path(p).exists() or _blob_sha(Path(p)) != sha]
    assert changed == []
    assert len(FROZEN_BLOBS) == 474


def test_rc1_code_and_results_are_covered():
    for path in ("aivd_rc1/driver.py", "aivd_rc1/verifier.py", "aivd_rc1/labeler.py", "AIVD_RC1.md",
                 "reports/aivd_rc1/final/results.json", "reports/aivd_rc1/P1/ledger_public.json",
                 "reports/aivd_rc1/P2/ledger_public.json", "reports/aivd_rc1/final/corpus_commitment.json",
                 "docs/rc1/AIVD_FINAL_STATUS_RC1.md", "tests/test_rc1_frozen.py"):
        assert path in FROZEN_BLOBS


def test_manifest_matches_git_history_when_available():
    try:
        out = subprocess.check_output(["git", "ls-tree", "-r", RC1_FINAL_COMMIT], stderr=subprocess.DEVNULL).decode()
    except Exception:
        return
    tree = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if path != ".gitignore":
            tree[MOVED_RC1_DOCS.get(path, path)] = meta.split()[2]
    assert tree == FROZEN_BLOBS


def test_rc1_tag_points_to_rc1_freeze_when_available():
    try:
        sha = subprocess.check_output(["git", "rev-parse", "AIVD-RC1^{commit}"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return
    assert sha == "aba2178f7d5638a276505e6c6605713ee750b363"
