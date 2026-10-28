"""Shared logic for live witness probe + tradable-session gate (PAPER_ONLY)."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
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
    if age < 0:
        return False, "QUOTE_TIME_AHEAD"
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
    root: Path | None = None,
    witnesses: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    t = now if now is not None else time.time()
    sess = session_report(fetch_ts)
    weekend = bool(sess.get("weekend_tehran"))
    by_desk: dict[str, list[dict[str, Any]]] = {}
    verified_desks: set[str] = set()
    tradable_desks: set[str] = set()
    for sym, (desk, _fee, _slip) in instruments.items():
        q = quotes.get(sym) or {}
        w = (witnesses or {}).get(sym) or witness(sym, q, second.get(sym))
        ok, reason = tradable_for_paper(desk, w["verdict"], q, now=t, weekend_tehran=weekend)
        row = {
            "symbol": sym,
            "verdict": w["verdict"],
            "gap": w.get("gap"),
            "source_a": w.get("source_a"),
            "source_b": w.get("source_b"),
            "source_c": w.get("source_c"),
            "pair": w.get("pair"),
            "contract_month_a": w.get("contract_month_a"),
            "diagnostics": w.get("diagnostics"),
            "quote_age_s": quote_age_seconds(q, t),
            "tradable_for_paper": ok,
            "tradable_reason": reason,
        }
        by_desk.setdefault(desk, []).append(row)
        if w["verdict"] == "VERIFIED":
            verified_desks.add(desk)
        if ok:
            tradable_desks.add(desk)
    payload: dict[str, Any] = {
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
    if root is not None:
        from architecture.markets.session_readiness_drill import build_session_readiness_drill

        drill = build_session_readiness_drill(root, quotes=quotes)
        payload["session_readiness_drill"] = {
            "summary_fa": drill.get("summary_fa"),
            "cash_sessions": drill.get("cash_sessions"),
            "adapters": drill.get("adapters"),
            "adv_cap_checks": drill.get("adv_cap_checks"),
        }
    return payload


def build_weekday_two_source_audit(root: Path, now: datetime | None = None) -> dict[str, Any]:
    """Session clock for now, plus the stored witness only as a stale or fresh label.

    A stored VERIFIED quote older than the paper freshness window is not a live witness.
    Cash desks on a Tehran weekend are not tradable. This function does not fetch prices.
    """
    import json

    from architecture.markets.paper_trader import INSTRUMENTS, MAX_TRADE_AGE_S
    from architecture.markets.weekday_session_gate import CASH_DESKS, SYMBOL_VENUE

    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    sess = session_report(moment)
    venues = sess.get("venues") if isinstance(sess.get("venues"), dict) else {}
    probe_path = root / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    probe: dict[str, Any] = {}
    if probe_path.is_file():
        try:
            loaded = json.loads(probe_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                probe = loaded
        except ValueError:
            probe = {}
    stored: dict[str, dict[str, Any]] = {}
    for rows in (probe.get("by_desk") or {}).values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and row.get("symbol"):
                stored[str(row["symbol"])] = row
    probe_utc = ((probe.get("session_gate") or {}) if isinstance(probe.get("session_gate"), dict) else {}).get("utc")
    probe_epoch = _parse(probe_utc) if isinstance(probe_utc, str) else None
    probe_age_s = None if probe_epoch is None else moment.timestamp() - probe_epoch
    probe_stale = probe_age_s is None or probe_age_s < 0 or probe_age_s > MAX_TRADE_AGE_S
    weekend = bool(sess.get("weekend_tehran"))
    out_rows = []
    for sym, (desk, _fee, _slip) in INSTRUMENTS.items():
        venue = SYMBOL_VENUE.get(sym)
        venue_row = venues.get(venue) if venue else None
        session_open = bool(venue_row.get("open")) if isinstance(venue_row, dict) else False
        prior = stored.get(sym) or {}
        stored_verdict = prior.get("verdict") if prior else None
        if probe_stale:
            live_witness = "STALE_STORED_PROBE" if stored_verdict else "NO_STORED_PROBE"
        elif stored_verdict in ("VERIFIED", "CONFLICT", "UNRESOLVED"):
            live_witness = stored_verdict
        else:
            live_witness = "NO_STORED_PROBE"
        if weekend and desk in CASH_DESKS:
            reason = "WEEKEND_CASH_SESSION"
        elif venue and not session_open:
            reason = "SESSION_CLOSED"
        elif live_witness != "VERIFIED":
            reason = live_witness
        else:
            reason = "OK"
        tradable = reason == "OK"
        out_rows.append({
            "symbol": sym,
            "desk": desk,
            "venue": venue,
            "session_open": session_open,
            "stored_verdict": stored_verdict,
            "live_witness": live_witness,
            "probe_stale": probe_stale,
            "tradable_for_paper": tradable,
            "tradable_reason": reason,
        })
    cash_open = [r["symbol"] for r in out_rows if r["desk"] in CASH_DESKS and r["session_open"]]
    snap = {
        "schema": "ahos.weekday_two_source_audit.v1",
        "generated_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "network_fetch": False,
        "weekend_tehran": weekend,
        "tehran_weekday": sess.get("tehran_weekday"),
        "probe_as_of": probe_utc,
        "probe_age_s": None if probe_age_s is None else round(probe_age_s, 1),
        "probe_stale": probe_stale,
        "symbols": [r["symbol"] for r in out_rows],
        "cash_symbols_open": cash_open,
        "tradable_symbols": [r["symbol"] for r in out_rows if r["tradable_for_paper"]],
        "rows": out_rows,
        "summary_fa": sess.get("summary_fa"),
    }
    path = root / "reports" / "grok" / "PAPER" / "weekday_two_source_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
