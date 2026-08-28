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
    _quote_sqlite_ident,
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
            trade_id TEXT PRIMARY KEY,
            amount_allocated REAL NOT NULL
        );
        CREATE TABLE portfolio_ledger (
            id INTEGER PRIMARY KEY,
            cash_after REAL NOT NULL
        );
        CREATE TABLE paper_exit_v3 (
            id INTEGER PRIMARY KEY,
            trade_id TEXT NOT NULL,
            allocated_retired_usd REAL NOT NULL
        );
        """
    )


def test_calibration_insufficient_data_is_unknown_not_healthy():
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    drift = snap.self_observation["score_drift"]
    cal_dim = snap.health_scorecard["dimensions"]["CALIBRATION_HEALTH"]
    # When calibration_status is INSUFFICIENT_DATA, dimension must be UNKNOWN.
    latest = snap.self_observation["calibration_state"].get("latest_artifact")
    if latest and latest.get("calibration_status") == "INSUFFICIENT_DATA":
        assert cal_dim["status"] == "UNKNOWN"
    if drift.get("verdict") == "INSUFFICIENT_DATA":
        assert snap.health_scorecard["dimensions"]["DRIFT_HEALTH"]["status"] == "UNKNOWN"


def test_provider_health_does_not_invent_closed_breakers():
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    assert snap.provider_health.get("breaker_state_source") == "UNAVAILABLE"
    assert snap.health_scorecard["dimensions"]["PROVIDER_HEALTH"]["status"] in (
        "UNKNOWN", "DEGRADED"
    )


def test_no_runs_yet_is_runtime_unknown():
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    snap.scheduler_status = {"last_run_status": "NO_RUNS_YET", "heartbeat_age_seconds": None}
    sc = engine._build_scorecard(snap)
    assert sc["dimensions"]["RUNTIME_HEALTH"]["status"] == "UNKNOWN"


def test_paper_only_unset_is_unknown_not_true(monkeypatch):
    monkeypatch.delenv("AHOS_PAPER_ONLY", raising=False)
    snap = HealthSnapshotEngine().generate_snapshot()
    assert snap.security_invariants["ahos_paper_only_enforced"] is None
    assert snap.security_invariants["ahos_paper_only_env"] == "unset_default_paper"


def test_fresh_install_accounting_has_no_mismatch_reason(tmp_path, monkeypatch):
    db = tmp_path / "paper.sqlite"
    conn = sqlite3.connect(str(db))
    _init_paper_schema(conn)
    conn.commit()
    conn.close()
    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_paper_trading_db_path",
        lambda: str(db),
    )
    snap = HealthSnapshotEngine(root_dir=ROOT).generate_snapshot()
    assert snap.track_b_accounting.get("bankroll_initialised") is False
    assert snap.track_b_accounting.get("is_accounting_consistent") is True
    assert not any("accounting mismatch" in r for r in snap.summary_reasons)
    assert not any("allocated with no portfolio ledger" in r for r in snap.summary_reasons)


def test_track_b_mismatch_is_critical(tmp_path, monkeypatch):
    db = tmp_path / "paper.sqlite"
    conn = sqlite3.connect(str(db))
    _init_paper_schema(conn)
    conn.execute("INSERT INTO portfolio_ledger(cash_after) VALUES (10.0)")
    conn.execute(
        "INSERT INTO paper_trade_v2(trade_id, amount_allocated) VALUES ('t1', 5.0)"
    )
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
    conn.execute(
        "INSERT INTO paper_trade_v2(trade_id, amount_allocated) VALUES ('t1', ?)",
        (allocated,),
    )
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


def test_quote_sqlite_ident_rejects_malicious_names():
    assert _quote_sqlite_ident("paper_trade_v2") == '"paper_trade_v2"'
    for bad in (
        "foo;DROP TABLE x",
        "a b",
        "x--",
        "1bad",
        'quote"me',
        "",
        None,
    ):
        with pytest.raises((ValueError, TypeError)):
            _quote_sqlite_ident(bad)  # type: ignore[arg-type]


def test_health_snapshot_does_not_mutate_operational_dbs(tmp_path, monkeypatch):
    """Snapshot generation must be side-effect free on SQLite stores."""
    import hashlib
    import shutil

    from config import paths as pathmod

    stores = {
        "discovery": pathmod.get_discovery_db_path(),
        "paper": pathmod.get_paper_trading_db_path(),
        "local": pathmod.get_local_db_path(),
        "knowledge": pathmod.get_knowledge_db_path(),
    }
    copies: dict[str, Path] = {}
    for name, src in stores.items():
        dst = tmp_path / f"{name}.sqlite"
        src_p = Path(src)
        if src_p.exists():
            shutil.copy2(src_p, dst)
        else:
            sqlite3.connect(str(dst)).close()
        copies[name] = dst

    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_discovery_db_path",
        lambda: str(copies["discovery"]),
    )
    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_paper_trading_db_path",
        lambda: str(copies["paper"]),
    )
    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_local_db_path",
        lambda: str(copies["local"]),
    )
    monkeypatch.setattr(
        "architecture.runtime.observability_snapshot.get_knowledge_db_path",
        lambda: str(copies["knowledge"]),
    )

    def _fp() -> dict[str, tuple[str, list[str], dict[str, int]]]:
        out: dict[str, tuple[str, list[str], dict[str, int]]] = {}
        for name, path in copies.items():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            conn = sqlite3.connect(str(path))
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY 1"
                ).fetchall()
            ]
            counts = {
                t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                for t in tables
                if t.isidentifier()
            }
            conn.close()
            out[name] = (digest, tables, counts)
        return out

    before = _fp()
    HealthSnapshotEngine(root_dir=ROOT).generate_snapshot()
    HealthSnapshotEngine(root_dir=ROOT).generate_snapshot()
    after = _fp()
    assert after == before


def test_evidence_package_scorecard_cannot_fabricate_lane_a_ok():
    """Rebuilt scorecards must honor serialized lane_a_ok, never hardcode True."""
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    # Simulate evidence-package reconstruction from serialized health JSON.
    proxy = type(
        "Snap",
        (),
        {
            "timestamp_utc": snap.timestamp_utc,
            "overall_verdict": snap.overall_verdict,
            "self_observation": snap.self_observation,
            "database_integrity": snap.database_integrity,
            "provider_health": snap.provider_health,
            "scheduler_status": snap.scheduler_status,
            "security_invariants": snap.security_invariants,
            "lane_a_ok": False,
            "lane_a_detail": "lane_a_freeze_drift: synthetic",
        },
    )()
    sc = engine._build_scorecard(proxy)
    assert sc["dimensions"]["ARCHITECTURE_HEALTH"]["status"] == "FAIL"
    assert any("FAILED" in e for e in sc["dimensions"]["ARCHITECTURE_HEALTH"]["evidence"])


def test_stale_artifact_never_reports_test_health_healthy(monkeypatch):
    """Force stale SHA and prove TEST_HEALTH cannot be HEALTHY."""
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    so = dict(snap.self_observation)
    so["test_health"] = {
        "pytest": {
            "present": True,
            "exit_code": 0,
            "commit_sha": "deadbeef" * 5,
            "head_sha": "cafebabe" * 5,
            "stale_vs_head": True,
            "evidence_completeness": "COMPLETE",
        },
        "validate": {
            "present": True,
            "exit_code": 0,
            "commit_sha": "deadbeef" * 5,
            "head_sha": "cafebabe" * 5,
            "stale_vs_head": True,
            "evidence_completeness": "COMPLETE",
        },
    }
    snap.self_observation = so
    sc = engine._build_scorecard(snap)
    assert sc["dimensions"]["TEST_HEALTH"]["status"] == "UNKNOWN"
