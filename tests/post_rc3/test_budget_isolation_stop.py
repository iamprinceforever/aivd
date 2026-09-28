"""Budget accounting, retry charging, model isolation, stop conditions, seal integrity."""

import json
from pathlib import Path

import pytest

from aivd_post_rc3 import config as C
from aivd_post_rc3.corpus import BENIGN_KINDS, SECURITY_KINDS, dimensions, draw, public_commitment_view, relation_types
from aivd_post_rc3.models import MODEL_DIRS, MODELS
from aivd_post_rc3.seeds import discovery_seed_for
from aivd_post_rc3.stop import (StopCondition, check_candidate_ids_unique, check_corpus_commitment,
                                check_ledger_integrity, check_model_match, check_no_target_leakage,
                                check_no_verifier_leakage)
from aivd_rc3.provider import commit, public_manifest


def test_budget_preregistration_constants():
    assert (C.DISCOVERY_LIMIT, C.INVESTIGATION_LIMIT, C.VERIFICATION_LIMIT) == (48, 32, 16)
    assert C.MODEL_ALLOCATION == 96 and C.TOTAL_ALLOCATION == 288
    assert C.VERIFY_COST == 3 and C.MAX_TRANSPORT_ATTEMPTS == 3
    assert C.REPRO_COUNTS_INSIDE_96 is False and C.REPRO_CALLS_PER_MODEL == 6


def test_exact_models_no_substitution():
    assert MODELS == ("openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b")
    assert len(set(MODEL_DIRS.values())) == 3


def test_independent_seeds_per_model():
    seeds = [discovery_seed_for(m) for m in MODELS]
    assert len(set(seeds)) == 3
    with pytest.raises(ValueError):
        discovery_seed_for("other")


def test_corpus_shape_dimensions_relations():
    seal = draw(b"\x01" * 32)
    sec = [r for r in seal["targets"] if r["family"] == "security"]
    ben = [r for r in seal["targets"] if r["family"] == "benign"]
    assert len(sec) == 8 and len(ben) == 8
    assert len(dimensions(seal)) == 8
    assert {"D_CONFIDENTIALITY", "D_INFORMATION_FLOW", "D_AUTHORIZATION", "D_POLICY_INTEGRITY",
            "D_CONTEXT_ISOLATION", "D_STATE_PERSISTENCE", "D_PRIVILEGE_TRANSITION",
            "D_INSTRUCTION_INTEGRITY"} == set(dimensions(seal))
    assert {r[:1] for r in relation_types(seal)} == set("ABCDE")
    assert {"id_upper", "id_punct", "id_mixed", "gen_key", "discarded_draft", "reset_survival"} <= set(BENIGN_KINDS)
    assert all(r["token"] == "" for r in ben)
    assert len({r["scenario_id"] for r in seal["targets"]}) == 16


def test_public_views_carry_no_sealed_material():
    seal = draw(b"\x02" * 32)
    pub = json.dumps(public_manifest(seal)) + json.dumps(public_commitment_view(seal))
    for r in seal["targets"]:
        if r["token"]:
            assert r["token"] not in pub
        assert r["note"] not in pub
    for word in ('"relation"', '"family"', '"token"', '"note"'):
        assert word not in json.dumps(public_manifest(seal))
    view = public_commitment_view(seal)
    assert view["corpus_commitment"] == commit(seal) and view["dimension_count"] == 8


def test_seal_commitment_detects_tamper():
    seal = draw(b"\x03" * 32)
    c0 = commit(seal)
    seal["targets"][0]["note"] += "!"
    assert commit(seal) != c0


def test_fresh_against_prior_manifests():
    seal = draw(b"\x04" * 32)
    ids = {r["scenario_id"] for r in seal["targets"]}
    for manifest in Path("reports").glob("aivd_rc*/final/public_manifest.json"):
        old = {r["scenario_id"] for r in json.loads(manifest.read_text())}
        assert not ids & old


def test_stop_conditions_fire():
    with pytest.raises(StopCondition):
        check_model_match("openai/gpt-oss-20b", "openai/gpt-oss-120b")
    with pytest.raises(StopCondition):
        check_corpus_commitment("a" * 64, "b" * 64)
    with pytest.raises(StopCondition):
        check_candidate_ids_unique([{"candidate_id": "x"}, {"candidate_id": "x"}])
    with pytest.raises(StopCondition):
        check_no_target_leakage("... 0123456789abcdef ...", ["0123456789abcdef"], [])
    with pytest.raises(StopCondition):
        check_no_verifier_leakage({"candidates": [{"relation": "A"}]})
    with pytest.raises(StopCondition):
        check_ledger_integrity({"frozen_hash": "nope"})
    check_model_match("qwen/qwen3.8-27b", "qwen/qwen3.8-27b")


def test_runner_isolation_forbids_other_models_and_seal():
    src = Path("scripts/post_rc3_run_model.py").read_text()
    assert "install(forbidden)" in src
    assert src.index("install(forbidden)") < src.index("from aivd_post_rc3.driver import run_model")
    assert 'protected/final_seal.json' in src and 'protected/wire' in src


def test_gitignore_protects_raw_material():
    gi = Path(".gitignore").read_text()
    for line in ("reports/aivd_post_rc3/protected/", "reports/aivd_post_rc3/**/raw/",
                 "reports/aivd_post_rc3/**/wire/"):
        assert line in gi
