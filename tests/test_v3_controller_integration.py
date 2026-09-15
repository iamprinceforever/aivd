"""Integration: controller with optional WM / critic / ppo still runs offline."""
from __future__ import annotations

from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.config import AIVDConfig


def test_controller_defaults_still_run(tmp_path: Path):
    cfg = AIVDConfig(seed=1)
    cfg.data_dir = tmp_path / "d"
    cfg.db_path = cfg.data_dir / "aivd.db"
    cfg.audit_path = cfg.data_dir / "audit.jsonl"
    cfg.budget.max_experiments = 5
    ctrl = Controller(config=cfg, explorer_name="random")
    results = ctrl.run(n=5)
    assert len(results) == 5


def test_controller_world_model_and_ppo(tmp_path: Path):
    cfg = AIVDConfig(seed=2)
    cfg.data_dir = tmp_path / "d2"
    cfg.db_path = cfg.data_dir / "aivd.db"
    cfg.audit_path = cfg.data_dir / "audit.jsonl"
    cfg.budget.max_experiments = 10
    cfg.world_model = True
    cfg.use_critic = True
    cfg.use_counterfactual = True
    ctrl = Controller(config=cfg, explorer_name="ppo")
    results = ctrl.run(n=10)
    assert len(results) == 10
    assert ctrl.world_model is not None
    assert ctrl.world_model.train_steps >= 1
