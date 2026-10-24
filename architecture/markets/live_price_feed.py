"""Live market price feed (PAPER_ONLY) â€” real quotes only, never constants.

Sources:
- Yahoo Finance chart API (oil BZ=F / CL=F, gold GC=F, ^GSPC, ^GDAXI, ^N225, DX-Y.NYB,
  plus equities/FX/crypto cross-check symbols)
- CoinGecko simple price (crypto + PAX Gold)
- Alternative.me Fear & Greed, CoinGecko global

Every quote carries ``source`` and ``fetched_at`` (plus the exchange ``market_time`` when known)
and a ``freshness`` of LIVE (fetched < 5 min ago), STALE (older, with ``age_seconds``) or
UNAVAILABLE (no data: ``price`` is None). There is NO constant fallback anywhere: when a fetch
fails the price is simply unavailable and consumers must say so.
"""
from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PAPER_ONLY: bool = True
LIVE_TRADING: bool = False

LIVE_MAX_AGE_SECONDS = 300
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=2d&interval=5m"
COINGECKO_SIMPLE_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,solana,pax-gold,binancecoin,ripple,dogecoin,toncoin"
    "&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true"
    "&include_last_updated_at=true"
)
ALTERNATIVE_FNG_URL = "https://api.alternative.me/fng/?limit=1"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"

