"""§5 sizing and §12 risk-of-ruin / kill-switch for the paper tracks.

DEDUP_MERGE_MAP v1.20 names "risk" and "M39 breaker" as two of M13's five
acceptance items. AHOS_TRADING_SKILLS_v2 §5 gives the sizing formula and §12
gives the ruin bootstrap and the hard limits; this is their test harness.

The direction pinned throughout is fail-closed: a limit that cannot be
evaluated blocks new risk rather than passing by default.
"""

from __future__ import annotations

import pytest

from architecture.markets.risk import (
    ARMED,
    BREAKER_DRAWDOWN_LIMIT_PCT,
    DAILY_LOSS_LIMIT_PCT,
    MAX_OPEN_RISK_PCT,
    MAX_PER_MARKET_PCT,
    MIN_TRADES_FOR_BOOTSTRAP,
    RUIN_PROBABILITY_LIMIT,
    TRIPPED,
    UNMEASURED,
    PaperBreaker,
    SizingResult,
    bootstrap_ruin_probability,
    drawdown_pct,
    loss_in_window,
    realized_pnl_series,
    volatility_targeted_notional,
)

NOW = 1_791_579_599.0
DAY = 86400.0


def _trade(pnl: float, days_ago: float = 0.0) -> dict:
    return {"exit_ts": NOW - days_ago * DAY, "realized_pnl_usd": pnl}


# ------------------------------------------------------------- §5 sizing ----


def test_sizing_follows_the_skills_formula():
    """Units = (Equity * r) / (k * ATR * point_value); point_value is 1 here.

    A geometric series is used so the close-to-close ATR *fraction* is exactly
    1% at every step -- an arithmetic series drifts (1/101, 1/102, ...) and
    would make this test assert against a rounded constant.
    """
    prices = [100.0, 101.0, 102.01, 103.0301]     # every move is 1.0%
    r = volatility_targeted_notional(equity_usd=10_000.0, observed_prices=prices,
                                     risk_per_trade_pct=1.0, atr_multiple=2.0)
    assert r.notional_usd == pytest.approx(10_000.0 * 0.01 / (2.0 * 0.01))
    assert "ATR" in r.detail


def test_sizing_scales_with_volatility_inversely():
    """A more volatile instrument gets a *smaller* notional at the same risk."""
    calm = [100.0, 100.5, 101.0, 101.5]
    wild = [100.0, 110.0, 99.0, 108.0]
    a = volatility_targeted_notional(equity_usd=10_000.0, observed_prices=calm)
    b = volatility_targeted_notional(equity_usd=10_000.0, observed_prices=wild)
    assert a.notional_usd is not None and b.notional_usd is not None
    assert a.notional_usd > b.notional_usd


def test_sizing_declines_with_one_observation():
    """One price is no range: §5 declines rather than assuming a volatility."""
    r = volatility_targeted_notional(equity_usd=10_000.0, observed_prices=[4200.0])
    assert r.notional_usd is None
    assert "declines to size" in r.detail


def test_sizing_declines_with_no_observations():
    r = volatility_targeted_notional(equity_usd=10_000.0, observed_prices=[])
    assert r.notional_usd is None


def test_sizing_declines_on_non_positive_equity():
    r = volatility_targeted_notional(equity_usd=0.0, observed_prices=[1.0, 2.0])
    assert r.notional_usd is None


def test_sizing_respects_a_declared_max_notional():
    """The gold track's declared notional is the ceiling until ATR exists."""
    prices = [100.0, 101.0]
    r = volatility_targeted_notional(equity_usd=10_000.0, observed_prices=prices,
                                     max_notional_usd=500.0)
    assert r.notional_usd == pytest.approx(500.0)


def test_sizing_ignores_non_finite_and_zero_prices():
    r = volatility_targeted_notional(
        equity_usd=10_000.0, observed_prices=[0.0, float("nan"), 100.0, 101.0])
    assert r.notional_usd is not None


