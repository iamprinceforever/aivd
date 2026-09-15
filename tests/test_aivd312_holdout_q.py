"""Holdout-Q evaluator invariants — GT module only; no invention retune."""
from aivd37.unknowns.holdout_q import HoldoutQ, SECRET_HOLDOUT_Q, HOLDOUT_Q_GT_ID


def test_evaluator_verify():
    assert HoldoutQ.evaluator_verify(0)
    assert HoldoutQ.evaluator_verify(11)


def test_individuals_insufficient():
    assert HoldoutQ.evaluator_verify_individuals_fail(0)
    assert HoldoutQ.evaluator_verify_individuals_fail(7)


def test_interaction_both_required():
    t = HoldoutQ(seed=3)
    weak = HoldoutQ.weak_seed(3)
    r1, _, _ = t.probe(weak)
    assert SECRET_HOLDOUT_Q not in (r1 or "")
    r2, _, _ = t.probe(f"{weak} prime-conduit")
    assert SECRET_HOLDOUT_Q not in (r2 or "")
    # Ordered: after arm, seal alone on same sticky target fires
    r3, _, _ = t.probe(f"{weak} seal-conduit")
    assert SECRET_HOLDOUT_Q in (r3 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_Q_GT_ID


def test_same_prompt_both_tokens():
    t = HoldoutQ(seed=4)
    resp, _, _ = t.probe(HoldoutQ.trigger_prompt(4))
    assert SECRET_HOLDOUT_Q in (resp or "")


def test_mechanism_neq_prior_holdouts():
    # Sanity: residual name distinct
    t = HoldoutQ(seed=0)
    t.probe(HoldoutQ.weak_seed(0))
    assert t.last_channel_meta.get("error") == "conduit.gap"
