#!/usr/bin/env python3
"""Tests for Market Collector Engine, Circuit Breaker, and Retry Policy (Phase XX)."""
import sys, time, sqlite3, json
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.collector.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from architecture.collector.retry import RetryPolicy
from architecture.collector.engine import CollectorEngine, CollectedObservationRecord
from architecture.providers.contracts import NormalizedTokenCandidate, ProviderResponse, MarketMetrics, SecuritySignals
from architecture.providers.registry import ProviderRouter


# ---------------- Circuit Breaker Tests ----------------
def test_circuit_breaker_initial_closed():
    cb = CircuitBreaker("test_cb")
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_circuit_breaker_trips_to_open():
    cb = CircuitBreaker("test_cb", CircuitBreakerConfig(failure_threshold=3, recovery_timeout_sec=10.0))
    now = 1000.0
    cb.record_failure(now=now)
    assert cb.state == CircuitState.CLOSED
    cb.record_failure(now=now)
    assert cb.state == CircuitState.CLOSED
    cb.record_failure(now=now)
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request(now=now + 1.0) is False


def test_circuit_breaker_transitions_to_half_open_and_recovers():
    cb = CircuitBreaker("test_cb", CircuitBreakerConfig(failure_threshold=2, recovery_timeout_sec=5.0))
    now = 1000.0
    cb.record_failure(now=now)
    cb.record_failure(now=now)
    assert cb.state == CircuitState.OPEN

    # After recovery timeout
    assert cb.allow_request(now=now + 6.0) is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success restores to CLOSED
    cb.record_success(now=now + 6.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure_reopens():
    cb = CircuitBreaker("test_cb", CircuitBreakerConfig(failure_threshold=2, recovery_timeout_sec=5.0))
    now = 1000.0
    cb.record_failure(now=now)
    cb.record_failure(now=now)
    assert cb.state == CircuitState.OPEN

    assert cb.allow_request(now=now + 6.0) is True
    assert cb.state == CircuitState.HALF_OPEN

    # Failure in HALF_OPEN trips immediately back to OPEN
    cb.record_failure(now=now + 6.0)
    assert cb.state == CircuitState.OPEN


# ---------------- Retry Policy Tests ----------------
def test_retry_policy_immediate_success():
    rp = RetryPolicy(max_retries=3)
    calls = []
    res = rp.execute(lambda: calls.append(1) or "OK")
    assert res == "OK"
    assert len(calls) == 1


def test_retry_policy_recovers_after_transient_failure():
    rp = RetryPolicy(max_retries=3, initial_delay_sec=0.01)
    attempts = [0]

    def _flaky():
        attempts[0] += 1
        if attempts[0] < 3:
            raise ConnectionError("transient network drop")
        return "SUCCESS"

    slept = []
    res = rp.execute(_flaky, sleep_fn=lambda d: slept.append(d))
    assert res == "SUCCESS"
    assert attempts[0] == 3
    assert len(slept) == 2


def test_retry_policy_raises_after_max_retries():
    rp = RetryPolicy(max_retries=2, initial_delay_sec=0.01)
    attempts = [0]

    def _always_fail():
        attempts[0] += 1
        raise ValueError("permanent error")

    with pytest.raises(ValueError):
        rp.execute(_always_fail, sleep_fn=lambda d: None)
    assert attempts[0] == 3


# ---------------- Collector Engine Tests ----------------
class MockProvider:
    def __init__(self, name: str, should_fail: bool = False):
        self.provider_id = name
        self.capabilities = ["discovery"]
        self.should_fail = should_fail

    def fetch_candidate_tokens(self, chain: str, limit: int = 10):
        if self.should_fail:
            return ProviderResponse(self.provider_id, "ERROR", error_message="Service Unavailable")
        tok = NormalizedTokenCandidate(
            chain=chain,
            address=f"Tok{self.provider_id}1111111111111111111111111",
            symbol=f"{self.provider_id[:3].upper()}",
            name="Mock Token",
            source_provider=self.provider_id,
            metrics=MarketMetrics(price_usd=1.5, liquidity_usd=25000.0, volume_1h=8000.0)
        )
        return ProviderResponse(self.provider_id, "OK", tokens=[tok])

    def fetch_token_metrics(self, chain: str, address: str):
        return ProviderResponse(self.provider_id, "OK", tokens=[])


def test_collector_engine_ingestion_and_provenance(tmp_path):
    db_file = tmp_path / "test_discovery.sqlite"
    router = ProviderRouter()
    router.providers["dexscreener"] = MockProvider("dexscreener")
    router.providers["geckoterminal"] = MockProvider("geckoterminal")

    collector = CollectorEngine(db_path=str(db_file), router=router)
    records = collector.collect_candidates(chain="solana", limit=2)

    assert len(records) >= 1
    rec = records[0]
    assert rec.chain == "solana"
    assert rec.obs_id != ""
    assert rec.raw_evidence_hash != ""
    assert rec.provider_source in ("dexscreener", "geckoterminal")
    assert "metrics.volume_24h" in rec.unknown_fields or rec.metrics.get("volume_1h") == 8000.0

    # Verify storage
    conn = sqlite3.connect(str(db_file))
    rows = conn.execute("SELECT * FROM production_observations").fetchall()
    assert len(rows) == len(records)
    conn.close()


def test_collector_engine_circuit_breaker_trips_on_failures(tmp_path):
    db_file = tmp_path / "test_discovery.sqlite"
    router = ProviderRouter()
    router.providers["dexscreener"] = MockProvider("dexscreener", should_fail=True)
    router.providers["geckoterminal"] = MockProvider("geckoterminal", should_fail=True)

    collector = CollectorEngine(db_path=str(db_file), router=router)
    collector.collect_candidates(chain="solana", limit=2)
    collector.collect_candidates(chain="solana", limit=2)
    collector.collect_candidates(chain="solana", limit=2)

    health = collector.get_provider_health()
    assert health["dexscreener"]["failure_count"] >= 3
    assert health["dexscreener"]["state"] == "OPEN"


def _obs(**over) -> CollectedObservationRecord:
    base = dict(
        obs_id="obs_pair_ts_001",
        token_address="So11111111111111111111111111111111111111112",
        chain="solana",
        symbol="TOK",
        name="Token",
        provider_source="dexscreener",
        retrieved_ts=1_800_000_000.0,
        raw_evidence_hash="ab" * 32,
        confidence_level="MED",
        metrics={"price_usd": 1.0, "liquidity_usd": 10_000.0},
        security={},
        unknown_fields=[],
        pair_created_ts=None,
        created_utc="2026-09-09T10:49:08.624882+00:00",
    )
    base.update(over)
    return CollectedObservationRecord(**base)


def _read_pair_ts(db_path: str, obs_id: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT pair_created_ts FROM production_observations WHERE obs_id = ?",
        (obs_id,),
    ).fetchone()
    conn.close()
    return None if row is None else row["pair_created_ts"]


def test_pair_created_ts_known_value_persists_exactly(tmp_path):
    """Case A/C: a real pair_created_ts is stored and read back without loss."""
    db_file = tmp_path / "prod_obs.sqlite"
    collector = CollectorEngine(db_path=str(db_file), router=ProviderRouter())
    ts = 1_780_000_000.25
    rec = _obs(pair_created_ts=ts)
    collector._persist_records([rec])
    assert _read_pair_ts(str(db_file), rec.obs_id) == ts


def test_pair_created_ts_unknown_persists_null(tmp_path):
    """Case B: missing pair_created_ts stays SQL NULL — never zero-filled."""
    db_file = tmp_path / "prod_obs.sqlite"
    collector = CollectorEngine(db_path=str(db_file), router=ProviderRouter())
    rec = _obs(obs_id="obs_pair_ts_null", pair_created_ts=None)
    collector._persist_records([rec])
    assert _read_pair_ts(str(db_file), rec.obs_id) is None


def test_pair_created_ts_migrate_does_not_rewrite_existing_rows(tmp_path):
    """Pre-column stores gain a NULL column; historical rows stay unknown."""
    db_file = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(str(db_file))
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
            confidence_level TEXT NOT NULL,
            price_usd REAL,
            liquidity_usd REAL,
            volume_1h REAL,
            volume_24h REAL,
            metrics_json TEXT NOT NULL,
            security_json TEXT NOT NULL,
            unknown_fields_json TEXT NOT NULL,
            created_utc TEXT NOT NULL
        )"""
    )
    conn.execute(
        "INSERT INTO production_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "legacy_obs", "AddrLegacy11111111111111111111111111", "solana",
            "OLD", "Old", "dexscreener", 1_700_000_000.0, "cd" * 32, "LOW",
            None, None, None, None, "{}", "{}", "[]", "2026-01-01T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    collector = CollectorEngine(db_path=str(db_file), router=ProviderRouter())
    assert _read_pair_ts(str(db_file), "legacy_obs") is None

    known = 1_775_000_000.0
    collector._persist_records([_obs(obs_id="new_obs", pair_created_ts=known)])
    assert _read_pair_ts(str(db_file), "legacy_obs") is None
    assert _read_pair_ts(str(db_file), "new_obs") == known


def test_pair_created_ts_persist_does_not_weaken_identity_or_overlay(tmp_path):
    """Case D: storing pair age is not a security/identity PASS and not a BUY."""
    from architecture.decision.authority import (
        identity_allows_positive_decision,
        identity_from_candidate,
    )
    from architecture.security.gate import (
        SecurityState,
        evaluate_security,
        security_allows_positive_eligibility,
    )
    from tests.helpers_security import NOW, OLD_POOL_TS, passing_security_signals

    db_file = tmp_path / "prod_obs.sqlite"
    collector = CollectorEngine(db_path=str(db_file), router=ProviderRouter())
    rec = _obs(pair_created_ts=OLD_POOL_TS)
    collector._persist_records([rec])
    stored = _read_pair_ts(str(db_file), rec.obs_id)
    assert stored == OLD_POOL_TS

    cand = NormalizedTokenCandidate(
        chain="solana",
        address=rec.token_address,
        symbol=rec.symbol,
        name=rec.name,
        source_provider="dexscreener",
        retrieved_ts=NOW,
        pair_created_ts=stored,
    )
    ident = identity_from_candidate(cand, now=NOW)
    assert ident.token.state.value == "UNRESOLVED"
    assert identity_allows_positive_decision(ident) is False

    missing_age = evaluate_security(
        passing_security_signals(), now=NOW, pair_created_ts=None, retrieved_ts=NOW,
    )
    assert missing_age.state == SecurityState.INCOMPLETE
    assert not security_allows_positive_eligibility(missing_age)

    stored_age_empty_security = evaluate_security(
        None, now=NOW, pair_created_ts=stored, retrieved_ts=NOW,
    )
    assert stored_age_empty_security.state == SecurityState.INCOMPLETE
    assert not security_allows_positive_eligibility(stored_age_empty_security)
