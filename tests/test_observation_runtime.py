#!/usr/bin/env python3
"""Phase 6 — Observation Runtime hardening tests.

Laws pinned here (operational directive §2/§4 + doctrine):
  * the observation cycle is fail-closed: a safety veto BLOCKS the cycle
    before the frozen Lane-A poller is ever invoked
  * the runtime WRAPS discovery.observe_active (reuse, never reimplementation):
    reports carry the frozen scheduler version, and cycles land in the same
    operational metrics store as pipeline cycles
  * provider failures are honest DEGRADED reports — nothing is fabricated,
    nothing raises out of the cycle
  * Lane-A drift is detected against the frozen manifest (fail-closed)

Network-free: fetch is injected; the fixture store uses the real frozen schema
via discovery.observations (identical pattern to test_observation_scheduler).
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from discovery import observations as obs          # noqa: E402
from discovery import lifecycle                     # noqa: E402
from architecture.runtime.metrics import OperationalMetricsTracker  # noqa: E402
from architecture.runtime.observation_loop import (  # noqa: E402
    ObservationRuntime,
    RuntimeSafetyGate,
    STATUS_SUCCESS,
    STATUS_DEGRADED,
    STATUS_BLOCKED,
    STATUS_FAILED,
)

T0 = 1_786_500_000.0
FORBIDDEN_ENV = ["AHOS_ALLOW_REAL_FUNDS", "AHOS_EXECUTE_LIVE_TRADES",
                 "BINANCE_API_KEY", "COINBASE_API_KEY", "KRAKEN_API_KEY"]


# ------------------------------------------------------------------ fixtures
def _clean_env(monkeypatch):
    for var in FORBIDDEN_ENV:
        monkeypatch.delenv(var, raising=False)


def _mk(conn, chain, addr, t0, price=1.0):
    tid = obs.upsert_token(conn, chain, addr, first_seen_ts=t0, provider="fx", symbol=addr[-4:])
    raw0 = obs.store_raw(conn, "fx", f"/fx/{addr}", t0, 200, {"fx": addr})
    pid = obs.upsert_pair(conn, chain, "raydium", f"pair_{addr}", tid, t0, "fx", raw0)
    lifecycle.register_discovery(conn, tid, t0)
    obs.record_observation(conn, tid, "fx", t0, raw0, pair=pid, metrics={"price_usd": price})
    lifecycle.on_observation(conn, tid, t0)
    return tid


def _env_ok(addr, price=2.0):
    return {"availability": "OK", "provider_id": "dexscreener",
            "endpoint": f"/tokens/v1/solana/{addr}", "http_status": 200,
            "payload": [{"chainId": "solana", "pairAddress": f"pair_{addr}",
                         "dexId": "raydium", "priceUsd": str(price),
                         "baseToken": {"address": addr, "symbol": "X", "name": "X"},
                         "quoteToken": {"symbol": "SOL"}, "liquidity": {"usd": 50000},
                         "fdv": 1_000_000, "marketCap": 900_000, "volume": {"h24": 1000},
                         "txns": {}, "priceChange": {}}]}


@pytest.fixture
def runtime(tmp_path):
    """ObservationRuntime wired to isolated stores; fetch stubbed via factory."""
    discovery_db = tmp_path / "discovery.sqlite"
    local_db = tmp_path / "local.sqlite"
    conn = obs.open_store(discovery_db)
    _mk(conn, "solana", "TOK1", T0)
    conn.commit()
    conn.close()

    holder = {}

    def build(fetch):
        holder["metrics"] = OperationalMetricsTracker(db_path=str(local_db))
        holder["runtime"] = ObservationRuntime(
            workspace_root=ROOT,                       # real root => gate verifies real Lane-A
            discovery_db_path=str(discovery_db),
            tracked_store_path="",                     # no paper store in these tests
            metrics_tracker=holder["metrics"],
            fetch=fetch)
        return holder["runtime"], local_db, discovery_db

    holder["build"] = build
    return holder


def _metric_rows(db: Path, run_id: str) -> list[tuple]:
    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT metric_name, status, metric_value FROM runtime_operational_metrics "
        "WHERE run_id=?", (run_id,)).fetchall()
    conn.close()
    return rows


# --------------------------------------------------------------------- tests

def test_safety_gate_accepts_clean_environment(monkeypatch):
    _clean_env(monkeypatch)
    verdict = RuntimeSafetyGate(root=ROOT).check()
    assert verdict.ok, verdict.reasons
    assert verdict.checks["env_safety"]["ok"] is True
    assert verdict.checks["lane_a_freeze"]["ok"] is True


def test_safety_gate_blocks_live_trading_veto(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("AHOS_EXECUTE_LIVE_TRADES", "1")
    verdict = RuntimeSafetyGate(root=ROOT).check()
    assert not verdict.ok
    assert any("env_safety" in r for r in verdict.reasons)
    assert verdict.checks["env_safety"]["ok"] is False


def test_safety_gate_fails_closed_on_lane_a_drift(tmp_path):
    """A drifted scientific surface must veto the cycle — never harvest on it."""
    fake_root = tmp_path / "repo"
    shutil.copytree(ROOT / "discovery", fake_root / "discovery",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "paper_trading", fake_root / "paper_trading",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (fake_root / "config").mkdir()
    shutil.copy(ROOT / "config" / "lane_a_freeze.sha256",
                fake_root / "config" / "lane_a_freeze.sha256")
    (fake_root / "discovery" / "__init__.py").write_text(
        (fake_root / "discovery" / "__init__.py").read_text() + "\n# drifted\n",
        encoding="utf-8")

    verdict = RuntimeSafetyGate(root=fake_root).check()
    assert not verdict.ok
    assert "lane_a_freeze_drift" in verdict.reasons[0]


def test_blocked_cycle_never_touches_the_discovery_store(monkeypatch, runtime):
    _clean_env(monkeypatch)
    monkeypatch.setenv("AHOS_ALLOW_REAL_FUNDS", "1")
    calls = []

    def fetch(chain, address, now):  # must never be invoked
        calls.append(address)
        raise AssertionError("poller executed despite safety veto")

    rt, metrics_db, discovery_db = runtime["build"](fetch)
    rep = rt.run_cycle(now=T0 + 3600, min_interval=0)
    assert rep.status == STATUS_BLOCKED
    assert rep.safety.ok is False
    assert rep.attempted == 0 and rep.recorded == 0 and rep.failures == 0
    assert calls == []
    conn = sqlite3.connect(str(discovery_db))
    assert conn.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0] == 1
    conn.close()
    rows = _metric_rows(metrics_db, rep.run_id)
    assert ("cycle_status", "ERROR") in {(n, s) for n, s, v in rows}


def test_successful_cycle_records_observations_and_metrics(monkeypatch, runtime):
    _clean_env(monkeypatch)
    rt, metrics_db, _ = runtime["build"](lambda c, a, n: _env_ok(a))
    rep = rt.run_cycle(now=T0 + 3600, min_interval=0)
    assert rep.status == STATUS_SUCCESS
    assert rep.attempted == 1 and rep.recorded == 1 and rep.failures == 0
    assert rep.obs_ids, "successful cycle must expose the recorded obs_ids"
    rows = _metric_rows(metrics_db, rep.run_id)
    names = {n for n, s, v in rows}
    assert {"cycle_status", "attempted", "recorded", "failures",
            "cycle_duration_ms"} <= names
    assert ("recorded", "OK", 1.0) in rows


def test_provider_failure_reports_degraded_honestly(monkeypatch, runtime):
    _clean_env(monkeypatch)
    down = {"availability": "DOWN", "provider_id": "dexscreener",
            "endpoint": "/tokens/v1/solana/TOK1", "http_status": 521,
            "payload": None, "error_state": {"kind": "http_error", "code": 521}}
    rt, metrics_db, discovery_db = runtime["build"](lambda c, a, n: down)
    rep = rt.run_cycle(now=T0 + 3600, min_interval=0)
    assert rep.status == STATUS_DEGRADED
    assert rep.failures == 1 and rep.recorded == 0
    conn = sqlite3.connect(str(discovery_db))
    row = conn.execute(
        "SELECT price_usd, error_state FROM discovery_observations "
        "WHERE error_state IS NOT NULL ORDER BY retrieved_ts DESC LIMIT 1").fetchone()
    conn.close()
    assert row is not None and row[0] is None and "521" in row[1]   # explicit, never fabricated
    rows = _metric_rows(metrics_db, rep.run_id)
    assert ("failures", "WARN", 1.0) in rows


def test_fetch_exception_is_failed_report_not_fatal(monkeypatch, runtime):
    _clean_env(monkeypatch)

    def fetch(chain, address, now):
        raise RuntimeError("network layer exploded")

    rt, metrics_db, _ = runtime["build"](fetch)
    rep = rt.run_cycle(now=T0 + 3600, min_interval=0)          # must NOT raise
    assert rep.status == STATUS_FAILED
    assert rep.trace is not None and rep.trace.error_class == "RUNTIME_ERROR"
    rows = _metric_rows(metrics_db, rep.run_id)
    assert ("cycle_status", "ERROR", 1.0) in rows


def test_cycle_reuses_the_frozen_poller_and_reports_its_version(monkeypatch, runtime):
    _clean_env(monkeypatch)
    rt, _, _ = runtime["build"](lambda c, a, n: _env_ok(a))
    rep = rt.run_cycle(now=T0 + 3600, min_interval=0)
    assert rep.status == STATUS_SUCCESS
    assert rep.details["tool"] == "observe_active"                    # the frozen poller ran
    assert rep.details["scheduler_version"] == "observation_scheduler:v1"
    assert rep.details["version"] == "observe_active:v2"
