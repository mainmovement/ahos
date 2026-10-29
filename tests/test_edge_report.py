from __future__ import annotations

import json
from pathlib import Path

from scripts.export_edge_report import build_edge_report


def test_edge_report_builds_from_live_log(tmp_path: Path, monkeypatch):
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(35):
        rows.append(
            {
                "event": "CLOSE",
                "symbol": "BTC",
                "desk": "CRYPTO",
                "side": "SHORT",
                "realized_pnl_usd": -0.01 if i % 3 == 0 else 0.02,
                "fees_usd": 0.001,
                "reason": "SIGNAL_REVERSAL",
                "opened_at": "2026-10-01T12:00:00Z",
                "closed_at": f"2026-10-{1 + i % 28:02d}T12:00:00Z",
                "entry_brain": {
                    "contributions": [{"signal": "mtf_trend", "weight": 0.4, "score": 0.5}],
                },
            }
        )
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        "scripts.export_edge_report.export_paper_trade_audit_snapshot",
        lambda _r: {"status": "GREEN"},
    )
    report = build_edge_report(tmp_path)
    assert report["promotion_gate"]["n_closed"] == 35
    assert report["edge_status"] == "UNPROVEN_EDGE"
    assert report["promotion_gate"]["eligible"] is False
