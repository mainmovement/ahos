#!/usr/bin/env python3
"""Tests for exit feasibility and holder-concentration analysis.

These guard the two questions that decide whether a "winning" token is actually
profitable: can you sell, and who is standing behind you when you try?

Proves:
  - honeypot / mint / freeze / extreme tax produce HARD VETOES
  - realizable value shrinks as position size grows against pool depth
  - unknown price or liquidity => UNKNOWN, never an optimistic guess
  - concentration is a risk DEDUCTION, and rising concentration during a pump
    is flagged as a trap
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intel.exitability import ExitabilityAnalyzer, SELL_TAX_VETO_PCT  # noqa: E402
from architecture.intel.whales import (  # noqa: E402
    WhaleTracker, CONCENTRATION_CRITICAL, SINGLE_WALLET_CRITICAL,
)
from architecture.providers.contracts import (  # noqa: E402
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals,
)


def _cand(metrics=None, security=None, chain="solana") -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain=chain, address="Tok111", symbol="TOK", name="Token",
        metrics=metrics or MarketMetrics(), security=security or SecuritySignals(),
    )


# ============================ HARD VETOES ==================================

def test_honeypot_is_an_absolute_veto():
    c = _cand(MarketMetrics(price_usd=0.01, liquidity_usd=500_000),
              SecuritySignals(is_honeypot=True))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.verdict == "TRAPPED"
    assert r.hard_vetoes
    assert r.is_safe is False


def test_extreme_sell_tax_is_a_soft_honeypot_veto():
    c = _cand(MarketMetrics(price_usd=1.0, liquidity_usd=500_000),
              SecuritySignals(sell_tax_pct=SELL_TAX_VETO_PCT + 5))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.verdict == "TRAPPED"
    assert any("مالیات فروش" in v for v in r.hard_vetoes)


@pytest.mark.parametrize("field", ["has_mint_authority", "has_freeze_authority"])
def test_live_authorities_are_vetoes(field):
    c = _cand(MarketMetrics(price_usd=1.0, liquidity_usd=500_000),
              SecuritySignals(**{field: True}))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.hard_vetoes, f"{field}=True must veto entry"
    assert r.verdict == "TRAPPED"


def test_clean_token_with_deep_pool_is_exitable():
    c = _cand(MarketMetrics(price_usd=0.001, liquidity_usd=250_000),
              SecuritySignals(is_honeypot=False, sell_tax_pct=1.0,
                              liquidity_locked_pct=95.0,
                              has_mint_authority=False, has_freeze_authority=False))
    r = ExitabilityAnalyzer().analyze(c, position_usd=200)
    assert r.verdict == "EXITABLE"
    assert r.is_safe is True
    assert r.realizable_fraction > 0.9


# ========================= SIZE / DEPTH MATHS ==============================

def test_realizable_fraction_degrades_as_position_grows():
    """The core lesson: the same token is fine at $100 and a trap at $100k."""
    c = _cand(MarketMetrics(price_usd=0.001, liquidity_usd=50_000),
              SecuritySignals(is_honeypot=False, sell_tax_pct=1.0))
    a = ExitabilityAnalyzer()
    fractions = [a.analyze(c, position_usd=n).realizable_fraction
                 for n in (100, 1_000, 10_000, 40_000)]
    assert all(f is not None for f in fractions)
    assert fractions == sorted(fractions, reverse=True), "bigger exit must cost more"
    assert fractions[0] > 0.9
    assert fractions[-1] < 0.5


def test_oversized_position_is_flagged_trapped():
    c = _cand(MarketMetrics(price_usd=0.001, liquidity_usd=20_000),
              SecuritySignals(is_honeypot=False, sell_tax_pct=1.0))
    r = ExitabilityAnalyzer().analyze(c, position_usd=18_000)
    assert r.verdict == "TRAPPED"
    assert r.pool_share_pct > 50


def test_max_safe_position_is_computed_and_respected():
    c = _cand(MarketMetrics(price_usd=0.001, liquidity_usd=100_000),
              SecuritySignals(is_honeypot=False, sell_tax_pct=1.0))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.max_safe_position_usd is not None
    assert 0 < r.max_safe_position_usd <= 100_000
    safe = ExitabilityAnalyzer().analyze(c, position_usd=r.max_safe_position_usd)
    assert safe.verdict in ("EXITABLE", "DEGRADED")


# ============================== UNKNOWNS ===================================

def test_missing_liquidity_is_unknown_not_optimistic():
    c = _cand(MarketMetrics(price_usd=0.01, liquidity_usd=None))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.verdict == "UNKNOWN"
    assert r.realizable_fraction is None
    assert r.unknowns


def test_missing_price_is_unknown():
    c = _cand(MarketMetrics(price_usd=None, liquidity_usd=100_000))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.verdict == "UNKNOWN"
    assert r.realizable_fraction is None


def test_veto_survives_missing_data():
    """A honeypot with unknown liquidity is still a honeypot."""
    c = _cand(MarketMetrics(price_usd=None, liquidity_usd=None),
              SecuritySignals(is_honeypot=True))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert r.verdict == "TRAPPED"
    assert r.hard_vetoes


def test_unlocked_liquidity_warns():
    c = _cand(MarketMetrics(price_usd=0.001, liquidity_usd=100_000),
              SecuritySignals(is_honeypot=False, sell_tax_pct=1.0,
                              liquidity_locked_pct=5.0, liquidity_burned_pct=0.0))
    r = ExitabilityAnalyzer().analyze(c, position_usd=100)
    assert any("قفل" in w for w in r.warnings)


# ============================== WHALES =====================================

def test_unknown_holder_data_is_unknown():
    """Free RPC usually refuses holder lists — we must say so, not estimate."""
    s = WhaleTracker().analyze("TOK", top10_share_pct=None)
    assert s.label == "UNKNOWN"
    assert s.is_known is False
    assert s.risk_penalty == 0.0
    assert s.unknowns


def test_critical_concentration_is_dangerous_and_penalised():
    s = WhaleTracker().analyze("TOK", top10_share_pct=CONCENTRATION_CRITICAL + 5)
    assert s.label == "DANGEROUS"
    assert s.risk_penalty > 0
    assert s.warnings


def test_single_dominant_wallet_is_dangerous():
    s = WhaleTracker().analyze("TOK", top10_share_pct=45.0,
                               top1_share_pct=SINGLE_WALLET_CRITICAL + 5)
    assert s.label == "DANGEROUS"
    assert any("تک‌نقطه‌ای" in w for w in s.warnings)


def test_healthy_distribution_scores_no_penalty():
    s = WhaleTracker().analyze("TOK", top10_share_pct=15.0, top1_share_pct=4.0,
                               holder_count=5000)
    assert s.label == "STABLE"
    assert s.risk_penalty == 0.0
    assert s.reasons


def test_distribution_trend_detected():
    s = WhaleTracker().analyze("TOK", top10_share_pct=30.0,
                               previous_top10_share_pct=45.0)
    assert s.label == "DISTRIBUTING"
    assert s.delta_pct_points == pytest.approx(-15.0)


def test_accumulation_during_pump_is_flagged_as_trap():
    """Concentration rising while price rips == float being thinned under buyers."""
    s = WhaleTracker().analyze("TOK", top10_share_pct=60.0,
                               previous_top10_share_pct=45.0,
                               price_change_pct=150.0)
    assert s.label == "ACCUMULATING"
    assert any("تله" in w for w in s.warnings)
    assert s.risk_penalty > 0


def test_penalty_is_bounded():
    s = WhaleTracker().analyze("TOK", top10_share_pct=99.0, top1_share_pct=95.0,
                               previous_top10_share_pct=10.0, holder_count=3,
                               price_change_pct=500.0)
    assert 0.0 <= s.risk_penalty <= 50.0
