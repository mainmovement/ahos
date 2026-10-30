"""Free execution prices. Yahoo stays the fallback and the witness.

Crypto spot uses Binance and OKX public REST. No key. The cycle transport is
REST: a websocket client is not pinned, and both venues publish the same
public book over REST. When the two marks agree, Binance is the fill and OKX
is the witness. When they do not, the fill stays on Yahoo or CoinGecko.

US names that IEX actually prints (QQQ, SPY, NVDA) use Alpaca's free IEX feed
only when a key is already in the environment. SPX and NDX are indexes. IEX
does not print them, so they stay on Yahoo. Forex, gold, and oil use the
OANDA practice host only when a practice token is present. EU and Asia stay
on Yahoo plus the existing second witness.

A key is never copied onto a quote.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.markets.crypto_futures_paper import parse_okx_candles
from architecture.markets.second_source import DEFAULT_TOL, TOLERANCE

SPOT = {"BTC": ("BTCUSDT", "BTC-USDT"), "ETH": ("ETHUSDT", "ETH-USDT"), "SOL": ("SOLUSDT", "SOL-USDT")}
IEX_SYMBOLS = ("QQQ", "SPY", "NVDA")
INDEX_NO_IEX = ("SPX", "NDX")
OANDA_SYMBOLS = {"EURUSD": "EUR_USD", "USDJPY": "USD_JPY", "XAU": "XAU_USD", "WTI": "WTICO_USD", "BRENT": "BCO_USD"}
YAHOO_DESKS = ("DAX", "N225", "HSI")
_KEY_NAMES = (
    "APCA_API_KEY_ID", "APCA_API_SECRET_KEY", "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY",
    "OANDA_API_TOKEN", "OANDA_PRACTICE_TOKEN",
)
BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr?symbol={sym}"
BINANCE_KLINES = "https://api.binance.com/api/v3/klines?symbol={sym}&interval=5m&limit=100"
OKX_TICKER = "https://www.okx.com/api/v5/market/ticker?instId={inst}"
OKX_CANDLES = "https://www.okx.com/api/v5/market/candles?instId={inst}&bar=5m&limit=100"
ALPACA_SNAPSHOT = "https://data.alpaca.markets/v2/stocks/snapshots?symbols={syms}&feed=iex"
OANDA_CANDLES = "https://api-fxpractice.oanda.com/v3/instruments/{inst}/candles?price=M&granularity=M5&count=100"


def redact(text: str, secrets: list[str] | tuple[str, ...]) -> str:
    out = text
    for secret in secrets:
        if secret:
            out = out.replace(secret, "[redacted]")
    return out


def _gap(a: float, b: float) -> float:
    return abs(a - b) / ((a + b) / 2.0)


def _px(q: dict[str, Any] | None) -> float | None:
    if not isinstance(q, dict):
        return None
    price = q.get("price")
    if isinstance(price, (int, float)) and price > 0:
        return float(price)
    return None


def _witness_from(q: dict[str, Any] | None) -> dict[str, Any] | None:
    price = _px(q)
    if price is None or not isinstance(q, dict):
        return None
    return {"price": price, "source": q.get("source"), "latency_ms": q.get("latency_ms"), "transport": q.get("transport") or "rest"}


def _iso_from_epoch(ms: Any) -> str | None:
    try:
        n = float(ms)
    except (TypeError, ValueError):
        return None
    if n > 1e12:
        n = n / 1000.0
    try:
        return datetime.fromtimestamp(n, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OverflowError, OSError, ValueError):
        return None


def _iso_text(raw: Any) -> str | None:
    if not isinstance(raw, str) or "T" not in raw:
        return None
    head = raw.replace("Z", "").split(".", 1)[0]
    if len(head) == 19:
        return head + "Z"
    return None


def resolve_native(primary: dict[str, Any] | None, secondary: dict[str, Any] | None,
                   fallback: dict[str, Any] | None, *, tol: float) -> dict[str, Any] | None:
    """Use the preferred exchange print when it agrees with the other print."""
    p, s, f = _px(primary), _px(secondary), _px(fallback)
    if p and s and _gap(p, s) <= tol:
        out = dict(primary or {})
        out["source_role"] = "native"
        out["native_verdict"] = "AGREE"
        out["native_witness"] = _witness_from(secondary)
        out["transport"] = out.get("transport") or "rest"
        return out
    if p and s:
        out = dict(fallback or {})
        if f is None:
            return None
        out["source_role"] = "yahoo_fallback" if str(out.get("source") or "").startswith("yahoo") else "fallback"
        out["native_verdict"] = "CONFLICT"
        out["native_gap"] = round(_gap(p, s), 5)
        return out
    lone = primary if p else secondary if s else None
    lone_px = _px(lone)
    if lone is not None and f is not None and lone_px is not None and _gap(lone_px, f) <= tol:
        out = dict(lone)
        out["source_role"] = "native"
        out["native_verdict"] = "AGREE"
        out["native_witness"] = _witness_from(fallback)
        out["transport"] = out.get("transport") or "rest"
        return out
    if lone is not None and f is not None and lone_px is not None:
        out = dict(fallback or {})
        out["source_role"] = "yahoo_fallback" if str(out.get("source") or "").startswith("yahoo") else "fallback"
        out["native_verdict"] = "CONFLICT"
        out["native_gap"] = round(_gap(lone_px, f), 5)
        return out
    if lone is not None:
        out = dict(lone)
        out["source_role"] = "native"
        out["native_verdict"] = "SINGLE"
        out["transport"] = out.get("transport") or "rest"
        return out
    if isinstance(fallback, dict):
        out = dict(fallback)
        out.setdefault("source_role", "yahoo")
        return out
    return None


def _annotate(quotes: dict[str, Any], sym: str, note: str) -> None:
    q = quotes.get(sym)
    if isinstance(q, dict):
        q["native_note"] = note
        q.setdefault("source_role", "yahoo")


def load_feed_keys() -> dict[str, str]:
    """Key presence only. Values stay in this dict and are not returned to a quote."""
    found: dict[str, str] = {}
    for name in _KEY_NAMES:
        val = os.environ.get(name)
        if val and val.strip():
            found[name] = val.strip()
    missing = [name for name in _KEY_NAMES if name not in found]
    path = Path(__file__).resolve().parents[2] / ".env"
    if missing and path.is_file():
        want = set(missing)
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, _, val = raw.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key in want and val:
                found[key] = val
    return found


def feed_status(env: dict[str, str] | None = None) -> dict[str, str]:
    env = load_feed_keys() if env is None else env
    alpaca_id = env.get("APCA_API_KEY_ID") or env.get("ALPACA_API_KEY_ID")
    alpaca_secret = env.get("APCA_API_SECRET_KEY") or env.get("ALPACA_API_SECRET_KEY")
    oanda = env.get("OANDA_API_TOKEN") or env.get("OANDA_PRACTICE_TOKEN")
    return {
        "alpaca": "CONFIGURED" if alpaca_id and alpaca_secret else "ABSENT_NO_KEY",
        "oanda": "CONFIGURED" if oanda else "ABSENT_NO_KEY",
        "crypto": "PUBLIC_REST",
    }


def apply_native_quotes(quotes: dict[str, Any], *, spot: dict[str, dict[str, Any]] | None = None,
                        iex: dict[str, dict[str, Any]] | None = None,
                        oanda: dict[str, dict[str, Any]] | None = None,
                        status: dict[str, str] | None = None) -> dict[str, Any]:
    """Replace a quote only when the native pair agrees. Yahoo remains otherwise."""
    status = status or {"alpaca": "ABSENT_NO_KEY", "oanda": "ABSENT_NO_KEY", "crypto": "PUBLIC_REST"}
    spot = spot or {}
    iex = iex or {}
    oanda = oanda or {}
    for sym in SPOT:
        pair = spot.get(sym) or {}
        yahoo = quotes.get(f"{sym}_YAHOO")
        fallback = yahoo if _px(yahoo) else quotes.get(sym)
        chosen = resolve_native(pair.get("binance"), pair.get("okx"), fallback if isinstance(fallback, dict) else None,
                                tol=TOLERANCE.get(sym, DEFAULT_TOL))
        if isinstance(chosen, dict):
            if yahoo and chosen.get("source_role") == "native" and not chosen.get("ohlcv_5m"):
                chosen["ohlcv_5m"] = yahoo.get("ohlcv_5m") or []
                chosen["ohlcv_5m_ts"] = yahoo.get("ohlcv_5m_ts") or []
            quotes[sym] = chosen
    for sym in INDEX_NO_IEX:
        note = "IEX_DOES_NOT_PRINT_INDEX" if status.get("alpaca") == "CONFIGURED" else "ABSENT_NO_KEY"
        _annotate(quotes, sym, note)
    for sym in IEX_SYMBOLS:
        if status.get("alpaca") != "CONFIGURED":
            _annotate(quotes, sym, "ABSENT_NO_KEY")
            continue
        chosen = resolve_native(iex.get(sym), None, quotes.get(sym) if isinstance(quotes.get(sym), dict) else None,
                                tol=TOLERANCE.get(sym, 0.0035))
        if isinstance(chosen, dict):
            quotes[sym] = chosen
    for sym in OANDA_SYMBOLS:
        if status.get("oanda") != "CONFIGURED":
            _annotate(quotes, sym, "ABSENT_NO_KEY")
            continue
        chosen = resolve_native(oanda.get(sym), None, quotes.get(sym) if isinstance(quotes.get(sym), dict) else None,
                                tol=TOLERANCE.get(sym, 0.0035 if sym in ("EURUSD", "USDJPY") else 0.005))
        if isinstance(chosen, dict):
            quotes[sym] = chosen
    for sym in YAHOO_DESKS:
        q = quotes.get(sym)
        if isinstance(q, dict):
            q.setdefault("source_role", "yahoo")
            q["native_note"] = "YAHOO_PLUS_SECOND_WITNESS"
    return quotes


def _num(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x <= 0 or x != x:
        return None
    return x


def parse_binance_ticker(payload: Any, *, latency_ms: int | None = None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    px = _num(payload.get("lastPrice"))
    if px is None:
        return None
    return {"price": px, "source": f"binance:{payload.get('symbol') or 'spot'}", "market_time": _iso_from_epoch(payload.get("closeTime")),
            "latency_ms": latency_ms, "transport": "rest", "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def parse_binance_klines(payload: Any) -> tuple[list[list[float]], list[float]]:
    bars: list[list[float]] = []
    stamps: list[float] = []
    for row in payload or []:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            continue
        o, h, l, c, v = (_num(row[1]), _num(row[2]), _num(row[3]), _num(row[4]), _num(row[5]) or 0.0)
        ts = _num(row[0])
        if None in (o, h, l, c) or ts is None:
            continue
        bars.append([o, h, l, c, v])
        stamps.append(ts / 1000.0 if ts > 1e12 else ts)
    return bars, stamps


def parse_okx_ticker(payload: Any, *, inst: str, latency_ms: int | None = None) -> dict[str, Any] | None:
    rows = (payload or {}).get("data") if isinstance(payload, dict) else None
    if not rows:
        return None
    px = _num(rows[0].get("last"))
    if px is None:
        return None
    return {"price": px, "source": f"okx:{inst}", "market_time": _iso_from_epoch(rows[0].get("ts")),
            "latency_ms": latency_ms, "transport": "rest",
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def parse_alpaca_snapshots(payload: Any, *, latency_ms: int | None = None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(payload, dict):
        return out
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for sym, row in payload.items():
        if sym in ("quotes", "symbol") or not isinstance(row, dict):
            continue
        trade = row.get("latestTrade") or {}
        px = _num(trade.get("p"))
        if px is None:
            continue
        out[sym] = {"price": px, "source": f"alpaca:iex:{sym}", "market_time": _iso_text(trade.get("t")),
                    "latency_ms": latency_ms, "transport": "rest", "fetched_at": now}
    return out


def parse_oanda_candles(payload: Any, *, inst: str, latency_ms: int | None = None) -> dict[str, Any] | None:
    rows = (payload or {}).get("candles") if isinstance(payload, dict) else None
    if not rows:
        return None
    last = rows[-1]
    mid = last.get("mid") or {}
    px = _num(mid.get("c"))
    if px is None:
        return None
    bars: list[list[float]] = []
    stamps: list[float] = []
    for row in rows:
        m = row.get("mid") or {}
        o, h, l, c = (_num(m.get("o")), _num(m.get("h")), _num(m.get("l")), _num(m.get("c")))
        if None in (o, h, l, c):
            continue
        bars.append([o, h, l, c, 0.0])
    return {"price": px, "source": f"oanda:{inst}", "market_time": _iso_text(last.get("time")),
            "latency_ms": latency_ms, "transport": "rest", "ohlcv_5m": bars, "ohlcv_5m_ts": stamps,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def _request_json(url: str, *, headers: dict[str, str] | None = None, timeout: float = 6.0,
                  secrets: tuple[str, ...] = ()) -> tuple[Any, int | None]:
    t0 = time.perf_counter()
    req = urllib.request.Request(url, headers={"User-Agent": "ahos-paper/1.0", "Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return data, int((time.perf_counter() - t0) * 1000)
    except Exception:
        return None, int((time.perf_counter() - t0) * 1000)


def fetch_spot_rest(getter: Callable[[str], tuple[Any, int | None]] | None = None) -> dict[str, dict[str, Any]]:
    get = getter or (lambda url: _request_json(url))
    jobs: list[tuple[str, str, str]] = []
    for sym, (bsym, okx) in SPOT.items():
        jobs.append((sym, "binance_ticker", BINANCE_TICKER.format(sym=bsym)))
        jobs.append((sym, "binance_klines", BINANCE_KLINES.format(sym=bsym)))
        jobs.append((sym, "okx_ticker", OKX_TICKER.format(inst=okx)))
        jobs.append((sym, "okx_candles", OKX_CANDLES.format(inst=okx)))

    def one(job: tuple[str, str, str]) -> tuple[str, str, Any, int | None]:
        sym, kind, url = job
        try:
            payload, latency = get(url)
        except Exception:
            payload, latency = None, None
        return sym, kind, payload, latency

    raw: dict[str, dict[str, Any]] = {sym: {} for sym in SPOT}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for sym, kind, payload, latency in pool.map(one, jobs):
            raw[sym][kind] = (payload, latency)
    out: dict[str, dict[str, Any]] = {}
    for sym, (bsym, okx) in SPOT.items():
        bt, bl = raw[sym].get("binance_ticker") or (None, None)
        bk, _ = raw[sym].get("binance_klines") or (None, None)
        ot, ol = raw[sym].get("okx_ticker") or (None, None)
        oc, _ = raw[sym].get("okx_candles") or (None, None)
        bq = parse_binance_ticker(bt, latency_ms=bl)
        if bq is not None:
            bars, stamps = parse_binance_klines(bk)
            bq["ohlcv_5m"] = bars
            bq["ohlcv_5m_ts"] = stamps
            bq["source"] = f"binance:{bsym}"
        oq = parse_okx_ticker(ot, inst=okx, latency_ms=ol)
        if oq is not None:
            bars, stamps = parse_okx_candles(oc)
            oq["ohlcv_5m"] = bars
            oq["ohlcv_5m_ts"] = stamps
        out[sym] = {"binance": bq, "okx": oq}
    return out


def fetch_iex(env: dict[str, str], getter: Callable[..., tuple[Any, int | None]] | None = None) -> dict[str, dict[str, Any]]:
    key = env.get("APCA_API_KEY_ID") or env.get("ALPACA_API_KEY_ID") or ""
    secret = env.get("APCA_API_SECRET_KEY") or env.get("ALPACA_API_SECRET_KEY") or ""
    if not key or not secret:
        return {}
    url = ALPACA_SNAPSHOT.format(syms=",".join(IEX_SYMBOLS))
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    get = getter or (lambda u, h: _request_json(u, headers=h, secrets=(key, secret)))
    try:
        payload, latency = get(url, headers)
    except Exception:
        return {}
    return parse_alpaca_snapshots(payload, latency_ms=latency)


def fetch_oanda(env: dict[str, str], getter: Callable[..., tuple[Any, int | None]] | None = None) -> dict[str, dict[str, Any]]:
    token = env.get("OANDA_API_TOKEN") or env.get("OANDA_PRACTICE_TOKEN") or ""
    if not token:
        return {}
    headers = {"Authorization": f"Bearer {token}"}
    get = getter or (lambda u, h: _request_json(u, headers=h, secrets=(token,)))
    out: dict[str, dict[str, Any]] = {}
    for sym, inst in OANDA_SYMBOLS.items():
        try:
            payload, latency = get(OANDA_CANDLES.format(inst=inst), headers)
        except Exception:
            continue
        q = parse_oanda_candles(payload, inst=inst, latency_ms=latency)
        if q is not None:
            out[sym] = q
    return out


def overlay_native_witnesses(second: dict[str, Any], quotes: dict[str, Any], symbols) -> dict[str, Any]:
    """The agreeing exchange print is source B. An injected witness is left alone by the caller."""
    for sym in symbols:
        native = (quotes.get(sym) or {}).get("native_witness")
        if isinstance(native, dict) and isinstance(native.get("price"), (int, float)):
            second[sym] = native
    return second


def apply_live_native_quotes(quotes: dict[str, Any]) -> dict[str, Any]:
    env = load_feed_keys()
    status = feed_status(env)
    try:
        spot = fetch_spot_rest()
    except Exception:
        spot = {}
    try:
        iex = fetch_iex(env) if status["alpaca"] == "CONFIGURED" else {}
    except Exception:
        iex = {}
    try:
        oanda = fetch_oanda(env) if status["oanda"] == "CONFIGURED" else {}
    except Exception:
        oanda = {}
    return apply_native_quotes(quotes, spot=spot, iex=iex, oanda=oanda, status=status)
