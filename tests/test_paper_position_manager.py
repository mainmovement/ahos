#!/usr/bin/env python3
"""Tests for Paper Position Management Domain (Section XI)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.positions.manager import PaperPositionManager


@pytest.fixture
def manager(tmp_path):
    db_file = tmp_path / "test_paper.sqlite"
    return PaperPositionManager(str(db_file))


def test_open_paper_position(manager):
    pos = manager.open_position(
        chain="solana",
        token_address="TokPaperTest11111111111111111111111111111",
        symbol="PTST",
        allocated_usd=100.0,
        entry_price_usd=2.0,
        fee_bps=30.0,
        impact_bps=25.0
    )
    assert pos.position_id
    assert pos.status == "OPEN"
    assert pos.fee_entry_usd == 0.30
    assert pos.tokens_amount == (100.0 - 0.30) / 2.0


def test_position_take_profit_exit(manager):
    pos = manager.open_position(
        chain="solana",
        token_address="TokTPTest1111111111111111111111111111111",
        symbol="TPTST",
        allocated_usd=100.0,
        entry_price_usd=2.0
    )
    now = time.time()
    # Price moves to 3.20 (+60% profit) -> triggers TP exit (threshold +50%)
    res = manager.evaluate_position(
        position_id=pos.position_id,
        current_price_usd=3.20,
        last_obs_ts=now,
        now=now
    )
    assert res.action_taken == "TP_EXIT"
    assert res.status == "CLOSED_TP"
    assert res.unrealized_pnl_pct == pytest.approx(60.0)


def test_position_stop_loss_exit(manager):
    pos = manager.open_position(
        chain="solana",
        token_address="TokSLTest1111111111111111111111111111111",
        symbol="SLTST",
        allocated_usd=100.0,
        entry_price_usd=2.0
    )
    now = time.time()
    # Price moves to 1.40 (-30% loss) -> triggers SL exit (threshold -25%)
    res = manager.evaluate_position(
        position_id=pos.position_id,
        current_price_usd=1.40,
        last_obs_ts=now,
        now=now
    )
    assert res.action_taken == "SL_EXIT"
    assert res.status == "CLOSED_SL"
    assert res.unrealized_pnl_pct == pytest.approx(-30.0)


def test_position_invalidation_exit(manager):
    pos = manager.open_position(
        chain="solana",
        token_address="TokInvTest111111111111111111111111111111",
        symbol="INVTST",
        allocated_usd=100.0,
        entry_price_usd=2.0
    )
    now = time.time()
    # Honeypot signal emerges
    res = manager.evaluate_position(
        position_id=pos.position_id,
        current_price_usd=2.10,
        last_obs_ts=now,
        is_honeypot=True,
        now=now
    )
    assert res.action_taken == "INVALIDATION_EXIT"
    assert res.status == "CLOSED_INVALIDATED"


def test_position_stale_observation_handling(manager):
    pos = manager.open_position(
        chain="solana",
        token_address="TokStaleTest1111111111111111111111111111",
        symbol="STL",
        allocated_usd=100.0,
        entry_price_usd=2.0
    )
    now = time.time()
    # Observation is 5 hours old (>4h stale threshold)
    res = manager.evaluate_position(
        position_id=pos.position_id,
        current_price_usd=2.20,
        last_obs_ts=now - 5 * 3600,
        now=now
    )
    assert res.action_taken == "NO_DATA_HOLD"
    assert res.status == "OPEN"
