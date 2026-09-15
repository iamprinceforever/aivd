"""Policy / checkpoint store — save/load RL weights + config fingerprint."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

import torch


def config_fingerprint(config: dict[str, Any] | None = None, **extra: Any) -> str:
    payload = dict(config or {})
    payload.update(extra)
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


class CheckpointStore:
    """Filesystem checkpoint store for PPO (and optional WM / encoder)."""

    def __init__(self, root: Path | str = "aivd_data/checkpoints"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str, namespace: str = "global") -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
        ns = "".join(c if c.isalnum() or c in "-_." else "_" for c in namespace)
        d = self.root / ns
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{safe}.pt"

    def save(
        self,
        name: str,
        *,
        policy_state: dict[str, Any],
        optimizer_state: Optional[dict[str, Any]] = None,
        world_model_state: Optional[dict[str, Any]] = None,
        encoder_state: Optional[dict[str, Any]] = None,
        meta: Optional[dict[str, Any]] = None,
        namespace: str = "global",
        config: Optional[dict[str, Any]] = None,
    ) -> Path:
        fp = config_fingerprint(config, name=name, namespace=namespace)
        payload = {
            "policy_state": policy_state,
            "optimizer_state": optimizer_state,
            "world_model_state": world_model_state,
            "encoder_state": encoder_state,
            "meta": meta or {},
            "config_fingerprint": fp,
            "config": config or {},
            "namespace": namespace,
            "name": name,
        }
        path = self.path_for(name, namespace=namespace)
        torch.save(payload, path)
        # Sidecar JSON for inspect without loading tensors
        side = path.with_suffix(".json")
        side.write_text(
            json.dumps(
                {
                    "name": name,
                    "namespace": namespace,
                    "config_fingerprint": fp,
                    "meta": meta or {},
                    "path": str(path),
                },
                indent=2,
            )
        )
        return path

    def load(self, name: str, namespace: str = "global") -> dict[str, Any]:
        path = self.path_for(name, namespace=namespace)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        return torch.load(path, map_location="cpu", weights_only=False)

    def exists(self, name: str, namespace: str = "global") -> bool:
        return self.path_for(name, namespace=namespace).exists()

    def list_checkpoints(self, namespace: str | None = None) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        roots = [self.root / namespace] if namespace else list(self.root.iterdir()) if self.root.exists() else []
        if namespace:
            roots = [self.root / namespace]
        elif self.root.exists():
            roots = [p for p in self.root.iterdir() if p.is_dir()]
        for d in roots:
            if not d.is_dir():
                continue
            for p in d.glob("*.json"):
                try:
                    out.append(json.loads(p.read_text()))
                except Exception:
                    out.append({"path": str(p), "error": "unreadable"})
        return out
