"""Daily FX sanity from Frankfurter. Not a tick. PAPER_ONLY."""
from __future__ import annotations

from typing import Any, Callable

from architecture.markets.http_guard import fetch_json

SOURCE = "frankfurter"
URL = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,JPY"


def parse_frankfurter(payload: Any, latency_ms: int) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    rates = payload.get("rates") or {}
    stamp = payload.get("date")
    out: dict[str, dict[str, Any]] = {}
    try:
        eur = float(rates.get("EUR"))
        jpy = float(rates.get("JPY"))
    except (TypeError, ValueError):
        return {}
    if eur > 0:
        out["EURUSD"] = _row(1.0 / eur, stamp, latency_ms)
    if jpy > 0:
        out["USDJPY"] = _row(jpy, stamp, latency_ms)
    return out


def _row(price: float, stamp: Any, latency_ms: int) -> dict[str, Any]:
    return {
        "price": price,
        "source": "frankfurter:USD",
        "source_role": "witness",
        "market_time": None if stamp is None else f"{stamp}T00:00:00Z",
        "source_timestamp": None if stamp is None else f"{stamp}T00:00:00Z",
        "latency_ms": latency_ms,
        "delay_flag": "daily",
        "delay_s": 86400,
        "paper_only": True,
    }


def fetch_frankfurter(*, opener: Callable[..., bytes] | None = None, now: float | None = None) -> dict[str, dict[str, Any]]:
    result = fetch_json(URL, source=SOURCE, opener=opener, now=now)
    if not result.get("ok"):
        return {}
    return parse_frankfurter(result.get("data"), int(result.get("latency_ms") or 0))
