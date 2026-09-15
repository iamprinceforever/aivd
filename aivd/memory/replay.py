"""Persistent experience replay surviving process death (SQLite + prioritized sampling)."""
from __future__ import annotations

import json
import math
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


class ExperienceReplay:
    """SQLite-backed transitions: state, action, reward, embeddings, region, novelty, …"""

    def __init__(self, db_path: Path | str = "aivd_data/continual_memory/replay.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transitions (
                    id TEXT PRIMARY KEY,
                    namespace TEXT,
                    run_id TEXT,
                    target_id TEXT,
                    region_id TEXT,
                    state_json TEXT,
                    action_json TEXT,
                    reward REAL,
                    embedding_json TEXT,
                    novelty REAL,
                    global_novelty REAL,
                    security REAL,
                    verification REAL,
                    priority REAL,
                    vuln_id TEXT,
                    trigger_family TEXT,
                    strategy TEXT,
                    meta_json TEXT,
                    created_at REAL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_replay_ns ON transitions(namespace)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_replay_pri ON transitions(priority DESC)"
            )

    def add(
        self,
        *,
        state: list[float] | dict[str, Any],
        action: list[float] | str | dict[str, Any],
        reward: float,
        embedding: list[float] | None = None,
        region_id: str = "",
        novelty: float = 0.0,
        global_novelty: float = 0.0,
        security: float = 0.0,
        verification: float = 0.0,
        run_id: str = "",
        target_id: str = "",
        namespace: str = "target",
        vuln_id: str = "",
        trigger_family: str = "",
        strategy: str = "",
        meta: Optional[dict[str, Any]] = None,
        priority: float | None = None,
    ) -> str:
        tid = uuid4().hex[:16]
        # Prioritize unique / high security / high global novelty — not newest-only
        if priority is None:
            unique_boost = 1.0 if vuln_id else 0.0
            priority = (
                0.35 * abs(float(reward))
                + 0.25 * float(security)
                + 0.20 * float(global_novelty)
                + 0.15 * float(novelty)
                + 0.20 * unique_boost
            )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO transitions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    tid,
                    namespace,
                    run_id,
                    target_id,
                    str(region_id),
                    json.dumps(state),
                    json.dumps(action),
                    float(reward),
                    json.dumps(embedding or []),
                    float(novelty),
                    float(global_novelty),
                    float(security),
                    float(verification),
                    float(priority),
                    vuln_id or "",
                    trigger_family or "",
                    strategy or "",
                    json.dumps(meta or {}),
                    time.time(),
                ),
            )
        return tid

    def count(self, namespace: str | None = None) -> int:
        with self._connect() as conn:
            if namespace:
                return int(
                    conn.execute(
                        "SELECT COUNT(*) FROM transitions WHERE namespace=?", (namespace,)
                    ).fetchone()[0]
                )
            return int(conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0])

    def sample(
        self,
        n: int = 32,
        *,
        namespace: str | None = None,
        prioritized: bool = True,
    ) -> list[dict[str, Any]]:
        """Prioritized sampling (softmax over priority); not newest-only."""
        with self._connect() as conn:
            if namespace:
                rows = conn.execute(
                    "SELECT * FROM transitions WHERE namespace=?", (namespace,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM transitions").fetchall()
        if not rows:
            return []
        items = [dict(r) for r in rows]
        if not prioritized or len(items) <= n:
            # still shuffle by priority weight if possible
            items.sort(key=lambda r: -float(r["priority"]))
            return items[:n]

        import random

        weights = []
        for r in items:
            w = math.exp(min(5.0, float(r["priority"])))
            weights.append(w)
        total = sum(weights) or 1.0
        probs = [w / total for w in weights]
        # sample without replacement
        chosen_idx: list[int] = []
        pool = list(range(len(items)))
        pool_probs = list(probs)
        for _ in range(min(n, len(items))):
            # weighted choice
            x = random.random()
            cum = 0.0
            pick = pool[-1]
            for i, idx in enumerate(pool):
                cum += pool_probs[i]
                if x <= cum:
                    pick = idx
                    del pool[i]
                    del pool_probs[i]
                    break
            chosen_idx.append(pick)
            s = sum(pool_probs) or 1.0
            pool_probs = [p / s for p in pool_probs]
        return [items[i] for i in chosen_idx]

    def stats(self, namespace: str | None = None) -> dict[str, Any]:
        with self._connect() as conn:
            if namespace:
                rows = conn.execute(
                    "SELECT reward, priority, novelty, global_novelty, security FROM transitions WHERE namespace=?",
                    (namespace,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT reward, priority, novelty, global_novelty, security FROM transitions"
                ).fetchall()
        n = len(rows)
        if n == 0:
            return {"n": 0, "namespace": namespace}
        rewards = [float(r["reward"]) for r in rows]
        return {
            "n": n,
            "namespace": namespace,
            "mean_reward": sum(rewards) / n,
            "mean_priority": sum(float(r["priority"]) for r in rows) / n,
            "mean_global_novelty": sum(float(r["global_novelty"]) for r in rows) / n,
            "mean_security": sum(float(r["security"]) for r in rows) / n,
        }
