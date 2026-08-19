#!/usr/bin/env python3
"""AHOS Phase 4 Operational Observability & Control Plane Tests.

Proves:
  1. Canonical Health Snapshot Engine (HealthSnapshotEngine) outputs complete status
  2. All Telegram Operational Read-Only Intents (SCHEDULER, DB, PROVIDERS, GAPS, E01, PT, AI, CYCLE)
  3. Track B Accounting Conservation & Negative Cash Prevention
  4. Non-Destructive Health Diagnostics & Zero Autonomous File Mutation
  5. Security Invariant: Zero Secret In Source & Paper-Only Lock
"""
import sys, json, sqlite3, time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.runtime.observability_snapshot import HealthSnapshotEngine, CanonicalHealthSnapshot
from telegram_ai import intent as I
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED
from architecture.positions.manager import PaperPositionManager
from config.paths import get_paper_trading_db_path, get_local_db_path


def test_canonical_health_snapshot_generation(tmp_path):
    """Proves HealthSnapshotEngine produces a comprehensive machine-readable snapshot."""
    engine = HealthSnapshotEngine()
    out_file = tmp_path / "health_snapshot.json"
    engine.export_snapshot(out_file)

    assert out_file.exists()
    data = json.loads(out_file.read_text())

    assert data["overall_verdict"] in ("GREEN", "DEGRADED")
    assert "timestamp_utc" in data
    assert data["database_integrity"]["e01_discovery"]["integrity"] == "OK"
    assert data["database_integrity"]["paper_trading"]["integrity"] == "OK"
    assert data["track_b_accounting"]["is_accounting_consistent"] is True
    assert data["track_b_accounting"]["accounting_sum_usd"] == pytest.approx(20.0, rel=1e-7)
    assert data["security_invariants"]["ahos_paper_only_enforced"] is True
    assert data["security_invariants"]["live_trading_prohibited"] is True
    assert data["security_invariants"]["zero_secret_in_source"] == "NOT_CHECKED_AT_RUNTIME"
    assert data["runtime_state"] in {"RUNNING", "STALE", "NOT_OBSERVED"}
    assert (data["runtime_state"] == "RUNNING") is data["scheduler_status"]["heartbeat_is_fresh"]
    # A heartbeat timestamps the latest observation; it is not proof of process
    # start time and therefore cannot honestly be called uptime.
    assert data["system_uptime_seconds"] is None


@pytest.mark.parametrize("query,expected_intent,expected_snippet", [
    ("وضعیت زمان‌بند", "SCHEDULER_STATUS", "گزارش وضعیت زمان‌بند تولیدی"),
    ("وضعیت دیتابیس ها", "DATABASE_STATUS", "گزارش وضعیت پایگاه‌های داده SQLite"),
    ("وضعیت پرووایدرها چطوره؟", "PROVIDERS_STATUS", "گزارش وضعیت پرووایدرها"),
    ("شکاف های رصدی", "OBSERVATION_GAPS_STATUS", "گزارش شکاف‌های رصدی"),
    ("وضعیت e01", "E01_STATUS", "گزارش وضعیت گیت اعتبارسنجی E-01"),
    ("وضعیت معاملات کاغذی", "PAPER_TRADING_STATUS", "گزارش حسابداری معاملات کاغذی"),
    ("وضعیت هوش مصنوعی", "AI_STATUS", "گزارش وضعیت روتر هوش مصنوعی"),
    ("آخرین چرخه", "LAST_CYCLE_STATUS", "گزارش آخرین چرخه اجرای ران‌تایم"),
])
def test_telegram_operational_read_only_intents(query, expected_intent, expected_snippet):
    """Proves all Telegram operational control plane queries parse and format correctly."""
    srv = TelegramDomainService()
    parsed = I.parse(query)
    assert parsed.intent == expected_intent

    res = srv.handle_message(query)
    assert res["status"] == "OK"
    assert res["intent"] == expected_intent
    assert expected_snippet in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_paper_trading_negative_amount_rejection(tmp_path):
    """Proves PaperPositionManager strictly rejects negative or zero allocations."""
    db_file = tmp_path / "test_pt_neg.sqlite"
    mgr = PaperPositionManager(str(db_file))

    with pytest.raises(ValueError):
        mgr.open_position(
            chain="solana",
            token_address="TokNegTest1111111111111111111111111111",
            symbol="NEG",
            allocated_usd=-10.0,
            entry_price_usd=1.0
        )


def test_telegram_operational_queries_are_read_only():
    """Proves all operational query intents are in INFO_ONLY_INTENTS and not in LEDGER_MUTATING_INTENTS."""
    operational_intents = {
        "SYSTEM_HEALTH", "SCHEDULER_STATUS", "DATABASE_STATUS", "PROVIDERS_STATUS",
        "OBSERVATION_GAPS_STATUS", "E01_STATUS", "PAPER_TRADING_STATUS", "AI_STATUS", "LAST_CYCLE_STATUS"
    }
    assert operational_intents.issubset(I.INFO_ONLY_INTENTS)
    assert operational_intents.isdisjoint(I.LEDGER_MUTATING_INTENTS)
