"""Optional tiny Torch encoder (CPU) over hashed bag features — no pretrained weights."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from aivd.behavior.encoder import BehaviorEncoder


class TinyProjector(nn.Module):
    def __init__(self, dim: int = 64, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TorchBehaviorEncoder:
    """Hash features → small learned projector (identity-init friendly, CPU)."""

    def __init__(self, dim: int = 64, seed: int = 42):
        self.base = BehaviorEncoder(dim=dim, seed=seed)
        self.dim = dim
        torch.manual_seed(seed)
        self.model = TinyProjector(dim=dim)
        self.model.eval()

    def encode(self, text: str) -> np.ndarray:
        vec = self.base.encode(text)
        with torch.no_grad():
            t = torch.tensor(vec, dtype=torch.float32).unsqueeze(0)
            out = self.model(t).squeeze(0).numpy()
        n = np.linalg.norm(out)
        if n > 1e-9:
            out = out / n
        return out.astype(np.float64)
