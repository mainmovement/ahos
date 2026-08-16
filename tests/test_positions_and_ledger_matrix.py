#!/usr/bin/env python3
"""Paper Position, Ledger Invariants, Fees, Slippage & PnL Matrix Tests (Phase XXI)."""
import sys, time, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.positions.manager import PaperPositionManager, PaperPosition, PositionEvaluation


@pytest.fixture
def manager(tmp_path):
    db_file = tmp_path / "positions_matrix.sqlite"
    return PaperPositionManager(str(db_file))


# ---------------- Fee, Impact & Slippage Calculation Tests ----------------
@pytest.mark.parametrize("alloc_usd,fee_bps,impact_bps,entry_px,expected_fee", [
    (100.0, 30.0, 25.0, 1.0, 0.30),
    (1000.0, 30.0, 25.0, 2.5, 3.00),
    (50.0, 50.0, 50.0, 0.5, 0.25),
    (500.0, 10.0, 10.0, 10.0, 0.50),
])
def test_paper_position_fee_deduction(manager, alloc_usd, fee_bps, impact_bps, entry_px, expected_fee):
    pos = manager.open_position(
        chain="solana",
        token_address="TokFeeTest11111111111111111111111111111",
        symbol="FEE",
        allocated_usd=alloc_usd,
        entry_price_usd=entry_px,
        fee_bps=fee_bps,
        impact_bps=impact_bps
    )
    assert pos.fee_entry_usd == pytest.approx(expected_fee)
    assert pos.tokens_amount == pytest.approx((alloc_usd - expected_fee) / entry_px)


# ---------------- Realizable vs Displayed PnL Matrix ----------------
@pytest.mark.parametrize("entry_px,current_px,expected_action,expected_status", [
    (1.0, 1.60, "TP_EXIT", "CLOSED_TP"),      # +60% >= +50% TP
    (1.0, 2.00, "TP_EXIT", "CLOSED_TP"),      # +100% >= +50% TP
    (1.0, 0.70, "SL_EXIT", "CLOSED_SL"),      # -30% <= -25% SL
    (1.0, 0.50, "SL_EXIT", "CLOSED_SL"),      # -50% <= -25% SL
    (1.0, 1.10, "HOLD", "OPEN"),              # +10% within hold bounds
    (1.0, 0.90, "HOLD", "OPEN"),              # -10% within hold bounds
])
def test_paper_position_pnl_thresholds(manager, entry_px, current_px, expected_action, expected_status):
    pos = manager.open_position(
        chain="solana",
        token_address="TokPnlTest1111111111111111111111111111",
        symbol="PNL",
        allocated_usd=100.0,
        entry_price_usd=entry_px
    )
    now = time.time()
    res = manager.evaluate_position(
        position_id=pos.position_id,
        current_price_usd=current_px,
        last_obs_ts=now,
        now=now
    )
    assert res.action_taken == expected_action
    assert res.status == expected_status


def test_paper_position_invalid_inputs_rejected(manager):
    with pytest.raises(ValueError):
        manager.open_position(
            chain="solana",
            token_address="TokInvalid1111111111111111111111111",
            symbol="INV",
            allocated_usd=-50.0,
            entry_price_usd=1.0
        )
    with pytest.raises(ValueError):
        manager.open_position(
            chain="solana",
            token_address="TokInvalid1111111111111111111111111",
            symbol="INV",
            allocated_usd=50.0,
            entry_price_usd=0.0
        )


def test_paper_position_closed_position_reevaluation_noop(manager):
    pos = manager.open_position(
        chain="solana",
        token_address="TokCloseTest1111111111111111111111111",
        symbol="CLS",
        allocated_usd=100.0,
        entry_price_usd=1.0
    )
    now = time.time()
    # Close via TP
    res1 = manager.evaluate_position(pos.position_id, current_price_usd=1.60, last_obs_ts=now, now=now)
    assert res1.action_taken == "TP_EXIT"

    # Subsequent evaluation returns CLOSED without action
    res2 = manager.evaluate_position(pos.position_id, current_price_usd=1.70, last_obs_ts=now, now=now)
    assert res2.action_taken == "NONE"
    assert res2.status == "CLOSED"
