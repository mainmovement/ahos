"""Public funding and open-interest change for BTC, ETH, and SOL. Context only. PAPER_ONLY."""
from __future__ import annotations

from typing import Any

SYMBOLS = ("BTC", "ETH", "SOL")


def _f(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def parse_binance_funding(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    return _f(payload.get("lastFundingRate"))


def parse_binance_oi_change(payload: Any) -> float | None:
    if not isinstance(payload, list) or len(payload) < 2:
        return None
    points = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        stamp = _f(row.get("timestamp"))
        value = _f(row.get("sumOpenInterestValue"))
        if stamp is None or value is None or value <= 0:
            continue
        points.append((stamp, value))
    if len(points) < 2:
        return None
    points.sort()
    older, newer = points[-2][1], points[-1][1]
    return (newer - older) / older


def parse_okx_funding(payload: Any) -> float | None:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return None
    return _f(data[0].get("fundingRate"))


def parse_okx_oi_usd(payload: Any) -> float | None:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return None
    return _f(data[0].get("oiUsd"))


def parse_okx_oi_change(payload: Any) -> float | None:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or len(data) < 2:
        return None
    points = []
    for row in data:
        if not isinstance(row, list) or len(row) < 4:
            continue
        stamp, value = _f(row[0]), _f(row[3])
        if stamp is None or value is None or value <= 0:
            continue
        points.append((stamp, value))
    if len(points) < 2:
        return None
    points.sort()
    older, newer = points[-2][1], points[-1][1]
    return (newer - older) / older


def _sign(value: float | None) -> int | None:
    if value is None or value == 0:
        return None
    return 1 if value > 0 else -1


def build_futures_context(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Log both venues. This does not change the funding_oi composite weight."""
    out: dict[str, Any] = {}
    for sym in SYMBOLS:
        row = payloads.get(sym) or {}
        binance_funding = parse_binance_funding(row.get("binance_funding"))
        okx_funding = parse_okx_funding(row.get("okx_funding"))
        binance_oi = parse_binance_oi_change(row.get("binance_oi"))
        okx_oi = parse_okx_oi_change(row.get("okx_oi_hist"))
        funding_signs = {s for s in (_sign(binance_funding), _sign(okx_funding)) if s is not None}
        oi_signs = {s for s in (_sign(binance_oi), _sign(okx_oi)) if s is not None}
        out[sym] = {
            "binance_funding": binance_funding,
            "okx_funding": okx_funding,
            "binance_oi_change": None if binance_oi is None else round(binance_oi, 6),
            "okx_oi_change": None if okx_oi is None else round(okx_oi, 6),
            "okx_oi_usd": parse_okx_oi_usd(row.get("okx_oi")),
            "funding_agreement": "agree" if len(funding_signs) == 1 else "conflict" if len(funding_signs) > 1 else "incomplete",
            "oi_agreement": "agree" if len(oi_signs) == 1 else "conflict" if len(oi_signs) > 1 else "incomplete",
        }
    return {
        "paper_only": True,
        "composite_weight": 0.0,
        "changes_funding_oi_weight": False,
        "symbols": out,
    }
