"""PPO training loop (CPU-friendly, small nets)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
import torch.nn.functional as F

from aivd.rl.buffer import TrajectoryBuffer
from aivd.rl.policy import ActorCritic


@dataclass
class PPOConfig:
    state_dim: int = 64 + 10 + 8  # z + extras + hint (matches BehavioralState.as_tensor_view default z)
    action_dim: int = 8
    hidden: int = 64
    lr: float = 3e-4
    gamma: float = 0.99
    lam: float = 0.95
    clip_eps: float = 0.2
    epochs: int = 4
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    seed: int = 42


# Action layout (modular):
# 0 strategy_family, 1 probe_family, 2 mutation, 3 encoding, 4 depth,
# 5 explore_vs_exploit (also gated by explore head), 6 rare_mix, 7 transform


class PPOAgent:
    def __init__(self, config: PPOConfig | None = None):
        self.config = config or PPOConfig()
        torch.manual_seed(self.config.seed)
        self.net = ActorCritic(self.config.state_dim, self.config.action_dim, self.config.hidden)
        self.opt = torch.optim.Adam(self.net.parameters(), lr=self.config.lr)
        self.buffer = TrajectoryBuffer()
        self._last: dict | None = None
        self.update_count: int = 0

    def _state_t(self, state: np.ndarray) -> torch.Tensor:
        s = np.asarray(state, dtype=np.float64).reshape(-1)
        if s.shape[0] < self.config.state_dim:
            s = np.pad(s, (0, self.config.state_dim - s.shape[0]))
        else:
            s = s[: self.config.state_dim]
        return torch.tensor(s, dtype=torch.float32)

    def act(self, state: np.ndarray) -> tuple[np.ndarray, float, float, float]:
        """Return action, log_prob, value, explore_prob."""
        self.net.eval()
        with torch.no_grad():
            dist, value, explore_p = self.net(self._state_t(state))
            action = dist.rsample()
            # blend explore head into action[5]
            a = action.clone()
            a[5] = explore_p * 2.0 - 1.0  # map to [-1,1]
            log_prob = dist.log_prob(a).sum()
        self._last = {
            "state": np.asarray(state, dtype=np.float64),
            "action": a.numpy().astype(np.float64),
            "log_prob": float(log_prob.item()),
            "value": float(value.item()),
            "explore_prob": float(explore_p.item()),
        }
        return (
            self._last["action"],
            self._last["log_prob"],
            self._last["value"],
            self._last["explore_prob"],
        )

    def observe(self, reward: float, done: bool = False) -> None:
        if not self._last:
            return
        self.buffer.add(
            self._last["state"],
            self._last["action"],
            self._last["log_prob"],
            reward,
            self._last["value"],
            done=done,
        )
        self._last = None

    def update(self) -> dict[str, float]:
        if len(self.buffer) < 2:
            return {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "n": 0}
        cfg = self.config
        returns, advantages = self.buffer.compute_returns_advantages(cfg.gamma, cfg.lam)
        adv = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        states = torch.tensor(np.stack([
            np.pad(s, (0, max(0, cfg.state_dim - len(s))))[: cfg.state_dim]
            for s in self.buffer.states
        ]), dtype=torch.float32)
        actions = torch.tensor(np.stack([
            np.pad(a, (0, max(0, cfg.action_dim - len(a))))[: cfg.action_dim]
            for a in self.buffer.actions
        ]), dtype=torch.float32)
        old_logp = torch.tensor(self.buffer.log_probs, dtype=torch.float32)
        ret = torch.tensor(returns, dtype=torch.float32)
        adv_t = torch.tensor(adv, dtype=torch.float32)

        self.net.train()
        last = {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "n": len(self.buffer)}
        for _ in range(cfg.epochs):
            dist, values, _explore = self.net(states)
            logp = dist.log_prob(actions).sum(dim=-1)
            ratio = torch.exp(logp - old_logp)
            unclipped = ratio * adv_t
            clipped = torch.clamp(ratio, 1.0 - cfg.clip_eps, 1.0 + cfg.clip_eps) * adv_t
            policy_loss = -torch.min(unclipped, clipped).mean()
            value_loss = F.mse_loss(values, ret)
            entropy = dist.entropy().sum(dim=-1).mean()
            loss = policy_loss + cfg.vf_coef * value_loss - cfg.ent_coef * entropy
            self.opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
            self.opt.step()
            last = {
                "policy_loss": float(policy_loss.item()),
                "value_loss": float(value_loss.item()),
                "entropy": float(entropy.item()),
                "n": len(self.buffer),
            }
        self.buffer.clear()
        self.update_count += 1
        return last

    def state_dict_bundle(self) -> dict[str, Any]:
        return {
            "policy_state": self.net.state_dict(),
            "optimizer_state": self.opt.state_dict(),
            "config": {
                "state_dim": self.config.state_dim,
                "action_dim": self.config.action_dim,
                "hidden": self.config.hidden,
                "lr": self.config.lr,
                "seed": self.config.seed,
            },
            "update_count": self.update_count,
            "aivd_version": "3.18.0",
            "checkpoint_format": 2,
        }

    def load_state_dict_bundle(self, bundle: dict[str, Any]) -> None:
        ps = bundle.get("policy_state") or bundle.get("state_dict")
        if ps is None:
            raise KeyError("No policy_state in checkpoint bundle")
        self.net.load_state_dict(ps)
        opt = bundle.get("optimizer_state")
        if opt:
            try:
                self.opt.load_state_dict(opt)
            except Exception:
                pass
        self.update_count = int(bundle.get("update_count") or 0)

    def save_checkpoint(self, path: Path | str, meta: Optional[dict[str, Any]] = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        bundle = self.state_dict_bundle()
        bundle["meta"] = meta or {}
        torch.save(bundle, path)
        return path

    def load_checkpoint(self, path: Path | str) -> dict[str, Any]:
        path = Path(path)
        bundle = torch.load(path, map_location="cpu", weights_only=False)
        self.load_state_dict_bundle(bundle)
        return bundle
