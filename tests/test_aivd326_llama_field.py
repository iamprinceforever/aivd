"""Evaluator-only Llama field-label oracle. Private, post 3.26 freeze."""
from aivd.science.audit import scan_science_source
from aivd37.unknowns.llama_field import (
    LlamaFieldTarget,
    SECRET_LLAMA_FIELD,
    WEAK_SEED,
)


def test_leakage_pass():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space_no_colon_newline():
    assert LlamaFieldTarget.existing_space_oracle(0) is True


def test_llama_available():
    from aivd.targets.llama_infer import available
    assert available() is True


def test_field_oracle():
    assert LlamaFieldTarget.evaluator_verify(0, vulnerable=True) is True


def test_field_control():
    assert LlamaFieldTarget.evaluator_verify(0, vulnerable=False) is True


def test_seed_no_secret():
    t = LlamaFieldTarget(seed=0, vulnerable=True)
    r, _, err = t.probe(WEAK_SEED)
    assert err is None
    assert SECRET_LLAMA_FIELD not in (r or "")
    assert ":\n" not in WEAK_SEED
