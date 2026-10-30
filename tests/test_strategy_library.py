"""The library cites its sources and does not promote a missing path."""
from __future__ import annotations

from pathlib import Path

from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)
from architecture.strategies.leaderboard import export_leaderboard, gate, write_registry
from architecture.strategies.library import SPECS
from architecture.strategies.meta_brain import capped_kelly, thompson_weights
from architecture.strategies.signals import (
    apply_cost,
    donchian,
    dual_ma,
    funding_carry,
    futures_carry,
    liquidation_fade,
    vol_breakout,
    pairs_zscore,
    pump_token_allowed,
    rsi2,
    ts_momentum,
    wick_sweep,
)
from architecture.strategies.wisdom import cut_loser, daily_loss_stop, max_risk, no_average_down


def test_signals_are_causal_and_a_token_cannot_open_alone() -> None:
    rising = [float(i) for i in range(1, 40)]
    assert ts_momentum(rising, 12)[-1] == 1
    assert ts_momentum(rising, 12)[:12] == [0] * 12
    highs = rising
    lows = [value - 0.5 for value in rising]
    full = donchian(highs, lows, 5, 3)
    assert donchian(highs[:20], lows[:20], 5, 3) == full[:20]
    assert dual_ma(rising, 3, 8)[-1] == 1
    crash = [10, 9, 8, 7, 6, 5]
    assert rsi2(crash, 2, 10, 90)[-1] == 1
    left = [10 + i * 0.01 for i in range(30)]
    right = [5 + i * 0.01 for i in range(30)]
    assert pairs_zscore(left, right, 10, 2)[-1] == 0
    assert futures_carry(100, 101) == 1
    assert funding_carry(0.01) == -1
    ranges = [1.0] * 20 + [5.0]
    closes = [10.0 + i * 0.1 for i in range(21)]
    assert vol_breakout(ranges, closes, 14, 1.5)[-1] == 1
    assert liquidation_fade(10, 1) == 1
    assert wick_sweep(10, 10.2, 8, 10.1, 0.6) == 1
    assert pump_token_allowed(safety_pass=True, agreeing_families=1, time_stop_set=True) is False
    assert pump_token_allowed(safety_pass=True, agreeing_families=2, time_stop_set=True) is True
    assert apply_cost(0.01, 0.001, 0.001) == 0.006


def test_the_gate_rejects_a_lookback_even_when_the_numbers_look_strong() -> None:
    assert MIN_AGREEING_FAMILIES == 2
    assert VOTE_SCORE_FLOOR == 0.05
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
    assert gate(dsr=0.99, pbo=0.1, oos_n=40, after_fees=True, fresh=False, red_team_survived=False) is False
    assert gate(dsr=0.99, pbo=0.1, oos_n=40, after_fees=True, fresh=True, red_team_survived=False) is False
    assert gate(dsr=0.90, pbo=0.1, oos_n=40, after_fees=True, fresh=True, red_team_survived=True) is False


def test_turn_of_month_uses_the_calendar_day_and_old_closes_stay_out_of_the_fresh_rank(tmp_path: Path) -> None:
    from architecture.strategies.signals import sign_on_frame
    signs = sign_on_frame("turn_of_month", {"closes": [10, 11, 12, 13], "days": [2, 10, 15, 30]})
    assert signs == [1, 0, 0, 1]
    assert sign_on_frame("commodity_calendar", {"closes": [1, 2, 3]}) is None
    assert sign_on_frame("pump_token", {"closes": [1.0, 2.0], "safety_pass": False}) == [0, 0]
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    prereg = tmp_path / "docs" / "prereg"
    prereg.mkdir(parents=True)
    origin = Path(__file__).resolve().parents[1] / "docs" / "prereg" / "MEGA11.yaml"
    (prereg / "MEGA11.yaml").write_bytes(origin.read_bytes())
    (paper / "paper_trades.jsonl").write_text(
        '{"event":"CLOSE","desk":"US_EQUITIES","regime":"NEUTRAL_CHOP","exit_price":10,"closed_at":"2026-10-02T00:00:00Z"}\n'
        '{"event":"CLOSE","desk":"US_EQUITIES","regime":"NEUTRAL_CHOP","exit_price":11,"closed_at":"2026-10-10T00:00:00Z"}\n'
        '{"event":"CLOSE","desk":"US_EQUITIES","regime":"NEUTRAL_CHOP","exit_price":12,"closed_at":"2026-10-30T00:00:00Z"}\n',
        encoding="utf-8",
    )
    doc = export_leaderboard(tmp_path)
    month = [row for row in doc["rows"] if row["id"] == "turn_of_month" and row["closes"] > 0]
    assert month
    assert month[0]["reason"] == "SHADOW_LOOKBACK"
    assert month[0]["fresh_closes"] == 0
    assert doc["desk_focus"]["hypothesis_status"] == "WAITING_FOR_FRESH"
    assert doc["desk_focus"]["promoted"] is False
    assert doc["live_promoted"] == 0


def test_a_price_series_makes_a_shadow_close_and_does_not_promote(tmp_path: Path) -> None:
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    lines = []
    price = 100.0
    for i in range(40):
        price = price * (1.01 if i % 2 == 0 else 0.99)
        lines.append(
            '{"event":"CLOSE","desk":"CRYPTO","regime":"NEUTRAL_CHOP","exit_price":%s,"closed_at":"2026-10-30T00:%02d:00Z","realized_pnl_usd":0.01}\n'
            % (round(price, 4), i)
        )
    (paper / "paper_trades.jsonl").write_text("".join(lines), encoding="utf-8")
    doc = export_leaderboard(tmp_path)
    hits = [row for row in doc["rows"] if row["id"] == "short_term_reversal" and row["closes"] > 0]
    assert hits
    assert hits[0]["reason"] == "SHADOW_LOOKBACK"
    assert hits[0]["applied_to_live"] is False
    assert doc["live_promoted"] == 0
    assert doc["pass_stats"] is False
    assert doc["meta_brain"]["can_open_without_family_votes"] is False


def test_leaderboard_stays_shadow(tmp_path: Path) -> None:
    first = write_registry(tmp_path)
    doc = export_leaderboard(tmp_path)
    second = write_registry(tmp_path)
    assert second["registered_at"] == first["registered_at"]
    assert len(doc["rows"]) == len(SPECS)
    assert all(row["citation"] for row in doc["rows"])
    assert all(row["state"] == "shadow" for row in doc["rows"])
    assert all(row["dsr"] is None and row["pbo"] is None for row in doc["rows"])
    assert all(row["pass_stats"] is False for row in doc["rows"])
    assert doc["live_promoted"] == 0
    assert doc["applied_to_live"] is False
    brain = doc["meta_brain"]
    assert brain["applied_to_live"] is False
    assert brain["can_open_without_family_votes"] is False
    assert abs(sum(brain["weights"].values()) - 1.0) < 1e-3
    assert brain["kelly"] is None
    assert capped_kelly(None, 1.0) is None
    assert cut_loser(0.02, 0.01) == "EXIT"
    assert no_average_down(-1.0, True) is False
    assert max_risk(100, 100, 0.01) is False
    assert daily_loss_stop(-1.0) == "STOP_NEW_RISK"
    assert doc["research"]["upstream_executed"] is False
