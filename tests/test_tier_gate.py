"""T0 -> T1 promotion gate — the vision's ten exit criteria, measured, never
promoted.

The ladder makes promotion an owner act plus the three gate agents (قاسم AG-16,
رضا AG-19, سپهر AG-03), and AG-28's charter forbids DECIDE and PROMOTE
outright. So the evaluator measures; it never promotes. These tests pin the
fail-closed direction, the one structural unmeasurability, and that an
unmeasurable criterion blocks readiness instead of being waived.
"""

from __future__ import annotations

import math

import pytest

from architecture.markets.tier_gate import (
    CRITERIA,
    TIER_T0,
    CriterionResult,
    TierGateReport,
    evaluate_tier_gate,
    write_gate_report,
)

MONTH = 30 * 24 * 3600.0


def _trades(n: int, pnl: float = 12.0, start: float = 1_791_579_599.0) -> list[dict]:
    """n winning trades, one per day, small drawdowns, non-degenerate PnL.

    The PnL is varied deterministically: a perfectly constant stream has zero
    variance and Sharpe is genuinely undefined for it, which would test nothing.
    """
    out = []
    for i in range(n):
        out.append({
            "exit_ts": start + i * 86400.0,
            "realized_pnl_usd": pnl + (i % 5) - 2.0,
            "drawdown_pct": 4.0,
            "regime": "BULL_TREND",
        })
    return out


def _losing(n: int, pnl: float = -6.0, start: float = 1_791_579_599.0) -> list[dict]:
    return [{"exit_ts": start + i * 86400.0,
             "realized_pnl_usd": pnl + (i % 5) - 2.0,
             "drawdown_pct": 4.0, "regime": "BEAR_VOLATILE"} for i in range(n)]


# --------------------------------------------------------------- the ladder --


def test_the_report_names_t0_and_never_promotes():
    r = evaluate_tier_gate(market="gold", trades=_trades(5))
    assert r.tier_today == TIER_T0
    assert r.promoted is False
    assert r.ready_for_owner_review is False


def test_an_empty_track_is_not_ready_and_reports_no_vacuous_pass():
    r = evaluate_tier_gate(market="gold", trades=[])
    assert r.ready_for_owner_review is False
    by_id = {c.criterion: c for c in r.criteria}
    # Zero trades must not produce a 0.00% drawdown PASS on no evidence.
    assert by_id["max_drawdown_pct"].passed is None
    assert by_id["trade_count"].passed is False       # 0 is a real measurement


def test_code_cannot_promote_even_when_everything_passes():
    """Even a perfect track reports promoted=False; the act is the owner's."""
    r = evaluate_tier_gate(
        market="gold",
        trades=_trades(250),
        months_of_data=8.0,
        regime_counts={"BULL_TREND": 100, "BEAR_VOLATILE": 80, "NEUTRAL_CHOP": 70},
        declared_cost_model="net of fees and funding with 2x slippage (measured)",
        backtest_max_drawdown_pct=5.0,
        walk_forward_evidence=True,
    )
    assert r.promoted is False
    assert r.tier_today == TIER_T0


# ------------------------------------------------- the 3-vs-4 unmeasurability --


def test_regime_coverage_is_unmeasurable_as_specified_and_blocks_readiness():
    """The exit gate wants >=3 of 4 regimes; the code defines 3.

    This is structural, not incidental: MarketRegimeClassifier(n_regimes=4)
    would relabel the extra state to NEUTRAL_CHOP via the REGIME_LABELS.get
    fallback at regimes.py:92, so a fourth regime has no name in code and is
    not invented here.
    """
    r = evaluate_tier_gate(market="gold", trades=_trades(250))
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["regime_coverage"].passed is None
    assert "UNMEASURABLE" in by_id["regime_coverage"].detail
    assert "regime_coverage" in r.unmeasurable
    assert r.ready_for_owner_review is False
    assert any("M-REGIME-4" in q for q in r.open_questions)


