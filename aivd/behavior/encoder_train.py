"""Training losses for LearnedBehaviorEncoder (contrastive + temporal + recon + security)."""
from __future__ import annotations

from typing import Any

import torch
import torch.nn.functional as F


def default_lambdas() -> dict[str, float]:
    return {
        "contrastive": 1.0,
        "temporal": 0.25,
        "reconstruction": 0.1,
        "security": 0.5,
    }


def combined_loss(
    model: Any,
    feat_a: torch.Tensor,
    feat_p: torch.Tensor,
    feat_n: torch.Tensor,
    *,
    sec_label: float = 0.0,
    temperature: float = 0.2,
    lambdas: dict[str, float] | None = None,
    feat_next: torch.Tensor | None = None,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Multi-objective loss. ``feat_*`` are input feature bags (hash+structured)."""
    lam = lambdas or default_lambdas()
    if feat_a.dim() == 1:
        feat_a = feat_a.unsqueeze(0)
        feat_p = feat_p.unsqueeze(0)
        feat_n = feat_n.unsqueeze(0)

    za = F.normalize(model(feat_a), dim=-1)
    zp = F.normalize(model(feat_p), dim=-1)
    zn = F.normalize(model(feat_n), dim=-1)

    # Contrastive InfoNCE-style (pos vs neg)
    pos = (za * zp).sum(dim=-1) / temperature
    neg = (za * zn).sum(dim=-1) / temperature
    logits = torch.stack([pos, neg], dim=-1)
    labels = torch.zeros(logits.size(0), dtype=torch.long)
    l_con = F.cross_entropy(logits, labels)

    # Temporal: if next features provided, pull za toward encode(next); else use positive as proxy
    if feat_next is not None:
        if feat_next.dim() == 1:
            feat_next = feat_next.unsqueeze(0)
        z_next = F.normalize(model(feat_next), dim=-1)
        l_temp = 1.0 - (za * z_next).sum(dim=-1).mean()
    else:
        l_temp = 1.0 - (za * zp).sum(dim=-1).mean()

    # Reconstruction of input features from latent
    recon_a = model.recon(za)
    l_rec = F.mse_loss(recon_a, feat_a)

    # Security representation: predict security label from latent
    sec_pred = model.sec(za).squeeze(-1)
    target = torch.full_like(sec_pred, float(sec_label))
    l_sec = F.mse_loss(sec_pred, target)

    total = (
        lam.get("contrastive", 1.0) * l_con
        + lam.get("temporal", 0.25) * l_temp
        + lam.get("reconstruction", 0.1) * l_rec
        + lam.get("security", 0.5) * l_sec
    )
    parts = {
        "total": float(total.detach()),
        "contrastive": float(l_con.detach()),
        "temporal": float(l_temp.detach()),
        "reconstruction": float(l_rec.detach()),
        "security": float(l_sec.detach()),
    }
    return total, parts
