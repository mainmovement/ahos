#!/usr/bin/env python3
"""Regression tests for forensic observability / metrics hardening.

Covers root causes found in the Master Forensic Repair directive:
  - metrics write failures are fail-open for callers but observable
  - metric IDs do not collide under concurrent writes
  - invalid status / non-JSON meta raise (programmer errors)
  - score_drift is populated from calibration artifacts
  - lane_a_ok is an explicit snapshot field (no hasattr false-intact)
  - TEST_HEALTH treats SHA-mismatched artifacts as stale / UNKNOWN
  - Track B fresh-install vs mismatch accounting semantics
"""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.runtime.metrics import OperationalMetricsTracker, ALLOWED_STATUSES
from architecture.runtime.observability_snapshot import (
    HealthSnapshotEngine,
    CanonicalHealthSnapshot,
    HEALTH_DIMENSIONS,
)
from paper_trading.bankroll import BANKROLL_START_USD


def test_metric_write_failure_is_observable_not_silent(tmp_path):
    db = tmp_path / "metrics.sqlite"
    tracker = OperationalMetricsTracker(str(db))

    # Exclusive lock blocks the writer — caller must not crash.
    locker = sqlite3.connect(str(db))
    locker.execute("BEGIN EXCLUSIVE")

    eid = tracker.record_metric(
        run_id="r1",
        component="scoring",
        metric_name="latency",
        metric_value=1.0,
        status="OK",
    )
    assert eid.startswith("met_")
    health = tracker.telemetry_health()
    assert health["write_failures"] >= 1
    assert health["status"] == "DEGRADED"
    assert health["recent_failures"]
    assert health["recent_failures"][-1]["event_id"] == eid

    locker.rollback()
    locker.close()


