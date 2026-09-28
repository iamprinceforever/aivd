"""Committed preregistration binds the frozen harness code and the sealed corpus commitment."""

import hashlib
import json
from pathlib import Path

import pytest

BASE = Path("reports/aivd_post_rc3/final")
pytestmark = pytest.mark.skipif(not (BASE / "preregistration.json").exists(), reason="not yet preregistered")


def test_harness_code_matches_preregistration():
    prereg = json.loads((BASE / "preregistration.json").read_text())
    for path, sha in prereg["harness_code_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha, path
    files = {str(p) for p in Path("aivd_post_rc3").glob("*.py")} | {str(p) for p in Path("scripts").glob("post_rc3_*.py")}
    assert files == set(prereg["harness_code_sha256"])


def test_corpus_commitment_consistent_and_shape():
    prereg = json.loads((BASE / "preregistration.json").read_text())
    view = json.loads((BASE / "corpus_commitment.json").read_text())
    summary = json.loads((BASE / "corpus_summary.json").read_text())
    assert prereg["corpus_commitment"] == view["corpus_commitment"] == summary["seal_hash_corpus_commitment"]
    assert (summary["target_count"], summary["benign_count"]) == (8, 8)
    assert summary["dimension_count"] >= 8 and summary["relation_type_count"] == 5
    assert prereg["allocation_total"] == 288 and prereg["repeat_set"]["counts_inside_96"] is False
    assert prereg["models"] == ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"]


def test_public_manifest_matches_commitment_and_hides_labels():
    from aivd_stateful.hashing import digest
    manifest = json.loads((BASE / "public_manifest.json").read_text())
    view = json.loads((BASE / "corpus_commitment.json").read_text())
    assert digest(manifest) == view["public_manifest_sha256"] and len(manifest) == 16
    text = json.dumps(manifest)
    for key in ('"family"', '"relation"', '"token"', '"note"', '"label_salt"', '"dimension"'):
        assert key not in text


def test_seal_matches_commitment_when_available():
    seal_path = Path("reports/aivd_post_rc3/protected/final_seal.json")
    if not seal_path.exists():
        pytest.skip("protected seal not present (expected outside the evaluator box)")
    from aivd_rc3.provider import commit
    view = json.loads((BASE / "corpus_commitment.json").read_text())
    assert commit(json.loads(seal_path.read_text())) == view["corpus_commitment"]
