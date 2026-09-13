"""Behavioral semantic memory — per-region records with namespaces."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from aivd.memory.regions import RegionRecord, region_priority


class SemanticMemory:
    """Persists RegionRecords under run / target / global namespaces."""

    def __init__(self, db_path: Path | str = "aivd_data/continual_memory/semantic.db"):
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
                CREATE TABLE IF NOT EXISTS regions (
                    namespace TEXT NOT NULL,
                    region_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at REAL,
                    PRIMARY KEY (namespace, region_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings_archive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    namespace TEXT,
                    region_id TEXT,
                    embedding_json TEXT,
                    vuln_id TEXT,
                    created_at REAL
                )
                """
            )

    def get(self, region_id: str, namespace: str = "target") -> RegionRecord:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM regions WHERE namespace=? AND region_id=?",
                (namespace, str(region_id)),
            ).fetchone()
        if row is None:
            return RegionRecord(region_id=str(region_id), namespace=namespace)
        data = json.loads(row["payload"])
        data["region_id"] = str(region_id)
        data["namespace"] = namespace
        return RegionRecord.from_dict(data)

    def put(self, record: RegionRecord, namespace: str | None = None) -> None:
        ns = namespace or record.namespace
        record.namespace = ns
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO regions(namespace, region_id, payload, updated_at)
                VALUES (?,?,?,?)
                """,
                (ns, str(record.region_id), json.dumps(record.to_dict()), time.time()),
            )

    def list_regions(self, namespace: str = "target") -> list[RegionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM regions WHERE namespace=?", (namespace,)
            ).fetchall()
        out = []
        for r in rows:
            data = json.loads(r["payload"])
            out.append(RegionRecord.from_dict(data))
        return out

    def add_embedding(
        self,
        embedding: list[float],
        *,
        region_id: str = "",
        namespace: str = "target",
        vuln_id: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO embeddings_archive(namespace, region_id, embedding_json, vuln_id, created_at)
                VALUES (?,?,?,?,?)
                """,
                (namespace, str(region_id), json.dumps(embedding), vuln_id, time.time()),
            )

    def archive_embeddings(self, namespace: str = "target", limit: int = 5000) -> list[list[float]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT embedding_json FROM embeddings_archive
                WHERE namespace=? ORDER BY id DESC LIMIT ?
                """,
                (namespace, limit),
            ).fetchall()
        return [json.loads(r["embedding_json"]) for r in rows]

    def consolidate(self, source_ns: str = "run", target_ns: str = "target") -> dict[str, Any]:
        """Merge run-namespace regions into target/global (union findings, max signals)."""
        src = self.list_regions(source_ns)
        merged = 0
        for rec in src:
            dst = self.get(rec.region_id, namespace=target_ns)
            for v in rec.known_findings:
                if v not in dst.known_findings:
                    dst.known_findings.append(v)
            dst.unique_findings = len(dst.known_findings)
            for f in rec.trigger_families:
                if f not in dst.trigger_families:
                    dst.trigger_families.append(f)
            for k, v in rec.successful_strategies.items():
                dst.successful_strategies[k] = int(dst.successful_strategies.get(k, 0)) + int(v)
            for k, v in rec.failed_strategies.items():
                dst.failed_strategies[k] = int(dst.failed_strategies.get(k, 0)) + int(v)
            for d, c in rec.dimensions_coverage.items():
                dst.dimensions_coverage[d] = max(float(dst.dimensions_coverage.get(d, 0.0)), float(c))
            dst.confirmation_events += rec.confirmation_events
            dst.visit_count += rec.visit_count
            dst.security_relevance_max = max(dst.security_relevance_max, rec.security_relevance_max)
            dst.vulnerability_density = max(dst.vulnerability_density, rec.vulnerability_density)
            # Residual uncertainty: take max of remaining (do not collapse on merge)
            dst.residual_uncertainty = max(dst.residual_uncertainty, rec.residual_uncertainty * 0.9)
            dst.expected_ig = max(dst.expected_ig, rec.expected_ig * 0.9)
            dst.coverage = dst._mean_dim_coverage()
            dst.saturated = dst.is_saturated()
            self.put(dst, namespace=target_ns)
            # also mirror to global
            if target_ns != "global":
                g = self.get(rec.region_id, namespace="global")
                for v in dst.known_findings:
                    if v not in g.known_findings:
                        g.known_findings.append(v)
                g.unique_findings = len(g.known_findings)
                g.residual_uncertainty = max(g.residual_uncertainty, dst.residual_uncertainty)
                g.vulnerability_density = max(g.vulnerability_density, dst.vulnerability_density)
                g.coverage = max(g.coverage, dst.coverage)
                self.put(g, namespace="global")
            merged += 1
        # Clear source namespace after merge into target to avoid double-counting on re-consolidate
        if source_ns == "run" and target_ns == "target" and merged:
            with self._connect() as conn:
                conn.execute("DELETE FROM regions WHERE namespace=?", (source_ns,))
        return {"merged_regions": merged, "source": source_ns, "target": target_ns, "cleared_source": source_ns == "run"}

    def stats(self, namespace: str = "target") -> dict[str, Any]:
        regions = self.list_regions(namespace)
        if not regions:
            return {"n_regions": 0, "namespace": namespace}
        priorities = [region_priority(r) for r in regions]
        return {
            "n_regions": len(regions),
            "namespace": namespace,
            "total_unique_findings": sum(r.unique_findings for r in regions),
            "total_confirmation_events": sum(r.confirmation_events for r in regions),
            "mean_residual_uncertainty": sum(r.residual_uncertainty for r in regions) / len(regions),
            "mean_priority": sum(priorities) / len(priorities),
            "saturated_count": sum(1 for r in regions if r.saturated),
            "region_ids": [r.region_id for r in regions],
        }

    def inspect(self, region_id: str, namespace: str = "target") -> dict[str, Any]:
        rec = self.get(region_id, namespace=namespace)
        return {
            **rec.to_dict(),
            "priority": region_priority(rec),
            "unexplored_coverage": rec.unexplored_coverage(),
            "is_saturated": rec.is_saturated(),
        }