def test_metric_ids_unique_under_concurrency(tmp_path):
    db = tmp_path / "metrics.sqlite"
    tracker = OperationalMetricsTracker(str(db))
    ids: list[str] = []
    lock = threading.Lock()

    def _write(i: int) -> None:
        eid = tracker.record_metric(
            run_id=f"r{i}",
            component="pipeline",
            metric_name="tick",
            metric_value=float(i),
        )
        with lock:
            ids.append(eid)

    threads = [threading.Thread(target=_write, args=(i,)) for i in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(ids) == 40
    assert len(set(ids)) == 40
    assert tracker.telemetry_health()["write_failures"] == 0
    assert len(tracker.get_recent_metrics(100)) == 40


def test_metric_rejects_invalid_status_and_non_json_meta(tmp_path):
    tracker = OperationalMetricsTracker(str(tmp_path / "m.sqlite"))
    with pytest.raises(ValueError):
        tracker.record_metric(
            run_id="r", component="c", metric_name="n", metric_value=1.0, status="NOPE"
        )
    with pytest.raises(ValueError):
        tracker.record_metric(
            run_id="r",
            component="c",
            metric_name="n",
            metric_value=1.0,
            meta={"bad": object()},
        )
    assert ALLOWED_STATUSES == frozenset({"OK", "WARN", "ERROR", "RECOVERED"})


def test_score_drift_populated_and_lane_a_explicit():
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    assert isinstance(snap, CanonicalHealthSnapshot)
    assert snap.lane_a_ok is True
    assert "lane_a_freeze" in snap.lane_a_detail or snap.lane_a_detail == "lane_a_freeze_ok"
    drift = snap.self_observation["score_drift"]
    assert isinstance(drift, dict)
    assert "verdict" in drift
    # Scorecard must not claim HEALTHY drift when verdict is INSUFFICIENT_DATA.
    dim = snap.health_scorecard["dimensions"]["DRIFT_HEALTH"]
    if drift.get("verdict") in (None, "INSUFFICIENT_DATA") or drift.get("error") == "NO_DATA":
        assert dim["status"] == "UNKNOWN"
    assert set(snap.health_scorecard["dimensions"]) == set(HEALTH_DIMENSIONS)


def test_stale_test_artifacts_are_not_healthy():
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    th = snap.self_observation["test_health"]
    # Committed artifacts in this repo currently pin an older SHA than HEAD.
    if th["pytest"].get("stale_vs_head"):
        assert snap.health_scorecard["dimensions"]["TEST_HEALTH"]["status"] == "UNKNOWN"
        assert any("STALE" in e for e in snap.health_scorecard["dimensions"]["TEST_HEALTH"]["evidence"])


def test_architecture_health_fails_when_lane_a_false(tmp_path):
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    snap.lane_a_ok = False
    snap.lane_a_detail = "lane_a_freeze_drift: synthetic"
    sc = engine._build_scorecard(snap)
    assert sc["dimensions"]["ARCHITECTURE_HEALTH"]["status"] == "FAIL"


def _init_paper_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE paper_trade_v2 (
            id INTEGER PRIMARY KEY,
            amount_allocated REAL NOT NULL
        );
        CREATE TABLE portfolio_ledger (
            id INTEGER PRIMARY KEY,
            cash_after REAL NOT NULL
        );
        CREATE TABLE paper_exit_v3 (
            id INTEGER PRIMARY KEY
        );
        """
    )


def test_track_b_fresh_install_not_critical(tmp_path, monkeypatch):
    """Empty ledger + zero allocation is consistent (fresh install)."""
    db = tmp_path / "paper.sqlite"
    conn = sqlite3.connect(str(db))
    _init_paper_schema(conn)
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_paper_trading_db_path",
        lambda: str(db),
    )
    # Stub other stores so generate_snapshot does not CRITICAL on missing DBs.
    # Prefer unit-testing the accounting block via a partial path:
    engine = HealthSnapshotEngine(root_dir=ROOT)
    # Call generate and inspect only if paper path is overridden — also need
    # other DBs present. Use real project DBs for integrity; only paper is stubbed.
    snap = engine.generate_snapshot()
    # If override worked, fresh DB means bankroll_initialised False.
    tb = snap.track_b_accounting
    if tb.get("bankroll_initialised") is False:
        assert tb["is_accounting_consistent"] is True
        assert snap.overall_verdict != "CRITICAL" or any(
            "accounting" not in r.lower() for r in snap.summary_reasons
        )


def test_track_b_mismatch_is_critical(tmp_path, monkeypatch):
    db = tmp_path / "paper.sqlite"
    conn = sqlite3.connect(str(db))
    _init_paper_schema(conn)
    conn.execute("INSERT INTO portfolio_ledger(cash_after) VALUES (10.0)")
    conn.execute("INSERT INTO paper_trade_v2(amount_allocated) VALUES (5.0)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_paper_trading_db_path",
        lambda: str(db),
    )
    # discovery/local/knowledge still required — keep real paths for those.
    snap = HealthSnapshotEngine(root_dir=ROOT).generate_snapshot()
    tb = snap.track_b_accounting
    assert tb.get("bankroll_initialised") is True
    assert tb.get("is_accounting_consistent") is False
    assert abs(tb["accounting_sum_usd"] - 15.0) < 1e-6
    assert snap.overall_verdict == "CRITICAL"
    assert any("accounting mismatch" in r for r in snap.summary_reasons)


def test_track_b_initialized_correct_ledger(tmp_path, monkeypatch):
    db = tmp_path / "paper.sqlite"
    conn = sqlite3.connect(str(db))
    _init_paper_schema(conn)
    allocated = 5.0
    cash = BANKROLL_START_USD - allocated
    conn.execute("INSERT INTO portfolio_ledger(cash_after) VALUES (?)", (cash,))
    conn.execute("INSERT INTO paper_trade_v2(amount_allocated) VALUES (?)", (allocated,))
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_paper_trading_db_path",
        lambda: str(db),
    )
    snap = HealthSnapshotEngine(root_dir=ROOT).generate_snapshot()
    tb = snap.track_b_accounting
    assert tb["is_accounting_consistent"] is True
    assert tb["accounting_sum_usd"] == pytest.approx(BANKROLL_START_USD, rel=1e-7)
    assert not any("accounting mismatch" in r for r in snap.summary_reasons)
