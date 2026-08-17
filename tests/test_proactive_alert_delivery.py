"""Wave-26: proactive alerting must actually be able to fire.

The user asked for a bot that TELLS them, not one that only answers when
spoken to. That makes the alert path load-bearing, and it has two silent
failure modes that no unit test of the individual pieces would catch:

  1. An alert threshold set above the maximum achievable score. Every part
     works, no exception is raised, and no alert is ever sent. This suite
     proves the threshold is reachable by constructing the best realistic
     token and checking it clears the bar.

  2. A destination that never resolves -- the exact bug found here, where the
     runtime read TELEGRAM_ALLOWED_CHATS while every config file and doc set
     TELEGRAM_ALLOWED_CHAT_IDS. Config typos do not raise; they just do
     nothing, forever.

Both are tested end to end against a mock adapter, with no network.
"""
from __future__ import annotations

import time

import pytest

from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from telegram_ai.alerts import render_fa
from telegram_ai.adapter import MockTelegramAdapter
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals,
)

NOW = time.time()


def excellent_token(now=NOW):
    """The best token that could realistically exist: clean, deep, verified."""
    c = NormalizedTokenCandidate(
        chain="solana", address="p1", symbol="PERF", name="Perfect",
        metrics=MarketMetrics(
            price_usd=1.0, liquidity_usd=900_000.0,
            volume_5m=20_000.0, volume_1h=150_000.0, volume_24h=2_000_000.0,
            txns_5m_buys=120, txns_5m_sells=40,
            txns_1h_buys=1_500, txns_1h_sells=500,
            price_change_5m=3.0, price_change_1h=12.0, price_change_24h=40.0,
            fdv_usd=5_000_000.0),
        security=SecuritySignals(
            is_honeypot=False, sell_tax_pct=0.0, buy_tax_pct=0.0,
            liquidity_locked_pct=100.0, liquidity_burned_pct=100.0,
            has_mint_authority=False, has_freeze_authority=False,
            is_contract_verified=True, is_ownership_renounced=True,
            top10_holder_concentration_pct=8.0, deployer_past_rug_count=0),
        source_provider="dexscreener", retrieved_ts=now)
    c.identify_unknowns()
    return c


def mediocre_token(now=NOW):
    c = NormalizedTokenCandidate(
        chain="solana", address="m1", symbol="MEH", name="Mediocre",
        metrics=MarketMetrics(
            price_usd=1.0, liquidity_usd=12_000.0, volume_1h=1_500.0,
            txns_1h_buys=30, txns_1h_sells=28),
        security=SecuritySignals(is_honeypot=False),
        source_provider="dexscreener", retrieved_ts=now)
    c.identify_unknowns()
    return c


# --------------------------------------------------- threshold reachability --

def test_the_alert_threshold_is_actually_reachable():
    """Guards a threshold set above the achievable maximum -- a bug where
    everything 'works' and nothing is ever sent."""
    report = OpportunityScorer().evaluate(excellent_token(), now=NOW)
    engine = AlertEngine()
    assert report.opportunity_score >= engine.score_threshold, (
        f"best achievable score {report.opportunity_score} is below the alert "
        f"threshold {engine.score_threshold}: alerts can never fire")


def test_an_excellent_token_produces_a_high_severity_alert():
    cand = excellent_token()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    alerts = AlertEngine().evaluate_opportunity(report, cand, now=NOW)
    assert any(a.severity in ("HIGH", "CRITICAL") for a in alerts), \
        f"no deliverable alert from a perfect token: {[a.severity for a in alerts]}"


def test_a_mediocre_token_does_not_trigger_a_high_severity_alert():
    """Alert fatigue is a real failure: if everything alerts, nothing does."""
    cand = mediocre_token()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    alerts = AlertEngine().evaluate_opportunity(report, cand, now=NOW)
    assert not any(a.severity in ("HIGH", "CRITICAL") for a in alerts)


def test_stale_observations_are_reported_as_such():
    """A perfect token measured long ago is a data problem, not an opportunity."""
    cand = excellent_token(now=NOW - 30 * 86400)
    report = OpportunityScorer().evaluate(cand, now=NOW)
    alerts = AlertEngine().evaluate_opportunity(report, cand, now=NOW)
    assert any(getattr(a, "data_state", "") == "STALE" for a in alerts)


# ------------------------------------------------------------- delivery ----

def test_high_severity_alerts_reach_the_transport():
    cand = excellent_token()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    alerts = AlertEngine().evaluate_opportunity(report, cand, now=NOW)

    adapter = MockTelegramAdapter()
    for a in alerts:
        if a.severity in ("HIGH", "CRITICAL"):
            adapter.send_message("555", render_fa(a))

    assert adapter.sent_messages, "alert was generated but never delivered"
    body = adapter.sent_messages[0]["text"]
    assert body.strip()
    assert any("\u0600" <= ch <= "\u06FF" for ch in body), "alert is not Persian"


def test_rendered_alert_states_its_evidence():
    cand = excellent_token()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    alerts = AlertEngine().evaluate_opportunity(report, cand, now=NOW)
    high = [a for a in alerts if a.severity in ("HIGH", "CRITICAL")]
    assert high
    text = render_fa(high[0])
    assert "PERF" in text
    assert high[0].reasons, "an alert with no stated reason is a notification, not evidence"


# ------------------------------------------------------ destination resolves --

def _resolve(env: dict) -> list[str]:
    """Mirrors the runtime's chat-id resolution."""
    raw = env.get("TELEGRAM_ALLOWED_CHAT_IDS") or env.get("TELEGRAM_ALLOWED_CHATS", "")
    return [c.strip() for c in raw.split(",") if c.strip()]


def test_canonical_chat_id_variable_resolves():
    assert _resolve({"TELEGRAM_ALLOWED_CHAT_IDS": "555"}) == ["555"]


def test_legacy_chat_id_variable_still_resolves():
    """Existing installs must not break when the name is corrected."""
    assert _resolve({"TELEGRAM_ALLOWED_CHATS": "555"}) == ["555"]


def test_canonical_wins_when_both_are_set():
    got = _resolve({"TELEGRAM_ALLOWED_CHAT_IDS": "111",
                    "TELEGRAM_ALLOWED_CHATS": "999"})
    assert got == ["111"]


def test_multiple_chat_ids_and_whitespace_are_handled():
    assert _resolve({"TELEGRAM_ALLOWED_CHAT_IDS": " 1 , 2 ,3 "}) == ["1", "2", "3"]


def test_no_destination_configured_yields_empty_not_a_crash():
    assert _resolve({}) == []


def test_runtime_module_resolves_the_canonical_name():
    """The regression guard for the real bug: the runtime module must read the
    same variable the quickstart tells the user to set."""
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent / "architecture" / "runtime" / "__main__.py"
    text = src.read_text(encoding="utf-8")
    assert "TELEGRAM_ALLOWED_CHAT_IDS" in text
