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
