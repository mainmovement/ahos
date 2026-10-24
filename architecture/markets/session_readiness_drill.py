"""M13/M19/M20 — Weekday cash session countdown + adapter readiness drill (PAPER_ONLY)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from architecture.markets.oms import CCXTPaperAdapter, IBKRPaperAdapter
from architecture.markets.signal_brain import adv_cap_check
from architecture.markets.weekday_session_gate import session_report

OUT_REL = Path("reports") / "grok" / "PAPER" / "session_readiness_drill.json"
TEHRAN = ZoneInfo("Asia/Tehran")

SESSION_BLOCKS: tuple[tuple[str, ZoneInfo, int, int, tuple[str, ...]], ...] = (
    ("توکیو", ZoneInfo("Asia/Tokyo"), 9, 0, ("N225", "HSI")),
    ("فرانکفورت/لندن", ZoneInfo("Europe/Berlin"), 9, 0, ("DAX", "BRENT", "EURUSD")),
    ("نیویورک", ZoneInfo("America/New_York"), 9, 30, ("SPX", "QQQ", "WTI", "XAU", "USDJPY")),
)


def _next_weekday_open(now_utc: datetime, tz: ZoneInfo, hour: int, minute: int) -> datetime:
    local = now_utc.astimezone(tz)
    candidate = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if local.weekday() >= 5:
        days_ahead = 7 - local.weekday()
        candidate = (local + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif local >= candidate:
        candidate += timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
    return candidate.astimezone(timezone.utc)


def _countdown_fa(delta: timedelta) -> str:
    total_m = int(delta.total_seconds() // 60)
    h, m = divmod(total_m, 60)
    return f"{h} ساعت و {m} دقیقه"


def build_session_readiness_drill(root: Path, *, quotes: dict[str, Any] | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    sess = session_report(now)
    sessions: list[dict[str, Any]] = []
    for label_fa, tz, hh, mm, symbols in SESSION_BLOCKS:
        nxt = _next_weekday_open(now, tz, hh, mm)
        delta = nxt - now
        sessions.append({
            "label_fa": label_fa,
            "symbols": list(symbols),
            "next_open_utc": nxt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "next_open_tehran": nxt.astimezone(TEHRAN).strftime("%Y-%m-%d %H:%M"),
            "countdown_fa": _countdown_fa(delta),
            "hours_until": round(delta.total_seconds() / 3600, 2),
        })
    ccxt = CCXTPaperAdapter()
    ibkr = IBKRPaperAdapter(account_id="DU1234567")
    ccxt_probe = ccxt.submit_order(symbol="BTC/USDT", side="buy", notional_usd=5.0)
    ibkr_probe = ibkr.submit_order(symbol="SPX", side="buy", notional_usd=5.0)
    adv_checks: dict[str, Any] = {}
    if quotes:
        for sym in ("SPX", "BTC", "ETH", "BRENT", "XAU", "EURUSD"):
            q = quotes.get(sym) or {}
            adv_checks[sym] = adv_cap_check(100.0, q, q.get("ohlcv_5m") or [])
    payload = {
        "schema": "ahos.session_readiness_drill.v1",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "session_gate": sess,
        "cash_sessions": sessions,
        "adapters": {
            "ccxt_paper": {"oms_state": ccxt_probe.oms_state, "reason": ccxt_probe.reason, "sandbox": ccxt_probe.sandbox},
            "ibkr_paper": {"oms_state": ibkr_probe.oms_state, "reason": ibkr_probe.reason, "account": ibkr_probe.venue_id},
        },
        "adv_cap_checks": adv_checks,
        "summary_fa": (
            f"آمادگی پیش‌بازار: نزدیک‌ترین سشن {sessions[0]['label_fa']} در {sessions[0]['countdown_fa']} (تهران). "
            f"آداپتورهای کاغذی CCXT/IBKR: {ccxt_probe.oms_state}/{ibkr_probe.oms_state}. "
            f"{sess.get('summary_fa', '')}"
        ),
    }
    out = root / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def export_session_readiness_drill(root: Path | None = None, *, quotes: dict[str, Any] | None = None) -> dict[str, Any]:
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    if quotes is None:
        try:
            from architecture.markets.live_price_feed import fetch_live_market_prices

            quotes = (fetch_live_market_prices() or {}).get("quotes") or {}
        except Exception:
            quotes = {}
    return build_session_readiness_drill(repo, quotes=quotes)
