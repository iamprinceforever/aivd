"""AIVD 3.25 — ontology gap + observation-driven compiler. Not a holdout score."""
from aivd import __version__
from aivd.core.config import AIVDConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.gap import compile_from_harvest, harvest_unseen_chars, rejoin_at
from aivd.science.methods import MethodInventor
from aivd.science.ontology import intervention_ontology
from aivd37.unknowns.llama_discourse import (
    LlamaDiscourseTarget,
    WEAK_SEED,
)


def test_version_325():
    assert __version__ == "3.30.0"
    cfg = AIVDConfig(epistemic_mode="full_3_25", invention_mode="full_3_25")
    assert cfg.epistemic_mode == "full_3_25"
    assert is_science_mode("full_3_25")
    assert epistemic_owns_episode("full_3_25")


def test_ontology_excludes_newline_and_paraphrase():
    ont = intervention_ontology()
    fam = set(ont["families"])
    assert "intra-token" in fam
    assert "newline_utterance_split" in ont["cannot_express"]


def test_324_grammar_cannot_introduce_newline():
    assert LlamaDiscourseTarget.existing_space_oracle(0) is True


def test_harvest_compiler_can_express_newline_if_observed():
    """Compiler is general: only if \\n appeared in observations."""
    assert "\n" not in harvest_unseen_chars(["hello world"])
    chars = harvest_unseen_chars(["line1\nline2"])
    assert "\n" in chars
    inv = MethodInventor()
    new = compile_from_harvest(inv._register, prompt=WEAK_SEED, chars=chars)
    assert any(n.startswith("rejoin_") for n in new)
    mid = len(WEAK_SEED.split()) // 2
    out = rejoin_at(WEAK_SEED, mid, "\n")
    assert out.count("\n") == 1
    # Winning op is not pre-registered
    assert "rejoin_10_i5" not in __import__("aivd.science.operators", fromlist=["OPERATORS"]).OPERATORS


def test_trigger_is_turn_split_not_revchar():
    t = LlamaDiscourseTarget.trigger_prompt(0)
    assert "\n" in t
    assert t.replace("\n", " ").split() == WEAK_SEED.split()
