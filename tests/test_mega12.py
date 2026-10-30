"""MEGA12 stays shadow and ignores closes from before the stamp."""
from datetime import datetime, timezone
from pathlib import Path

from architecture.markets.mega12_shadow import evaluate, mtf_agrees, non_news_agrees
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)


def _row(**extra):
    base = {
        "event": "CLOSE",
        "desk": "GOLD",
        "side": "LONG",
        "opened_at": "2026-10-30T19:50:00Z",
        "closed_at": "2026-10-30T20:10:00Z",
        "realized_pnl_usd": -2.0,
        "entry_price": 100.0,
        "fill_price": 98.0,
        "qty": 1.0,
        "entry_brain": {"signals": [{"name": "news", "available": True, "score": 0.8}], "contributions": []},
    }
    base.update(extra)
    return base


def test_a_news_chase_is_skipped_and_an_old_close_is_not_scored(tmp_path: Path) -> None:
    origin = Path(__file__).resolve().parents[1] / "docs" / "prereg" / "MEGA12.yaml"
    dest = tmp_path / "docs" / "prereg"
    dest.mkdir(parents=True)
    (dest / "MEGA12.yaml").write_bytes(origin.read_bytes())
    event = datetime(2026, 10, 30, 19, 40, tzinfo=timezone.utc)
    agreed = _row(
        realized_pnl_usd=1.0,
        entry_brain={
            "signals": [
                {"name": "news", "available": True, "score": 0.8},
                {"name": "candles", "available": True, "score": 0.4},
                {"name": "macro", "available": True, "score": 0.4},
                {"name": "mtf_trend", "available": True, "score": 0.5},
            ],
            "contributions": [{"signal": "mtf_trend", "contribution": 0.5}],
        },
    )
    old = _row(opened_at="2026-10-30T12:00:00Z", closed_at="2026-10-30T18:00:00Z", realized_pnl_usd=-9.0)
    doc = evaluate(tmp_path, rows=[_row(), agreed, old], events=[event])
    assert doc["fresh_closes"] == 2
    assert doc["news"]["news_cooldown_15"]["trades_skipped"] == 1
    assert doc["news"]["news_cooldown_15"]["loss_avoided_usd"] == 2.0
    assert doc["news"]["fade_first_spike_15"]["trades_skipped"] == 2
    assert doc["promoted"] is False
    assert doc["applied_to_live"] is False
    assert doc["gold"]["pick"] is None
    assert doc["entry"]["fresh_kept"] == 1
    assert doc["tilt"]["applied_to_live"] is False
    assert doc["tilt"]["floors_unchanged"]["min_agreeing_families"] == 2
    assert non_news_agrees(agreed) >= 2
    assert mtf_agrees(agreed) is True
    assert MIN_AGREEING_FAMILIES == 2
    assert VOTE_SCORE_FLOOR == 0.05
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
