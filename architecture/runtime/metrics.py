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

Telemetry write failures MUST NOT crash the runtime (fail-open for the
caller), but MUST NOT disappear silently: failures are counted, retained
in a bounded ring buffer, and emitted via the standard logging channel so
observability of observability remains auditable.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
import weakref
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import get_local_db_path

log = logging.getLogger("ahos.runtime.metrics")

ALLOWED_STATUSES = frozenset({"OK", "WARN", "ERROR", "RECOVERED"})

# Process-local registry so read-only health snapshots can observe in-process
# write failures without constructing a new tracker (which would mkdir/CREATE).
_TRACKER_REGISTRY: weakref.WeakSet = weakref.WeakSet()
_TRACKER_REGISTRY_LOCK = threading.Lock()

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


@dataclass(frozen=True)
class MetricWriteFailure:
    """Auditable record of a telemetry write that failed."""
    timestamp_utc: str
    event_id: str
    error_type: str
    error_message: str
    component: str
    metric_name: str


class OperationalMetricsTracker:
    """SQLite-backed operational metrics with fail-open, observable writes."""

    def __init__(self, db_path: str | None = None, *, max_failure_history: int = 64):
        self.db_path = db_path or get_local_db_path()
        self._lock = threading.Lock()
        self._write_failures = 0
        self._failure_history: deque[MetricWriteFailure] = deque(maxlen=max_failure_history)
        self._init_db()
        with _TRACKER_REGISTRY_LOCK:
            _TRACKER_REGISTRY.add(self)

    @classmethod
    def registered_telemetry_health(cls) -> dict[str, Any] | None:
        """Merge telemetry_health from live in-process trackers, or None if none.

        Never constructs a tracker (no mkdir / CREATE TABLE side effects).
        """
        with _TRACKER_REGISTRY_LOCK:
            trackers = list(_TRACKER_REGISTRY)
        if not trackers:
            return None
        total_failures = 0
        recent: list[dict[str, Any]] = []
        for t in trackers:
            h = t.telemetry_health()
            total_failures += int(h.get("write_failures") or 0)
            recent.extend(list(h.get("recent_failures") or []))
        recent.sort(key=lambda r: str(r.get("timestamp_utc") or ""), reverse=True)
        return {
            "write_failures": total_failures,
            "recent_failures": recent[:64],
            "status": "OK" if total_failures == 0 else "DEGRADED",
            "source": "in_process_registry",
            "tracker_count": len(trackers),
        }

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            conn.executescript(SCHEMA_METRICS)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _validate_status(status: str) -> str:
        s = (status or "").strip().upper()
        if s not in ALLOWED_STATUSES:
            raise ValueError(
                f"invalid metric status {status!r}; allowed={sorted(ALLOWED_STATUSES)}"
            )
        return s

    @staticmethod
    def _json_dump(value: Any, *, label: str) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            raise ValueError(f"{label} is not JSON-serializable: {e}") from e

    def record_metric(
        self,
        *,
        run_id: str,
        component: str,
        metric_name: str,
        metric_value: float,
        status: str = "OK",
        evidence_refs: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> str:
        """Record one metric. Never raises for storage failures.

        Returns the allocated event_id even when the SQLite write fails, so
        callers can correlate. Use :meth:`telemetry_health` to observe write
        failures. Invalid arguments (status / JSON) raise ValueError — those
        are programmer errors, not environmental telemetry faults.
        """
        status_n = self._validate_status(status)
        ev_refs = list(evidence_refs or [])
        meta_d = dict(meta or {})
        # Collision-resistant: ms timestamp alone collides under concurrency.
        eid = (
            f"met_{int(time.time() * 1000)}_{uuid.uuid4().hex[:12]}_"
            f"{component[:6]}_{metric_name[:8]}"
        )
        ts_utc = datetime.now(timezone.utc).isoformat()
        refs_json = self._json_dump(ev_refs, label="evidence_refs")
        meta_json = self._json_dump(meta_d, label="meta")

        conn: sqlite3.Connection | None = None
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, timeout=5.0)
                conn.execute(
                    """INSERT INTO runtime_operational_metrics(
                        event_id, run_id, timestamp_utc, component, metric_name,
                        metric_value, status, evidence_refs, meta_json
                    ) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        eid,
                        run_id,
                        ts_utc,
                        component,
                        metric_name,
                        float(metric_value),
                        status_n,
                        refs_json,
                        meta_json,
                    ),
                )
                conn.commit()
        except Exception as e:
            self._note_write_failure(
                event_id=eid,
                error=e,
                component=component,
                metric_name=metric_name,
            )
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        return eid

    def _note_write_failure(
        self,
        *,
        event_id: str,
        error: BaseException,
        component: str,
        metric_name: str,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        failure = MetricWriteFailure(
            timestamp_utc=ts,
            event_id=event_id,
            error_type=type(error).__name__,
            error_message=str(error)[:500],
            component=component,
            metric_name=metric_name,
        )
        with self._lock:
            self._write_failures += 1
            self._failure_history.append(failure)
        log.warning(
            "operational metric write failed event_id=%s component=%s "
            "metric=%s error=%s: %s",
            event_id,
            component,
            metric_name,
            type(error).__name__,
            str(error)[:200],
        )

    def telemetry_health(self) -> dict[str, Any]:
        """Observable status of the metrics writer itself (never empty silence)."""
        with self._lock:
            recent = [
                {
                    "timestamp_utc": f.timestamp_utc,
                    "event_id": f.event_id,
                    "error_type": f.error_type,
                    "error_message": f.error_message,
                    "component": f.component,
                    "metric_name": f.metric_name,
                }
                for f in list(self._failure_history)
            ]
            failures = self._write_failures
        return {
            "write_failures": failures,
            "recent_failures": recent,
            "status": "OK" if failures == 0 else "DEGRADED",
        }

    def get_recent_metrics(self, limit: int = 50) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM runtime_operational_metrics "
                "ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
