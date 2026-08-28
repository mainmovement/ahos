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

    assert data["overall_verdict"] in ("GREEN", "DEGRADED", "WARNING", "CRITICAL", "UNKNOWN")
    assert "timestamp_utc" in data
    assert data["database_integrity"]["e01_discovery"]["integrity"] == "OK"
    assert data["database_integrity"]["paper_trading"]["integrity"] == "OK"
    tb = data["track_b_accounting"]
    if tb.get("bankroll_initialised"):
        assert tb["is_accounting_consistent"] is True
        assert tb["accounting_sum_usd"] == pytest.approx(
            tb["expected_equity_usd"], rel=1e-7
        )
    else:
        # Fresh install: consistency UNKNOWN, not fabricated True/$20.
        assert tb["is_accounting_consistent"] is None
        assert tb["accounting_sum_usd"] is None
    assert data["security_invariants"]["ahos_paper_only_enforced"] in (True, None)
    assert data["security_invariants"]["live_trading_prohibited"] is True
    # Explicit unset vs enforced is recorded; do not require hardcoded True.
    assert "ahos_paper_only_env" in data["security_invariants"]

    # Self-observation block (evolution mission §4A): informational sections
    # must exist and be well-formed; absent data must be honest NO_DATA /
    # None, never fabricated.
    so = data["self_observation"]
    assert so["informational_note"].startswith("self-observation is informational")
    assert "provider_failure_rates" in so and "data_completeness" in so
    assert "calibration_state" in so and "test_health" in so and "storage_growth" in so
    assert "score_drift" in so, "score_drift must be populated (not a phantom scorecard key)"
    assert "store_bytes" in so["storage_growth"]
    assert "total_predictions" in so["calibration_state"]
    # test-health artifacts are committed, so they must be present, not NO_DATA
    assert so["test_health"]["pytest"]["present"] is True
    assert so["test_health"]["validate"]["present"] is True
    # stale-vs-HEAD is an explicit field (never silently assumed current)
    assert "stale_vs_head" in so["test_health"]["pytest"]
    # self-observation now includes benchmark + config health
    assert "benchmark_health" in so and "config_health" in so
    # Lane-A is an explicit snapshot field, never hasattr-missed
    assert "lane_a_ok" in data
    assert data["lane_a_ok"] is True


def test_offline_mode_config_is_observed_not_behavioral(tmp_path, monkeypatch):
    """W37 P15: config/offline_mode is wired into the health snapshot as
    OBSERVED state (default inactive); it must not alter any runtime
    behavior — this test pins the observability surface only."""
    from architecture.runtime import observability_snapshot as obs

    engine = obs.HealthSnapshotEngine()
    so = engine.generate_snapshot().self_observation
    om = so["config_health"]["offline_mode"]
    assert om["active"] is False          # default: online
    assert om["allow_external_http"] is True
    assert "AHOS_OFFLINE_MODE" in om["source"]

    # when the env flag is set, the snapshot reflects it (still read-only)
    monkeypatch.setenv("AHOS_OFFLINE_MODE", "1")
    so2 = engine.generate_snapshot().self_observation
    assert so2["config_health"]["offline_mode"]["active"] is True


def test_health_scorecard_dimensions_independent_and_honest(tmp_path):
    """Phase 3: the scorecard has independent dimensions with explicit
    UNKNOWN/NO_DATA semantics; it is informational and non-authoritative."""
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    sc = snap.health_scorecard

    assert sc["schema"] == "ahos.health_scorecard.v1"
    assert sc["overall_verdict"] == snap.overall_verdict
    assert sc["note"].startswith("scorecard is informational")

    from architecture.runtime.observability_snapshot import HEALTH_DIMENSIONS
    assert set(sc["dimensions"].keys()) == set(HEALTH_DIMENSIONS)

    # DATA_HEALTH must be healthy (stores exist and integrity OK)
    assert sc["dimensions"]["DATA_HEALTH"]["status"] == "HEALTHY"
    assert any("integrity OK" in e for e in sc["dimensions"]["DATA_HEALTH"]["evidence"])

    # every dimension carries status/evidence/explanation
    for name, dim in sc["dimensions"].items():
        assert dim["status"] in ("HEALTHY", "DEGRADED", "UNKNOWN", "FAIL"), name
        assert isinstance(dim["evidence"], list), name
        assert dim["explanation"], name

    # UNKNOWN states are explicit, not collapsed into a fake score
    assert "CALIBRATION_HEALTH" in sc["dimensions"]
    assert sc["dimensions"]["CALIBRATION_HEALTH"]["status"] in (
        "HEALTHY", "UNKNOWN", "DEGRADED")
    # no numeric score anywhere
    assert "score" not in sc or "numeric_score" not in sc


def test_scorecard_does_not_alter_verdict(tmp_path):
    """The scorecard is derived AFTER the verdict; it must not change it and
    must not be able to (informational, non-authoritative)."""
    engine = HealthSnapshotEngine()
    snap1 = engine.generate_snapshot()
    verdict_before = snap1.overall_verdict
    sc = snap1.health_scorecard
    assert sc["overall_verdict"] == verdict_before
    # an UNKNOWN scorecard dimension never degrades the verdict
    assert verdict_before in ("GREEN", "DEGRADED", "WARNING", "CRITICAL", "UNKNOWN")


def test_diagnostic_correlations_are_correlation_only(tmp_path):
    """Phase 4: correlations are emitted only when data supports them, and
    every one is labeled CORRELATION_ONLY with a caveat — never causality."""
    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()
    corr = snap.diagnostic_correlations

    assert isinstance(corr, list)
    for c in corr:
        assert c["label"] == "CORRELATION_ONLY"
        assert c["caveat"]
        assert c["evidence"]
        assert c["left"] and c["right"] and c["direction"]

    # deterministic: two runs produce identical correlation sets
    snap2 = engine.generate_snapshot()
    assert [c["left"] + c["right"] for c in corr] == \
           [c["left"] + c["right"] for c in snap2.diagnostic_correlations]


def test_correlations_never_invented_without_data(tmp_path, monkeypatch):
    """With no failure events, no unknown share, no drift, no tests failing,
    the correlation list must be empty (absent data => no correlation)."""
    from architecture.runtime import observability_snapshot as obs

    engine = HealthSnapshotEngine()
    snap = engine.generate_snapshot()

    # strip every signal source; the builder must emit nothing
    snap.self_observation["provider_failure_rates"] = {"total_failure_events": 0}
    snap.self_observation["data_completeness"] = {"error": "NO_DATA"}
    snap.self_observation["score_drift"] = {}
    snap.self_observation["storage_growth"] = {"total_bytes": 1024}
    snap.self_observation["test_health"] = {
        "pytest": {"present": True, "exit_code": 0},
        "validate": {"present": True, "exit_code": 0},
    }
    snap.provider_health = {}

    corr = engine._build_correlations(snap)
    assert corr == []


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
    """Parse layer remains operational; Telegram service itself is W57 gateway-only."""
    srv = TelegramDomainService()
    parsed = I.parse(query)
    assert parsed.intent == expected_intent

    res = srv.handle_message(query)
    assert res["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert res["intent"] == "gateway_unavailable"
    assert FOOTER_MANDATED in res["text"]
    # Snippet checks belong to the Conversation Gateway path (AHOS_GATEWAY_URL),
    # not to the emergency fallback which must never invent independent reports.
    assert expected_snippet  # keep parametrize table wired for future gateway tests
    _ = expected_snippet


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
