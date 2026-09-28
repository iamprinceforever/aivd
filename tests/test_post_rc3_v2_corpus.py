"""Offline checks for the fresh V2 corpus generator. No network and no seal required."""

import json
from pathlib import Path

from aivd_post_rc3 import EXPERIMENT_ID as V1_ID
from aivd_post_rc3_v2 import EXPERIMENT_ID, HISTORICAL_ABORTED_COMMITMENT
from aivd_post_rc3_v2.corpus import KINDS, dimensions, draw
from aivd_rc3.provider import commit, public_commitment_view, public_manifest


REQUIRED = {
    "D_CONFIDENTIALITY", "D_INFORMATION_FLOW", "D_AUTHORIZATION", "D_POLICY_INTEGRITY",
    "D_CONTEXT_ISOLATION", "D_STATE_PERSISTENCE", "D_PRIVILEGE_TRANSITION",
    "D_INSTRUCTION_INTEGRITY", "D_BRANCH_ISOLATION", "D_STATE_TRANSITION",
}


def test_v2_shape_hides_secrets_and_is_not_the_aborted_corpus():
    seal = draw(b"\x11" * 32)
    assert seal["security_count"] == seal["benign_count"] == 12
    assert len(seal["targets"]) == 24
    assert REQUIRED <= set(dimensions(seal))
    assert len({r["scenario_id"] for r in seal["targets"]}) == 24
    benign = [r for r in seal["targets"] if r["family"] == "benign"]
    assert {r["kind"] for r in benign} == set(KINDS)
    assert all(r["token"] == "" for r in benign)
    pub = json.dumps(public_manifest(seal)) + json.dumps(public_commitment_view(seal))
    for row in seal["targets"]:
        if row["token"]:
            assert row["token"] not in pub
        assert row["note"] not in pub
    assert commit(seal) != HISTORICAL_ABORTED_COMMITMENT
    again = draw(b"\x11" * 32)
    assert commit(again) == commit(seal)


def test_historical_v1_commitment_file_unchanged_and_ids_disjoint():
    view = json.loads(Path("reports/aivd_post_rc3/final/corpus_commitment.json").read_text())
    assert view["corpus_commitment"] == HISTORICAL_ABORTED_COMMITMENT
    old = {r["scenario_id"] for r in json.loads(Path("reports/aivd_post_rc3/final/public_manifest.json").read_text())}
    seal = draw(b"\x12" * 32)
    assert not old & {r["scenario_id"] for r in seal["targets"]}
    assert V1_ID == "POST-RC3-GROQ"
    assert EXPERIMENT_ID == "POST-RC3-GROQ-V2"


def test_bind_does_not_rewrite_the_v1_package_constant():
    from aivd_post_rc3_v2.bind import bind, unbind
    import aivd_post_rc3.authorize as auth

    bind()
    try:
        assert auth.EXPERIMENT_ID == "POST-RC3-GROQ-V2"
        assert V1_ID == "POST-RC3-GROQ"
    finally:
        unbind()
    assert auth.EXPERIMENT_ID == "POST-RC3-GROQ"
