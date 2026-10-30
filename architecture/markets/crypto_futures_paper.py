"""Paper crypto perpetual swaps.

OKX public mark is the execution price. Binance public mark is the second
witness. Funding is a paper cashflow. Liquidation is a simulated flat.
Leverage stays 1.0. There is no wallet and no live order.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.markets.family_vote_scorecard import OBS_REL

DESK = "CRYPTO_FUTURES"
EQUITY_CAP = 0.10
LEVERAGE_CAP = 1.0
SCORECARD_DAYS = 7
# Pre-registered isolated maintenance fraction. Not fit to a book.
MAINTENANCE_MARGIN_RATE = 0.005
MARK_TOLERANCE = 0.0015
FUNDING_PERIOD_S = 8 * 3600
# OKX public VIP0 USDT-swap taker is 0.05%. Slippage is a pre-registered 4 bps.
FEE = 0.0005
SLIP = 0.0004

SWAP_INST = {
    "BTC-SWAP": "BTC-USDT-SWAP",
    "ETH-SWAP": "ETH-USDT-SWAP",
    "SOL-SWAP": "SOL-USDT-SWAP",
}
BINANCE_SYMBOL = {"BTC-SWAP": "BTCUSDT", "ETH-SWAP": "ETHUSDT", "SOL-SWAP": "SOLUSDT"}

OKX_MARK = "https://www.okx.com/api/v5/public/mark-price?instId={inst}"
OKX_FUNDING = "https://www.okx.com/api/v5/public/funding-rate?instId={inst}"
OKX_CANDLES = "https://www.okx.com/api/v5/market/candles?instId={inst}&bar=5m&limit=100"
BINANCE_MARK = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}"


def liquidation_price(side: str, entry: float, leverage: float = LEVERAGE_CAP,
                      mmr: float = MAINTENANCE_MARGIN_RATE) -> float | None:
    """Isolated mark where margin minus maintenance is gone. At 1x that is a near-total move."""
    if leverage <= 0 or entry <= 0:
        return None
    buf = (1.0 / leverage) - mmr
    if buf <= 0:
        return None
    if side == "LONG":
        return entry * (1.0 - buf)
    if side == "SHORT":
        return entry * (1.0 + buf)
    return None


def simulated_liquidation(side: str, price: float, liq: Any) -> bool:
    if not isinstance(liq, (int, float)) or not isinstance(price, (int, float)):
        return False
    if side == "LONG":
        return price <= float(liq)
    if side == "SHORT":
        return price >= float(liq)
    return False


def funding_cashflow(side: str, notional: float, rate_8h: Any, elapsed_s: float) -> float:
    """Positive 8h rate: longs pay, shorts receive. Paper cash only."""
    if elapsed_s <= 0 or not isinstance(rate_8h, (int, float)) or not isinstance(notional, (int, float)):
        return 0.0
    sign = 1.0 if side == "LONG" else -1.0
    return -sign * float(notional) * float(rate_8h) * (float(elapsed_s) / FUNDING_PERIOD_S)


def accrue_funding(pos: dict[str, Any], rate_8h: Any, now_ts: float) -> float:
    if not isinstance(rate_8h, (int, float)) or not isinstance(now_ts, (int, float)):
        return 0.0
    last = pos.get("funding_ts")
    if not isinstance(last, (int, float)):
        last = pos.get("opened_ts")
    if not isinstance(last, (int, float)):
        return 0.0
    cash = funding_cashflow(str(pos.get("side")), float(pos.get("notional_usd") or 0), rate_8h, now_ts - float(last))
    pos["funding_usd"] = round(float(pos.get("funding_usd") or 0) + cash, 6)
    pos["funding_ts"] = now_ts
    return cash


def scorecard_span_days(root: Path) -> float | None:
    path = Path(root) / OBS_REL
    if not path.is_file():
        return None
    stamps: list[datetime] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line).get("ts")
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        stamps.append(dt)
    if len(stamps) < 2:
        return None
    return (max(stamps) - min(stamps)).total_seconds() / 86400.0


def leverage_decision(root: Path, requested: float = LEVERAGE_CAP) -> dict[str, Any]:
    """1.0 is the only applied leverage. A finished scorecard week does not raise it."""
    span = scorecard_span_days(root)
    locked = span is None or span < SCORECARD_DAYS
    applied = min(LEVERAGE_CAP, float(requested))
    return {
        "requested": float(requested),
        "applied": applied,
        "lock": "SCORECARD_WEEK_INCOMPLETE" if locked else "CAP_HELD_AT_1",
        "span_days": None if span is None else round(span, 4),
        "equity_cap": EQUITY_CAP,
        "paper_only": True,
    }


def book_notional_cap(equity: float, open_futures_notional: float) -> float:
    return max(0.0, EQUITY_CAP * float(equity) - float(open_futures_notional))


def _http_json(url: str, timeout: float = 8.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "ahos-paper/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _num(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:
        return None
    return x


def _iso(ms: Any) -> str | None:
    n = _num(ms)
    if n is None:
        return None
    if n > 1e12:
        n = n / 1000.0
    try:
        return datetime.fromtimestamp(n, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OverflowError, OSError, ValueError):
        return None


def parse_okx_mark(payload: Any) -> tuple[float | None, str | None]:
    rows = (payload or {}).get("data") if isinstance(payload, dict) else None
    if not rows:
        return None, None
    row = rows[0]
    px = _num(row.get("markPx"))
    if px is None or px <= 0:
        return None, None
    return px, _iso(row.get("ts"))


def parse_okx_funding(payload: Any) -> float | None:
    rows = (payload or {}).get("data") if isinstance(payload, dict) else None
    if not rows:
        return None
    return _num(rows[0].get("fundingRate"))


def parse_okx_candles(payload: Any) -> tuple[list[list[float]], list[float]]:
    rows = (payload or {}).get("data") if isinstance(payload, dict) else None
    bars: list[list[float]] = []
    stamps: list[float] = []
    for row in reversed(rows or []):
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            continue
        o, h, l, c, v = (_num(row[1]), _num(row[2]), _num(row[3]), _num(row[4]), _num(row[5]))
        ts = _num(row[0])
        if None in (o, h, l, c) or ts is None:
            continue
        bars.append([o, h, l, c, v or 0.0])
        stamps.append(ts / 1000.0 if ts > 1e12 else ts)
    return bars, stamps


def parse_binance_mark(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    px = _num(payload.get("markPrice"))
    if px is None or px <= 0:
        return None
    return px


def fetch_swap_quotes(getter: Callable[[str], Any] | None = None) -> dict[str, dict[str, Any]]:
    get = getter or _http_json
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: dict[str, dict[str, Any]] = {}
    for sym, inst in SWAP_INST.items():
        try:
            started = time.perf_counter()
            px, ts = parse_okx_mark(get(OKX_MARK.format(inst=inst)))
            latency_ms = int((time.perf_counter() - started) * 1000)
            if px is None:
                continue
            rate = parse_okx_funding(get(OKX_FUNDING.format(inst=inst)))
            bars, stamps = parse_okx_candles(get(OKX_CANDLES.format(inst=inst)))
        except Exception:
            continue
        out[sym] = {
            "price": px,
            "source": f"okx:{inst}",
            "source_role": "native",
            "transport": "rest",
            "latency_ms": latency_ms,
            "market_time": ts or now,
            "fetched_at": now,
            "funding_rate_8h": rate,
            "ohlcv_5m": bars,
            "ohlcv_5m_ts": stamps,
        }
    return out


def fetch_swap_witnesses(getter: Callable[[str], Any] | None = None) -> dict[str, dict[str, Any]]:
    get = getter or _http_json
    out: dict[str, dict[str, Any]] = {}
    for sym, bsym in BINANCE_SYMBOL.items():
        try:
            px = parse_binance_mark(get(BINANCE_MARK.format(sym=bsym)))
        except Exception:
            px = None
        if px is None:
            continue
        out[sym] = {"price": px, "source": f"binance:{bsym}", "vendor": "binance"}
    return out


def merge_swap_quotes(quotes: dict[str, Any], getter: Callable[[str], Any] | None = None) -> None:
    for sym, q in fetch_swap_quotes(getter).items():
        quotes[sym] = q
