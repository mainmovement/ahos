"""One TradingView scanner batch per cycle. Yahoo remains the fallback. PAPER_ONLY."""
from __future__ import annotations

import re
from typing import Any, Callable

from architecture.markets.http_guard import fetch_json

SOURCE = "tradingview"
URL = "https://scanner.tradingview.com/global/scan"
# Delay comes from the feed's update_mode. Streaming is not stamped as 15 minutes.
TICKERS = {
    "EURUSD": "FX:EURUSD",
    "USDJPY": "FX:USDJPY",
    "XAU": "TVC:GOLD",
    "N225": "TVC:NI225",
    "HSI": "TVC:HSI",
    "DAX": "XETR:DAX",
    "FDAX": "EUREX:FDAX1!",
    "ES": "CME_MINI:ES1!",
    "NQ": "CME_MINI:NQ1!",
    "NKD": "CME:NKD1!",
    "CL": "NYMEX:CL1!",
    "WTI": "NYMEX:CL1!",
    "BZ": "ICEEUR:BRN1!",
    "BRENT": "ICEEUR:BRN1!",
    "GC": "COMEX:GC1!",
}


def delay_flag(update_mode: Any) -> tuple[int, str]:
    text = str(update_mode or "")
    match = re.search(r"(\d+)$", text)
    if match and "delayed" in text:
        seconds = int(match.group(1))
        return seconds, f"delayed_{seconds}s"
    if text == "streaming":
        return 0, "streaming"
    return 0, "realtime"


def _symbols_for(ticker: Any) -> list[str]:
    return [sym for sym, code in TICKERS.items() if code == ticker]


def parse_tradingview(payload: Any, latency_ms: int) -> dict[str, dict[str, Any]]:
    """One scanner row can fill the cash book and the listed book when they share a ticker."""
    out: dict[str, dict[str, Any]] = {}
    for row in (payload or {}).get("data") or []:
        if not isinstance(row, dict):
            continue
        cols = row.get("d") or []
        price = cols[0] if cols else None
        if not isinstance(price, (int, float)) or price <= 0:
            continue
        seconds, flag = delay_flag(cols[1] if len(cols) > 1 else None)
        for sym in _symbols_for(row.get("s")):
            out[sym] = {
                "price": float(price),
                "source": f"tradingview:{row.get('s')}",
                "source_role": "primary",
                "latency_ms": latency_ms,
                "delay_flag": flag,
                "delay_s": seconds,
                "paper_only": True,
            }
    return out


def fetch_tradingview_batch(*, opener: Callable[..., bytes] | None = None, now: float | None = None) -> dict[str, dict[str, Any]]:
    result = fetch_json(
        URL, source=SOURCE, method="POST",
        payload={"symbols": {"tickers": list(dict.fromkeys(TICKERS.values()))}, "columns": ["close", "update_mode"]},
        opener=opener, now=now,
    )
    if not result.get("ok"):
        return {}
    return parse_tradingview(result.get("data"), int(result.get("latency_ms") or 0))
