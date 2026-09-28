"""All historical stages, all RC1 artifacts AND all RC2 artifacts are byte-identical to RC2 final a00ea2f."""

import hashlib
import subprocess
from pathlib import Path

from aivd_rc3.frozen_manifest import FROZEN_BLOBS, MOVED_RC2_DOCS, RC2_FINAL_COMMIT


def _blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def test_every_historical_rc1_and_rc2_file_is_unchanged():
    changed = [p for p, sha in FROZEN_BLOBS.items() if not Path(p).exists() or _blob_sha(Path(p)) != sha]
    assert changed == []
    assert len(FROZEN_BLOBS) == 531


def test_rc2_code_results_and_docs_are_covered():
    for path in ("aivd_rc2/verifier.py", "aivd_rc2/driver.py", "aivd_rc2/represent.py", "aivd_rc2/provider.py",
                 "AIVD_RC2.md", "AIVD_RC2_AUDIT.md", "AIVD_RC2_DEVELOPMENT.md", "AIVD_RC2_REPRODUCIBILITY.md",
                 "reports/aivd_rc2/final/results.json", "reports/aivd_rc2/final/security_fp_analysis.json",
                 "reports/aivd_rc2/P1/ledger_public.json", "reports/aivd_rc2/P2/ledger_public.json",
                 "reports/aivd_rc2/final/corpus_commitment.json", "reports/aivd_rc2/final/label_reveal.json",
                 "reports/aivd_rc2/final/preregistration.json", "reports/aivd_rc2/dev_e2e_summary.json",
                 "docs/rc2/AIVD_FINAL_STATUS_RC2.md", "docs/rc2/AIVD_FINAL_SECURITY_EVALUATION_RC2.md",
                 "docs/rc2/AIVD_REPRODUCIBILITY_RC2.md", "tests/test_rc2_frozen.py",
                 "scripts/rc2_reveal_and_analyze.py"):
        assert path in FROZEN_BLOBS, path


def test_rc1_and_older_stages_still_covered():
    for path in ("aivd_rc1/verifier.py", "AIVD_RC1.md", "reports/aivd_rc1/final/results.json",
                 "docs/rc1/AIVD_FINAL_STATUS_RC1.md", "tests/test_rc1_frozen.py"):
        assert path in FROZEN_BLOBS, path


def test_manifest_matches_git_history_when_available():
    try:
        out = subprocess.check_output(["git", "ls-tree", "-r", RC2_FINAL_COMMIT], stderr=subprocess.DEVNULL).decode()
    except Exception:
        return
    tree = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if path != ".gitignore":
            tree[MOVED_RC2_DOCS.get(path, path)] = meta.split()[2]
    assert tree == FROZEN_BLOBS


def test_rc_tags_point_to_their_freezes_when_available():
    for tag, sha in (("AIVD-RC1", "aba2178f7d5638a276505e6c6605713ee750b363"),
                     ("AIVD-RC2", "986dd4bc9d856576ed2753104a2c2a5d4c7e9abf")):
        try:
            got = subprocess.check_output(["git", "rev-parse", tag + "^{commit}"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            continue
        assert got == sha, tag
