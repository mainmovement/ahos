from architecture.university.kl_dro_shadow import WARMUP, evaluate, kl_robust_mean, strategy_path
from architecture.university.research_institute import DESKS
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO


def test_the_robust_mean_stays_at_or_below_the_sample_mean():
    sample = [0.02, 0.01, -0.03, 0.015, 0.005]
    mean = sum(sample) / len(sample)
    assert kl_robust_mean(sample, 0.0) == mean
    robust = kl_robust_mean(sample, 0.05)
    wider = kl_robust_mean(sample, 0.15)
    assert robust is not None and wider is not None
    assert wider <= robust <= mean
    assert kl_robust_mean([0.01, 0.01, 0.01], 0.05) <= 0.01


def test_a_step_uses_only_earlier_closes_on_that_desk():
    closes = []
    for i, pnl in enumerate([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, -0.4]):
        closes.append({
            "desk": "GOLD",
            "notional_usd": 10.0,
            "realized_pnl_usd": pnl,
            "closed_at": f"2026-01-{i + 1:02d}T00:00:00Z",
        })
    path, counts = strategy_path(closes, 0.05)
    assert len(path) == 1
    assert path[0] < 0
    assert counts["misses"] == 1
    scored = evaluate(closes)
    assert scored["n_steps"] == len(closes) - WARMUP
    assert scored["predicted_score"]["GOLD"] is not None
    assert set(scored["predicted_score"]) == set(DESKS)
    assert scored["applied_to_live_weights"] is False
    assert scored["upstream_executed"] is False
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
