"""AIVD 3.40 — mock matrix controls."""
from __future__ import annotations

from aivd.experiments.aivd340.condition import CONTROL_IDS, condition_from_id
from aivd.experiments.aivd340.mock_matrix import (
    CONTROL_FNS,
    control_leakage_canary,
    control_no_firewall,
    control_behavioral_equivalence,
    control_textual_difference,
)
from aivd.experiments.aivd340.runner import ConditionMixError, ConditionRunner
import pytest


def test_all_control_fns_registered():
    assert set(CONTROL_FNS) == set(CONTROL_IDS)


def test_leakage_canary_pass():
    r = control_leakage_canary()
    assert r.pass_ is True


def test_no_firewall_failclosed():
    r = control_no_firewall()
    assert r.pass_ is True
    assert r.detail["firewall_epoch"] == 0
    assert r.detail["n_independent"] == 0


def test_behavioral_and_textual_controls():
    assert control_behavioral_equivalence().pass_ is True
    assert control_textual_difference().pass_ is True


def test_condition_runner_no_mix_across_controls():
    r = ConditionRunner.from_id("NORMAL-R0")
    r.begin_episode(seed=0, plant_id="AIVD340-HX8-ODDSTRIDE")
    with pytest.raises(ConditionMixError):
        r.assert_same_condition("NORMAL-R1")
    r.end_episode({})


def test_sacred_flag_false_on_factorial():
    for cid in ("B32-R0", "B32-R1", "BH-R0", "BH-R1"):
        assert condition_from_id(cid).allow_sacred is False