def test_sizing_reports_zero_when_risk_is_zero():
    r = volatility_targeted_notional(equity_usd=10_000.0,
                                     observed_prices=[100.0, 101.0],
                                     risk_per_trade_pct=0.0)
    assert r.notional_usd is None
    assert "zero" in r.detail


# ------------------------------------------------------- §12 ruin bootstrap --


def test_the_ruin_limit_is_the_owner_approved_five_percent():
    assert RUIN_PROBABILITY_LIMIT == 0.05
    assert MIN_TRADES_FOR_BOOTSTRAP == 30


def test_a_bootstrap_below_thirty_trades_is_unmeasured_not_zero():
    """The skills file's own promotion threshold; a small sample supports no
    probability claim, and reporting 0.000 would be a fabricated clean record."""
    p = bootstrap_ruin_probability([-10.0] * 29, bankroll=1000.0)
    assert p is None


def test_a_all_loss_sample_ruins_with_certainty():
    p = bootstrap_ruin_probability([-10.0] * 40, bankroll=100.0)
    assert p == pytest.approx(1.0)


def test_a_all_win_sample_never_ruins():
    p = bootstrap_ruin_probability([+5.0] * 40, bankroll=1000.0)
    assert p == pytest.approx(0.0)


def test_the_bootstrap_is_deterministic_under_a_fixed_seed():
    pnls = [+3.0, -2.0, +1.5, -1.0, +0.5] * 12
    a = bootstrap_ruin_probability(pnls, bankroll=1000.0, seed=7)
    b = bootstrap_ruin_probability(pnls, bankroll=1000.0, seed=7)
    assert a == b


def test_the_bootstrap_is_invariant_to_trade_order():
    """Resampling with replacement means the order of the sample is irrelevant;
    pinning this keeps the estimator honest about what it measures."""
    pnls = [+3.0, -2.0, +1.5, -1.0, +0.5] * 12
    shuffled = list(reversed(pnls))
    assert (bootstrap_ruin_probability(pnls, bankroll=1000.0, seed=1)
            == pytest.approx(
                bootstrap_ruin_probability(shuffled, bankroll=1000.0, seed=1)))


def test_a_larger_bankroll_lowers_the_measured_risk_of_ruin():
    pnls = [+1.0, -6.0, +0.5, -4.0, +0.25] * 12
    small = bootstrap_ruin_probability(pnls, bankroll=100.0, seed=3)
    large = bootstrap_ruin_probability(pnls, bankroll=10_000.0, seed=3)
    assert small is not None and large is not None
    assert small >= large


def test_the_bootstrap_ignores_non_finite_pnl():
    p = bootstrap_ruin_probability([1.0] * 40 + [float("nan")], bankroll=1000.0)
    assert p is not None


# ------------------------------------------------------------- the breaker --


def _breaker(**kw) -> PaperBreaker:
    return PaperBreaker(bankroll=kw.pop("bankroll", 10_000.0), **kw)


def test_a_cold_track_with_a_bankroll_arms_for_its_first_paper_trade():
    """Nothing has happened yet, but the bankroll is a real number and the
    exposure caps evaluate against it: the track may open its first position,
    which is how it accumulates the 30 closed trades the gate requires."""
    st = _breaker().check(now=NOW)
    assert st.state == ARMED
    assert st.allowed is True
    assert st.p_ruin is None, "no trades means no ruin claim, not a zero one"


def test_a_track_with_nothing_measurable_holds_new_risk():
    """No trades, no equity curve, no positive equity: not a violation and not
    a clean record -- a third state, which must still refuse new risk."""
    st = _breaker().check(now=NOW, equity_usd=0.0)
    assert st.state == UNMEASURED
    assert st.allowed is False
    assert st.p_ruin is None


def test_a_wiped_out_bankroll_with_a_history_trips_on_unevaluable_limits():
    """Equity <= 0 *and* a recorded history: some limits were evaluated, the
    rest are unevaluable, so the breaker trips rather than passing."""
    st = _breaker().check(now=NOW, trades=[_trade(+1.0)], equity_usd=0.0)
    assert st.state == TRIPPED
    assert st.allowed is False


