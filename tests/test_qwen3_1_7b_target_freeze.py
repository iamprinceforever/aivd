import hashlib
from pathlib import Path

import pytest

from aivd_f3_lm.interface_1_1 import build_context, preflight
from aivd_f3_lm.qwen3_1_7b_target import (
    F3_LM_EXECUTION_AUTHORIZED,
    LOCAL_BYTE_COMMITMENT,
    OLLAMA_DIGEST,
    TEMPLATE_SHA256,
    ExecutionRefused,
    admission_reasons,
    guarded_generate,
    host_env,
    manifest_sha256,
    memory_admitted,
)

ROOT = Path(__file__).resolve().parents[1]


def test_identity_memory_and_closed_firewall():
    manifest = (ROOT / "freeze/qwen3_1_7b/manifest.json").read_bytes()
    template = (ROOT / "freeze/qwen3_1_7b/template").read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == OLLAMA_DIGEST
    assert hashlib.sha256(template).hexdigest() == TEMPLATE_SHA256
    assert b"/no_think" in template
    assert b'developer' not in template
    assert memory_admitted() is True
    reasons = admission_reasons(host_env())
    assert reasons == ["execution not authorized"]
    assert F3_LM_EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        guarded_generate()
    assert len(manifest_sha256()) == 64
    assert LOCAL_BYTE_COMMITMENT


def test_fail_closed_mismatches():
    base = host_env()
    checks = {
        "digest mismatch": {"ollama_digest": "0" * 64},
        "byte commitment mismatch": {"local_byte_commitment": "1" * 64},
        "runtime mismatch": {"executable_sha256": "ab" * 32},
        "template mismatch": {"template_sha256": "cd" * 32},
        "thinking mode mismatch": {"think_request": True},
        "insufficient memory": {"mem_available_kib": 1000},
        "context mismatch": {"num_ctx": 8192},
        "sampling mismatch": {"temperature": 0.6},
        "public baseline missing": {"baseline_present": False},
        "interface contract mismatch": {"interface_contract_sha256": "e" * 64},
    }
    for needle, patch in checks.items():
        reasons = admission_reasons({**base, **patch})
        assert needle in reasons
        assert "execution not authorized" in reasons


def test_static_render_keeps_private_out_of_the_user_region():
    built = build_context("PUBLIC_FIXTURE_456", "PRIVATE_FIXTURE_123", None)
    rendered = preflight(built["messages"], "PRIVATE_FIXTURE_123", "PUBLIC_FIXTURE_456", None)
    user_at = rendered.index("<|im_start|>user")
    assert "PRIVATE_FIXTURE_123" in rendered[:user_at]
    assert "PRIVATE_FIXTURE_123" not in rendered[user_at:]
    assert "/no_think" in rendered
    baseline = ROOT / "evaluator_only" / "qwen3_1_7b_public_record_baseline.json"
    digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
    assert digest == "1af2fd6e6ef0f15c7fa120e7d8cd4bdbe209a9ea342aac5ae1725273b785653e"
