from __future__ import annotations

import json
from pathlib import Path

from architecture.learning.shadow_forward_scorecard import build_shadow_forward_scorecard


def test_shadow_scorecard_writes_schema(tmp_path: Path) -> None:
    ledger = tmp_path / "reports" / "grok" / "PAPER"
    ledger.mkdir(parents=True)
    rows = [
        {
            "ts": "2026-01-01T12:00:00Z",
            "event": "OPEN",
            "symbol": "BTC",
            "price": 100.0,
            "brain": {"signals": [{"name": "stablecoin", "available": True, "score": 0.5}]},
        },
        {
            "ts": "2026-01-01T13:30:00Z",
            "event": "HOLD",
            "symbol": "BTC",
            "price": 110.0,
        },
        {
            "ts": "2026-01-01T14:00:00Z",
            "event": "OPEN",
            "symbol": "BTC",
            "price": 105.0,
            "brain": {"signals": [{"name": "stablecoin", "available": True, "score": -0.2}]},
        },
    ]
    (ledger / "paper_trades.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = build_shadow_forward_scorecard(tmp_path)
    assert out["schema"] == "ahos.shadow_forward_scorecard.v1"
    assert out["unproven_edge"] is True
    assert len(out["signals"]) >= 1
    impulse = next(s for s in out["signals"] if s["signal"] == "stablecoin_impulse")
    assert impulse["n"] >= 1
    path = tmp_path / "reports" / "grok" / "M28" / "shadow_forward_scorecard.json"
    assert path.is_file()
