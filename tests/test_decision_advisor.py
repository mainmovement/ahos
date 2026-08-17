#!/usr/bin/env python3
"""Tests for the decision advisor — the layer that says what to actually do.

This is where a mistake costs real money, so the gates are pinned hard:

  GATE 1  security veto  -> AVOID, unconditionally
  GATE 2  exitability    -> cannot get out => never go in
  GATE 3  liquidity floor
  GATE 4  score + evidence modifiers
  SIZING  bounded by pool depth AND bankroll, never by conviction alone
  EXITS   planned before entry, from the locked PT-X1-v1 rules
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.decision.advisor import (  # noqa: E402
    DecisionAdvisor, MIN_LIQUIDITY_USD, MAX_POOL_SHARE_PCT, MAX_BANKROLL_RISK_PCT,
)
from architecture.intel.exitability import ExitabilityAnalyzer  # noqa: E402
from architecture.intel.viral import ViralityTracker  # noqa: E402
from architecture.intel.whales import WhaleTracker  # noqa: E402
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from architecture.ai.council_live import CouncilVerdict  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals,
)
from paper_trading.exit_rules import EXIT_V1  # noqa: E402


def _healthy_metrics(**over):
    d = dict(price_usd=0.002, liquidity_usd=150_000,
             volume_5m=9_000, volume_1h=30_000, volume_24h=250_000,
             txns_5m_buys=90, txns_5m_sells=25,
             txns_1h_buys=400, txns_1h_sells=250, price_change_1h=12.0)
    d.update(over)
    return MarketMetrics(**d)


def _healthy_security(**over):
    d = dict(is_honeypot=False, sell_tax_pct=1.0, buy_tax_pct=1.0,
             liquidity_locked_pct=95.0, has_mint_authority=False,
             has_freeze_authority=False, is_contract_verified=True,
             top10_holder_concentration_pct=20.0)
    d.update(over)
    return SecuritySignals(**d)


def _cand(metrics=None, security=None, symbol="TOK"):
    return NormalizedTokenCandidate(
        chain="solana", address="Tok111", symbol=symbol, name=f"{symbol} Token",
        metrics=metrics if metrics is not None else _healthy_metrics(),
        security=security if security is not None else _healthy_security(),
        source_provider="dexscreener", retrieved_ts=time.time(),
    )


def _advise(cand, advisor=None, **kw):
    advisor = advisor or DecisionAdvisor(bankroll_usd=1000.0)
    report = OpportunityScorer().evaluate(cand)
    return advisor.advise_entry(
        cand, report,
        exitability=kw.pop("exitability", ExitabilityAnalyzer().analyze(cand, 200)),
        **kw,
    )


# ============================ GATE 1 — SECURITY ============================

def test_honeypot_is_avoided_regardless_of_everything_else():
    c = _cand(_healthy_metrics(), _healthy_security(is_honeypot=True))
    a = _advise(c)
    assert a.action == "AVOID"
    assert a.conviction == "NONE"
    assert a.hard_vetoes
    assert a.suggested_size_usd is None
    assert a.is_actionable is False


def test_serial_rugger_deployer_is_avoided():
    c = _cand(_healthy_metrics(), _healthy_security(deployer_past_rug_count=3))
    a = _advise(c)
    assert a.action == "AVOID"
    assert any("راگ" in v or "rug" in v.lower() for v in a.hard_vetoes)


def test_mint_authority_blocks_entry():
    c = _cand(_healthy_metrics(), _healthy_security(has_mint_authority=True))
    a = _advise(c)
    assert a.action == "AVOID"
    assert a.hard_vetoes


# ========================== GATE 2 — EXITABILITY ===========================

def test_trapped_exit_blocks_entry_even_with_great_metrics():
    """A token you cannot sell is not an opportunity at any score."""
    c = _cand(_healthy_metrics(liquidity_usd=800), _healthy_security())
    a = _advise(c, exitability=ExitabilityAnalyzer().analyze(c, position_usd=5_000))
    assert a.action == "AVOID"


def test_position_size_never_exceeds_exit_capacity():
    c = _cand(_healthy_metrics(liquidity_usd=60_000))
    ex = ExitabilityAnalyzer().analyze(c, position_usd=200)
    a = _advise(c, advisor=DecisionAdvisor(bankroll_usd=1_000_000), exitability=ex)
    if a.suggested_size_usd:
        assert a.suggested_size_usd <= ex.max_safe_position_usd


# =========================== GATE 3 — LIQUIDITY ============================

def test_liquidity_below_floor_is_avoided():
    c = _cand(_healthy_metrics(liquidity_usd=MIN_LIQUIDITY_USD - 1))
    a = _advise(c)
    assert a.action == "AVOID"
    assert any("نقدینگی" in r for r in a.reasons)


def test_unknown_liquidity_is_wait_not_avoid_and_not_enter():
    """UNKNOWN is its own answer: we neither reject nor gamble."""
    c = _cand(_healthy_metrics(liquidity_usd=None))
    a = _advise(c, exitability=None)
    assert a.action == "WAIT"
    assert a.unknowns


# ============================== SIZING =====================================

def test_size_is_bounded_by_pool_share_and_bankroll():
    c = _cand(_healthy_metrics(liquidity_usd=200_000))
    advisor = DecisionAdvisor(bankroll_usd=1_000.0)
    a = _advise(c, advisor=advisor)
    if a.action == "ENTER":
        pool_cap = 200_000 * MAX_POOL_SHARE_PCT / 100.0
        bankroll_cap = 1_000.0 * MAX_BANKROLL_RISK_PCT / 100.0
        assert a.suggested_size_usd <= min(pool_cap, bankroll_cap) + 1e-6


def test_lower_conviction_yields_smaller_size():
    c = _cand(_healthy_metrics(liquidity_usd=500_000))
    advisor = DecisionAdvisor(bankroll_usd=10_000.0)
    report = OpportunityScorer().evaluate(c)
    ex = ExitabilityAnalyzer().analyze(c, 200)

    high = advisor.advise_entry(c, report, exitability=ex)
    council_unclear = CouncilVerdict(final_stance="UNCLEAR", agreement="SPLIT",
                                     council_status="ONLINE", responded=2)
    lowered = advisor.advise_entry(c, report, exitability=ex, council=council_unclear)

    if high.action == "ENTER" and lowered.action == "ENTER":
        assert lowered.suggested_size_usd <= high.suggested_size_usd


def test_size_is_never_negative_or_nan():
    for liq in (10_001, 50_000, 1_000_000):
        c = _cand(_healthy_metrics(liquidity_usd=liq))
        a = _advise(c)
        if a.suggested_size_usd is not None:
            assert a.suggested_size_usd > 0


# ======================== EXIT PLAN BEFORE ENTRY ===========================

def test_entry_advice_always_ships_an_exit_plan():
    c = _cand()
    a = _advise(c)
    if a.action == "ENTER":
        assert a.take_profit_price is not None
        assert a.stop_loss_price is not None
        assert a.max_hold_hours == EXIT_V1["max_hold_hours"]
        assert a.stop_loss_price < a.entry_price_usd < a.take_profit_price
        assert len(a.invalidation) >= 3


def test_exit_targets_match_locked_rules():
    c = _cand()
    a = _advise(c)
    if a.action == "ENTER":
        price = a.entry_price_usd
        assert a.take_profit_price == pytest.approx(
            price * (1 + EXIT_V1["take_profit_pct"]), rel=1e-9)
        assert a.stop_loss_price == pytest.approx(
            price * (1 - EXIT_V1["stop_loss_pct"]), rel=1e-9)


# ============================== COUNCIL ====================================

def test_council_avoid_downgrades_entry():
    c = _cand()
    council = CouncilVerdict(final_stance="AVOID", agreement="MAJORITY",
                             council_status="ONLINE", responded=3)
    a = _advise(c, council=council)
    assert a.action in ("WAIT", "AVOID")


def test_offline_council_does_not_block_a_good_setup():
    """The deterministic floor must work with zero AI availability."""
    c = _cand()
    council = CouncilVerdict(final_stance="DETERMINISTIC_ONLY", agreement="NONE",
                             council_status="OFFLINE", responded=0)
    online = _advise(c)
    offline = _advise(c, council=council)
    assert offline.action == online.action


def test_council_cannot_upgrade_a_weak_setup():
    """AI enthusiasm must never manufacture conviction the data does not support."""
    c = _cand(_healthy_metrics(liquidity_usd=MIN_LIQUIDITY_USD - 1))
    council = CouncilVerdict(final_stance="ENTER", agreement="UNANIMOUS",
                             council_status="ONLINE", responded=5)
    a = _advise(c, council=council)
    assert a.action == "AVOID", "no council may override the liquidity floor"


# ============================== POSITIONS ==================================

def test_stop_loss_triggers_immediate_full_exit():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=1.0 - EXIT_V1["stop_loss_pct"] - 0.01,
        entry_ts=time.time() - 3600)
    assert a.action == "EXIT"
    assert a.urgency == "IMMEDIATE"
    assert a.sell_fraction == 1.0


def test_take_profit_scales_out_rather_than_all_out():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=1.0 + EXIT_V1["take_profit_pct"] + 0.01,
        entry_ts=time.time() - 3600)
    assert a.action == "REDUCE"
    assert 0.0 < a.sell_fraction < 1.0


def test_security_alert_beats_profit():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=5.0,
        entry_ts=time.time() - 3600, security_alert=True)
    assert a.action == "EXIT"
    assert a.urgency == "IMMEDIATE"
    assert a.sell_fraction == 1.0


def test_liquidity_collapse_forces_exit():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=1.1, entry_ts=time.time() - 3600,
        current_liquidity=EXIT_V1["liq_collapse_floor_usd"] - 1)
    assert a.action == "EXIT"
    assert a.urgency == "IMMEDIATE"


def test_time_horizon_exit():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=1.05,
        entry_ts=time.time() - (EXIT_V1["max_hold_hours"] + 1) * 3600)
    assert a.action == "EXIT"


def test_healthy_position_holds_with_visible_targets():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=1.10, entry_ts=time.time() - 3600)
    assert a.action == "HOLD"
    assert a.sell_fraction == 0.0
    assert a.pnl_pct == pytest.approx(10.0, rel=1e-6)
    assert len(a.reasons) >= 2


def test_missing_price_never_triggers_a_trade():
    a = DecisionAdvisor().advise_position(
        "TOK", entry_price=1.0, current_price=None, entry_ts=time.time() - 3600)
    assert a.action == "HOLD"
    assert a.sell_fraction == 0.0
    assert a.unknowns


# ============================== INVARIANTS =================================

def test_advice_is_serialisable_and_complete():
    a = _advise(_cand())
    d = a.to_dict()
    for key in ("action", "conviction", "reasons", "risks", "unknowns", "version"):
        assert key in d
    assert d["action"] in ("ENTER", "WAIT", "AVOID", "HOLD", "REDUCE", "EXIT")


def test_every_recommendation_carries_reasoning():
    """WHY-LAW: no verdict without justification."""
    for sec in (_healthy_security(),
                _healthy_security(is_honeypot=True),
                _healthy_security(has_mint_authority=True)):
        a = _advise(_cand(_healthy_metrics(), sec))
        assert a.reasons or a.hard_vetoes, "a verdict must always explain itself"
