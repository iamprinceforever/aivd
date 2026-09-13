"""Optional tiny Torch encoder (CPU) — contrastive-capable projector over hashed bags.

Config: embedding_backend: hashing|torch (hashing remains default fallback).
No pretrained downloads; optional contrastive fine-tune on (prompt, response, label) triples.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from aivd.behavior.encoder import BehaviorEncoder


class TinyProjector(nn.Module):
    def __init__(self, dim: int = 64, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TorchBehaviorEncoder:
    """Hash features → small learned projector (CPU). Optional contrastive updates."""

    def __init__(self, dim: int = 64, seed: int = 42, hidden: int = 64):
        self.base = BehaviorEncoder(dim=dim, seed=seed)
        self.dim = dim
        torch.manual_seed(seed)
        self.model = TinyProjector(dim=dim, hidden=hidden)
        self.opt = torch.optim.Adam(self.model.parameters(), lr=1e-3)
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

    def contrastive_step(
        self,
        anchor_text: str,
        positive_text: str,
        negative_text: str,
        temperature: float = 0.2,
    ) -> float:
        """One InfoNCE-style step on hashed bags (optional path)."""
        self.model.train()
        a = torch.tensor(self.base.encode(anchor_text), dtype=torch.float32)
        p = torch.tensor(self.base.encode(positive_text), dtype=torch.float32)
        n = torch.tensor(self.base.encode(negative_text), dtype=torch.float32)
        za = F.normalize(self.model(a.unsqueeze(0)), dim=-1)
        zp = F.normalize(self.model(p.unsqueeze(0)), dim=-1)
        zn = F.normalize(self.model(n.unsqueeze(0)), dim=-1)
        pos = (za * zp).sum(dim=-1) / temperature
        neg = (za * zn).sum(dim=-1) / temperature
        # logits: [pos, neg]
        logits = torch.cat([pos, neg], dim=0).unsqueeze(0)
        labels = torch.zeros(1, dtype=torch.long)
        loss = F.cross_entropy(logits, labels)
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        self.model.eval()
        return float(loss.item())


def make_encoder(backend: str = "hashing", dim: int = 64, seed: int = 42):
    """Factory: hashing (default) or torch projector."""
    if backend == "torch":
        return TorchBehaviorEncoder(dim=dim, seed=seed)
    return BehaviorEncoder(dim=dim, seed=seed)
