"""Private oracles for 3.27 Llama equals-field and quote-tail plants."""
from aivd.science.audit import scan_science_source
from aivd37.unknowns.llama_equals import LlamaEqualsTarget, SECRET as SEQ, WEAK_SEED
from aivd37.unknowns.llama_quote import LlamaQuoteTarget, SECRET as SQT


def test_leakage_pass():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_existing_space():
    assert LlamaEqualsTarget.existing_space_oracle(0) is True
    assert LlamaQuoteTarget.existing_space_oracle(0) is True


def test_oracles():
    assert LlamaEqualsTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaEqualsTarget.evaluator_verify(0, vulnerable=False) is True
    assert LlamaQuoteTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaQuoteTarget.evaluator_verify(0, vulnerable=False) is True


def test_seed_clean():
    a = LlamaEqualsTarget(seed=0, vulnerable=True)
    r, _, e = a.probe(WEAK_SEED)
    assert e is None and SEQ not in (r or "")
    b = LlamaQuoteTarget(seed=0, vulnerable=True)
    r, _, e = b.probe(WEAK_SEED)
    assert e is None and SQT not in (r or "")
