"""Five-minute estimated ranges for the shortlisted names. A session range is not a quote."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_REL = Path("reports") / "grok" / "PAPER" / "spread_samples.jsonl"

FALLBACK = (
    "NASDAQ:INTC", "NASDAQ:SPCX", "NASDAQ:AMZN", "NASDAQ:NVDA", "NYSE:NU",
    "NASDAQ:SOFI", "NASDAQ:CRWV", "NASDAQ:RIVN", "LSE:LLOY", "LSE:NWG",
    "LSE:GLEN", "LSE:BARC", "LSE:BT.A", "LSE:JD.", "LSE:VOD", "EURONEXT:BCP",
    "HKEX:6681", "HKEX:386", "HKEX:20", "HKEX:1398", "HKEX:939", "HKEX:2685",
    "HKEX:1810", "TSE:4564",
)


def shortlist(root: Path) -> list[str]:
    path = Path(root) / "reports" / "grok" / "PAPER" / "equity_universe.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return list(FALLBACK)
    names = []
    for row in doc.get("candidates") or []:
        if isinstance(row, dict) and row.get("symbol"):
            names.append(str(row["symbol"]))
    return names[:24] or list(FALLBACK)


def estimate_row(symbol: str, high: float, low: float, close: float) -> dict[str, Any]:
    span = None if close <= 0 else round((high - low) / close, 6)
    return {
        "symbol": symbol,
        "estimated_spread_pct": span,
        "source": "tradingview_session_range",
        "quoted": False,
        "note": "session high-low over close, not a bid-ask",
    }


def sample(root: Path, ranges: dict[str, dict[str, Any]], *, symbols: list[str] | None = None) -> dict[str, Any]:
    names = symbols if symbols is not None else shortlist(root)
    rows = []
    for symbol in names:
        quote = ranges.get(symbol) or {}
        high, low, close = quote.get("high"), quote.get("low"), quote.get("close")
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (high, low, close)):
            rows.append({"symbol": symbol, "estimated_spread_pct": None, "source": "ABSENT", "quoted": False})
            continue
        rows.append(estimate_row(symbol, float(high), float(low), float(close)))
    doc = {
        "schema": "ahos.spread_sample.v1",
        "paper_only": True,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n": len(rows),
        "quoted": False,
        "rows": rows,
        "applied_to_live": False,
    }
    path = Path(root) / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(doc, ensure_ascii=False) + "\n")
    return doc
