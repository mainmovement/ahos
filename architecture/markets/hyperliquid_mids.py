"""Hyperliquid xyz mids. A 24/7 perp witness, not the fill. PAPER_ONLY."""
from __future__ import annotations

from typing import Any, Callable

from architecture.markets.http_guard import fetch_json

SOURCE = "hyperliquid"
URL = "https://api.hyperliquid.xyz/info"
# Perp names on dex xyz. Cash indexes are compared after the listed-future basis.
MIDS = {
    "SPX": "xyz:SP500",
    "NDX": "xyz:XYZ100",
    "XAU": "xyz:GOLD",
    "CL": "xyz:CL",
    "BZ": "xyz:BRENTOIL",
    "EURUSD": "xyz:EUR",
    "USDJPY": "xyz:JPY",
    "NVDA": "xyz:NVDA",
}
# When this futures print exists, the perp is judged against it rather than the cash index.
BASIS_FUTURE = {"SPX": "ES", "NDX": "NQ"}


def parse_mids(payload: Any, latency_ms: int) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for sym, key in MIDS.items():
        try:
            price = float(payload.get(key))
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        out[sym] = {
            "price": price,
            "source": f"hyperliquid:{key}",
            "source_role": "witness",
            "latency_ms": latency_ms,
            "delay_flag": "realtime",
            "delay_s": 0,
            "perp": True,
            "basis_future": BASIS_FUTURE.get(sym),
            "paper_only": True,
        }
    return out


def fetch_hyperliquid_mids(*, opener: Callable[..., bytes] | None = None, now: float | None = None) -> dict[str, dict[str, Any]]:
    result = fetch_json(URL, source=SOURCE, method="POST", payload={"type": "allMids", "dex": "xyz"}, opener=opener, now=now)
    if not result.get("ok"):
        return {}
    return parse_mids(result.get("data"), int(result.get("latency_ms") or 0))
