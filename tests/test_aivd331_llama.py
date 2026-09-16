from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd37.unknowns.llama_331 import LlamaZipTarget, LlamaPairTarget, WEAK_SEED


def test_cap():
    assert INVENT_CAP == 48


def test_leakage():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space():
    assert LlamaZipTarget.existing_space_oracle(0) is True
    assert LlamaPairTarget.existing_space_oracle(0) is True


def test_oracle():
    assert LlamaZipTarget.evaluator_verify(0, vulnerable=True)
    assert LlamaZipTarget.evaluator_verify(0, vulnerable=False)
    assert LlamaPairTarget.evaluator_verify(0, vulnerable=True)
    assert LlamaPairTarget.evaluator_verify(0, vulnerable=False)


def test_identity_clean():
    for cls in (LlamaZipTarget, LlamaPairTarget):
        r, _, e = cls(seed=0, vulnerable=True).probe(WEAK_SEED)
        assert e is None and cls.SECRET not in (r or "")
