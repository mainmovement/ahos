"""Gold spot witness. The apex host did not serve JSON from this network. PAPER_ONLY."""
from __future__ import annotations

from typing import Any, Callable

from architecture.markets.http_guard import fetch_json

SOURCE = "gold_api"
# gold-api.com/price/XAU returned an HTML 404. This host returned the price.
URL = "https://api.gold-api.com/price/XAU"


def parse_gold(payload: Any, latency_ms: int) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    try:
        price = float(payload.get("price"))
    except (TypeError, ValueError):
        return None
    if price <= 0 or payload.get("symbol") not in (None, "XAU"):
        return None
    stamp = payload.get("updatedAt")
    return {
        "price": price,
        "source": "gold-api:XAU",
        "source_role": "witness",
        "market_time": stamp,
        "source_timestamp": stamp,
        "latency_ms": latency_ms,
        "delay_flag": "realtime",
        "delay_s": 0,
        "paper_only": True,
    }


def fetch_gold_witness(*, opener: Callable[..., bytes] | None = None, now: float | None = None) -> dict[str, dict[str, Any]]:
    result = fetch_json(URL, source=SOURCE, opener=opener, now=now)
    if not result.get("ok"):
        return {}
    row = parse_gold(result.get("data"), int(result.get("latency_ms") or 0))
    return {} if row is None else {"XAU": row}
