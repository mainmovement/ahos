from __future__ import annotations

import json
from pathlib import Path

from scripts.reconcile_spec_trace_partial import build_partial_receipt


def test_partial_receipt_counts_desk_closes(tmp_path: Path):
    edge = tmp_path / "reports" / "grok" / "PAPER" / "edge_report.json"
    edge.parent.mkdir(parents=True, exist_ok=True)
    edge.write_text(
        json.dumps(
            {
                "edge_status": "UNPROVEN_EDGE",
                "promotion_gate": {"n_closed": 10, "eligible": False},
                "deflated_sharpe": 0.0,
                "desks": [
                    {"desk": "US_EQUITIES", "closes": 2},
                    {"desk": "ASIA_EQUITIES", "closes": 5},
                    {"desk": "CRYPTO", "closes": 3},
                ],
            }
        ),
        encoding="utf-8",
    )
    report = build_partial_receipt(tmp_path)
    assert report["live_book"]["closed_trades"] == 10
    assert report["recommended_upgrades"]["M13.3"]["closes"] == 2
    assert "M19" not in report["recommended_upgrades"] or report["recommended_upgrades"]["M19"]["to"] == "REAL"
    assert "M13" in report["still_partial"]
