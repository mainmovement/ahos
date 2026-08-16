#!/usr/bin/env python3
"""AHOS Operational Metrics & Observability Collector (Phase XXIV - Section 4).

Tracks:
  - Cycle execution time & latency
  - Provider latency & error counts
  - Missed observation windows
  - Data freshness distribution
  - Scoring throughput & score distribution
  - Alerts generated
  - Database writes
  - Recovery & restart events

Every event carries run_id, timestamp, component, status, and evidence_refs.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from config.paths import get_local_db_path

SCHEMA_METRICS = """
CREATE TABLE IF NOT EXISTS runtime_operational_metrics (
  event_id         TEXT PRIMARY KEY,
  run_id           TEXT NOT NULL,
  timestamp_utc    TEXT NOT NULL,
  component        TEXT NOT NULL,
  metric_name      TEXT NOT NULL,
  metric_value     REAL NOT NULL,
  status           TEXT NOT NULL,    -- OK | WARN | ERROR | RECOVERED
  evidence_refs    TEXT NOT NULL,    -- JSON array of references
  meta_json        TEXT
);
"""


@dataclass
class OperationalMetricEvent:
    event_id: str
    run_id: str
    component: str
    metric_name: str
    metric_value: float
    status: str                                  # OK | WARN | ERROR | RECOVERED
    evidence_refs: list[str] = field(default_factory=list)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    meta: dict[str, Any] = field(default_factory=dict)


class OperationalMetricsTracker:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_local_db_path()
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA_METRICS)
        conn.close()

    def record_metric(self, *, run_id: str, component: str,
                      metric_name: str, metric_value: float,
                      status: str = "OK",
                      evidence_refs: list[str] | None = None,
                      meta: dict[str, Any] | None = None) -> str:
        eid = f"met_{int(time.time()*1000)}_{component[:6]}_{metric_name[:8]}"
        ev_refs = evidence_refs or []
        ts_utc = datetime.now(timezone.utc).isoformat()
        meta_d = meta or {}

        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT INTO runtime_operational_metrics(
                    event_id, run_id, timestamp_utc, component, metric_name,
                    metric_value, status, evidence_refs, meta_json
                ) VALUES (?,?,?,?,?,?,?,?,?)""",
                (eid, run_id, ts_utc, component, metric_name, float(metric_value), status, json.dumps(ev_refs), json.dumps(meta_d))
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        return eid

    def get_recent_metrics(self, limit: int = 50) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM runtime_operational_metrics ORDER BY rowid DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
