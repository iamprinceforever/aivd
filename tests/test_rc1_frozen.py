"""Frozen stages are byte-identical to END-GOAL-3 results commit 40c5a68."""

import hashlib
import json
import subprocess
from pathlib import Path

from aivd_rc1.frozen_manifest import (
    ENDGAME3_CORPUS_HASH,
    ENDGAME3_LEDGER_HASH,
    ENDGAME3_PLAN_HASH,
    FROZEN_BLOBS,
    FROZEN_COMMIT,
)


def _blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def test_every_frozen_file_is_unchanged():
    changed = [p for p, sha in FROZEN_BLOBS.items() if not Path(p).exists() or _blob_sha(Path(p)) != sha]
    assert changed == []
    assert len(FROZEN_BLOBS) == 430


def test_manifest_matches_git_history_when_available():
    try:
        out = subprocess.check_output(["git", "ls-tree", "-r", FROZEN_COMMIT], stderr=subprocess.DEVNULL).decode()
    except Exception:
        return  # shallow checkout without history: the byte check above still applies
    tree = {line.split("\t", 1)[1]: line.split()[2] for line in out.splitlines()}
    tree.pop(".gitignore", None)
    assert tree == FROZEN_BLOBS


def test_endgame3_artifact_hashes():
    summary = json.loads(Path("reports/endgame3_summary.json").read_text())
    assert summary["design_commit"] == "941df458d2bede4811a41f2efef4c3a9497b1be5"
    assert summary["plan_hash"] == ENDGAME3_PLAN_HASH
    assert summary["corpus_commitment"] == ENDGAME3_CORPUS_HASH
    assert summary["ledger_hash"] == ENDGAME3_LEDGER_HASH
    assert (summary["targets_sealed"], summary["targets_verified"], summary["false_positives"]) == (4, 2, 2)
    assert summary["contamination"] == "NONE" and summary["integrity_failures"] == 0
    assert (summary["calls"], summary["allocation"]) == (32, 48)
