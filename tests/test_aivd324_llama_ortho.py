"""Evaluator-only oracle for the Llama intra-token reversal target."""
from aivd37.unknowns.llama_orthography import (
    LlamaOrthoTarget,
    SECRET_LLAMA_ORTHO,
    WEAK_SEED,
)


def test_llama_available():
    from aivd.targets.llama_infer import available
    assert available() is True


def test_ortho_oracle():
    assert LlamaOrthoTarget.evaluator_verify(0, vulnerable=True) is True


def test_ortho_control():
    assert LlamaOrthoTarget.evaluator_verify(0, vulnerable=False) is True


def test_ortho_battery_cannot_express():
    assert LlamaOrthoTarget.evaluator_battery_fails(0) is True


def test_seed_has_no_secret():
    t = LlamaOrthoTarget(seed=1, vulnerable=True)
    r, _, err = t.probe(WEAK_SEED)
    assert err is None
    assert SECRET_LLAMA_ORTHO not in (r or "")