def test_the_regime_criterion_counts_only_defined_labels():
    r = evaluate_tier_gate(
        market="gold", trades=_trades(10),
        regime_counts={"BULL_TREND": 40, "BEAR_VOLATILE": 35, "NEUTRAL_CHOP": 30,
                       "INVENTED_FIFTH": 999})
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["regime_coverage"].passed is None   # still unmeasurable


# --------------------------------------------------------- fail-closed gaps --


def test_missing_numbers_are_unmeasurable_and_block_readiness():
    """An unsupplied measurement is UNMEASURABLE, not FAIL -- stricter, because
    the gate then cannot be evaluated at all."""
    r = evaluate_tier_gate(market="gold", trades=_trades(250))
    by_id = {c.criterion: c for c in r.criteria}
    for key in ("data_depth_months", "cost_model", "walk_forward"):
        assert by_id[key].passed is None, f"{key} should be unmeasurable"
        assert key in r.unmeasurable
    assert r.ready_for_owner_review is False


def test_an_unmeasurable_drawdown_reference_blocks_readiness():
    r = evaluate_tier_gate(market="gold", trades=_trades(250),
                           months_of_data=8.0,
                           backtest_max_drawdown_pct=None)
    assert "drawdown_vs_backtest_multiple" in r.unmeasurable
    assert any("M-DD-BACKTEST" in q for q in r.open_questions)
    assert r.ready_for_owner_review is False


def test_a_measured_backtest_reference_makes_the_multiple_evaluable():
    r = evaluate_tier_gate(market="gold", trades=_trades(250),
                           backtest_max_drawdown_pct=5.0)
    by_id = {c.criterion: c for c in r.criteria}
    c = by_id["drawdown_vs_backtest_multiple"]
    assert c.passed is True       # 4% paper vs 5% backtest = 0.8x <= 1.5x
    assert "regime_coverage" in r.unmeasurable   # still blocked by the 3-vs-4


# ------------------------------------------------------------ the metrics ---


def test_a_track_with_no_drawdown_readings_scores_no_vacuous_pass():
    """Trades without a ``drawdown_pct`` field must not yield a 0.00% PASS.

    A caller that has not attached per-trade drawdowns is the realistic case for
    any track that is not yet computing them, and a 0.00% reading there would
    pass the <=15% criterion on missing evidence -- the vacuous pass the module
    exists to refuse.
    """
    trades = [{"exit_ts": 1_791_579_599.0 + i * 86400.0,
               "realized_pnl_usd": 10.0} for i in range(30)]
    r = evaluate_tier_gate(market="gold", trades=trades)
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["max_drawdown_pct"].passed is None
    assert "max_drawdown_pct" in r.unmeasurable
    assert r.ready_for_owner_review is False


def test_a_non_numeric_drawdown_is_ignored_not_crashed():
    trades = [{"exit_ts": 1_791_579_599.0, "realized_pnl_usd": 10.0,
               "drawdown_pct": "n/a"}]
    r = evaluate_tier_gate(market="gold", trades=trades)
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["max_drawdown_pct"].passed is None


def test_excessive_drawdown_fails():
    trades = _trades(10)
    trades[0]["drawdown_pct"] = 40.0
    r = evaluate_tier_gate(market="gold", trades=trades)
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["max_drawdown_pct"].passed is False


def test_sharpe_is_undefined_below_two_trades():
    r = evaluate_tier_gate(market="gold", trades=[{"exit_ts": 1.0,
                                                   "realized_pnl_usd": 5.0}])
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["sharpe"].passed is None
    assert by_id["dsr_psr"].passed is None


def test_sharpe_passes_on_a_consistent_positive_stream():
    r = evaluate_tier_gate(market="gold", trades=_trades(60))
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["sharpe"].measured is not None
    assert float(by_id["sharpe"].measured) >= CRITERIA["sharpe"]
    assert by_id["sharpe"].passed is True


