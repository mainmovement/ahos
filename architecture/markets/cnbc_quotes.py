"""CNBC public quotes. Primary for SPX, NDX, SPY, QQQ, and NVDA. Never Brent. PAPER_ONLY."""
from __future__ import annotations

import urllib.parse
from typing import Any, Callable

from architecture.markets.http_guard import fetch_json

SOURCE = "cnbc"
SYMBOLS = {"SPX": ".SPX", "NDX": ".NDX", "SPY": "SPY", "QQQ": "QQQ", "NVDA": "NVDA"}
URL = (
    "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={syms}"
    "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json"
)


def _num(text: Any) -> float | None:
    if isinstance(text, (int, float)) and text > 0:
        return float(text)
    if isinstance(text, str):
        try:
            value = float(text.replace(",", "").replace("%", ""))
        except ValueError:
            return None
        return value if value > 0 else None
    return None


def parse_cnbc(payload: Any, latency_ms: int) -> dict[str, dict[str, Any]]:
    rows = ((payload or {}).get("FormattedQuoteResult") or {}).get("FormattedQuote") if isinstance(payload, dict) else None
    if isinstance(rows, dict):
        rows = [rows]
    rev = {code: sym for sym, code in SYMBOLS.items()}
    out: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        sym = rev.get(row.get("symbol"))
        price = _num(row.get("last"))
        if sym is None or price is None or row.get("code") not in (0, "0", None):
            continue
        out[sym] = {
            "price": price,
            "source": f"cnbc:{row.get('symbol')}",
            "source_role": "primary",
            "market_time": row.get("last_time"),
            "source_timestamp": row.get("last_time"),
            "latency_ms": latency_ms,
            "delay_flag": "realtime",
            "delay_s": 0,
            "paper_only": True,
        }
    return out


def fetch_cnbc_primary(*, opener: Callable[..., bytes] | None = None, now: float | None = None) -> dict[str, dict[str, Any]]:
    encoded = urllib.parse.quote("|".join(SYMBOLS.values()), safe="")
    result = fetch_json(URL.format(syms=encoded), source=SOURCE, opener=opener, now=now)
    if not result.get("ok"):
        return {}
    return parse_cnbc(result.get("data"), int(result.get("latency_ms") or 0))