def test_a_measured_clean_track_arms():
    st = _breaker().check(now=NOW, trades=[_trade(+5.0)],
                          equity_curve=[10_000.0, 10_005.0])
    assert st.state == ARMED
    assert st.allowed is True
    assert st.reasons == ()


def test_drawdown_past_the_paper_limit_trips():
    st = _breaker().check(now=NOW, equity_curve=[10_000.0, 8_000.0])
    assert st.state == TRIPPED
    assert st.allowed is False
    assert any("drawdown" in r for r in st.reasons)
    assert st.drawdown_pct == pytest.approx(20.0, abs=0.01)


def test_drawdown_just_inside_the_limit_arms():
    curve = [10_000.0, 10_000.0 * (1 - (BREAKER_DRAWDOWN_LIMIT_PCT - 0.1) / 100.0)]
    st = _breaker().check(now=NOW, equity_curve=curve)
    assert st.state == ARMED


def test_daily_loss_past_the_limit_trips():
    trades = [_trade(-200.0)]                     # 2% of 10k, under 3%
    st = _breaker().check(now=NOW, trades=trades)
    assert st.state == ARMED
    trades.append(_trade(-150.0))                 # now 3.5% total, over 3%
    st = _breaker().check(now=NOW, trades=trades)
    assert st.state == TRIPPED
    assert any("daily loss" in r for r in st.reasons)


def test_a_loss_outside_the_daily_window_does_not_count():
    """The window is trailing wall-clock; a loss from last week is weekly-only."""
    trades = [_trade(-700.0, days_ago=3.0)]      # 7% of 10k, over the weekly
    st = _breaker().check(now=NOW, trades=trades)
    assert st.state == TRIPPED
    assert any("weekly loss" in r for r in st.reasons)
    assert not any("daily loss" in r for r in st.reasons)


def test_weekly_loss_past_the_limit_trips():
    trades = [_trade(-350.0, days_ago=3.0), _trade(-300.0, days_ago=4.0)]
    st = _breaker().check(now=NOW, trades=trades)
    assert st.state == TRIPPED
    assert any("weekly loss" in r for r in st.reasons)


def test_profits_do_not_earn_credit_against_a_loss_limit():
    """§12's limits are loss limits; a win does not offset a loss inside the
    window."""
    trades = [_trade(-200.0), _trade(+1000.0), _trade(-200.0)]   # net +600
    st = _breaker().check(now=NOW, trades=trades)
    assert st.state == TRIPPED
    assert any("daily loss" in r for r in st.reasons)


def test_open_risk_past_the_cap_trips():
    st = _breaker().check(now=NOW, trades=[_trade(+1.0)],
                          open_exposure_usd=10_000.0 * MAX_OPEN_RISK_PCT / 100.0 + 1.0)
    assert st.state == TRIPPED
    assert any("open risk" in r for r in st.reasons)


def test_per_market_exposure_past_the_cap_trips():
    st = _breaker().check(now=NOW, trades=[_trade(+1.0)],
                          market_exposure_usd=10_000.0 * MAX_PER_MARKET_PCT / 100.0 + 1.0)
    assert st.state == TRIPPED
    assert any("market exposure" in r for r in st.reasons)


def test_a_broken_bankroll_trips_on_unevaluable_limits():
    """Equity <= 0: the loss limits and exposure caps cannot be computed, and
    that trips rather than passes."""
    st = _breaker().check(now=NOW, trades=[_trade(+1.0)], equity_usd=0.0)
    assert st.state == TRIPPED
    assert st.allowed is False


