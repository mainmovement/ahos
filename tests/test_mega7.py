"""MEGA 7 stays paper-only: a fourth regime, a token veto, and no promotion."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from architecture.intel.regimes import MarketRegimeClassifier
from architecture.markets.family_marginal import measure
from architecture.markets.tier_gate import CRITERIA
from architecture.mission.seats import SEATS, probe
from scripts.soak_stall import stall_decision


def test_liquidity_stress_is_the_fourth_regime() -> None:
    assert MarketRegimeClassifier.REGIME_LABELS[3] == "LIQUIDITY_STRESS"
    assert CRITERIA["regime_coverage"]["of_total"] == 4
    assert CRITERIA["regime_coverage"]["min_regimes"] == 3
    quiet = MarketRegimeClassifier().predict_regime_probabilities(np.array([0.0001, -0.0001, 0.0002]))
    assert quiet["active_regime"] != "LIQUIDITY_STRESS"
    shock = MarketRegimeClassifier().predict_regime_probabilities(np.array([0.2, -0.2, 0.15, -0.18]))
    assert shock["active_regime"] == "LIQUIDITY_STRESS"
    assert shock["regime_id"] == 3


def test_family_marginal_does_not_promote() -> None:
    closes = [
        {"event": "CLOSE", "realized_pnl_usd": 1.0, "entry_brain": {"contributions": [
            {"signal": "mtf_trend", "contribution": 0.2},
            {"signal": "news", "contribution": 0.0},
        ]}},
        {"event": "CLOSE", "realized_pnl_usd": -1.0, "entry_brain": {"contributions": [
            {"signal": "mtf_trend", "contribution": 0.4},
        ]}},
    ]
    doc = measure(closes)
    assert doc["pass_stats"] is False
    assert doc["applied_to_live_weights"] is False
    assert doc["mtf_trend_dominant"] == 2
    breadth = next(row for row in doc["families"] if row["family"] == "breadth")
    assert breadth["reason"] == "WEIGHT_ZERO_OR_ABSENT"


def test_seats_call_real_modules() -> None:
    assert SEATS["GOLD-SCI"]["applied_to_live_weights"] is False
    assert SEATS["GUARD-2"]["max_wallet_pct"] == 0.30
    fired = probe()
    assert fired["GOLD-SCI"] in ("BULL_TREND", "BEAR_VOLATILE", "NEUTRAL_CHOP", "LIQUIDITY_STRESS")
    assert fired["GUARD-2"] == "VETOED_FAIL_CLOSED"


def test_a_fresh_soak_is_not_restarted_and_a_reboot_is_not_claimed() -> None:
    now = datetime(2026, 10, 30, 15, 0, tzinfo=timezone.utc)
    fresh = stall_decision(
        {"window_started_utc": "2026-10-29T00:45:31Z", "last_cycle": {"ts": "2026-10-30T14:50:00Z"}},
        now, 900,
    )
    assert fresh["action"] == "HOLD"
    assert fresh["window_started_utc"] == "2026-10-29T00:45:31Z"
    assert fresh["reboot_proven"] is False
    stale = stall_decision(
        {"window_started_utc": "2026-10-29T00:45:31Z", "last_cycle": {"ts": "2026-10-30T12:00:00Z"}},
        now, 900,
    )
    assert stale["action"] == "RESTART_KEEP_WINDOW"
    assert stale["window_started_utc"] == "2026-10-29T00:45:31Z"
