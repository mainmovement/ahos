"""Paper leverage ladder for futures desks, plus a shadow high-leverage book.

The live book starts at 1x. It may step to 2x, then 3x, then 5x only when that
desk's own closes clear the evidence bar. A drawdown past the cap steps down
one rung. The shadow book replays the same open at 5x and 10x and does not
change live equity. Missing DSR or PBO is not a pass.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNGS = (1.0, 2.0, 3.0, 5.0)
SHADOW_LEVERAGES = (5.0, 10.0)
MIN_CLOSED = 30
DSR_MIN = 0.95
PBO_MAX = 0.5
# Same drawdown cap as the T0 exit-gate criterion. Not fit to this book.
MAX_DRAWDOWN = 0.15
FUTURES_DESKS = ("CRYPTO_FUTURES", "LISTED_FUTURES")
STATE_REL = Path("reports") / "grok" / "PAPER" / "leverage_ladder_state.json"
SHADOW_STATE_REL = Path("reports") / "grok" / "PAPER" / "shadow_leverage_book.json"
SHADOW_LOG_REL = Path("reports") / "grok" / "PAPER" / "shadow_leverage_book.jsonl"
REPORT_REL = Path("reports") / "grok" / "PAPER" / "leverage_books_report.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _write(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _snap(lev: float) -> float:
    best = RUNGS[0]
    for rung in RUNGS:
        if abs(float(lev) - rung) < 1e-9:
            return rung
        if rung < float(lev):
            best = rung
    return best


def _higher(lev: float) -> float:
    cur = _snap(lev)
    for rung in RUNGS:
        if rung > cur:
            return rung
    return cur


def _lower(lev: float) -> float:
    cur = _snap(lev)
    prev = RUNGS[0]
    for rung in RUNGS:
        if rung >= cur:
            return prev
        prev = rung
    return RUNGS[0]


def _max_drawdown(pnls: list[float]) -> float:
    eq = peak = 0.0
    worst = 0.0
    for x in pnls:
        eq += x
        peak = max(peak, eq)
        if peak > 0:
            worst = max(worst, (peak - eq) / peak)
    return worst


def _trade_leverage(row: dict[str, Any]) -> float:
    raw = row.get("leverage")
    if isinstance(raw, (int, float)) and raw > 0:
        return _snap(float(raw))
    return 1.0


def measure(pnls: list[float], trial_paths: list[list[float]] | None = None) -> dict[str, Any]:
    """DSR and PBO use the existing research functions. One path cannot pass them."""
    dsr = None
    pbo = None
    paths = [p for p in (trial_paths or []) if isinstance(p, list)]
    if len(paths) >= 2 and len(pnls) >= 10:
        from architecture.learning.walk_forward import deflated_sharpe, pbo_cscv, sharpe

        sharpes = [sharpe(p) for p in paths if len(p) >= 2]
        dsr = deflated_sharpe(pnls, len(paths), sharpes)
        width = min(len(p) for p in paths)
        if width >= 8:
            pbo = pbo_cscv([p[:width] for p in paths])
    dd = _max_drawdown(pnls)
    return {
        "closed": len(pnls),
        "dsr": dsr,
        "pbo": pbo,
        "max_drawdown_pct": round(dd * 100, 4),
        "dsr_measurable": isinstance(dsr, (int, float)),
        "pbo_measurable": isinstance(pbo, (int, float)),
        "min_closed": MIN_CLOSED,
        "dsr_min": DSR_MIN,
        "pbo_max": PBO_MAX,
        "max_drawdown_cap_pct": MAX_DRAWDOWN * 100,
    }


def evidence_passes(evidence: dict[str, Any]) -> bool:
    dsr, pbo = evidence.get("dsr"), evidence.get("pbo")
    dd = evidence.get("max_drawdown_pct")
    return (
        int(evidence.get("closed") or 0) >= MIN_CLOSED
        and isinstance(dsr, (int, float)) and float(dsr) > DSR_MIN
        and isinstance(pbo, (int, float)) and float(pbo) < PBO_MAX
        and isinstance(dd, (int, float)) and float(dd) <= MAX_DRAWDOWN * 100
    )


def rung_decision(current: float, evidence: dict[str, Any], drawdown: float) -> dict[str, Any]:
    cur = _snap(current)
    base = {
        "requested": cur,
        "evidence": evidence,
        "drawdown": round(float(drawdown), 6),
        "drawdown_cap": MAX_DRAWDOWN,
        "rungs": list(RUNGS),
        "shadow_leverages": list(SHADOW_LEVERAGES),
        "paper_only": True,
        "changes_live_equity": True,
    }
    if drawdown > MAX_DRAWDOWN:
        if cur > RUNGS[0]:
            nxt = _lower(cur)
            return {**base, "applied": nxt, "lock": "DRAWDOWN_STEP_DOWN", "previous": cur}
        return {**base, "applied": RUNGS[0], "lock": "DRAWDOWN_FLOOR", "previous": cur}
    if evidence_passes(evidence) and cur < RUNGS[-1]:
        nxt = _higher(cur)
        return {**base, "applied": nxt, "lock": "EVIDENCE_STEP_UP", "previous": cur}
    lock = "RUNG_HELD" if evidence_passes(evidence) else "EVIDENCE_INCOMPLETE"
    return {**base, "applied": cur, "lock": lock, "previous": cur}


def live_rung(root: Path, desk: str, closes: list[dict[str, Any]] | None = None, *,
              unrealized: float = 0.0, stamp: str = "", trial_paths: list[list[float]] | None = None) -> dict[str, Any]:
    path = Path(root) / STATE_REL
    state = _read(path)
    row = dict(state.get(desk) or {})
    if stamp and row.get("evaluated_at") == stamp and isinstance(row.get("last"), dict):
        return dict(row["last"])
    rung = _snap(float(row.get("rung") or 1.0))
    same = [t for t in (closes or []) if _trade_leverage(t) == rung and isinstance(t.get("realized_pnl_usd"), (int, float))]
    evidence = measure([float(t["realized_pnl_usd"]) for t in same], trial_paths)
    realized = sum(float(t["realized_pnl_usd"]) for t in (closes or []) if isinstance(t.get("realized_pnl_usd"), (int, float)))
    marked = realized + float(unrealized)
    peak = max(float(row.get("peak_pnl_usd") or 0.0), marked, 0.0)
    dd = (peak - marked) / peak if peak > 0 else 0.0
    decision = rung_decision(rung, evidence, dd)
    decision["desk"] = desk
    decision["peak_pnl_usd"] = round(peak, 6)
    decision["marked_pnl_usd"] = round(marked, 6)
    row.update({"rung": decision["applied"], "peak_pnl_usd": peak, "evaluated_at": stamp or _now(), "last": decision})
    state[desk] = row
    state["paper_only"] = True
    _write(path, state)
    return decision


def _mmr(desk: str) -> float:
    if desk == "CRYPTO_FUTURES":
        from architecture.markets.crypto_futures_paper import MAINTENANCE_MARGIN_RATE
        return MAINTENANCE_MARGIN_RATE
    from architecture.markets.listed_futures_paper import MAINTENANCE_MARGIN_RATE
    return MAINTENANCE_MARGIN_RATE


def _liquidation(desk: str, side: str, entry: float, leverage: float) -> float | None:
    mmr = _mmr(desk)
    if desk == "CRYPTO_FUTURES":
        from architecture.markets.crypto_futures_paper import liquidation_price
    else:
        from architecture.markets.listed_futures_paper import liquidation_price
    return liquidation_price(side, entry, leverage=leverage, mmr=mmr)


def mirror_shadow_open(root: Path, *, symbol: str, desk: str, side: str, margin_usd: float, price: float,
                       fee: float, slip: float, ts: float, opened_at: str, contract_month: str | None = None,
                       funding_rate: float | None = None, votes: list[dict[str, Any]] | None = None) -> None:
    """Open 5x and 10x shadow legs on the live signal. Live equity is not touched."""
    if desk not in FUTURES_DESKS or margin_usd <= 0 or price <= 0:
        return
    path = Path(root) / SHADOW_STATE_REL
    state = _read(path)
    legs = list(state.get("legs") or [])
    for lev in SHADOW_LEVERAGES:
        if any(x.get("symbol") == symbol and x.get("leverage") == lev and x.get("open") for x in legs):
            continue
        d = 1 if side == "LONG" else -1
        fill = price * (1 + slip * d)
        exposure = round(float(margin_usd) * lev, 6)
        qty = exposure / fill
        liq = _liquidation(desk, side, fill, lev)
        leg = {
            "open": True, "symbol": symbol, "desk": desk, "side": side, "leverage": lev,
            "margin_usd": round(float(margin_usd), 6), "exposure_usd": exposure, "qty": qty,
            "entry_price": round(fill, 6), "entry_fee_usd": round(exposure * fee, 6),
            "opened_ts": ts, "opened_at": opened_at, "funding_usd": 0.0, "funding_ts": ts,
            "funding_rate_8h": funding_rate, "mark_price": price,
            "liquidation_price": None if liq is None else round(liq, 8),
            "maintenance_margin_rate": _mmr(desk), "contract_month": contract_month,
            "fee": fee, "slip": slip,
            "families": votes or [], "changes_live_equity": False, "paper_only": True,
        }
        legs.append(leg)
        _append(Path(root) / SHADOW_LOG_REL, {"ts": opened_at, "event": "SHADOW_OPEN", **{k: leg[k] for k in
                ("symbol", "desk", "side", "leverage", "margin_usd", "exposure_usd", "entry_price", "liquidation_price")}})
    state["legs"] = legs
    state["paper_only"] = True
    state["changes_live_equity"] = False
    _write(path, state)


def _close_leg(leg: dict[str, Any], price: float, ts: float, reason: str, slip: float, fee: float) -> dict[str, Any]:
    from architecture.markets.crypto_futures_paper import funding_cashflow

    side = str(leg.get("side"))
    d = 1 if side == "LONG" else -1
    rate = leg.get("funding_rate_8h")
    last = leg.get("funding_ts") or leg.get("opened_ts")
    if isinstance(rate, (int, float)) and isinstance(last, (int, float)):
        cash = funding_cashflow(side, float(leg.get("exposure_usd") or 0), rate, ts - float(last))
        leg["funding_usd"] = round(float(leg.get("funding_usd") or 0) + cash, 6)
    exit_px = price * (1 - slip * d)
    qty = float(leg.get("qty") or 0)
    gross = (exit_px - float(leg.get("entry_price") or 0)) * qty * d
    exit_fee = exit_px * qty * fee
    pnl = round(gross - exit_fee - float(leg.get("entry_fee_usd") or 0) + float(leg.get("funding_usd") or 0), 6)
    leg["open"] = False
    leg["closed_at"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    leg["close_reason"] = reason
    leg["realized_pnl_usd"] = pnl
    leg["mark_price"] = price
    return leg


def mark_shadow_book(root: Path, quotes: dict[str, Any], ts: float, *,
                     fee_of: dict[str, float] | None = None, slip_of: dict[str, float] | None = None,
                     live_open: set[str] | None = None) -> None:
    path = Path(root) / SHADOW_STATE_REL
    state = _read(path)
    legs = list(state.get("legs") or [])
    if not legs:
        return
    fee_of = fee_of or {}
    slip_of = slip_of or {}
    for leg in legs:
        if not leg.get("open"):
            continue
        sym = str(leg.get("symbol"))
        q = quotes.get(sym) or {}
        price = q.get("price")
        if not isinstance(price, (int, float)) or price <= 0:
            continue
        if isinstance(q.get("funding_rate_8h"), (int, float)):
            leg["funding_rate_8h"] = q.get("funding_rate_8h")
        from architecture.markets.crypto_futures_paper import simulated_liquidation

        side = str(leg.get("side"))
        slip = float(leg.get("slip") if leg.get("slip") is not None else slip_of.get(sym) or 0.0)
        fee = float(leg.get("fee") if leg.get("fee") is not None else fee_of.get(sym) or 0.0)
        if simulated_liquidation(side, float(price), leg.get("liquidation_price")):
            _close_leg(leg, float(price), ts, "SIMULATED_LIQUIDATION", slip, fee)
            _append(Path(root) / SHADOW_LOG_REL, {"ts": leg.get("closed_at"), "event": "SHADOW_CLOSE", "symbol": sym,
                    "leverage": leg.get("leverage"), "reason": "SIMULATED_LIQUIDATION", "realized_pnl_usd": leg.get("realized_pnl_usd"),
                    "changes_live_equity": False})
            continue
        if live_open is not None and sym not in live_open:
            _close_leg(leg, float(price), ts, "MIRROR_CLOSE", slip, fee)
            _append(Path(root) / SHADOW_LOG_REL, {"ts": leg.get("closed_at"), "event": "SHADOW_CLOSE", "symbol": sym,
                    "leverage": leg.get("leverage"), "reason": "MIRROR_CLOSE", "realized_pnl_usd": leg.get("realized_pnl_usd"),
                    "changes_live_equity": False})
            continue
        from architecture.markets.crypto_futures_paper import funding_cashflow

        rate = leg.get("funding_rate_8h")
        last = leg.get("funding_ts") or leg.get("opened_ts")
        if isinstance(rate, (int, float)) and isinstance(last, (int, float)) and ts > float(last):
            cash = funding_cashflow(side, float(leg.get("exposure_usd") or 0), rate, ts - float(last))
            leg["funding_usd"] = round(float(leg.get("funding_usd") or 0) + cash, 6)
            leg["funding_ts"] = ts
        leg["mark_price"] = price
    state["legs"] = legs
    state["updated_at"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(path, state)


def books_report(root: Path, positions: dict[str, Any], closes: list[dict[str, Any]]) -> dict[str, Any]:
    ladder = _read(Path(root) / STATE_REL)
    shadow = _read(Path(root) / SHADOW_STATE_REL)
    legs = list(shadow.get("legs") or [])
    rows = []
    symbols = set(positions) | {str(x.get("symbol")) for x in legs}
    for sym in sorted(symbols):
        live = positions.get(sym)
        if live and live.get("desk") not in FUTURES_DESKS:
            continue
        row: dict[str, Any] = {"symbol": sym, "live": None, "shadow": {}}
        if live and live.get("desk") in FUTURES_DESKS:
            row["desk"] = live.get("desk")
            row["live"] = {
                "side": live.get("side"), "leverage": live.get("leverage") or 1.0,
                "notional_usd": live.get("notional_usd"), "exposure_usd": live.get("exposure_usd") or live.get("notional_usd"),
                "liquidation_price": live.get("liquidation_price"), "contract_month": live.get("contract_month"),
            }
        for lev in SHADOW_LEVERAGES:
            leg = next((x for x in legs if x.get("symbol") == sym and x.get("leverage") == lev), None)
            if leg is None:
                continue
            row["desk"] = row.get("desk") or leg.get("desk")
            row["shadow"][str(lev)] = {
                "open": bool(leg.get("open")), "side": leg.get("side"), "exposure_usd": leg.get("exposure_usd"),
                "liquidation_price": leg.get("liquidation_price"),
                "realized_pnl_usd": leg.get("realized_pnl_usd"), "funding_usd": leg.get("funding_usd"),
                "close_reason": leg.get("close_reason"), "families": leg.get("families") or [],
            }
        if row["live"] or row["shadow"]:
            rows.append(row)
    desks = {}
    for desk in FUTURES_DESKS:
        last = ((ladder.get(desk) or {}).get("last") or {})
        desk_closes = [t for t in closes if t.get("desk") == desk]
        realized = round(sum(float(x.get("realized_pnl_usd") or 0) for x in legs if x.get("desk") == desk and not x.get("open")), 6)
        desks[desk] = {
            "live_leverage": (ladder.get(desk) or {}).get("rung") or 1.0,
            "lock": last.get("lock") or "EVIDENCE_INCOMPLETE",
            "evidence": last.get("evidence"),
            "live_closed": len(desk_closes),
            "shadow_realized_pnl_usd": realized,
            "shadow_changes_live_equity": False,
        }
    doc = {
        "paper_only": True,
        "live_book": "1x until per-desk evidence; then 2x, 3x, 5x one rung at a time",
        "shadow_book": "5x and 10x on the same signal; funding, fees, and liquidation are simulated",
        "shadow_changes_live_equity": False,
        "desks": desks,
        "rows": rows,
        "updated_at": _now(),
    }
    _write(Path(root) / REPORT_REL, doc)
    return doc
