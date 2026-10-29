from __future__ import annotations

import json
from pathlib import Path

from architecture.university.research_prediction_scoring import (
    append_close_outcomes,
    backfill_outcomes_from_log,
    build_hypothesis_scorecard,
    export_research_hypothesis_scorecard,
    outcomes_from_close_row,
)


def _close(side: str, pnl: float, preds: dict) -> dict:
    return {
        "event": "CLOSE",
        "symbol": "BTC",
        "desk": "CRYPTO",
        "side": side,
        "closed_at": "2026-10-30T00:00:00Z",
        "realized_pnl_usd": pnl,
        "research_predictions": preds,
    }


def test_shadow_hit_when_aligned_short_wins(tmp_path: Path):
    preds = {
        "schema": "ahos.research_predictions.v1",
        "desk": "CRYPTO",
        "predictions": [
            {
                "hypothesis_id": "H15",
                "verdict": "SHADOW_FORWARD_TEST",
                "predicted_direction": "SHORT",
                "composite_weight": 0.0,
            }
        ],
    }
    rows = outcomes_from_close_row(_close("SHORT", 0.05, preds))
    assert len(rows) == 1
    assert rows[0]["outcome_label"] == "HIT"
    assert rows[0]["composite_weight_was"] == 0.0


def test_shadow_skipped_when_prediction_opposes_trade(tmp_path: Path):
    preds = {
        "predictions": [
            {
                "hypothesis_id": "H15",
                "predicted_direction": "LONG",
                "composite_weight": 0.0,
            }
        ],
    }
    rows = outcomes_from_close_row(_close("SHORT", 0.05, preds))
    assert rows[0]["outcome_label"] == "SKIPPED"
    assert rows[0]["outcome_reason"] == "prediction_not_aligned_with_executed_side"


def test_append_idempotent_and_scorecard(tmp_path: Path):
    close = _close(
        "SHORT",
        0.1,
        {
            "predictions": [
                {"hypothesis_id": "H15", "predicted_direction": "SHORT", "composite_weight": 0.0},
            ]
        },
    )
    assert len(append_close_outcomes(tmp_path, close)) == 1
    assert len(append_close_outcomes(tmp_path, close)) == 0
    card = export_research_hypothesis_scorecard(tmp_path)
    h15 = next(h for h in card["hypotheses"] if h["hypothesis_id"] == "H15")
    assert h15["hits"] == 1
    assert h15["hit_rate"] == 1.0


def test_backfill_reads_entry_brain_predictions(tmp_path: Path):
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "event": "CLOSE",
        "symbol": "SOL",
        "desk": "CRYPTO",
        "side": "SHORT",
        "closed_at": "2026-10-29T20:52:43Z",
        "realized_pnl_usd": 0.12,
        "entry_brain": {
            "research_predictions": {
                "predictions": [
                    {"hypothesis_id": "H15", "predicted_direction": "LONG", "composite_weight": 0.0},
                ]
            }
        },
    }
    log.write_text(json.dumps(row) + "\n", encoding="utf-8")
    n = backfill_outcomes_from_log(tmp_path)
    assert n == 1
    assert build_hypothesis_scorecard(tmp_path)["outcomes_total"] == 1
