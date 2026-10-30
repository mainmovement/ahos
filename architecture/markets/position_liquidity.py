"""Copy a liquidity figure that is already on the quote or the CFTC evidence onto an open position."""
from __future__ import annotations

from typing import Any


def attach_liquidity(position: dict[str, Any], signals: list[dict[str, Any]] | None, quote: dict[str, Any] | None) -> dict[str, Any] | None:
    """Attach one measured figure. A missing figure stays missing."""
    if not isinstance(position, dict):
        return None
    quote = quote or {}
    usd = quote.get("liquidity_usd")
    if isinstance(usd, (int, float)) and not isinstance(usd, bool) and usd > 0:
        record = {"value": float(usd), "unit": "usd", "source": "quote", "field": "liquidity_usd"}
        position["liquidity"] = record
        return record
    for signal in signals or []:
        if not isinstance(signal, dict) or signal.get("name") != "cftc_cot":
            continue
        evidence = signal.get("evidence") if isinstance(signal.get("evidence"), dict) else {}
        interest = evidence.get("open_interest")
        if isinstance(interest, (int, float)) and not isinstance(interest, bool) and interest > 0:
            record = {
                "value": float(interest),
                "unit": "contracts",
                "source": "cftc_cot",
                "field": "open_interest",
            }
            position["liquidity"] = record
            return record
    return None
