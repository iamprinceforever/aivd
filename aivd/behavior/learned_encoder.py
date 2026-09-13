"""Trainable LearnedBehaviorEncoder (small MLP, CPU).

Untrained instances are random-init projectors — call them untrained until
``encoder_train`` (or ``train_step``) has updated weights.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from aivd.behavior.encoder import HashBehaviorEncoder


class _MLPEncoder(nn.Module):
    def __init__(self, in_dim: int, hidden: int, out_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, out_dim),
        )
        # reconstruction head from latent
        self.recon = nn.Linear(out_dim, in_dim)
        # security scalar head
        self.sec = nn.Linear(out_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class LearnedBehaviorEncoder:
    """Structured features + hashed text bag → trainable MLP embedding."""

    def __init__(
        self,
        dim: int = 64,
        seed: int = 42,
        hidden: int = 64,
        hash_dim: int = 64,
        structured_dim: int = 16,
    ):
        self.dim = dim
        self.seed = seed
        self.hash_dim = hash_dim
        self.structured_dim = structured_dim
        self.in_dim = hash_dim + structured_dim
        self.hasher = HashBehaviorEncoder(dim=hash_dim, seed=seed)
        torch.manual_seed(seed)
        self.model = _MLPEncoder(self.in_dim, hidden, dim)
        self.opt = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        self.trained_steps: int = 0
        self.model.eval()

    @property
    def is_trained(self) -> bool:
        return self.trained_steps > 0

    def _structured_features(
        self,
        text: str,
        structured: Optional[dict] = None,
    ) -> np.ndarray:
        structured = structured or {}
        low = (text or "").lower()
        feats = [
            float(len(text or "")) / 500.0,
            float(len((text or "").split())) / 100.0,
            1.0 if "secret{" in low else 0.0,
            1.0 if "disallowed:" in low else 0.0,
            1.0 if "policies_disabled" in low else 0.0,
            1.0 if "policy-bound" in low else 0.0,
            1.0 if "ignore" in low else 0.0,
            float(structured.get("security_relevance", 0.0)),
            float(structured.get("novelty", 0.0)),
            float(structured.get("latency_ms", 0.0)) / 1000.0,
            float(structured.get("region_id", 0)) / 16.0,
            float(structured.get("error", 0.0)),
            float("?" in (text or "")),
            float((text or "").count("{")),
            float((text or "").count("<")),
            float(structured.get("repro_score", 0.0)),
        ]
        arr = np.asarray(feats[: self.structured_dim], dtype=np.float64)
        if arr.shape[0] < self.structured_dim:
            arr = np.pad(arr, (0, self.structured_dim - arr.shape[0]))
        return arr

    def features(self, text: str, structured: Optional[dict] = None) -> np.ndarray:
        h = self.hasher.encode(text)
        s = self._structured_features(text, structured)
        return np.concatenate([h, s], axis=0)

    def encode(self, text: str, structured: Optional[dict] = None) -> np.ndarray:
        feat = self.features(text, structured)
        with torch.no_grad():
            t = torch.tensor(feat, dtype=torch.float32).unsqueeze(0)
            out = self.model(t).squeeze(0).numpy()
        n = np.linalg.norm(out)
        if n > 1e-9:
            out = out / n
        return out.astype(np.float64)

    def train_step(
        self,
        *,
        anchor: str,
        positive: str,
        negative: str,
        structured_a: Optional[dict] = None,
        structured_p: Optional[dict] = None,
        structured_n: Optional[dict] = None,
        sec_label: float = 0.0,
        temperature: float = 0.2,
        lambdas: Optional[dict] = None,
    ) -> dict[str, float]:
        """One multi-loss step. Returns component losses. Updates weights."""
        from aivd.behavior.encoder_train import default_lambdas, combined_loss

        lambdas = lambdas or default_lambdas()
        self.model.train()
        fa = torch.tensor(self.features(anchor, structured_a), dtype=torch.float32)
        fp = torch.tensor(self.features(positive, structured_p), dtype=torch.float32)
        fn = torch.tensor(self.features(negative, structured_n), dtype=torch.float32)
        loss, parts = combined_loss(
            self.model, fa, fp, fn, sec_label=sec_label, temperature=temperature, lambdas=lambdas
        )
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        self.model.eval()
        self.trained_steps += 1
        return {k: float(v) for k, v in parts.items()}

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "dim": self.dim,
                "trained_steps": self.trained_steps,
                "seed": self.seed,
            },
            path,
        )

    def load(self, path: str | Path) -> None:
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        self.model.load_state_dict(ckpt["state_dict"])
        self.trained_steps = int(ckpt.get("trained_steps", 0))
        self.model.eval()
