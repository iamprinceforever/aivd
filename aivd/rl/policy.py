"""Actor-critic networks for state-conditioned PPO."""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.distributions import Normal


class ActorCritic(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden: int = 64):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
        )
        self.mu = nn.Linear(hidden, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim))
        self.v = nn.Linear(hidden, 1)
        # explicit explore vs exploit logit head (dynamic, not fixed 50/50)
        self.explore_logit = nn.Linear(hidden, 1)

    def forward(self, state: torch.Tensor):
        h = self.backbone(state)
        mu = torch.tanh(self.mu(h))
        std = torch.exp(self.log_std.clamp(-3.0, 0.5))
        dist = Normal(mu, std)
        value = self.v(h).squeeze(-1)
        explore_p = torch.sigmoid(self.explore_logit(h)).squeeze(-1)
        return dist, value, explore_p