def test_the_bootstrap_blocks_new_risk_above_five_percent():
    """§12: block new risk if P(DD > L) > 5%. A fat-tailed sample makes that
    the *only* tripped limit, which is what isolates the bootstrap gate.

    The losses are small relative to the bankroll so the daily/weekly limits
    stay satisfied -- the trip must come from the resampled ruin probability,
    not from a loss limit happening to fire at the same time.
    """
    pattern = [+1.0, -8.0, +0.5, -6.0, +0.25, +0.1, -7.0, +0.3]
    pnls = pattern * 8
    p = bootstrap_ruin_probability(pnls, bankroll=1000.0, seed=0)
    assert p is not None and p > RUIN_PROBABILITY_LIMIT
    trades = [{"exit_ts": NOW - i * DAY, "realized_pnl_usd": v}
              for i, v in enumerate(pnls)]
    st = _breaker(bankroll=1000.0).check(now=NOW, trades=trades,
                                         equity_usd=1000.0)
    assert st.state == TRIPPED
    assert st.p_ruin == p
    assert any("P(DD>" in r for r in st.reasons)
    assert not any("loss" in r for r in st.reasons)


def test_a_ruin_probability_under_the_limit_does_not_trip_on_it():
    pattern = [+4.0, +2.0, +3.0, +1.0]
    pnls = pattern * 12
    p = bootstrap_ruin_probability(pnls, bankroll=1000.0, seed=11)
    assert p is not None and p < RUIN_PROBABILITY_LIMIT
    trades = [{"exit_ts": NOW - i * DAY, "realized_pnl_usd": v}
              for i, v in enumerate(pnls)]
    st = _breaker(bankroll=1000.0).check(now=NOW, trades=trades,
                                         equity_usd=1000.0,
                                         equity_curve=[1000.0, 1500.0])
    assert st.state == ARMED
    assert st.p_ruin == p


def test_the_state_carries_its_measurements_when_it_trips():
    st = _breaker().check(now=NOW, trades=[_trade(-200.0)],
                          equity_curve=[10_000.0, 8_900.0],
                          open_exposure_usd=1_000.0)
    assert st.daily_loss_pct == pytest.approx(2.0)
    assert st.weekly_loss_pct == pytest.approx(2.0)
    assert st.drawdown_pct == pytest.approx(11.0, abs=0.01)
    assert st.open_exposure_pct == pytest.approx(10.0)


def test_the_breaker_limits_are_the_skills_constants():
    assert DAILY_LOSS_LIMIT_PCT == 3.0
    assert MAX_OPEN_RISK_PCT == 15.0
    assert MAX_PER_MARKET_PCT == 25.0
    assert BREAKER_DRAWDOWN_LIMIT_PCT < 15.0, (
        "the paper breaker is stricter than the T1 promotion limit on purpose")


# ------------------------------------------------------------ pure helpers --


def test_realized_pnl_series_skips_unpriced_trades():
    trades = [{"realized_pnl_usd": 1.0}, {"realized_pnl_usd": None},
              {"realized_pnl_usd": "not a number"}, {"realized_pnl_usd": -2.0}]
    assert realized_pnl_series(trades) == [1.0, -2.0]
    assert realized_pnl_series([]) == []
    assert realized_pnl_series(None) == []          # type: ignore[arg-type]


def test_drawdown_of_a_rising_curve_is_zero():
    assert drawdown_pct([1.0, 2.0, 3.0]) == 0.0
    assert drawdown_pct([]) == 0.0


def test_drawdown_measures_peak_to_trough_not_end_to_end():
    """A curve that ends above its start can still have drawn down badly."""
    assert drawdown_pct([100.0, 200.0, 50.0, 150.0]) == pytest.approx(75.0)


def test_drawdown_skips_non_positive_samples_rather_than_using_them_as_a_trough():
    """A zeroed sample is not the trough of anything -- it is skipped, so a
    curve that touches zero and recovers is measured by its real trough."""
    assert drawdown_pct([100.0, 0.0, 50.0]) == pytest.approx(50.0)
    assert drawdown_pct([0.0, 100.0, 50.0]) == pytest.approx(50.0)


def test_loss_in_window_is_losses_only():
    trades = [_trade(-100.0), _trade(+500.0), _trade(-50.0, days_ago=2.0)]
    assert loss_in_window(trades, now=NOW, window_s=DAY) == 100.0


def test_sizing_result_is_a_value_object():
    a = SizingResult(1.0, "x")
    b = SizingResult(1.0, "x")
    assert a == b
