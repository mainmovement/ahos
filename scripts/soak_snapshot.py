#!/usr/bin/env python3
"""AHOS Month 1 Soak — Evidence Snapshot Tool (Phase 3 instrumentation).

Reads the LIVE operational stores and emits one JSON snapshot per invocation:
scheduler runs/status/drift, heartbeat ages, stuck leases, watchdog verdict,
operational metrics, observation counts, DB integrity. Read-only; never mutates
operational state; missing stores are reported as NO_DATA (never guessed).

Usage:
    python scripts/soak_snapshot.py                     # -> reports/soak_snapshot_<ts>.json
    python scripts/soak_snapshot.py --window-hours 1 --stdout
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import connect_sqlite_ro, get_local_db_path, get_discovery_db_path  # noqa: E402
from architecture.scheduling import watchdog  # noqa: E402


def _query(db_path: str, sql: str, params: tuple = ()) -> list[dict]:
    try:
        conn = connect_sqlite_ro(db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return []


def _integrity(db_path: str) -> str:
    try:
        conn = connect_sqlite_ro(db_path)
        verdict = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        return verdict
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return "NO_DATA"


def snapshot(local_db: str | None = None, discovery_db: str | None = None,
             window_hours: float = 24.0, now: float | None = None) -> dict:
    local_db = local_db or get_local_db_path()
    discovery_db = discovery_db or get_discovery_db_path()
    ts = time.time() if now is None else now
    cutoff = ts - window_hours * 3600.0

    runs = _query(local_db,
                  "SELECT run_id, schedule_name, started_ts, finished_ts, status, "
                  "clock_drift_sec, tasks_executed, tasks_failed, error_summary "
                  "FROM scheduler_runs WHERE started_ts >= ? ORDER BY started_ts", (cutoff,))
    status_counts: dict[str, int] = {}
    for r in runs:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    for r in runs:  # derive observables
        if r["finished_ts"]:
            r["duration_sec"] = round(r["finished_ts"] - r["started_ts"], 3)
            r["start_to_start_gap"] = None  # filled below
    for i in range(1, len(runs)):
        runs[i]["start_to_start_gap"] = round(runs[i]["started_ts"] - runs[i - 1]["started_ts"], 3)

    heartbeats = _query(local_db, "SELECT component, last_heartbeat_ts, downtime_detected_sec "
                                  "FROM scheduler_heartbeats")
    for hb in heartbeats:
        hb["age_sec"] = round(ts - hb["last_heartbeat_ts"], 1)

    locks = _query(local_db, "SELECT lock_name, acquired_by_run, acquired_ts, lease_expires_ts "
                             "FROM scheduler_locks WHERE lease_expires_ts > ?", (ts,))

    metrics = _query(local_db,
                     "SELECT component, status, COUNT(*) AS n FROM runtime_operational_metrics "
                     "WHERE timestamp_utc >= ? GROUP BY component, status",
                     (time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(cutoff)),))

    prod_obs = _query(discovery_db, "SELECT COUNT(*) AS n, MAX(retrieved_ts) AS last_ts, "
                                    "COUNT(DISTINCT token_address) AS tokens "
                                    "FROM production_observations WHERE retrieved_ts >= ?", (cutoff,))
    e01_obs = _query(discovery_db, "SELECT COUNT(*) AS n, MAX(retrieved_ts) AS last_ts "
                                   "FROM discovery_observations WHERE retrieved_ts >= ?", (cutoff,))
    gaps = _query(discovery_db, "SELECT kind, COUNT(*) AS n FROM gap_register "
                                "WHERE noted_ts >= ? GROUP BY kind", (cutoff,))
    pfe = _query(discovery_db, "SELECT kind, provider_id, COUNT(*) AS n FROM provider_failure_events "
                               "WHERE event_ts >= ? GROUP BY kind, provider_id", (cutoff,))

    return {
        "snapshot_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
        "window_hours": window_hours,
        "watchdog": watchdog.watchdog_report(local_db, max_age_sec=300.0, now=ts),
        "scheduler": {
            "runs_in_window": len(runs),
            "status_counts": status_counts,
            "max_clock_drift_sec": max((r["clock_drift_sec"] for r in runs), default=None),
            "last_runs": runs[-5:],
            "heartbeat_ages_sec": {h["component"]: h["age_sec"] for h in heartbeats},
            "live_leases": locks,
        },
        "metrics": metrics,
        "observations": {
            "production_window_count": prod_obs[0]["n"] if prod_obs else "NO_DATA",
            "production_distinct_tokens": prod_obs[0]["tokens"] if prod_obs else "NO_DATA",
            "e01_window_count": e01_obs[0]["n"] if e01_obs else "NO_DATA",
            "gap_register_window": {g["kind"]: g["n"] for g in gaps} or "NO_DATA",
            "provider_failure_events": ({" / ".join([e["kind"], e["provider_id"]]): e["n"]
                                         for e in pfe} if pfe else "NO_DATA"),
        },
        "integrity": {"local_db": _integrity(local_db), "discovery_db": _integrity(discovery_db)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS soak evidence snapshot (read-only)")
    ap.add_argument("--local-db", default=None)
    ap.add_argument("--discovery-db", default=None)
    ap.add_argument("--window-hours", type=float, default=24.0)
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args(argv)

    snap = snapshot(args.local_db, args.discovery_db, args.window_hours)
    text = json.dumps(snap, indent=2, ensure_ascii=False, default=str)
    if args.stdout:
        print(text)
    else:
        out = ROOT / "reports" / f"soak_snapshot_{snap['snapshot_utc'].replace(':', '').replace('-', '')}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"snapshot written: {out}")
        s, w = snap["scheduler"], snap["watchdog"]
        print(f"runs={s['runs_in_window']} statuses={s['status_counts']} "
              f"watchdog={w['status']} integrity={snap['integrity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