# internal symbol -> yahoo ticker
YAHOO_SYMBOLS: dict[str, str] = {
    "BRENT": "BZ=F",
    "WTI": "CL=F",
    "GOLD_FUT": "GC=F",
    "SPX": "^GSPC",
    "DAX": "^GDAXI",
    "N225": "^N225",
    "DXY": "DX-Y.NYB", "US10Y": "^TNX",
    "HSI": "^HSI",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "NVDA": "NVDA",
    "EXW1.DE": "EXW1.DE",
    "EURUSD": "EURUSD=X",
    "USDJPY": "JPY=X",
    "BTC_Y": "BTC-USD",
    "ETH_Y": "ETH-USD",
    "SOL_Y": "SOL-USD",
    "UNI_Y": "UNI7083-USD",
}
COINGECKO_IDS: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "UNI": "uniswap",
    "XAU": "pax-gold",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "TON": "toncoin",
}


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _fetch_json(url: str, timeout: float = 6.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def _num(v: Any) -> float | None:
    if isinstance(v, (int, float)) and math.isfinite(float(v)) and float(v) > 0:
        return float(v)
    return None


def unavailable_quote(source: str) -> dict[str, Any]:
    return {
        "price": None,
        "change_24h": None,
        "source": source,
        "fetched_at": None,
        "market_time": None,
        "freshness": "UNAVAILABLE",
        "age_seconds": None,
    }


def classify_freshness(quote: dict[str, Any], now_ts: float | None = None) -> dict[str, Any]:
    """Recompute freshness from fetched_at: LIVE < 5 min, STALE otherwise, UNAVAILABLE if no price."""
    q = dict(quote)
    if _num(q.get("price")) is None or not q.get("fetched_at"):
        q.update(price=None, freshness="UNAVAILABLE", age_seconds=None)
        return q
    try:
        fetched = datetime.strptime(str(q["fetched_at"]), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        q.update(freshness="STALE", age_seconds=None)
        return q
    age = max(0, int((now_ts if now_ts is not None else _now_ts()) - fetched.timestamp()))
    q["age_seconds"] = age
    q["freshness"] = "LIVE" if age < LIVE_MAX_AGE_SECONDS else "STALE"
    return q


def fetch_yahoo_quote(yahoo_sym: str, *, timeout: float = 6.0) -> dict[str, Any]:
    url = YAHOO_CHART_URL.format(sym=urllib.parse.quote(yahoo_sym, safe=""))
    src = f"yahoo_finance:{yahoo_sym}"
    data = _fetch_json(url, timeout=timeout)
    try:
        res = data["chart"]["result"][0]  # type: ignore[index]
        meta = res["meta"]
    except Exception:
        return unavailable_quote(src)
    price = _num(meta.get("regularMarketPrice"))
    if price is None:
        return unavailable_quote(src)
    prev = _num(meta.get("chartPreviousClose")) or _num(meta.get("previousClose"))
    closes: list[float] = []
    try:
        closes = [round(float(c), 4) for c in res["indicators"]["quote"][0]["close"] if _num(c) is not None]
    except Exception:
        closes = []
    ohlcv: list[list[float]] = []
    ohlcv_ts: list[int] = []
    try:
        qd = res["indicators"]["quote"][0]
        stamps = res.get("timestamp") or [None] * len(qd["close"])
        for ts, o, h, l, c, v in zip(stamps, qd["open"], qd["high"], qd["low"], qd["close"], qd.get("volume") or [0] * len(qd["close"])):
            if None not in (_num(o), _num(h), _num(l), _num(c)):
                ohlcv.append([round(float(o), 6), round(float(h), 6), round(float(l), 6), round(float(c), 6), float(v or 0)])
                ohlcv_ts.append(int(ts) if isinstance(ts, (int, float)) else 0)
    except Exception:
        ohlcv, ohlcv_ts = [], []
    mt = meta.get("regularMarketTime")
    now = _now_ts()
    return {
        "price": round(price, 4 if price < 10 else 2),
        "change_24h": round((price - prev) / prev * 100.0, 2) if prev else None,
        "previous_close": prev,
        "source": src,
        "fetched_at": _iso(now),
        "market_time": _iso(float(mt)) if isinstance(mt, (int, float)) else None,
        "freshness": "LIVE",
        "age_seconds": 0,
        "history": closes[-48:],
        "ohlcv_5m": ohlcv[-288:],
        "ohlcv_5m_ts": ohlcv_ts[-288:],
        "currency": meta.get("currency"),
        "_regular_market_time": mt if isinstance(mt, (int, float)) else None,
    }


# Continuous Yahoo futures roll on Yahoo's own schedule, which differs from TradingView/Stooq "1!" continuous
# contracts (e.g. BZ=F already on Jan while ICE BRN1! is still Dec). The witness must compare the SAME month.
FUTURES_ROOTS: dict[str, tuple[str, str]] = {"BRENT": ("BZ", "NYM"), "WTI": ("CL", "NYM"), "XAU": ("GC", "CMX")}
MONTH_CODES = "FGHJKMNQUVXZ"
_CONTRACT_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
CONTRACT_CACHE_TTL_S = 3600.0


def _candidate_months(now_ts: float, n: int = 6) -> list[tuple[int, int]]:
    d = datetime.fromtimestamp(now_ts, tz=timezone.utc)
    out = []
    y, m = d.year, d.month
    for _ in range(n):
        out.append((y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def resolve_yahoo_contract_month(sym: str, continuous: dict[str, Any], *,
                                 fetch: Any = None, now_ts: float | None = None) -> dict[str, Any] | None:
    """Identify which explicit contract Yahoo's continuous future currently is, using only Yahoo itself
    (same regularMarketTime and same price as an explicit ``BZF27.NYM``-style contract). No cross-vendor matching:
    a match against another vendor would make the later agreement test circular."""
    root = FUTURES_ROOTS.get(sym)
    price, mt = continuous.get("price"), continuous.get("_regular_market_time")
    if root is None or _num(price) is None or not isinstance(mt, (int, float)):
        return None
    now = now_ts if now_ts is not None else _now_ts()
    cached = _CONTRACT_CACHE.get(sym)
    if fetch is None and cached and now - cached[0] < CONTRACT_CACHE_TTL_S and cached[1].get("price") == price:
        return cached[1]
    getter = fetch or (lambda s: _fetch_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(s, safe='')}?range=1d&interval=1d"))
    for y, m in _candidate_months(now):
        code = f"{root[0]}{MONTH_CODES[m - 1]}{y % 100:02d}.{root[1]}"
        data = getter(code)
        try:
            meta = data["chart"]["result"][0]["meta"]  # type: ignore[index]
        except Exception:
            continue
        p, t = _num(meta.get("regularMarketPrice")), meta.get("regularMarketTime")
        if p is not None and isinstance(t, (int, float)) and abs(p - float(price)) < 1e-9 and abs(float(t) - float(mt)) <= 60:
            res = {"contract_month": f"{y:04d}-{m:02d}", "contract_symbol": code, "price": price,
                   "method": "yahoo_self_identity(price+regularMarketTime)"}
            if fetch is None:
                _CONTRACT_CACHE[sym] = (now, res)
            return res
    return None


def fetch_coingecko_quotes(*, timeout: float = 6.0) -> dict[str, dict[str, Any]]:
    data = _fetch_json(COINGECKO_SIMPLE_URL, timeout=timeout)
    now = _now_ts()
    out: dict[str, dict[str, Any]] = {}
    for sym, cg_id in COINGECKO_IDS.items():
        src = f"coingecko:{cg_id}"
        row = data.get(cg_id) if isinstance(data, dict) else None
        price = _num(row.get("usd")) if isinstance(row, dict) else None
        if price is None:
            out[sym] = unavailable_quote(src)
            continue
        chg = row.get("usd_24h_change")
        lu = row.get("last_updated_at")
        out[sym] = {
            "price": round(price, 4 if price < 10 else 2),
            "change_24h": round(float(chg), 2) if isinstance(chg, (int, float)) else None,
            "vol_24h": _num(row.get("usd_24h_vol")),
            "mcap": _num(row.get("usd_market_cap")),
            "source": src,
            "fetched_at": _iso(now),
            "market_time": _iso(float(lu)) if isinstance(lu, (int, float)) else None,
            "freshness": "LIVE",
            "age_seconds": 0,
        }
    return out


def _fmt_vol(vol: Any) -> str:
    v = _num(vol)
    if v is None:
        return "â€”"
    if v >= 1e9:
        return f"{v / 1e9:.1f}B"
    if v >= 1e6:
        return f"{v / 1e6:.0f}M"
    return f"{v:.0f}"


MARKET_ROWS: list[tuple[str, str, str, str, str]] = [
    # symbol, fa, en, category, unit
    ("BTC", "Ø¨ÛŒØªâ€ŒÚ©ÙˆÛŒÙ†", "Bitcoin", "crypto", "USD"),
    ("ETH", "Ø§ØªØ±ÛŒÙˆÙ…", "Ethereum", "crypto", "USD"),
    ("SOL", "Ø³ÙˆÙ„Ø§Ù†Ø§", "Solana", "crypto", "USD"),
    ("XAU", "Ø·Ù„Ø§ÛŒ Ø¬Ù‡Ø§Ù†ÛŒ", "Gold (COMEX GC=F)", "gold", "USD / oz"),
    ("BRENT", "Ù†ÙØª Ø¨Ø±Ù†Øª", "Brent Crude (BZ=F)", "oil", "USD / bbl"),
    ("WTI", "Ù†ÙØª WTI", "WTI Crude (CL=F)", "oil", "USD / bbl"),
    ("SPX", "Ø§Ø³â€ŒØ§Ù†Ø¯Ù¾ÛŒ ÛµÛ°Û°", "S&P 500", "us", "points"),
    ("DAX", "Ø¯Ú©Ø³ Ø¢Ù„Ù…Ø§Ù†", "DAX", "eu", "points"),
    ("N225", "Ù†ÛŒÚ©ÛŒ Ú˜Ø§Ù¾Ù†", "Nikkei 225", "asia", "points"),
    ("DXY", "Ø´Ø§Ø®Øµ Ø¯Ù„Ø§Ø±", "US Dollar Index", "fx", "points"),
]


def fetch_live_market_prices(*, timeout: float = 6.0) -> dict[str, Any]:
    """Fetch real quotes. Missing data -> UNAVAILABLE (price None). Never a constant."""
    now_iso = _iso(_now_ts())
    yq = {k: fetch_yahoo_quote(v, timeout=timeout) for k, v in YAHOO_SYMBOLS.items()}
    cg = fetch_coingecko_quotes(timeout=timeout)
    fng = _fetch_json(ALTERNATIVE_FNG_URL, timeout=timeout)
    glob = _fetch_json(COINGECKO_GLOBAL_URL, timeout=timeout)

    quotes: dict[str, dict[str, Any]] = {}
    # crypto primary = CoinGecko (Yahoo crypto kept as independent cross-check)
    for sym in ("BTC", "ETH", "SOL", "UNI", "BNB", "XRP", "DOGE", "TON"):
        quotes[sym] = cg[sym]
        ycross = yq.get(f"{sym}_Y")
        if ycross is not None:
            quotes[f"{sym}_YAHOO"] = ycross
            if quotes[sym].get("price") is None and ycross.get("price") is not None:
                quotes[sym] = dict(ycross)
            elif quotes[sym].get("price") is not None and ycross.get("history"):
                quotes[sym]["history"] = ycross["history"]
                quotes[sym]["ohlcv_5m"] = ycross.get("ohlcv_5m") or []
    # gold primary = COMEX futures on Yahoo; PAXG kept as cross-check
    quotes["XAU"] = yq["GOLD_FUT"]
    quotes["PAXG"] = cg["XAU"]
    for k in ("BRENT", "WTI", "SPX", "DAX", "N225", "DXY", "US10Y", "HSI", "SPY", "QQQ", "NVDA", "EXW1.DE", "EURUSD", "USDJPY"):
        quotes[k] = yq[k]
    for k in FUTURES_ROOTS:
        if quotes.get(k, {}).get("price") is not None:
            res = resolve_yahoo_contract_month(k, quotes[k])
            quotes[k]["contract_month"] = (res or {}).get("contract_month")
            quotes[k]["contract_symbol"] = (res or {}).get("contract_symbol")

    macro: dict[str, Any] = {"fear_greed": None, "fear_greed_label": None, "total_mcap_usd": None,
                             "mcap_change_24h_pct": None, "btc_dominance_pct": None,
                             "source": "alternative.me+coingecko_global", "fetched_at": now_iso}
    if isinstance(fng, dict) and isinstance(fng.get("data"), list) and fng["data"]:
        first = fng["data"][0]
        try:
            macro["fear_greed"] = int(first.get("value"))
            macro["fear_greed_label"] = str(first.get("value_classification") or "")
        except Exception:
            pass
    if isinstance(glob, dict) and isinstance(glob.get("data"), dict):
        g = glob["data"]
        tmc = (g.get("total_market_cap") or {}).get("usd")
        macro["total_mcap_usd"] = _num(tmc)
        macro["btc_dominance_pct"] = _num((g.get("market_cap_percentage") or {}).get("btc"))
        mc = g.get("market_cap_change_percentage_24h_usd")
        macro["mcap_change_24h_pct"] = round(float(mc), 2) if isinstance(mc, (int, float)) else None

    markets_list = []
    for sym, fa, en, cat, unit in MARKET_ROWS:
        q = quotes.get(sym) or unavailable_quote("none")
        markets_list.append({
            "symbol": sym,
            "name": {"fa": fa, "en": en},
            "category": cat,
            "price": q.get("price"),
            "change": q.get("change_24h"),
            "volume": _fmt_vol(q.get("vol_24h")),
            "freshness": q.get("freshness"),
            "history": list(q.get("history") or []),
            "unit": unit,
            "source": q.get("source"),
            "fetched_at": q.get("fetched_at"),
            "market_time": q.get("market_time"),
            "age_seconds": q.get("age_seconds"),
        })

    live_n = sum(1 for q in quotes.values() if q.get("freshness") == "LIVE")
    return {
        "schema": "ahos.live_market_prices.v2",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live_fetch_ok": live_n > 0,
        "live_quote_count": live_n,
        "source": "yahoo_finance_chart+coingecko_v3",
        "freshness_rule": "LIVE if fetched < 300s ago, else STALE; UNAVAILABLE if no data. No constant fallback.",
        "macro": macro,
        "quotes": quotes,
        "markets": markets_list,
    }


def _price(q: dict[str, Any], key: str) -> float | None:
    row = q.get(key)
    return _num(row.get("price")) if isinstance(row, dict) else None


def build_live_multi_market_fixtures(live_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """13-instrument witness rows built ONLY from real fetched quotes.

    Each quote is a real, independently fetched source. No synthetic Â±offsets. Where only one
    real source exists the desk will honestly report UNRESOLVED (needs >= 2 sources).
    """
    data = live_payload or fetch_live_market_prices()
    q = data.get("quotes") or {}

    def _row(desk: str, symbol: str, regime: str, pairs: list[tuple[str, str]]) -> dict[str, Any]:
        quotes = []
        for key, label in pairs:
            p = _price(q, key)
            if p is not None:
                quotes.append({"source": label or str((q.get(key) or {}).get("source")), "price": p})
        return {"desk": desk, "symbol": symbol, "regime": regime, "quotes": quotes}

    return [
        _row("GOLD", "XAUUSD", "BULL_TREND", [("XAU", "yahoo_gc_futures"), ("PAXG", "coingecko_paxg")]),
        _row("OIL", "WTI", "RANGE_CHOP", [("WTI", "yahoo_cl_futures")]),
        _row("CRYPTO", "BTCUSDT", "BULL_TREND", [("BTC", "coingecko_public"), ("BTC_YAHOO", "yahoo_btc_usd")]),
        _row("CRYPTO", "ETHUSDT", "BULL_TREND", [("ETH", "coingecko_public"), ("ETH_YAHOO", "yahoo_eth_usd")]),
        _row("US_EQUITIES", "SPY", "BULL_TREND", [("SPY", "yahoo_us")]),
        _row("US_EQUITIES", "QQQ", "BULL_TREND", [("QQQ", "yahoo_us")]),
        _row("US_EQUITIES", "NVDA", "BULL_TREND", [("NVDA", "yahoo_us")]),
        _row("EU_EQUITIES", "EXW1.DE", "RANGE_CHOP", [("EXW1.DE", "yahoo_eu")]),
        _row("EU_EQUITIES", "DAX", "BULL_TREND", [("DAX", "yahoo_eu")]),
        _row("ASIA_EQUITIES", "N225", "BULL_TREND", [("N225", "yahoo_asia")]),
        _row("ASIA_EQUITIES", "HSI", "RANGE_CHOP", [("HSI", "yahoo_asia")]),
        _row("FOREX", "EURUSD", "RANGE_CHOP", [("EURUSD", "yahoo_fx")]),
        _row("FOREX", "USDJPY", "BULL_TREND", [("USDJPY", "yahoo_fx")]),
    ]


def export_live_market_prices(repo_root: Path | None = None) -> dict[str, Any]:
    """Fetch and write reports/grok/M19/live_market_prices.json."""
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    payload = fetch_live_market_prices()
    out_dir = root / "reports" / "grok" / "M19"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "live_market_prices.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload
