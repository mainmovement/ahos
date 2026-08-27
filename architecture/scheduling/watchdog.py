#!/usr/bin/env python3
"""AHOS Scheduler Watchdog (Phase 7 — audit gap C).

Detects "silent death" of the 24/7 observation engine: components that record
heartbeats in `scheduler_heartbeats` but have gone quiet. This module performs
NO network I/O and mutates nothing — it is a read-only probe designed to be
wired into systemd `WatchdogSec=`/`OnFailure=`, docker healthchecks, or cron.

Month 1 hardening: connections are opened in SQLite read-only URI mode, so a
probe can never create or modify a store (previously a plain connect() created
an empty file when the store was missing).

Exit codes (fail-closed, per AHOS laws):
    0 = OK           — all recorded components beat within max_age_sec
    2 = STALE        — at least one component is silent for too long
    3 = NO_HEARTBEATS — the system has never recorded a heartbeat (fresh or dead)

Usage:
    python -m architecture.scheduling.watchdog --status
    python -m architecture.scheduling.watchdog --status --max-age-sec 300 --json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # direct-script execution support
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.paths import connect_sqlite_ro, get_local_db_path  # noqa: E402

DEFAULT_MAX_AGE_SEC = 300.0


def _connect_ro(db_path: str) -> sqlite3.Connection:
    """Read-only connection — can NEVER create or modify a store."""
    return connect_sqlite_ro(db_path)


def stale_components(db_path: str | None = None,
                     max_age_sec: float = DEFAULT_MAX_AGE_SEC,
                     now: float | None = None) -> list[dict[str, Any]]:
    """Returns components whose last heartbeat is older than `max_age_sec`.

    Missing database or missing table yields an empty list — callers needing
    freshness guarantees must also check `has_any_heartbeat()`.
    """
    ts = time.time() if now is None else now
    try:
        conn = _connect_ro(db_path or get_local_db_path())
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT component, last_heartbeat_ts, last_heartbeat_utc, downtime_detected_sec "
            "FROM scheduler_heartbeats"
        ).fetchall()
        conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return []

    stale: list[dict[str, Any]] = []
    for row in rows:
        age = ts - row["last_heartbeat_ts"]
        if age > max_age_sec:
            stale.append({
                "component": row["component"],
                "last_heartbeat_ts": row["last_heartbeat_ts"],
                "last_heartbeat_utc": row["last_heartbeat_utc"],
                "age_sec": round(age, 1),
            })
    return sorted(stale, key=lambda c: -c["age_sec"])


def has_any_heartbeat(db_path: str | None = None) -> bool:
    """True if at least one heartbeat row exists (system has run at least once)."""
    try:
        conn = _connect_ro(db_path or get_local_db_path())
        row = conn.execute("SELECT COUNT(*) FROM scheduler_heartbeats").fetchone()
        conn.close()
        return bool(row and row[0] > 0)
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return False


def watchdog_report(db_path: str | None = None,
                    max_age_sec: float = DEFAULT_MAX_AGE_SEC,
                    now: float | None = None) -> dict[str, Any]:
    """Structured watchdog verdict. `status` is one of OK | STALE | NO_HEARTBEATS."""
    if not has_any_heartbeat(db_path):
        return {
            "status": "NO_HEARTBEATS",
            "checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "max_age_sec": max_age_sec,
            "stale_components": [],
            "detail": "no heartbeat ever recorded — fresh install or silent death",
        }
    stale = stale_components(db_path, max_age_sec=max_age_sec, now=now)
    return {
        "status": "STALE" if stale else "OK",
        "checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "max_age_sec": max_age_sec,
        "stale_components": stale,
        "detail": (f"{len(stale)} component(s) silent beyond {max_age_sec}s"
                   if stale else "all components beating"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AHOS scheduler heartbeat watchdog (read-only probe)")
    parser.add_argument("--status", action="store_true", help="Print watchdog report and exit with code")
    parser.add_argument("--db-path", default=None, help="Path to ahos_local sqlite (default: resolved)")
    parser.add_argument("--max-age-sec", type=float, default=DEFAULT_MAX_AGE_SEC)
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args(argv)

    report = watchdog_report(args.db_path, max_age_sec=args.max_age_sec)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"[watchdog] status={report['status']} detail={report['detail']}")
        for comp in report["stale_components"]:
            print(f"  STALE: {comp['component']} silent for {comp['age_sec']}s "
                  f"(last beat {comp['last_heartbeat_utc']})")

    return {"OK": 0, "STALE": 2, "NO_HEARTBEATS": 3}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
