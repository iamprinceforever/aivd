import hashlib
from pathlib import Path

import pytest

from aivd_f3_lm.qwen3_target import (
    F3_LM_EXECUTION_AUTHORIZED,
    LOCAL_BYTE_COMMITMENT,
    OLLAMA_DIGEST,
    TEMPLATE_SHA256,
    ExecutionIntegrityFailure,
    ExecutionRefused,
    firewall_reasons,
    guarded_generate,
    runtime_hash,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "evaluator_only" / "qwen3_public_record_baseline.json"


def baseline_hash() -> str:
    return hashlib.sha256(BASELINE.read_bytes()).hexdigest()


def good_env(**overrides):
    env = {
        "execution_lock": True,
        "ollama_digest": OLLAMA_DIGEST,
        "local_byte_commitment": LOCAL_BYTE_COMMITMENT,
        "template_sha256": TEMPLATE_SHA256,
        "runtime_hash": runtime_hash(),
        "auto_update": False,
        "auto_pull": False,
        "baseline_frozen": True,
        "baseline_hash": baseline_hash(),
        "tools": False,
        "network_at_inference": False,
    }
    env.update(overrides)
    return env


def test_execution_stays_closed():
    assert F3_LM_EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        guarded_generate(good_env(), baseline_hash())


def test_digest_byte_template_runtime_and_baseline_gates():
    digest = baseline_hash()
    assert any("digest" in r for r in firewall_reasons(good_env(ollama_digest="0" * 64), digest))
    assert any("byte" in r for r in firewall_reasons(good_env(local_byte_commitment="1" * 64), digest))
    assert any("template" in r for r in firewall_reasons(good_env(template_sha256="2" * 64), digest))
    assert any("runtime" in r for r in firewall_reasons(good_env(runtime_hash="3" * 64), digest))
    assert any("update" in r for r in firewall_reasons(good_env(auto_pull=True), digest))
    assert any("baseline" in r for r in firewall_reasons(good_env(baseline_frozen=False), digest))
    assert any("unauthorized" in r for r in firewall_reasons(good_env(execution_lock=False), digest))


def test_forced_authorization_still_does_not_run(monkeypatch):
    import aivd_f3_lm.qwen3_target as target

    monkeypatch.setattr(target, "F3_LM_EXECUTION_AUTHORIZED", True)
    with pytest.raises(ExecutionIntegrityFailure):
        target.guarded_generate(good_env(), baseline_hash())


def test_template_file_matches_freeze_and_grammar_untouched():
    template = (ROOT / "freeze" / "qwen3" / "template").read_bytes()
    assert hashlib.sha256(template).hexdigest() == TEMPLATE_SHA256
    manifest = (ROOT / "freeze" / "qwen3" / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == OLLAMA_DIGEST
    grammar = (ROOT / "aivd_f3_lm" / "grammar.py").read_text(encoding="utf-8")
    assert "ROLE_PERMUTE" in grammar
    assert "qwen" not in grammar.lower()
