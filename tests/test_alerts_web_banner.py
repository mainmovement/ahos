#!/usr/bin/env python3
"""Command Center must fetch /api/alerts; banner cannot mint BUY locally."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_alerts_route_rechecks_canonical_buy_and_overlay():
    text = (ROOT / "app" / "api" / "alerts" / "route.ts").read_text(encoding="utf-8")
    assert "evaluateWebAlertBanner" in text
    assert "loadCanonicalReadModel" in text
    assert "authorizeWebApi" in text
    assert "active: true" not in text


def test_command_center_fetches_alerts_api():
    text = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")
    assert 'webApiFetch("/api/alerts"' in text
    assert "monitor-banner" in text
    assert "alertBanner.active" in text
    # Must not treat the banner as a buy signal / flashing FOMO alarm.
    assert "سیگنال خرید" in text or "فقط کاغذی" in text
    assert "alarm-banner" in text  # system errors remain separate


def test_web_alert_banner_module_is_fail_closed():
    text = (ROOT / "alert_banner.ts").read_text(encoding="utf-8")
    assert "alertsAllowedFromCanonical" in text
    assert "canonicalSecurityAllowsSideEffect" in text
    assert "NOT_LIVE_BUY" in text
    assert "STORED_DECISION_NOT_BUY" in text
    assert 'outcome: "BUY"' not in text
