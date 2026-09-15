"""Behavioral world model: predict next z given (z, action) with ensemble uncertainty."""
from __future__ import annotations

from typing import Sequence

import numpy as np
import torch
import torch.nn as nn


class _DynamicsNet(nn.Module):
    def __init__(self, z_dim: int, action_dim: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(z_dim + action_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, z_dim),
        )

    def forward(self, z: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([z, a], dim=-1))


class BehavioralWorldModel:
    """Ensemble dynamics model → predictive mean + variance (real uncertainty).

    Uncertainty is the variance across ensemble members (not a constant stub).
    """

    def __init__(
        self,
        z_dim: int = 64,
        action_dim: int = 8,
        ensemble: int = 3,
        hidden: int = 64,
        seed: int = 42,
        lr: float = 1e-3,
    ):
        self.z_dim = z_dim
        self.action_dim = action_dim
        self.ensemble = max(1, int(ensemble))
        torch.manual_seed(seed)
        self.models = [_DynamicsNet(z_dim, action_dim, hidden) for _ in range(self.ensemble)]
        params = []
        for m in self.models:
            params += list(m.parameters())
        self.opt = torch.optim.Adam(params, lr=lr)
        self.train_steps = 0

    def _prep_action(self, action: np.ndarray | Sequence[float]) -> np.ndarray:
        a = np.asarray(action, dtype=np.float64).reshape(-1)
        if a.shape[0] < self.action_dim:
            a = np.pad(a, (0, self.action_dim - a.shape[0]))
        else:
            a = a[: self.action_dim]
        return a

    def _prep_z(self, z: np.ndarray | Sequence[float]) -> np.ndarray:
        v = np.asarray(z, dtype=np.float64).reshape(-1)
        if v.shape[0] < self.z_dim:
            v = np.pad(v, (0, self.z_dim - v.shape[0]))
        else:
            v = v[: self.z_dim]
        return v

    @torch.no_grad()
    def predict(self, z: np.ndarray | Sequence[float], action: np.ndarray | Sequence[float]) -> dict:
        zt = torch.tensor(self._prep_z(z), dtype=torch.float32).unsqueeze(0)
        at = torch.tensor(self._prep_action(action), dtype=torch.float32).unsqueeze(0)
        preds = []
        for m in self.models:
            m.eval()
            preds.append(m(zt, at).squeeze(0).numpy())
        stack = np.stack(preds, axis=0)
        mean = stack.mean(axis=0)
        var = stack.var(axis=0)
        uncertainty = float(var.mean())
        return {
            "z_pred": mean.astype(np.float64),
            "variance": var.astype(np.float64),
            "uncertainty": uncertainty,
            "ensemble_size": self.ensemble,
        }

    def prediction_error(
        self,
        z: np.ndarray | Sequence[float],
        action: np.ndarray | Sequence[float],
        z_next: np.ndarray | Sequence[float],
    ) -> float:
        out = self.predict(z, action)
        zt = self._prep_z(z_next)
        return float(np.linalg.norm(out["z_pred"] - zt))

    def train_step(
        self,
        z: np.ndarray | Sequence[float],
        action: np.ndarray | Sequence[float],
        z_next: np.ndarray | Sequence[float],
    ) -> float:
        zt = torch.tensor(self._prep_z(z), dtype=torch.float32).unsqueeze(0)
        at = torch.tensor(self._prep_action(action), dtype=torch.float32).unsqueeze(0)
        target = torch.tensor(self._prep_z(z_next), dtype=torch.float32).unsqueeze(0)
        self.opt.zero_grad()
        loss_t = torch.tensor(0.0)
        for m in self.models:
            m.train()
            pred = m(zt, at)
            loss_t = loss_t + torch.mean((pred - target) ** 2)
        loss_t = loss_t / self.ensemble
        loss_t.backward()
        self.opt.step()
        self.train_steps += 1
        return float(loss_t.item())

    def uncertainty_reduction(
        self,
        z_before: np.ndarray | Sequence[float],
        action: np.ndarray | Sequence[float],
        z_after: np.ndarray | Sequence[float],
    ) -> float:
        """IG proxy: uncertainty(z,a) before observing vs residual error after."""
        u_before = float(self.predict(z_before, action)["uncertainty"])
        # After observing z_after, ensemble disagreement about that transition residual:
        err = self.prediction_error(z_before, action, z_after)
        u_after = float(err)  # realized surprise as post uncertainty proxy
        return float(max(0.0, u_before - 0.1 * u_after))
