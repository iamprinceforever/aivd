"""AIVD 3.39 sacred TinyLlama plants — environment-dependent."""
from __future__ import annotations

import pytest

transformers = pytest.importorskip("transformers", reason="transformers not installed")

from pathlib import Path

MODEL = Path("/workspace/models/tinyllama")
if not MODEL.is_dir():
    pytest.skip("TinyLlama weights absent at /workspace/models/tinyllama", allow_module_level=True)

from aivd37.unknowns.llama_339 import (
    LlamaOddDoubleTarget,
    LlamaRotateTarget,
    target_hash,
)


def test_339_plants_existing_space_miss():
    assert LlamaOddDoubleTarget.existing_space_oracle(0) is True
    assert LlamaRotateTarget.existing_space_oracle(0) is True


def test_339_evaluator_verify_direct():
    assert LlamaOddDoubleTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaRotateTarget.evaluator_verify(0, vulnerable=True) is True


def test_339_target_hash_stable():
    assert len(target_hash(LlamaOddDoubleTarget)) == 64
    assert len(target_hash(LlamaRotateTarget)) == 64
