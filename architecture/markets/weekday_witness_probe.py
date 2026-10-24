"""Shared logic for live witness probe + tradable-session gate (PAPER_ONLY)."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from architecture.markets.paper_trader import MAX_TRADE_AGE_S, _parse
from architecture.markets.second_source import witness
from architecture.markets.weekday_session_gate import CASH_DESKS, session_report


def quote_age_seconds(q: dict[str, Any], now: float) -> float | None:
    mt = _parse(q.get("market_time"))
    if mt is None:
        return None
    return now - mt


def tradable_for_paper(
    desk: str,
    witness_verdict: str,
    quote: dict[str, Any],
    *,
    now: float,
    weekend_tehran: bool,
) -> tuple[bool, str]:
    if witness_verdict != "VERIFIED":
        return False, f"WITNESS_{witness_verdict}"
    if weekend_tehran and desk in CASH_DESKS:
        return False, "WEEKEND_CASH_SESSION"
    age = quote_age_seconds(quote, now)
    if age is None:
        return False, "MARKET_TIME_UNKNOWN"
    if age > MAX_TRADE_AGE_S:
        return False, "MARKET_CLOSED_OR_STALE"
    return True, "OK"


def build_witness_probe_payload(
    instruments: dict[str, tuple[str, float, float]],
    quotes: dict[str, Any],
    second: dict[str, Any],
    *,
    now: float | None = None,
    fetch_ts: datetime | None = None,
) -> dict[str, Any]:
    t = now if now is not None else time.time()
    sess = session_report(fetch_ts)
    weekend = bool(sess.get("weekend_tehran"))
    by_desk: dict[str, list[dict[str, Any]]] = {}
    verified_desks: set[str] = set()
    tradable_desks: set[str] = set()
    for sym, (desk, _fee, _slip) in instruments.items():
        q = quotes.get(sym) or {}
        w = witness(sym, q, second.get(sym))
        ok, reason = tradable_for_paper(desk, w["verdict"], q, now=t, weekend_tehran=weekend)
        row = {
            "symbol": sym,
            "verdict": w["verdict"],
            "gap": w.get("gap"),
            "source_a": w.get("source_a"),
            "source_b": w.get("source_b"),
            "quote_age_s": quote_age_seconds(q, t),
            "tradable_for_paper": ok,
            "tradable_reason": reason,
        }
        by_desk.setdefault(desk, []).append(row)
        if w["verdict"] == "VERIFIED":
            verified_desks.add(desk)
        if ok:
            tradable_desks.add(desk)
    return {
        "schema": "ahos.weekday_witness_probe.v2",
        "paper_only": True,
        "session_gate": sess,
        "verified_asset_classes": sorted(verified_desks),
        "tradable_asset_classes": sorted(tradable_desks),
        "by_desk": by_desk,
        "summary_fa": (
            f"قابل معاملهٔ کاغذی الان: {', '.join(sorted(tradable_desks)) or 'هیچ'} · "
            f"شاهد VERIFIED (بدون تضمین سشن): {', '.join(sorted(verified_desks)) or 'هیچ'}. "
            f"{sess.get('summary_fa', '')}"
        ),
    }
