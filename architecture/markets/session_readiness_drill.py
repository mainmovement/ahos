"""M13/M19/M20 — Weekday cash session countdown + adapter readiness drill (PAPER_ONLY).

Countdowns come from per-venue regular hours (weekday_session_gate.VENUES, DST-aware, holidays not modeled).
The adapter preflight is a set of NEGATIVE CONTROLS on the paper-only stub adapters (live / non-DU / no-sandbox /
withdraw must all be refused); broker connectivity is NOT_VERIFIED because no broker session or credential is used."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from architecture.markets.oms import CCXTPaperAdapter, IBKRPaperAdapter
from architecture.markets.signal_brain import adv_cap_check
from architecture.markets.weekday_session_gate import SCHEDULE_BASIS, SYMBOL_VENUE, session_report, venue_status

OUT_REL = Path("reports") / "grok" / "PAPER" / "session_readiness_drill.json"
STATUS_REL = Path("reports") / "grok" / "PAPER" / "paper_trader_status.json"
TEHRAN = ZoneInfo("Asia/Tehran")
HEARTBEAT_STALE_S = 15 * 60
PAPER_NOTIONAL_FLOOR_USD = 100.0

SESSION_BLOCKS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("توکیو", ("TSE", "HKEX"), ("N225", "HSI")),
    ("فرانکفورت/لندن", ("XETRA", "LSE", "ICE_BRENT"), ("DAX", "BRENT", "EURUSD")),
    ("نیویورک", ("NYSE", "CME_GLOBEX", "FX_OTC"), ("SPX", "QQQ", "WTI", "XAU", "USDJPY")),
)


def _countdown_fa(minutes: int | None) -> str:
    if minutes is None:
        return "نامعلوم"
    if minutes == 0:
        return "باز است"
    h, m = divmod(int(minutes), 60)
    return f"{h} ساعت و {m} دقیقه"


def _heartbeat(root: Path, now: datetime) -> dict[str, Any]:
    try:
        s = json.loads((root / STATUS_REL).read_text(encoding="utf-8"))
        ts = datetime.fromisoformat(str(s.get("updated_at")).replace("Z", "+00:00"))
    except Exception:
        return {"status": "UNKNOWN", "age_s": None, "source": str(STATUS_REL).replace("\\", "/")}
    age = int((now - ts).total_seconds())
    return {"status": "FRESH" if age <= HEARTBEAT_STALE_S else "STALE", "age_s": age, "stale_after_s": HEARTBEAT_STALE_S,
            "source": str(STATUS_REL).replace("\\", "/"), "equity_usd": s.get("realized_equity_usd")}


def adapter_preflight() -> dict[str, Any]:
    probe = {"symbol": "SPX", "side": "buy", "notional_usd": 5.0}
    controls = {
        "ccxt_sandbox_paper_routes": CCXTPaperAdapter().submit_order(**{**probe, "symbol": "BTC/USDT"}).oms_state,
        "ccxt_live_true_refused": CCXTPaperAdapter().submit_order(**{**probe, "symbol": "BTC/USDT"}, live=True).oms_state,
        "ccxt_sandbox_false_refused": CCXTPaperAdapter(sandbox=False).submit_order(**{**probe, "symbol": "BTC/USDT"}).oms_state,
        "ccxt_withdraw_refused": CCXTPaperAdapter(allow_withdraw=True).submit_order(**{**probe, "symbol": "BTC/USDT"}).oms_state,
        "ibkr_du_paper_routes": IBKRPaperAdapter(account_id="DU_PREFLIGHT_PLACEHOLDER").submit_order(**probe).oms_state,
        "ibkr_non_du_account_refused": IBKRPaperAdapter(account_id="U_LIVE_PLACEHOLDER").submit_order(**probe).oms_state,
        "ibkr_live_true_refused": IBKRPaperAdapter(account_id="DU_PREFLIGHT_PLACEHOLDER").submit_order(**probe, live=True).oms_state,
    }
    refused = all(v == "REJECTED_LIVE_FORBIDDEN" for k, v in controls.items() if k.endswith("_refused"))
    routes = all(v != "REJECTED_LIVE_FORBIDDEN" for k, v in controls.items() if k.endswith("_routes"))
    return {"negative_controls": controls, "live_paths_refused": refused, "paper_paths_route": routes,
            "verdict": "PREFLIGHT_PASS" if refused and routes else "PREFLIGHT_FAIL",
            "broker_connectivity": "NOT_VERIFIED",
            "broker_connectivity_reason": "stub paper adapters only; no IBKR TWS/Gateway session, no CCXT sandbox keys used in the box",
            "account_ids": "placeholders only (DU* pattern check); no real account id read"}


def build_session_readiness_drill(root: Path, *, quotes: dict[str, Any] | None = None,
                                  now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    sess = session_report(now)
    sessions: list[dict[str, Any]] = []
    for label_fa, venues, symbols in SESSION_BLOCKS:
        vs = [venue_status(v, now) for v in venues]
        nxt = min((v for v in vs if v["minutes_until_open"] is not None), key=lambda v: v["minutes_until_open"], default=None)
        mins = nxt["minutes_until_open"] if nxt else None
        sessions.append({
            "label_fa": label_fa,
            "symbols": list(symbols),
            "venues": vs,
            "open_now": any(v["open"] for v in vs),
            "next_open_utc": nxt["next_open_utc"] if nxt and mins else (now.strftime("%Y-%m-%dT%H:%M:%SZ") if mins == 0 else None),
            "next_open_tehran": nxt["next_open_tehran"] if nxt and mins else (now.astimezone(TEHRAN).strftime("%Y-%m-%d %H:%M") if mins == 0 else None),
            "minutes_until_open": mins,
            "countdown_fa": _countdown_fa(mins),
            "hours_until": round(mins / 60, 2) if mins is not None else None,
        })
    from architecture.markets.paper_trader import DESK_WEIGHTS

    hb = _heartbeat(root, now)
    notional = max(PAPER_NOTIONAL_FLOOR_USD, float(hb.get("equity_usd") or 0) * max(DESK_WEIGHTS.values()))
    adv_checks: dict[str, Any] = {}
    for sym in ("SPX", "BTC", "ETH", "BRENT", "XAU", "EURUSD"):
        q = (quotes or {}).get(sym)
        if not q:
            adv_checks[sym] = {"allowed": None, "status": "NO_QUOTE"}
            continue
        adv_checks[sym] = adv_cap_check(notional, q, q.get("ohlcv_5m") or [])
    pre = adapter_preflight()
    soonest = min((s for s in sessions if s["minutes_until_open"] is not None), key=lambda s: s["minutes_until_open"], default=sessions[0])
    payload = {
        "schema": "ahos.session_readiness_drill.v1",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "schedule_basis": SCHEDULE_BASIS,
        "session_gate": sess,
        "cash_sessions": sessions,
        "symbol_venues": dict(SYMBOL_VENUE),
        "adapters": {
            "ccxt_paper": {"oms_state": pre["negative_controls"]["ccxt_sandbox_paper_routes"], "sandbox": True},
            "ibkr_paper": {"oms_state": pre["negative_controls"]["ibkr_du_paper_routes"], "account": "DU* placeholder"},
            "preflight": pre,
        },
        "adv_cap_checks": adv_checks,
        "adv_cap_notional_usd": round(notional, 2),
        "daemon_heartbeat": hb,
        "summary_fa": (
            f"آمادگی پیش‌بازار: نزدیک‌ترین سشن {soonest['label_fa']} — {soonest['countdown_fa']}"
            + (f" (تهران {soonest['next_open_tehran']})" if soonest.get("next_open_tehran") else "") + ". "
            f"کنترل‌های منفی آداپتورهای کاغذی: {pre['verdict']}؛ اتصال واقعی کارگزار: NOT_VERIFIED. "
            f"ضربان دیمون: {hb['status']}. {sess.get('summary_fa', '')}"
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
