import hashlib
from pathlib import Path

import pytest

from aivd_f3_lm.qwen3_runtime import (
    DISCOVERY_SEED,
    F3_LM_EXECUTION_AUTHORIZED,
    MODEL_SEED,
    NUM_CTX,
    NUM_PREDICT,
    OLLAMA_EXECUTABLE_SHA256,
    OLLAMA_VERSION,
    PUBLIC_BASELINE_SHA256,
    TEMPERATURE,
    THINKING,
    ExecutionIntegrityFailure,
    ExecutionRefused,
    SeparatedRNG,
    firewall_reasons,
    guarded_generate,
    runtime_manifest_hash,
)
from aivd_f3_lm.qwen3_target import OLLAMA_DIGEST, TEMPLATE_SHA256

ROOT = Path(__file__).resolve().parents[1]


def env(**overrides):
    base = {
        "execution_lock": True,
        "experiment_authorized": True,
        "tag": "8b",
        "ollama_version": OLLAMA_VERSION,
        "ollama_digest": OLLAMA_DIGEST,
        "local_byte_commitment": "e56d3bf948b1809641c48913c2a86d25277580ce1983e8904a9a3d6b6220feb1",
        "ollama_executable_sha256": OLLAMA_EXECUTABLE_SHA256,
        "template_sha256": TEMPLATE_SHA256,
        "thinking": THINKING,
        "think_request": False,
        "temperature": TEMPERATURE,
        "top_k": 1,
        "top_p": 1.0,
        "num_ctx": NUM_CTX,
        "num_predict": NUM_PREDICT,
        "model_seed": MODEL_SEED,
        "network": False,
        "tools": False,
        "baseline_frozen": True,
        "baseline_hash": PUBLIC_BASELINE_SHA256,
        "design_commit": "d36ebd5d53a5994ae31a87ac05eb37e0fd72a87a",
        "runtime_manifest_hash": runtime_manifest_hash(),
    }
    base.update(overrides)
    return base


def test_authorization_remains_false():
    assert F3_LM_EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        guarded_generate(env())


def test_mismatch_cases_are_rejected():
    cases = {
        "latest tags are rejected": {"tag": "latest"},
        "model digest mismatch": {"ollama_digest": "0" * 64},
        "runtime version mismatch": {"ollama_version": "0.0.0"},
        "runtime hash mismatch": {"ollama_executable_sha256": "ab" * 32},
        "template mismatch": {"template_sha256": "cd" * 32},
        "thinking mode mismatch": {"thinking": "ENABLED"},
        "temperature mismatch": {"temperature": 0.6},
        "top_k mismatch": {"top_k": 20},
        "top_p mismatch": {"top_p": 0.95},
        "num_ctx mismatch": {"num_ctx": 2048},
        "num_predict mismatch": {"num_predict": -1},
        "seed mismatch": {"model_seed": 1},
        "network enabled": {"network": True},
        "tools enabled": {"tools": True},
        "public-record baseline missing": {"baseline_frozen": False},
        "F3-LM design hash missing": {"design_commit": "f" * 40},
    }
    for needle, patch in cases.items():
        reasons = firewall_reasons(env(**patch))
        assert any(needle in reason for reason in reasons), reasons


def test_forced_flag_still_has_no_backend(monkeypatch):
    import aivd_f3_lm.qwen3_runtime as runtime

    monkeypatch.setattr(runtime, "F3_LM_EXECUTION_AUTHORIZED", True)
    with pytest.raises(ExecutionIntegrityFailure):
        runtime.guarded_generate(env())


def test_rngs_do_not_cross():
    rng = SeparatedRNG()
    before = rng.model_seed_for_call()
    draws = [rng.discovery_draw() for _ in range(5)]
    assert rng.model_seed_for_call() == before == MODEL_SEED
    assert draws[0] != draws[1]
    other = SeparatedRNG()
    assert other.discovery_draw() == draws[0]
    assert DISCOVERY_SEED != MODEL_SEED


def test_baseline_and_template_unchanged():
    baseline = ROOT / "evaluator_only" / "qwen3_public_record_baseline.json"
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == PUBLIC_BASELINE_SHA256
    template = ROOT / "freeze" / "qwen3" / "template"
    assert hashlib.sha256(template.read_bytes()).hexdigest() == TEMPLATE_SHA256
    assert "ROLE_PERMUTE" in (ROOT / "aivd_f3_lm" / "grammar.py").read_text(encoding="utf-8")
