"""Holdout-U evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_u import HoldoutU, SECRET_HOLDOUT_U, HOLDOUT_U_GT_ID


def test_holdout_u_oracle():
    assert HoldoutU.evaluator_verify(0)
    assert HoldoutU.evaluator_verify(11)


def test_holdout_u_both_flip_fail():
    assert HoldoutU.evaluator_verify_both_flip_fail(0)
    assert HoldoutU.evaluator_verify_both_flip_fail(7)


def test_holdout_u_distractor_fail():
    assert HoldoutU.evaluator_verify_distractor_fail(0)
    assert HoldoutU.evaluator_verify_distractor_fail(3)


def test_holdout_u_individuals_fail():
    assert HoldoutU.evaluator_verify_individuals_fail(0)
    assert HoldoutU.evaluator_verify_individuals_fail(4)


def test_holdout_u_sequence():
    t = HoldoutU(seed=3)
    weak = HoldoutU.weak_seed(3)
    t.probe(weak)
    r0, _, _ = t.probe(f"{weak} check-parity")
    assert SECRET_HOLDOUT_U not in (r0 or "")
    t.probe(f"{weak} left-dial")
    r1, _, _ = t.probe(f"{weak} check-parity")
    assert SECRET_HOLDOUT_U in (r1 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_U_GT_ID
