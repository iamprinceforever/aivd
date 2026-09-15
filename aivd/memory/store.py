"""SQLite experiment / finding store."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from aivd.core.types import Experiment, Finding, FindingStatus, Observation, RewardBreakdown


class ExperimentStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    explorer TEXT,
                    strategy TEXT,
                    prompt TEXT,
                    target_id TEXT,
                    seed INTEGER,
                    meta TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    response_text TEXT,
                    latency_ms REAL,
                    error TEXT,
                    features TEXT,
                    embedding TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    observation_id TEXT,
                    status TEXT,
                    security_relevance REAL,
                    novelty REAL,
                    impact_score REAL,
                    confidence REAL,
                    repro_score REAL,
                    summary TEXT,
                    ground_truth_hit TEXT,
                    evidence TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS rewards (
                    experiment_id TEXT PRIMARY KEY,
                    breakdown TEXT,
                    total REAL
                );
                """
            )

    def save_probe(
        self,
        experiment: Experiment,
        observation: Observation,
        finding: Finding,
        reward: RewardBreakdown,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO experiments VALUES (?,?,?,?,?,?,?,?)",
                (
                    experiment.id,
                    experiment.explorer,
                    experiment.strategy,
                    experiment.prompt,
                    experiment.target_id,
                    experiment.seed,
                    json.dumps(experiment.meta),
                    experiment.created_at.isoformat(),
                ),
            )
            conn.execute(
                "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?)",
                (
                    observation.id,
                    observation.experiment_id,
                    observation.response_text,
                    observation.latency_ms,
                    observation.error,
                    json.dumps(observation.features),
                    json.dumps(observation.embedding),
                    observation.created_at.isoformat(),
                ),
            )
            conn.execute(
                "INSERT OR REPLACE INTO findings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    finding.id,
                    finding.experiment_id,
                    finding.observation_id,
                    finding.status.value,
                    finding.security_relevance,
                    finding.novelty,
                    finding.impact_score,
                    finding.confidence,
                    finding.repro_score,
                    finding.summary,
                    finding.ground_truth_hit,
                    json.dumps(finding.evidence),
                    finding.created_at.isoformat(),
                    finding.updated_at.isoformat(),
                ),
            )
            conn.execute(
                "INSERT OR REPLACE INTO rewards VALUES (?,?,?)",
                (experiment.id, reward.model_dump_json(), reward.total),
            )

    def count_experiments(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0])

    def list_findings(self, status: Optional[FindingStatus] = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM findings WHERE status=?", (status.value,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM findings").fetchall()
            return [dict(r) for r in rows]

    def list_experiments(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM experiments").fetchall()]

    def recent_prompts(self, n: int = 50) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT prompt FROM experiments ORDER BY created_at DESC LIMIT ?", (n,)
            ).fetchall()
            return [r["prompt"] for r in rows]
