import hashlib
from pathlib import Path

import pytest

from aivd_f3_lm.interface_1_1 import build_context
from aivd_f3_lm.qwen3_4b_target import (
    F3_LM_EXECUTION_AUTHORIZED,
    LOCAL_BYTE_COMMITMENT,
    MODEL_BLOB_SHA256,
    OLLAMA_DIGEST,
    ExecutionRefused,
    admission_reasons,
    host_env,
    manifest_sha256,
)
from aivd_f3_lm.qwen3_runtime import F3_LM_EXECUTION_AUTHORIZED as RUNTIME_FLAG

ROOT = Path(__file__).resolve().parents[1]


def test_identity_and_firewall():
    assert OLLAMA_DIGEST == hashlib.sha256((ROOT / "freeze/qwen3_4b/manifest.json").read_bytes()).hexdigest()
    assert hashlib.sha256((ROOT / "freeze/qwen3_4b/template").read_bytes()).hexdigest().startswith("2d54db2b")
    assert F3_LM_EXECUTION_AUTHORIZED is False
    assert RUNTIME_FLAG is False
    reasons = admission_reasons(host_env())
    assert "insufficient RAM" in reasons
    assert "thinking mode cannot be disabled" in reasons
    assert "execution not authorized" in reasons
    with pytest.raises(ExecutionRefused):
        from aivd_f3_lm.qwen3_4b_target import guarded_generate

        guarded_generate(host_env())
    assert len(manifest_sha256()) == 64
    assert LOCAL_BYTE_COMMITMENT and MODEL_BLOB_SHA256


def test_admission_rejects_unsafe_variants():
    base = host_env()
    base["mem_available_kib"] = 9_000_000
    base["swap_total_kib"] = 8_000_000
    # Thinking-only template still blocks even with ample RAM.
    assert "thinking mode cannot be disabled" in admission_reasons(base)
    assert "wrong digest" in admission_reasons({**base, "ollama_digest": "0" * 64})
    assert "wrong quantization" in admission_reasons({**base, "file_type": 7, "quantization": "Q8_0"})
    assert "wrong runtime" in admission_reasons({**base, "executable_sha256": "ab" * 32})
    assert "excessive num_ctx" in admission_reasons({**base, "num_ctx": 8192})
    assert "excessive num_predict" in admission_reasons({**base, "num_predict": -1})
    assert "concurrent or duplicate model load" in admission_reasons({**base, "duplicate_load": True})
    low = dict(base)
    low["mem_available_kib"] = 1000
    low["swap_total_kib"] = 0
    assert "insufficient RAM" in admission_reasons(low)
    assert "network or tools enabled" in admission_reasons({**base, "network": True, "tools": True})


def test_interface_still_separates_private_and_public():
    built = build_context("PUBLIC_FIXTURE_456", "PRIVATE_FIXTURE_123", None)
    assert "PRIVATE_FIXTURE_123" in built["system"]
    assert "PRIVATE_FIXTURE_123" not in built["user"]
    assert built["messages"][0]["role"] == "system"
    baseline = ROOT / "evaluator_only" / "qwen3_4b_public_record_baseline.json"
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == "2dce1969c61b45204b3529e8b199005e5542e1a9a92f5a79b7d59174b1faa022"
