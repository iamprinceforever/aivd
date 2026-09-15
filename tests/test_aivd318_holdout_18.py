"""Holdout-18 evaluator-only oracle checks (post-freeze).

These tests do not run the discovery agent against the holdout as an
optimization target. They only lock the evaluator ground-truth contract.
"""
from aivd37.unknowns.holdout_18 import Holdout18, SECRET_HOLDOUT_18, HOLDOUT_18_GT_ID


def test_holdout_18_oracle():
    assert Holdout18.evaluator_verify(0)
    assert Holdout18.evaluator_verify(11)


def test_holdout_18_same_prompt_fail():
    assert Holdout18.evaluator_verify_same_prompt_fail(0)
    assert Holdout18.evaluator_verify_same_prompt_fail(7)


def test_holdout_18_early_spillway_fail():
    assert Holdout18.evaluator_verify_early_spillway_fail(0)
    assert Holdout18.evaluator_verify_early_spillway_fail(3)


def test_holdout_18_reverse_order_fail():
    assert Holdout18.evaluator_verify_reverse_order_fail(0)
    assert Holdout18.evaluator_verify_reverse_order_fail(4)


def test_holdout_18_distractor_fail():
    assert Holdout18.evaluator_verify_distractor_fail(0)
    assert Holdout18.evaluator_verify_distractor_fail(4)


def test_holdout_18_individuals_fail():
    assert Holdout18.evaluator_verify_individuals_fail(0)
    assert Holdout18.evaluator_verify_individuals_fail(2)


def test_holdout_18_sequence():
    t = Holdout18(seed=5)
    weak = Holdout18.weak_seed(5)
    t.probe(weak)
    r0, _, _ = t.probe(f"{weak} spillway")
    assert SECRET_HOLDOUT_18 not in (r0 or "")
    t.probe(f"{weak} sluice")
    r1, _, _ = t.probe(f"{weak} spillway")
    assert SECRET_HOLDOUT_18 not in (r1 or "")
    t.probe(f"{weak} weir")
    r2, _, _ = t.probe(f"{weak} spillway")
    assert SECRET_HOLDOUT_18 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_18_GT_ID
