#!/usr/bin/env python3
"""Prediction → Lane-A observation lifecycle bridge tests (P0-2b).

Pins:
  * scored/collected candidates register into observation_state
  * real metrics only (NULL preserved)
  * backfill uses production_observations without fabricating prices
  * full clock-injected path: register → RESOLVED → labels → calibration join
  * Lane-A freeze untouched (this module only calls frozen APIs)
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.collector.engine import CollectedObservationRecord  # noqa: E402
from architecture.learning.calibration import CalibrationHarness  # noqa: E402
from architecture.learning.prediction_lifecycle import (  # noqa: E402
    backfill_from_production_observations,
    lifecycle_status,
    register_for_observation,
)
from architecture.learning.score_ledger import SOURCE_LOCAL, ScoreLedger  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from discovery import observations as obs  # noqa: E402
from discovery.identity import token_id  # noqa: E402
from discovery.materialize import materialize_outcomes  # noqa: E402


def _rec(**kw) -> CollectedObservationRecord:
    base = dict(
        obs_id="abc123",
        token_address="LifecycleTestAddr1111111111111111111111",
        chain="solana",
        symbol="LIFE",
        name="Lifecycle",
        provider_source="dexscreener",
        retrieved_ts=1_700_000_000.0,
        raw_evidence_hash="deadbeef" * 8,
        confidence_level="HIGH",
        metrics={
            "price_usd": 1.0,
            "liquidity_usd": 50_000.0,
            "volume_1h": 10_000.0,
            "fdv_usd": 1_000_000.0,
            "market_cap_usd": 400_000.0,
            "txns_1h_buys": 40,
            "txns_1h_sells": 20,
        },
        security={},
        unknown_fields=[],
    )
    base.update(kw)
    return CollectedObservationRecord(**base)


def test_register_seeds_observation_state_and_discovery_obs(tmp_path):
    disc = tmp_path / "d.sqlite"
    result = register_for_observation([_rec()], discovery_db=str(disc), now=1_700_000_000.0)
    assert result.attempted == 1
    assert result.registered == 1
    assert result.observations_written == 1
    assert result.errors == []

    conn = obs.open_store(str(disc))
    tid = token_id("solana", "LifecycleTestAddr1111111111111111111111")
    st = conn.execute("SELECT state FROM observation_state WHERE token_id=?", (tid,)).fetchone()
    assert st is not None
    assert st["state"] in ("DISCOVERED", "OBSERVING")
    nobs = conn.execute(
        "SELECT COUNT(*) c FROM discovery_observations WHERE token_id=?", (tid,)
    ).fetchone()["c"]
    assert nobs >= 1
    # fdv alias mapped
    row = conn.execute(
        "SELECT fdv, market_cap, price_usd FROM discovery_observations WHERE token_id=?",
        (tid,),
    ).fetchone()
    assert row["price_usd"] == 1.0
    assert row["fdv"] == 1_000_000.0
    assert row["market_cap"] == 400_000.0
    conn.close()


def test_register_is_idempotent(tmp_path):
    disc = tmp_path / "d.sqlite"
    r1 = register_for_observation([_rec()], discovery_db=str(disc))
    r2 = register_for_observation([_rec()], discovery_db=str(disc))
    assert r1.registered == 1
    assert r2.registered == 0  # already in observation_state
    assert r2.observations_written == 1  # INSERT OR IGNORE may no-op same obs_id


def test_backfill_from_production_table(tmp_path):
    disc = tmp_path / "d.sqlite"
    # Create production_observations matching CollectorEngine._persist_records
    conn = sqlite3.connect(str(disc))
    conn.execute(
        """CREATE TABLE production_observations (
            obs_id TEXT PRIMARY KEY,
            token_address TEXT NOT NULL,
            chain TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            provider_source TEXT NOT NULL,
            retrieved_ts REAL NOT NULL,
            raw_evidence_hash TEXT NOT NULL,
            confidence_level TEXT,
            price_usd REAL,
            liquidity_usd REAL,
            volume_1h REAL,
            volume_24h REAL,
            metrics_json TEXT,
            security_json TEXT,
            unknown_fields_json TEXT,
            created_utc TEXT
        )"""
    )
    conn.execute(
        "INSERT INTO production_observations("
        "obs_id,token_address,chain,symbol,name,provider_source,retrieved_ts,"
        "raw_evidence_hash,confidence_level,price_usd,liquidity_usd,volume_1h,"
        "volume_24h,metrics_json,security_json,unknown_fields_json,created_utc)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "p1", "BackfillAddr2222222222222222222222", "solana", "BF", "Backfill",
            "geckoterminal", 1_700_000_100.0, "cafebabe" * 8, "HIGH",
            2.5, 12_000.0, 1_000.0, None,
            json.dumps({"price_usd": 2.5, "liquidity_usd": 12_000.0}),
            "{}", "[]", "2026-01-01T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    result = backfill_from_production_observations(discovery_db=str(disc))
    assert result.attempted == 1
    assert result.registered == 1
    assert result.observations_written == 1

    status = lifecycle_status(discovery_db=str(disc), ledger_db=str(tmp_path / "empty.sqlite"))
    assert sum(status["observation_state"].values()) >= 1
    assert status["discovery_observations"] >= 1


def test_clock_injected_register_to_calibration_join(tmp_path):
    """Genuine path: bridge → observations → RESOLVED → labels → join.

    Uses injected clock (T0 then T0+73h). Does NOT fabricate outcomes —
    labels come from frozen materialize_outcomes over real observation prices.
    """
    disc = tmp_path / "d.sqlite"
    led = tmp_path / "l.sqlite"
    t0 = 1_600_000_000.0
    addr = "JoinProofAddr3333333333333333333333"
    tid = token_id("solana", addr)

    # t0: register + score
    register_for_observation(
        [_rec(token_address=addr, retrieved_ts=t0,
              metrics={"price_usd": 1.0, "liquidity_usd": 80_000.0,
                       "volume_1h": 20_000.0, "txns_1h_buys": 100, "txns_1h_sells": 40})],
        discovery_db=str(disc),
        now=t0,
    )
    # Add later price observations so outcomes have a path (still real rows we insert
    # as observation evidence — same as Lane-A poller would write).
    conn = obs.open_store(str(disc))
    conn.execute(
        "INSERT OR IGNORE INTO raw_payloads(payload_sha256,provider,endpoint,retrieved_ts,payload_json)"
        " VALUES ('jp1','dexscreener','t',?, '{}')",
        (t0,),
    )
    for i, (off, price) in enumerate(((3600.0, 1.2), (7200.0, 1.8), (86400.0, 2.5))):
        conn.execute(
            "INSERT INTO discovery_observations(obs_id,token_id,provider,retrieved_ts,price_usd,raw_ref)"
            " VALUES (?,?,?,?,?,?)",
            (f"jp{i}", tid, "dexscreener", t0 + off, price, "jp1"),
        )
    conn.commit()

    candidate = NormalizedTokenCandidate(
        chain="solana", address=addr, symbol="JP", name="JoinProof",
        source_provider="dexscreener", retrieved_ts=t0,
        metrics=MarketMetrics(price_usd=1.0, liquidity_usd=80_000.0, volume_1h=20_000.0,
                              txns_1h_buys=100, txns_1h_sells=40),
        security=SecuritySignals(is_honeypot=False),
    )
    ScoreLedger(db_path=str(led), source=SOURCE_LOCAL).record(
        OpportunityScorer().evaluate(candidate, now=t0), run_id="join", now=t0
    )

    # t0+73h: resolve + materialize (frozen Lane-A)
    now_closed = t0 + 73 * 3600.0
    mat = materialize_outcomes(conn, now=now_closed)
    assert mat["outcome_rows_written"] > 0
    conn.close()

    report = CalibrationHarness(ledger_db=str(led), discovery_db=str(disc)).run()
    assert report.joined_pairs >= 1
    # Guards still not met with a single pair — honesty preserved.
    assert report.verdict == "INSUFFICIENT_DATA"


def test_lifecycle_status_notes_empty_active_set(tmp_path):
    disc = tmp_path / "d.sqlite"
    obs.open_store(str(disc)).close()
    led = tmp_path / "l.sqlite"
    ScoreLedger(db_path=str(led), source=SOURCE_LOCAL)  # creates empty ledger schema
    st = lifecycle_status(discovery_db=str(disc), ledger_db=str(led))
    assert st["schema"] == "ahos.prediction_lifecycle_status.v1"
    assert isinstance(st["notes"], list)
