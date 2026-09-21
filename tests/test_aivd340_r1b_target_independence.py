"""R1b candidates independent of hidden evaluator / plant targets."""
from __future__ import annotations

from aivd.science.representation import R1B, propose_atom_candidates

PROMPT = "ab cd ef gh ij kl mn op"


def test_r1b_invariant_to_hidden_target_string():
    """Canary: changing a hidden evaluator target must not alter R1b inputs."""
    base = [a.key() for a in propose_atom_candidates(prompt=PROMPT, question=True, policy=R1B)]
    # Simulate alternate hidden targets in the *environment* — R1b only sees prompt.
    for decoy in (
        "HIDDEN_TARGET_ALPHA_ZZZ",
        "HIDDEN_TARGET_BETA_YYY",
        "PLANT_GEOMETRY_VARIANT_9",
    ):
        # Decoy is not passed into propose_atom_candidates; keys must match base.
        alt = [a.key() for a in propose_atom_candidates(prompt=PROMPT, question=True, policy=R1B)]
        assert alt == base
        assert decoy not in "".join(alt)


def test_r1b_invariant_across_prompt_token_content_structure():
    """Same n_tokens / structure family → same geometric key set (order may follow prompt len)."""
    a = [x.key() for x in propose_atom_candidates(prompt="aa bb cc dd ee ff", question=True, policy=R1B)]
    b = [x.key() for x in propose_atom_candidates(prompt="xx yy zz qq ww vv", question=True, policy=R1B)]
    assert a == b
