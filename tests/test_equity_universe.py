"""The listed-stock scanner keeps a short shadow list and does not open live names."""
from __future__ import annotations

import json
from pathlib import Path

from architecture.markets.equity_universe import export_universe, write_registry
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)
from architecture.markets.paper_trader import INSTRUMENTS


def _row(symbol: str, price: float, volume: float, cap: float, change: float, vol: float) -> dict:
    return {"s": symbol, "d": [symbol.split(":")[-1], price, volume, cap, change, vol, None, None]}


def test_shortlist_is_shadow_and_live_floors_stay(tmp_path: Path) -> None:
    assert MIN_AGREEING_FAMILIES == 2
    assert VOTE_SCORE_FLOOR == 0.05
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
    before = set(INSTRUMENTS)
    rows = [
        _row("NASDAQ:ZZTEST", 20.0, 5_000_000, 5_000_000_000, 2.5, 12.0),
        _row("NASDAQ:TINY", 20.0, 10, 5_000_000_000, 2.5, 12.0),
    ]

    def fetch(url: str, payload: dict) -> dict:
        exchanges = payload["filter"][1]["right"]
        if "america" in url and exchanges == ["NASDAQ"]:
            start, end = payload["range"]
            page = rows[start:end]
            return {"ok": True, "data": {"totalCount": len(rows), "data": page}}
        return {"ok": True, "data": {"totalCount": 0, "data": []}}

    first = write_registry(tmp_path)
    doc = export_universe(tmp_path, fetch=fetch, use_cache=False)
    second = write_registry(tmp_path)
    assert second["registered_at"] == first["registered_at"]
    assert doc["applied_to_live"] is False
    assert doc["pass_stats"] is False
    assert doc["live_names_added"] == 0
    nasdaq = next(row for row in doc["exchanges"] if row["exchange"] == "NASDAQ")
    assert nasdaq["reported_total"] == 2
    assert nasdaq["scanned"] == 2
    assert nasdaq["truncated"] is False
    assert nasdaq["passed_measurable"] == 1
    assert doc["candidates_per_desk"]["US_EQUITIES"]["shortlist"] == 1
    assert doc["candidates_per_desk"]["US_EQUITIES"]["full_screen_pass"] == 0
    assert doc["candidates_per_desk"]["US_EQUITIES"]["live_open"] == 0
    picked = doc["candidates"][0]
    assert picked["symbol"] == "NASDAQ:ZZTEST"
    assert picked["spread_status"] == "UNKNOWN"
    assert picked["vote_applicable"] is False
    assert picked["fee_gate"] == "UNEVALUABLE"
    assert picked["live_open"] is False
    assert set(INSTRUMENTS) == before
    saved = json.loads((tmp_path / "reports" / "grok" / "PAPER" / "equity_universe.json").read_text(encoding="utf-8"))
    assert saved["live_names_added"] == 0
