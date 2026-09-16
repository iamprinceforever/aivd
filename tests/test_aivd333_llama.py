from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd37.unknowns.llama_333 import LlamaEvenTarget, LlamaSuffixTarget, WEAK_SEED


def test_cap():
    assert INVENT_CAP == 48


def test_leakage():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space():
    assert LlamaSuffixTarget.existing_space_oracle(0) is True
    assert LlamaEvenTarget.existing_space_oracle(0) is True


def test_oracle():
    assert LlamaSuffixTarget.evaluator_verify(0, vulnerable=True)
    assert LlamaSuffixTarget.evaluator_verify(0, vulnerable=False)
    assert LlamaEvenTarget.evaluator_verify(0, vulnerable=True)
    assert LlamaEvenTarget.evaluator_verify(0, vulnerable=False)


def test_identity_clean():
    for cls in (LlamaSuffixTarget, LlamaEvenTarget):
        r, _, e = cls(seed=0, vulnerable=True).probe(WEAK_SEED)
        assert e is None and cls.SECRET not in (r or "")
