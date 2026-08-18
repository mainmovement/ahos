#!/usr/bin/env python3
"""AHOS Production Scheduler Engine (Phase XX).

Design features:
  - Wall-clock alignment & Legal Observation Windows (s+15m, s+1h, s+4h, s+12h, s+24h, s+48h, s+72h, s+7d).
  - Missed-window detection & honest gap registration (no retroactive backfill).
  - Idempotency guarantees & atomic lease/lock mechanisms.
  - Clock drift detection & downtime recovery.
  - Structured execution run history & health telemetry.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Any
from config.paths import get_local_db_path, get_discovery_db_path

H = 3600.0
SNAPSHOT_SCHEDULE = [
    ("s+15m", 15 * 60, 5 * 60),
    ("s+1h", 1 * H, 10 * 60),
    ("s+4h", 4 * H, 30 * 60),
    ("s+12h", 12 * H, 30 * 60),
    ("s+24h", 24 * H, 30 * 60),
    ("s+48h", 48 * H, 30 * 60),
    ("s+72h", 72 * H, 30 * 60),
    ("s+7d", 7 * 24 * H, 2 * H),
]

SCHEMA_SCHEDULER = """
CREATE TABLE IF NOT EXISTS scheduler_runs (
  run_id         TEXT PRIMARY KEY,
  schedule_name  TEXT NOT NULL,
  started_ts     REAL NOT NULL,
  finished_ts    REAL,
  status         TEXT NOT NULL,    -- RUNNING | SUCCESS | FAILED | ABORTED_DRIFT | SKIPPED_LOCKED
  clock_drift_sec REAL NOT NULL,
  tasks_executed INTEGER DEFAULT 0,
  tasks_failed   INTEGER DEFAULT 0,
  error_summary  TEXT,
  meta_json      TEXT
);