def test_a_losing_stream_fails_sharpe_and_profit_factor():
    r = evaluate_tier_gate(market="gold", trades=_losing(60))
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["sharpe"].passed is False
    assert by_id["profit_factor"].passed is False


def test_profit_factor_is_undefined_with_no_losing_trades():
    """All winners: PF is genuinely undefined, not infinitely good."""
    r = evaluate_tier_gate(market="gold", trades=_trades(30))
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["profit_factor"].passed is None


def test_month_concentration_fails_when_one_month_dominates():
    trades = _trades(50, pnl=1.0)
    # One month carries all the profit, the others are flat.
    for t in trades[:40]:
        t["realized_pnl_usd"] = 0.0
    for t in trades[40:]:
        t["exit_ts"] = trades[40]["exit_ts"]      # same month
    r = evaluate_tier_gate(market="gold", trades=trades)
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["month_profit_share_pct"].passed is False


def test_month_concentration_passes_when_profit_is_spread():
    r = evaluate_tier_gate(market="gold", trades=_trades(200))
    by_id = {c.criterion: c for c in r.criteria}
    assert by_id["month_profit_share_pct"].passed is True


# ------------------------------------------------------------ readiness -----


def test_readiness_requires_every_measurable_criterion_to_pass_and_none_blocked():
    r = evaluate_tier_gate(
        market="gold",
        trades=_trades(250),
        months_of_data=8.0,
        declared_cost_model="net of fees and funding with 2x slippage (measured)",
        backtest_max_drawdown_pct=5.0,
        walk_forward_evidence=True,
    )
    assert r.measurable_and_passed == r.measurable_total
    # ...and yet still not ready, because the 3-vs-4 regime clause is unmeasurable.
    assert r.ready_for_owner_review is False
    assert r.promoted is False


def test_one_unmet_measurable_criterion_blocks_readiness():
    r = evaluate_tier_gate(
        market="gold", trades=_trades(5), months_of_data=8.0,
        declared_cost_model="net of fees and funding with 2x slippage",
        backtest_max_drawdown_pct=5.0, walk_forward_evidence=True)
    assert r.measurable_and_passed < r.measurable_total
    assert r.ready_for_owner_review is False


# ------------------------------------------------------------ rendering -----


def test_the_written_report_never_styles_a_gap_as_progress(tmp_path):
    r = evaluate_tier_gate(market="gold", trades=_trades(5))
    out = tmp_path / "gate" / "gold_tier_gate.md"
    write_gate_report(r, out)
    text = out.read_text(encoding="utf-8")
    assert "T0" in text and "Promoted by this evaluation: **False**" in text
    assert "UNMEASURABLE" in text
    assert "Not ready for owner review" in text
    assert "M-REGIME-4" in text
    assert "**Ready for owner review.**" not in text


def test_a_ready_report_says_ready_without_claiming_a_promotion(tmp_path):
    r = TierGateReport(
        market="gold", tier_today=TIER_T0,
        criteria=(CriterionResult("x", "y", "1", True, "ok"),),
        measurable_and_passed=1, measurable_total=1,
    )
    out = tmp_path / "ready.md"
    write_gate_report(r, out)
    text = out.read_text(encoding="utf-8")
    assert "**Ready for owner review.**" in text
    assert "Promoted by this evaluation: **False**" in text


def test_the_metrics_are_finite_on_a_normal_track():
    r = evaluate_tier_gate(market="gold", trades=_trades(60))
    numeric = {"data_depth_months", "max_drawdown_pct",
               "drawdown_vs_backtest_multiple", "sharpe", "dsr_psr",
               "profit_factor", "month_profit_share_pct"}
    for c in r.criteria:
        if c.measured is None or c.criterion not in numeric:
            continue                    # descriptive labels, e.g. regime counts
        try:
            assert math.isfinite(float(c.measured))
        except ValueError:
            pytest.fail(f"non-numeric measured value for {c.criterion}: {c.measured!r}")
