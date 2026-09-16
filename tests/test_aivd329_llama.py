from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd37.unknowns.llama_hash import LlamaHashTarget, SECRET, WEAK_SEED


def test_cap_still_48():
    assert INVENT_CAP == 48


def test_leakage_pass():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space():
    assert LlamaHashTarget.existing_space_oracle(0) is True


def test_oracle():
    assert LlamaHashTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaHashTarget.evaluator_verify(0, vulnerable=False) is True


def test_seed_clean():
    t = LlamaHashTarget(seed=0, vulnerable=True)
    r, _, e = t.probe(WEAK_SEED)
    assert e is None and SECRET not in (r or "")