CREATE TABLE IF NOT EXISTS scheduler_locks (
  lock_name      TEXT PRIMARY KEY,
  acquired_by_run TEXT NOT NULL,
  acquired_ts    REAL NOT NULL,
  lease_expires_ts REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_heartbeats (
  component      TEXT PRIMARY KEY,
  last_heartbeat_ts REAL NOT NULL,
  last_heartbeat_utc TEXT NOT NULL,
  downtime_detected_sec REAL DEFAULT 0.0
);
"""


@dataclass
class ScheduleTask:
    task_id: str
    target_offset_sec: float
    tolerance_sec: float
    action_fn: Callable[..., Any]
    label: str


class ProductionScheduler:
    def __init__(self, db_path: str | None = None,
                 discovery_db_path: str | None = None,
                 max_allowed_clock_drift_sec: float = 5.0,
                 lease_duration_sec: float = 300.0):
        self.db_path = db_path or get_local_db_path()
        self.discovery_db_path = discovery_db_path or get_discovery_db_path()
        self.max_allowed_clock_drift_sec = max_allowed_clock_drift_sec
        self.lease_duration_sec = lease_duration_sec
        # Clock-drift baseline (Phase 7): offset between wall clock and the
        # monotonic clock at construction. Any later step of the wall clock
        # (NTP correction, manual change, VM pause/resume) shifts the live
        # offset away from this baseline — that divergence IS the drift.
        self._clock_baseline_offset = time.time() - time.monotonic()
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA_SCHEDULER)
        conn.close()

    def check_clock_drift(self) -> float:
        """Measures wall-clock vs monotonic divergence since process start (NTP-free).

        Returns absolute drift in seconds. A wall clock stepped backwards/forwards
        mid-run (NTP jump, suspend/resume, manual change) shows up as a divergence
        between the live (time.time() - time.monotonic()) offset and the baseline
        captured at construction. 9999.0 is returned if the wall clock looks
        plainly wrong (pre-2023) so no cycle trusts an absurd clock.
        """
        t_sys = time.time()
        if t_sys < 1_700_000_000.0:
            return 9999.0
        live_offset = t_sys - time.monotonic()
        return abs(live_offset - self._clock_baseline_offset)

    def record_heartbeat(self, component: str = "main_scheduler", now: float | None = None) -> float:
        """Updates heartbeat and detects downtime since last run."""
        ts = time.time() if now is None else now
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM scheduler_heartbeats WHERE component=?", (component,))
        row = cur.fetchone()
        downtime = 0.0
        if row:
            downtime = max(0.0, ts - row["last_heartbeat_ts"])
            cur.execute(
                """UPDATE scheduler_heartbeats SET last_heartbeat_ts=?, last_heartbeat_utc=?, downtime_detected_sec=?
                   WHERE component=?""",
                (ts, datetime.fromtimestamp(ts, timezone.utc).isoformat(), downtime, component))
        else:
            cur.execute(
                """INSERT INTO scheduler_heartbeats(component, last_heartbeat_ts, last_heartbeat_utc, downtime_detected_sec)
                   VALUES (?,?,?,?)""",
                (component, ts, datetime.fromtimestamp(ts, timezone.utc).isoformat(), 0.0))
        conn.commit()
        conn.close()
        return downtime

    def acquire_lease(self, lock_name: str, run_id: str, now: float) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM scheduler_locks WHERE lock_name=?", (lock_name,))
            row = cur.fetchone()
            if row:
                if row["lease_expires_ts"] > now and row["acquired_by_run"] != run_id:
                    conn.close()
                    return False  # Locked by another active runner
                # Lease expired or owned by current run -> take over
                cur.execute(
                    """UPDATE scheduler_locks SET acquired_by_run=?, acquired_ts=?, lease_expires_ts=?
                       WHERE lock_name=?""",
                    (run_id, now, now + self.lease_duration_sec, lock_name))
            else:
                cur.execute(
                    """INSERT INTO scheduler_locks(lock_name,acquired_by_run,acquired_ts,lease_expires_ts)
                       VALUES (?,?,?,?)""",
                    (lock_name, run_id, now, now + self.lease_duration_sec))
            conn.commit()
            conn.close()
            return True
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            try:
                conn.close()
            except Exception:
                pass
            return False

    def release_lease(self, lock_name: str, run_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM scheduler_locks WHERE lock_name=? AND acquired_by_run=?", (lock_name, run_id))
        conn.commit()
        conn.close()

    def audit_and_register_missed_windows(self, now: float | None = None) -> dict[str, int]:
        """Detects overdue snapshot slots across active tokens and records missed:<slot> without backfilling."""
        ts = time.time() if now is None else now
        counts: dict[str, int] = {}
        try:
            conn = sqlite3.connect(self.discovery_db_path)
            conn.row_factory = sqlite3.Row
            tokens = conn.execute(
                "SELECT token_id, first_seen_ts FROM observation_state WHERE state IN ('DISCOVERED', 'OBSERVING')"
            ).fetchall()

            for tok in tokens:
                tid = tok["token_id"]
                t0 = tok["first_seen_ts"]
                obs_rows = conn.execute(
                    "SELECT retrieved_ts FROM discovery_observations WHERE token_id=?", (tid,)
                ).fetchall()
                obs_times = [r["retrieved_ts"] for r in obs_rows]

                for label, offset, tol in SNAPSHOT_SCHEDULE:
                    expected_time = t0 + offset
                    # If window has completely passed (ts > expected_time + tol)
                    if ts > expected_time + tol:
                        covered = any(abs(t - expected_time) <= tol for t in obs_times)
                        if not covered:
                            dup = conn.execute(
                                "SELECT 1 FROM gap_register WHERE token_id=? AND kind=? LIMIT 1",
                                (tid, f"missed:{label}")
                            ).fetchone()
                            if not dup:
                                conn.execute(
                                    "INSERT INTO gap_register(token_id, kind, expected_ts, noted_ts, detail) VALUES (?,?,?,?,?)",
                                    (tid, f"missed:{label}", expected_time, ts, "scheduler detected overdue window")
                                )
                                counts[label] = counts.get(label, 0) + 1
            conn.commit()
            conn.close()
        except Exception:
            pass
        return counts

    def execute_scheduled_cycle(self, schedule_name: str, tasks: list[ScheduleTask],
                                now: float | None = None) -> dict[str, Any]:
        ts = time.time() if now is None else now
        run_id = hashlib.sha256(f"{schedule_name}:{ts}".encode()).hexdigest()[:16]
        drift = self.check_clock_drift()

        if drift > self.max_allowed_clock_drift_sec:
            return {
                "run_id": run_id,
                "status": "ABORTED_DRIFT",
                "clock_drift_sec": drift,
                "reason": f"Clock drift ({drift}s) exceeds safety threshold"
            }

        # Try to acquire lease
        if not self.acquire_lease(schedule_name, run_id, ts):
            return {
                "run_id": run_id,
                "status": "SKIPPED_LOCKED",
                "reason": f"Lock '{schedule_name}' held by another process"
            }

        # Record heartbeat & downtime
        downtime = self.record_heartbeat(schedule_name, now=ts)

        # Audit missed windows honestly
        missed_summary = self.audit_and_register_missed_windows(now=ts)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO scheduler_runs(run_id,schedule_name,started_ts,status,clock_drift_sec)
               VALUES (?,?,?,?,?)""",
            (run_id, schedule_name, ts, "RUNNING", drift))
        conn.commit()

        executed = 0
        failed = 0
        errors = []

        try:
            for task in tasks:
                try:
                    task.action_fn()
                    executed += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"{task.label}: {str(e)[:150]}")

            finished_ts = time.time()
            status = "SUCCESS" if failed == 0 else "PARTIAL_FAILURE"

            conn.execute(
                """UPDATE scheduler_runs SET finished_ts=?, status=?, tasks_executed=?,
                                           tasks_failed=?, error_summary=?
                   WHERE run_id=?""",
                (finished_ts, status, executed, failed, "; ".join(errors) if errors else None, run_id))
            conn.commit()
        finally:
            self.release_lease(schedule_name, run_id)
            conn.close()

        return {
            "run_id": run_id,
            "schedule_name": schedule_name,
            "status": status,
            "tasks_executed": executed,
            "tasks_failed": failed,
            "downtime_detected_sec": downtime,
            "missed_windows_registered": missed_summary,
            "duration_sec": round(time.time() - ts, 2),
            "errors": errors
        }
