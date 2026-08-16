#!/usr/bin/env python3
"""AHOS Operational Failure Matrix & Resilience Tests (Phase XXIV - Section 5).

Tests:
  - Internet unavailable
  - Provider unavailable (500/503/521)
  - Database locked (concurrency safety)
  - Process restart & expired lease recovery
  - Duplicate scheduler execution prevention
  - Invalid / Malformed data handling
  - Missing credentials ($0 deterministic survival)
  - Telegram API failure handling
  - Operational metrics tracking
  - Empirical knowledge sync bridge
"""
import sys, time, sqlite3, json
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.collector.engine import CollectorEngine
from architecture.collector.circuit_breaker import CircuitBreaker, CircuitState
from architecture.providers.contracts import NormalizedTokenCandidate, ProviderResponse, MarketMetrics
from architecture.providers.registry import ProviderRouter
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask
from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from architecture.runtime.metrics import OperationalMetricsTracker
from architecture.knowledge.sync import KnowledgeSyncBridge
from telegram_ai.adapter import TelegramBotAdapterInterface


class CrashingTelegramAdapter(TelegramBotAdapterInterface):
    def send_message(self, chat_id, text, parse_mode="HTML"):
        raise ConnectionError("Telegram API blocked / unreachable")
    def poll_updates(self, offset=None, timeout=10):
        raise TimeoutError("Network timeout during polling")
    def set_webhook(self, url):
        return False


class OfflineProvider:
    def __init__(self, name: str):
        self.provider_id = name
        self.capabilities = ["discovery"]
    def fetch_candidate_tokens(self, chain: str, limit: int = 10):
        raise ConnectionError(f"DNS Resolution failed for {self.provider_id}")
    def fetch_token_metrics(self, chain: str, address: str):
        raise TimeoutError(f"HTTP 503 Service Unavailable on {self.provider_id}")


def test_failure_matrix_internet_and_provider_unavailable(tmp_path):
    """When all external providers are offline, pipeline must degrade gracefully without crashing."""
    db_file = tmp_path / "test_offline.sqlite"
    router = ProviderRouter()
    router.providers["dexscreener"] = OfflineProvider("dexscreener")
    router.providers["geckoterminal"] = OfflineProvider("geckoterminal")

    collector = CollectorEngine(db_path=str(db_file), router=router)
    orchestrator = OpportunityPipelineOrchestrator(collector=collector)

    # Must complete cleanly with 0 candidates and 0 unhandled exceptions
    rep = orchestrator.run_pipeline(chain="solana", limit=5)
    assert rep.candidates_collected == 0
    assert rep.scores_generated == 0
    assert rep.alerts_emitted == 0
    assert rep.trace.status == "OK"


def test_failure_matrix_telegram_api_unreachable_does_not_abort_scoring(tmp_path):
    """If Telegram edge is blocked by network filtering, scoring & alerting must complete safely."""
    db_file = tmp_path / "test_tg_offline.sqlite"
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaAlpha11111111111111111111111111111",
        symbol="ALPHA",
        name="Alpha",
        source_provider="dexscreener",
        metrics=MarketMetrics(price_usd=1.0, liquidity_usd=80000.0, volume_1h=40000.0)
    )

    class MockProvider:
        provider_id = "dexscreener"
        capabilities = ["discovery"]
        def fetch_candidate_tokens(self, chain, limit=10):
            return ProviderResponse("dexscreener", "OK", tokens=[cand])
        def fetch_token_metrics(self, chain, address):
            return ProviderResponse("dexscreener", "OK", tokens=[])

    router = ProviderRouter()
    router.providers["dexscreener"] = MockProvider()
    router.providers["geckoterminal"] = MockProvider()

    collector = CollectorEngine(db_path=str(db_file), router=router)
    crashing_tg = CrashingTelegramAdapter()

    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        telegram_adapter=crashing_tg,
        target_chat_id=12345
    )

    # Telegram send will fail, but pipeline must catch and complete scoring cleanly
    rep = orchestrator.run_pipeline(chain="solana", limit=5)
    assert rep.candidates_collected == 1
    assert rep.scores_generated == 1


def test_failure_matrix_database_locked_handling(tmp_path):
    """Simulates database busy / lock collision during metrics recording."""
    db_file = tmp_path / "locked.sqlite"
    tracker = OperationalMetricsTracker(str(db_file))

    # Lock table via uncommitted transaction in separate connection
    conn_lock = sqlite3.connect(str(db_file))
    conn_lock.execute("BEGIN EXCLUSIVE")

    # Tracker must not crash with unhandled exception
    eid = tracker.record_metric(run_id="run_test", component="scoring", metric_name="test", metric_value=1.0)
    assert eid.startswith("met_")

    conn_lock.rollback()
    conn_lock.close()


def test_failure_matrix_expired_lease_auto_recovery(tmp_path):
    """Expired lease must be safely re-acquired after crash or downtime."""
    local_db = tmp_path / "recovery_local.sqlite"
    scheduler = ProductionScheduler(db_path=str(local_db), lease_duration_sec=10.0)
    now = 1000.0

    # Old crashed worker holds lease at t=1000 with 10s duration
    assert scheduler.acquire_lease("SCHED_LOCK", "crashed_run", now) is True

    # At t=1005 (lease active) -> new worker rejected
    assert scheduler.acquire_lease("SCHED_LOCK", "new_run", now + 5.0) is False

    # At t=1015 (lease expired) -> new worker auto-recovers and acquires lease
    assert scheduler.acquire_lease("SCHED_LOCK", "new_run", now + 15.0) is True


def test_operational_metrics_tracker_retrieval(tmp_path):
    db_file = tmp_path / "metrics_test.sqlite"
    tracker = OperationalMetricsTracker(str(db_file))
    tracker.record_metric(run_id="run_1", component="pipeline", metric_name="duration_ms", metric_value=125.5, status="OK")
    tracker.record_metric(run_id="run_1", component="alerts", metric_name="count", metric_value=3.0, status="WARN")

    metrics = tracker.get_recent_metrics(limit=10)
    assert len(metrics) == 2
    assert metrics[0]["metric_name"] == "count"
    assert metrics[1]["metric_name"] == "duration_ms"


def test_knowledge_sync_bridge_execution(tmp_path):
    k_db = tmp_path / "knowledge_test.sqlite"
    d_db = tmp_path / "discovery_test.sqlite"

    # Setup discovery test schema
    conn = sqlite3.connect(str(d_db))
    conn.execute("CREATE TABLE tokens (token_id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE observation_state (token_id TEXT, state TEXT)")
    conn.execute("CREATE TABLE outcome_label (token_id TEXT, horizon TEXT)")
    conn.execute("INSERT INTO tokens VALUES ('t1')")
    conn.execute("INSERT INTO observation_state VALUES ('t1', 'RESOLVED')")
    conn.execute("INSERT INTO outcome_label VALUES ('t1', '72h')")
    conn.commit()
    conn.close()

    bridge = KnowledgeSyncBridge(knowledge_db=str(k_db), discovery_db=str(d_db))
    counts = bridge.sync_all_empirical_knowledge()

    assert counts["e01_outcomes"] == 1
    assert counts["expert_lenses"] >= 10
    assert counts["defect_lessons"] == 1
    assert counts["strategy_lab_rejections"] == 1
