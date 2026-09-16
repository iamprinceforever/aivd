from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd37.unknowns.llama_334 import LlamaOddTarget, LlamaPrefixTarget, WEAK_SEED


def test_cap():
    assert INVENT_CAP == 48


def test_leakage():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space():
    assert LlamaPrefixTarget.existing_space_oracle(0) is True
    assert LlamaOddTarget.existing_space_oracle(0) is True


def test_oracle():
    assert LlamaPrefixTarget.evaluator_verify(0, vulnerable=True)
    assert LlamaPrefixTarget.evaluator_verify(0, vulnerable=False)
    assert LlamaOddTarget.evaluator_verify(0, vulnerable=True)
    assert LlamaOddTarget.evaluator_verify(0, vulnerable=False)


def test_identity_clean():
    for cls in (LlamaPrefixTarget, LlamaOddTarget):
        r, _, e = cls(seed=0, vulnerable=True).probe(WEAK_SEED)
        assert e is None and cls.SECRET not in (r or "")


def test_not_333_plants():
    assert LlamaPrefixTarget.SECRET != "SECRET{AIVD333_LLAMA_SUFFIX}"
    assert LlamaOddTarget.SECRET != "SECRET{AIVD333_LLAMA_EVEN}"
    assert LlamaPrefixTarget.GT_ID != "AIVD333-LLAMA-SUFFIX"
    prefix = LlamaPrefixTarget.trigger_prompt(0)
    odd = LlamaOddTarget.trigger_prompt(0)
    toks = WEAK_SEED.split()
    suffix = " ".join(s + s[-1] for s in toks)
    even = " ".join(s[::2] for s in toks)
    assert prefix != suffix
    assert odd != even
    assert prefix != WEAK_SEED
    assert odd != WEAK_SEED
