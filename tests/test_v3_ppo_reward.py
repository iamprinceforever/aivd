"""Phase 5–6: PPO + reward calculator."""
from __future__ import annotations

import numpy as np
import torch

from aivd.core.types import FindingStatus
from aivd.explorers import get_explorer
from aivd.explorers.ppo_explorer import BaselineRLExplorer, PPOExplorer
from aivd.explorers.rl_explorer import RLExplorer
from aivd.reward.calculator import RewardCalculator
from aivd.rl.ppo import PPOAgent, PPOConfig


def test_baseline_rl_alias():
    assert BaselineRLExplorer is RLExplorer


def test_ppo_update_changes_weights():
    agent = PPOAgent(PPOConfig(state_dim=32, action_dim=8, seed=0, epochs=2))
    before = [p.detach().clone() for p in agent.net.parameters()]
    for i in range(8):
        s = np.random.randn(32)
        agent.act(s)
        agent.observe(0.5 + 0.01 * i)
    stats = agent.update()
    assert stats["n"] == 8
    changed = any(not torch.allclose(a, b) for a, b in zip(before, agent.net.parameters()))
    assert changed


def test_ppo_explorer_registered():
    ex = get_explorer("ppo", seed=1)
    assert isinstance(ex, PPOExplorer)
    s, p = ex.next_prompt({"coverage": 0.0})
    assert s.startswith("ppo:")
    assert p
    ex.observe(s, p, 0.2, {})


def test_reward_calculator_components_and_hacking():
    calc = RewardCalculator()
    rb = calc.compute(
        information_gain=0.0,
        delta_coverage=0.5,
        novelty=0.9,
        delta_uncertainty=0.0,
        security_relevance=0.0,
        repro_score=0.0,
        status=FindingStatus.TESTED,
        redundancy=0.0,
        low_info=0.0,
        invalid=0.0,
        repetition=0.0,
    )
    assert "components" in calc.history[-1]
    # high novelty gated → small effective; coverage can still raise reward
    flag = RewardCalculator.detect_reward_hacking(
        reward_total=0.5, information_gain=0.0, security_relevance=0.0
    )
    assert flag is True
    flag2 = RewardCalculator.detect_reward_hacking(
        reward_total=0.5, information_gain=0.5, security_relevance=0.5
    )
    assert flag2 is False
    assert isinstance(rb.total, float)


def test_wm_ig_path():
    calc = RewardCalculator()
    rb = calc.compute(
        information_gain=0.01,
        delta_coverage=0.0,
        novelty=0.0,
        delta_uncertainty=0.0,
        security_relevance=0.0,
        repro_score=0.0,
        status=FindingStatus.TESTED,
        redundancy=0.0,
        low_info=0.0,
        invalid=0.0,
        repetition=0.0,
        uncertainty_before=0.4,
        uncertainty_after=0.1,
        use_wm_ig=True,
    )
    assert abs(rb.information_gain - 0.3) < 1e-6
