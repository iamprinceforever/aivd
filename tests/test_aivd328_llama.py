from aivd.science.audit import scan_science_source
from aivd37.unknowns.llama_pipe import LlamaPipeTarget, SECRET, WEAK_SEED


def test_leakage_pass():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space():
    assert LlamaPipeTarget.existing_space_oracle(0) is True


def test_oracle():
    assert LlamaPipeTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaPipeTarget.evaluator_verify(0, vulnerable=False) is True


def test_seed_clean():
    t = LlamaPipeTarget(seed=0, vulnerable=True)
    r, _, e = t.probe(WEAK_SEED)
    assert e is None and SECRET not in (r or "")
