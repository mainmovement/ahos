"""Tests for M13 edge expectancy bootstrap & MGC/MCL margin simulator."""
from __future__ import annotations

from architecture.markets.edge_and_margin_sim import (
    BOOTSTRAP_DRAWS,
    evaluate_expectancy_bootstrap,
    simulate_instrument_leverage_ladder,
)


def test_bootstrap_hold_when_sample_small_or_ci_non_positive() -> None:
    short = evaluate_expectancy_bootstrap([0.01, -0.02, 0.015, -0.01] * 3)
    assert short["sample_size"] == 12
    assert short["verdict"] == "NO_PROVEN_EDGE_HOLD"

    negative_edge = [-0.01] * 40
    bad = evaluate_expectancy_bootstrap(negative_edge, cost_per_trade=0.0)
    assert bad["sample_size"] >= 30
    assert bad["ci95_lower"] <= 0
    assert bad["verdict"] == "NO_PROVEN_EDGE_HOLD"


def test_bootstrap_candidate_when_n30_and_positive_ci_lower() -> None:
    rets = [0.008, -0.002, 0.007, -0.0015, 0.0065] * 8
    res = evaluate_expectancy_bootstrap(rets, cost_per_trade=0.0002, draws=BOOTSTRAP_DRAWS)
    assert res["sample_size"] == 40
    assert res["ci95_lower"] > 0
    assert res["verdict"] == "STATISTICAL_EDGE_CANDIDATE_PAPER"
    assert res["paper_only"] is True
    assert res["live"] is False


def test_mgc_mcl_leverage_veto_at_10x_and_25x() -> None:
    mgc = simulate_instrument_leverage_ladder("MGC", atr_pct=1.25)
    by_lev = {r["leverage"]: r for r in mgc}
    assert by_lev[1]["classification"] == "SAFE_PAPER_BAND"
    assert by_lev[5]["classification"] == "CAUTION_ELEVATED_RISK"
    assert by_lev[10]["classification"] == "VETO_RUIN_DANGER"
    assert by_lev[25]["classification"] == "VETO_RUIN_DANGER"
    assert by_lev[10]["warning_fa"]
