"""Second independent free price sources + Two-Source Witness Law (Master Map law 6; Trading Skills v2 §0, §11).

Source B per market (all free, no key):
  * TradingView public scanner -> oil, gold futures, indices, FX, QQQ, DXY, US10Y (often 10-min delayed)
  * CNBC public quote service  -> same set, fallback (403 from Iran)
  * Kraken public ticker        -> BTC, ETH, SOL, PAXG (gold token)
Witness verdict per symbol: VERIFIED (both fresh, |gap| <= tol), CONFLICT (gap > tol),
UNRESOLVED (one source missing). Only VERIFIED may be traded. Gaps are evidence only, never traded.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

UA = {"User-Agent": "Mozilla/5.0 (AHOS paper research)"}
CNBC_URL = ("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={syms}"
            "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json")
CNBC_MAP = {"WTI": "@CL.1", "BRENT": "@LCO.1", "SPX": ".SPX", "DAX": ".GDAXI", "N225": ".N225",
            "HSI": ".HSI", "EURUSD": "EUR=", "USDJPY": "JPY=", "QQQ": "QQQ", "DXY": ".DXY", "US10Y": "US10Y"}
KRAKEN_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,PAXGUSD"
KRAKEN_MAP = {"XXBTZUSD": "BTC", "XETHZUSD": "ETH", "SOLUSD": "SOL", "PAXGUSD": "XAU"}
# tolerance per symbol (fraction). Gold B is PAXG (a token), futures vs spot basis -> wider.
TOLERANCE = {"XAU": 0.008, "WTI": 0.006, "BRENT": 0.006, "DXY": 0.004, "US10Y": 0.02}
DEFAULT_TOL = 0.004


def _get(url: str, timeout: float) -> Any:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _num(s: Any) -> float | None:
    if isinstance(s, (int, float)):
        return float(s)
    if isinstance(s, str):
        try:
            return float(s.replace(",", "").replace("%", ""))
        except ValueError:
            return None
    return None


def _iso_cnbc(t: str | None) -> str | None:
    if not t:
        return None
    try:
        return datetime.fromisoformat(t.replace(".000", "")).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def fetch_cnbc(timeout: float = 8.0) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        d = _get(CNBC_URL.format(syms="|".join(CNBC_MAP.values())), timeout)
        rows = d["FormattedQuoteResult"]["FormattedQuote"]
    except Exception:
        return out
    rev = {v: k for k, v in CNBC_MAP.items()}
    for q in rows:
        sym = rev.get(q.get("symbol"))
        px = _num(q.get("last"))
        if sym and px:
            out[sym] = {"price": px, "source": f"cnbc:{q.get('symbol')}", "market_time": _iso_cnbc(q.get("last_time")),
                        "volume": _num(q.get("volume"))}
    return out


def fetch_kraken(timeout: float = 8.0) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        res = _get(KRAKEN_URL, timeout)["result"]
    except Exception:
        return out
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for k, v in res.items():
        sym = KRAKEN_MAP.get(k)
        px = _num((v.get("c") or [None])[0])
        if sym and px:
            out[sym] = {"price": px, "source": f"kraken:{k}", "market_time": now, "volume_24h": _num((v.get("v") or [0, 0])[1])}
    return out


TV_URL = "https://scanner.tradingview.com/global/scan"
TV_MAP = {"WTI": "NYMEX:CL1!", "BRENT": "ICEEUR:BRN1!", "XAU": "COMEX:GC1!", "SPX": "SP:SPX", "DAX": "XETR:DAX",
          "N225": "TVC:NI225", "HSI": "TVC:HSI", "EURUSD": "FX:EURUSD", "USDJPY": "FX:USDJPY", "QQQ": "NASDAQ:QQQ",
          "DXY": "TVC:DXY", "US10Y": "TVC:US10Y"}


def fetch_tradingview(timeout: float = 8.0) -> dict[str, dict[str, Any]]:
    """TradingView public scanner (free, no key, reachable from Iran; CNBC returns 403 there). Often 10-min delayed."""
    body = json.dumps({"symbols": {"tickers": list(TV_MAP.values())}, "columns": ["close", "volume", "update_mode"]}).encode()
    try:
        req = urllib.request.Request(TV_URL, data=body, headers={**UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            rows = json.loads(r.read().decode("utf-8"))["data"]
    except Exception:
        return {}
    rev = {v: k for k, v in TV_MAP.items()}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {}
    for row in rows:
        sym = rev.get(row.get("s"))
        d = row.get("d") or []
        px = _num(d[0]) if d else None
        if sym and px:
            out[sym] = {"price": px, "source": f"tradingview:{row['s']}", "fetched_at": now,
                        "volume": _num(d[1]) if len(d) > 1 else None, "update_mode": d[2] if len(d) > 2 else None}
    return out


def fetch_second_sources(timeout: float = 8.0) -> dict[str, dict[str, Any]]:
    """Source B: TradingView first, CNBC fills gaps, Kraken for crypto (and PAXG only if gold is still missing)."""
    b = fetch_cnbc(timeout)
    b.update(fetch_tradingview(timeout))
    k = fetch_kraken(timeout)
    for sym, q in k.items():
        if sym != "XAU" or "XAU" not in b:
            b[sym] = q
    return b


def witness(sym: str, a: dict[str, Any] | None, b: dict[str, Any] | None) -> dict[str, Any]:
    pa = (a or {}).get("price")
    pb = (b or {}).get("price")
    tol = TOLERANCE.get(sym, DEFAULT_TOL)
    base = {"symbol": sym, "source_a": (a or {}).get("source"), "price_a": pa,
            "source_b": (b or {}).get("source"), "price_b": pb, "tolerance": tol}
    if not isinstance(pa, (int, float)) or not isinstance(pb, (int, float)) or pa <= 0 or pb <= 0:
        return {**base, "verdict": "UNRESOLVED", "gap": None}
    gap = abs(pa - pb) / ((pa + pb) / 2.0)
    return {**base, "verdict": "VERIFIED" if gap <= tol else "CONFLICT", "gap": round(gap, 5)}
