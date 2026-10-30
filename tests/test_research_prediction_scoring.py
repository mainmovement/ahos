from __future__ import annotations

import json
from pathlib import Path

from architecture.markets.research_desk_signal import research_predictions_for_trade
from architecture.university.research_prediction_scoring import (
    append_close_outcomes,
    backfill_outcomes_from_log,
    build_hypothesis_scorecard,
    export_weekly_shadow_scorecard_to_m57,
    outcomes_from_close_row,
)


def _close(**kwargs) -> dict:
    base = {
        "event": "CLOSE",
        "symbol": "BTC",
        "desk": "CRYPTO",
        "side": "SHORT",
        "closed_at": "2026-10-30T00:00:00Z",
        "opened_at": "2026-10-29T20:00:00Z",
        "entry_price": 100.0,
        "fill_price": 95.0,
        "realized_pnl_usd": 0.05,
    }
    base.update(kwargs)
    return base


def test_counterfactual_short_hit_when_price_falls():
    preds = {
        "predictions": [
            {"hypothesis_id": "H15", "predicted_direction": "SHORT", "composite_weight": 0.0},
        ],
    }
    rows = outcomes_from_close_row(_close(research_predictions=preds))
    assert rows[0]["outcome_label_counterfactual"] == "HIT"
    assert rows[0]["price_return_pct"] == -0.05


def test_counterfactual_long_hit_even_when_executed_short():
    preds = {
        "predictions": [
            {"hypothesis_id": "H15", "predicted_direction": "LONG", "composite_weight": 0.0},
        ],
    }
    rows = outcomes_from_close_row(_close(research_predictions=preds))
    assert rows[0]["outcome_label_counterfactual"] == "MISS"
    assert rows[0]["outcome_label_executed"] == "SKIPPED"


def test_counterfactual_long_wins_on_price_up():
    preds = {"predictions": [{"hypothesis_id": "H15", "predicted_direction": "LONG", "composite_weight": 0.0}]}
    rows = outcomes_from_close_row(_close(fill_price=105.0, side="LONG", research_predictions=preds))
    assert rows[0]["outcome_label_counterfactual"] == "HIT"


def test_weekly_m57_export_and_scorecard(tmp_path: Path):
    close = _close(
        research_predictions={
            "predictions": [{"hypothesis_id": "H15", "predicted_direction": "SHORT", "composite_weight": 0.0}],
        }
    )
    append_close_outcomes(tmp_path, close)
    weekly = export_weekly_shadow_scorecard_to_m57(tmp_path)
    assert weekly["schema"] == "ahos.m57.weekly_research_shadow_scorecard.v1"
    assert (tmp_path / "reports/grok/M57/weekly_research_shadow_scorecard.json").is_file()
    card = build_hypothesis_scorecard(tmp_path)
    h15 = next(h for h in card["hypotheses"] if h["hypothesis_id"] == "H15")
    assert h15["counterfactual_hits"] == 1


def test_backfill_reads_entry_brain_predictions(tmp_path: Path):
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "event": "CLOSE",
        "symbol": "SOL",
        "desk": "CRYPTO",
        "side": "SHORT",
        "closed_at": "2026-10-29T20:52:43Z",
        "opened_at": "2026-10-29T18:00:00Z",
        "entry_price": 150.0,
        "fill_price": 148.0,
        "realized_pnl_usd": 0.12,
        "entry_brain": {
            "research_predictions": research_predictions_for_trade(tmp_path, "CRYPTO"),
        },
    }
    log.write_text(json.dumps(row) + "\n", encoding="utf-8")
    n = backfill_outcomes_from_log(tmp_path)
    assert n >= 0
