"""AHOS $100 compounding multi-market paper trader (PAPER_ONLY; no broker, no real money, no keys).

Spec sources: AHOS_TRADING_SKILLS_v2 (§0 two-source, §2 MTF, §3 order flow, §5 vol sizing, §6 Kelly gate,
§10 news filter, §11 gaps evidence-only, §12 kill switches, §13 evals), Master Map laws 6 (two-source witness)
and 7 (one hash-chained ledger), owner orders t605u-t607u.

One shared account (starts $100.00). Per cycle (default 300 s):
  1. fetch source A (Yahoo/CoinGecko) + source B (CNBC/Kraken); witness each instrument -> only VERIFIED trades;
  2. skip closed markets (last trade older than 20 min);
  3. signal brain -> weighted composite with per-signal contributions (logged so Kian can explain);
  4. enter only if |composite| >= ENTRY and the higher timeframe agrees, news is not strongly against,
     the kill switch is clear and no HALT stands in the mission ledger;
  5. size by volatility (risk 0.5% of CURRENT equity per trade, stop = max(1%, 2*ATR_1h)) x regime multiplier,
     capped by desk allocation -> profits are reinvested (compounding). Kelly sizing stays OFF until n >= 30 (§6);
  6. fills pay adverse slippage + fee per side; exits on stop / take (1.5x stop) / reversal / 24 h;
  7. every decision -> reports/grok/PAPER/paper_trades.jsonl; every fill also -> mission ledger (law 7);
  8. after each CLOSE the University lesson step updates per-signal hit stats and (n >= 10) bounded weights,
     versioned in signal_weights.json (reversible: every version is kept).
A simple rule set, not a proven edge: profitability cannot be judged before >= 30 closed trades over weeks.
"""
from __future__ import annotations

import json
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.markets import signal_brain as sb
from architecture.markets.paper_account import INITIAL_CAPITAL_USD, LEDGER_REL, load_paper_trades, paper_account_summary
from architecture.markets.second_source import fetch_second_sources, witness
from architecture.execution.gateway import PaperOrder
from architecture.markets.oms import route as oms_route

PAPER_ONLY: bool = True
PAPER_DIR = Path("reports") / "grok" / "PAPER"
STATE_REL = PAPER_DIR / "paper_positions.json"
STATUS_REL = PAPER_DIR / "paper_trader_status.json"
WEIGHTS_REL = PAPER_DIR / "signal_weights.json"
LESSONS_REL = PAPER_DIR / "signal_lessons.jsonl"
MISSION_LEDGER_REL = Path("data") / "mission_ledger" / "mission_ledger.jsonl"
M49_DB_REL = Path("data") / "mission_ledger" / "m49_lessons.sqlite"   # same store gold_paper.py uses
AGENT = "agent:paper_trader"

INSTRUMENTS: dict[str, tuple[str, float, float]] = {   # sym -> (desk, fee/side, slippage/side)
    "BTC": ("CRYPTO", 0.0010, 0.0005), "ETH": ("CRYPTO", 0.0010, 0.0005), "SOL": ("CRYPTO", 0.0010, 0.0008),
    "XAU": ("GOLD", 0.0004, 0.0003),
    "WTI": ("OIL", 0.0005, 0.0004), "BRENT": ("OIL", 0.0005, 0.0004),
    "SPX": ("US_EQUITIES", 0.0003, 0.0002), "QQQ": ("US_EQUITIES", 0.0003, 0.0002),
    "DAX": ("EU_EQUITIES", 0.0004, 0.0003),
    "N225": ("ASIA_EQUITIES", 0.0004, 0.0003), "HSI": ("ASIA_EQUITIES", 0.0004, 0.0003),
    "EURUSD": ("FOREX", 0.0002, 0.0001), "USDJPY": ("FOREX", 0.0002, 0.0001),
}
DESK_WEIGHTS = {"CRYPTO": 0.25, "GOLD": 0.15, "OIL": 0.15, "US_EQUITIES": 0.15,
                "EU_EQUITIES": 0.10, "ASIA_EQUITIES": 0.10, "FOREX": 0.10}
MAX_TRADE_AGE_S = 20 * 60
ENTRY = 0.25
RISK_PER_TRADE = 0.005
MIN_STOP, TAKE_MULT = 0.010, 1.5
MAX_HOLD_S = 24 * 3600
DAILY_LOSS_LIMIT, WEEKLY_LOSS_LIMIT = 0.03, 0.06
MAX_OPEN_NOTIONAL = 1.0          # 1x equity in total, no leverage


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: str | None) -> float | None:
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() if ts else None
    except ValueError:
        return None


def _save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except ValueError:
        return default


def _append(root: Path, rel: Path, row: dict[str, Any]) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


class _Ledger:
    """Law 7: fills go into the one hash-chained mission ledger; a standing HALT blocks new risk."""

    def __init__(self, root: Path, enabled: bool) -> None:
        self.led = None
        self.error = None
        if enabled:
            try:
                from architecture.mission.ledger import MissionLedger
                p = root / MISSION_LEDGER_REL
                p.parent.mkdir(parents=True, exist_ok=True)
                self.led = MissionLedger(p)
            except Exception as exc:  # pragma: no cover
                self.error = repr(exc)[:200]

    def halted(self) -> tuple[bool, str | None]:
        if not self.led:
            return False, None
        h, row = self.led.halted()
        return h, (str((row or {}).get("payload", row)) if h else None)

    def fill(self, row: dict[str, Any]) -> str | None:
        if not self.led:
            return None
        try:
            keep = {k: row[k] for k in ("event", "symbol", "desk", "side", "fill_price", "notional_usd", "ts", "reason",
                                         "realized_pnl_usd") if k in row}
            e = self.led.decision({"market": f"PAPER_TRADER:{row['symbol']}", "type": "PAPER_FILL", **keep}, agent=AGENT)
            return e.get("entry_hash")
        except Exception as exc:
            self.error = repr(exc)[:200]
            return None


EDGE_STATUS = "UNPROVEN_EDGE"
EDGE_STATUS_FA = "لبهٔ سودآوری اثبات‌نشده — این معامله‌گر کاغذی داده برای یادگیری جمع می‌کند، نه سیستم سودده"


def _edge_evidence(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, rel in (("m28_walk_forward", Path("reports/grok/M28/walk_forward_snapshot.json")),
                     ("batch4", Path("reports/grok/M28/batch4_research.json"))):
        try:
            s = json.loads((root / rel).read_text(encoding="utf-8"))
            c = s.get("candidates") or []
            out[key] = {"trials": len(c), "pbo": s.get("pbo_cscv"),
                        "passed": sum(1 for x in c if x.get("gate") == "PASS_STATS"),
                        "best_dsr": max([x.get("deflated_sharpe") or 0 for x in c], default=None)}
        except Exception:
            out[key] = None
    return out


def load_weights(root: Path) -> dict[str, Any]:
    w = _load(root / WEIGHTS_REL, None)
    if not isinstance(w, dict) or "weights" not in w:
        w = {"version": 1, "weights": dict(sb.DEFAULT_WEIGHTS), "stats": {}, "history": [],
             "rule": "after each CLOSE: hit-rate per signal; when n>=10, w = base*(0.5+hit), bounded [0.5x,1.5x]"}
    return w


def university_lesson(root: Path, w: dict[str, Any], close_row: dict[str, Any], contributions: list[dict[str, Any]]) -> None:
    """M49/M58-style lesson from a REAL closed paper trade -> bounded, versioned weight change."""
    win = close_row["realized_pnl_usd"] > 0
    direction = 1 if close_row["side"] == "LONG" else -1
    changed = {}
    for c in contributions:
        if abs(c["score"]) < 0.1:
            continue
        st = w["stats"].setdefault(c["signal"], {"n": 0, "hits": 0})
        agreed = (c["score"] * direction > 0)
        st["n"] += 1
        st["hits"] += int(agreed == win)
        if st["n"] >= 10:
            base = sb.DEFAULT_WEIGHTS.get(c["signal"], 0.05)
            new = round(base * max(0.5, min(1.5, 0.5 + st["hits"] / st["n"])), 4)
            if new != w["weights"].get(c["signal"]):
                changed[c["signal"]] = [w["weights"].get(c["signal"]), new]
                w["weights"][c["signal"]] = new
    if changed:
        w["history"].append({"version": w["version"], "weights": dict(w["weights"]), "at": close_row["closed_at"]})
        w["version"] += 1
    m49_id = None
    try:  # M49: the one lessons ledger (append-only hash chain, UNVERIFIED until reviewer 16)
        from architecture.learning.lessons_ledger import LessonsLedger
        store = LessonsLedger(root / M49_DB_REL)
        try:
            top = sorted(contributions, key=lambda c: -abs(c.get("contribution", 0)))[:3]
            m49_id = f"PT-{close_row['symbol']}-{close_row['closed_at']}"
            store.append(lesson_id=m49_id, source="paper_trader", market=close_row["desk"].lower(),
                         taxonomy="paper_trade_outcome",
                         evidence_refs=[f"paper_trades.jsonl:{close_row['symbol']}:{close_row['closed_at']}",
                                        f"mission_ledger:{close_row.get('ledger_hash') or 'none'}"],
                         claim=f"{close_row['side']} {close_row['symbol']} {'won' if win else 'lost'} "
                               f"{close_row['realized_pnl_usd']} USD ({close_row['reason']}); top signals: "
                               + ", ".join(f"{c['signal']}={c['contribution']}" for c in top),
                         counterfactual="no trade (flat) = 0 USD; " + ("signals agreed with outcome" if win else "signals disagreed with outcome"),
                         valid_from=close_row["closed_at"])
        finally:
            store.close()
    except Exception as exc:  # never block trading on the lesson store
        m49_id = f"ERROR:{repr(exc)[:120]}"
    _append(root, LESSONS_REL, {"m49_lesson_id": m49_id, "ts": close_row["closed_at"], "symbol": close_row["symbol"], "win": win,
                                "pnl_usd": close_row["realized_pnl_usd"], "signals": contributions,
                                "weights_changed": changed, "weights_version": w["version"], "paper_only": True})
    _save_json(root / WEIGHTS_REL, w)


def performance(trades: list[dict[str, Any]], seed: int = 7) -> dict[str, Any]:
    """§13 evals from real closed paper trades (bootstrap 95% CI on expectancy)."""
    p = [float(t["realized_pnl_usd"]) for t in trades]
    n = len(p)
    if not n:
        return {"n": 0, "note": "no closed trades yet"}
    wins = [x for x in p if x > 0]
    losses = [x for x in p if x <= 0]
    mean = sum(p) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in p) / (n - 1)) if n > 1 else 0.0
    dsd = math.sqrt(sum(min(0.0, x) ** 2 for x in p) / n)
    eq, peak, mdd = INITIAL_CAPITAL_USD, INITIAL_CAPITAL_USD, 0.0
    for x in p:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)
    rnd = random.Random(seed)
    boots = sorted(sum(rnd.choice(p) for _ in range(n)) / n for _ in range(500)) if n > 1 else [mean]
    return {"n": n, "hit_rate": round(len(wins) / n, 3), "expectancy_usd": round(mean, 4),
            "expectancy_ci95": [round(boots[int(0.025 * len(boots))], 4), round(boots[int(0.975 * len(boots)) - 1], 4)],
            "profit_factor": round(sum(wins) / -sum(losses), 3) if losses and sum(losses) < 0 else None,
            "sharpe_per_trade": round(mean / sd, 3) if sd else None, "sortino_per_trade": round(mean / dsd, 3) if dsd else None,
            "max_drawdown_pct": round(mdd * 100, 2),
            "promotion_gate": "NOT_ELIGIBLE (needs >= 30 closed trades, CI lower bound > 0, DSR > 0.95)" if n < 30 else "EVALUATE"}


def kill_switch(trades: list[dict[str, Any]], equity: float, now: float) -> tuple[bool, str | None]:
    day = sum(float(t["realized_pnl_usd"]) for t in trades if (_parse(t.get("closed_at")) or 0) > now - 86400)
    week = sum(float(t["realized_pnl_usd"]) for t in trades if (_parse(t.get("closed_at")) or 0) > now - 7 * 86400)
    if day < -DAILY_LOSS_LIMIT * equity:
        return True, f"DAILY_LOSS {day:.2f} < -{DAILY_LOSS_LIMIT:.0%}"
    if week < -WEEKLY_LOSS_LIMIT * equity:
        return True, f"WEEKLY_LOSS {week:.2f} < -{WEEKLY_LOSS_LIMIT:.0%}"
    return False, None


def _atr_pct(ohlcv: list[list[float]]) -> float | None:
    h1 = sb.resample(sb.closed(ohlcv), 12)[-14:]
    if len(h1) < 5:
        return None
    trs = []
    for i in range(1, len(h1)):
        _, h, l, _, _ = h1[i]
        pc = h1[i - 1][3]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return (sum(trs) / len(trs)) / h1[-1][3]


def run_cycle(root: Path, *, fetch: Callable[[], dict[str, Any]] | None = None,
              fetch_b: Callable[[], dict[str, Any]] | None = None, signals_fn: Callable[..., list[dict[str, Any]]] | None = None,
              now: Callable[[], float] = time.time, use_ledger: bool = True) -> dict[str, Any]:
    if fetch is None:
        from architecture.markets.live_price_feed import fetch_live_market_prices as fetch
    t = now()
    quotes = (fetch() or {}).get("quotes") or {}
    second = (fetch_b or fetch_second_sources)()
    wit = {s: witness(s, quotes.get(s), second.get(s)) for s in set(INSTRUMENTS) | {"DXY", "US10Y"}}
    state = _load(root / STATE_REL, {})
    state.setdefault("positions", {})
    state.setdefault("brain", {})
    weights = load_weights(root)
    try:  # Stage 3: research -> trader only through the versioned, reversible promotion switch
        from architecture.learning import strategy_switch as _sw
        live_weights, switch_version = _sw.apply(weights["weights"], root)
    except Exception:
        live_weights, switch_version = dict(weights["weights"]), 0
    ledger = _Ledger(root, use_ledger)
    trades = load_paper_trades(root)
    equity = float(paper_account_summary(root)["current_equity_usd"])
    halted, halt_reason = ledger.halted()
    killed, kill_reason = kill_switch(trades, equity, t)
    news = [] if signals_fn else sb.fetch_news()
    positions: dict[str, Any] = state["positions"]
    per_desk_n = {d: sum(1 for v in INSTRUMENTS.values() if v[0] == d) for d in DESK_WEIGHTS}
    events: list[dict[str, Any]] = []

    def log(row: dict[str, Any]) -> None:
        _append(root, LEDGER_REL, row)
        events.append(row)

    for sym, (desk, fee, slip) in INSTRUMENTS.items():
        q = quotes.get(sym) or {}
        price = q.get("price")
        w = wit[sym]
        base = {"ts": _iso(t), "symbol": sym, "desk": desk, "paper_only": True, "source": q.get("source"),
                "market_time": q.get("market_time"), "witness": {k: w[k] for k in ("verdict", "source_b", "price_b", "gap")}}
        mt = _parse(q.get("market_time"))
        pos = positions.get(sym)
        if not isinstance(price, (int, float)) or price <= 0:
            log({**base, "event": "SKIP", "reason": "PRICE_UNAVAILABLE"}); continue
        if mt is None or t - mt > MAX_TRADE_AGE_S:
            log({**base, "event": "SKIP", "reason": "MARKET_CLOSED_OR_STALE", "price": price}); continue
        if w["verdict"] != "VERIFIED" and not pos:
            log({**base, "event": "SKIP", "reason": f"WITNESS_{w['verdict']}", "price": price}); continue
        ohlcv = q.get("ohlcv_5m") or []
        if signals_fn:
            sigs = signals_fn(sym, desk, q)
        else:
            sigs = [sb.mtf_trend(ohlcv), sb.candle_patterns(ohlcv), sb.zscore_mr(ohlcv), sb.news_signal(desk, news),
                    sb.macro_pressure(desk, quotes, wit), sb.macro_event(desk, root)]
            if desk == "CRYPTO":
                sigs += [sb.order_flow(sym), sb.large_trades(sym), sb.funding_oi(sym), sb.stablecoin_flow(state["brain"]),
                         sb.exchange_netflow(sym), sb.whale_mempool(sym), sb.stablecoin_impulse(sym)]
        regime = sb.vol_regime(ohlcv)
        comb = sb.combine(sigs, live_weights)
        comp = comb["composite"]
        mtf = next((s for s in sigs if s["name"] == "mtf_trend"), None)
        higher = (mtf or {}).get("evidence", {}).get("higher_tf_sign")
        newsig = next((s for s in sigs if s["name"] == "news"), None)
        brain = {"composite": comp, "contributions": comb["contributions"], "regime": regime,
                 "signals": [{k: s[k] for k in ("name", "score", "available", "source", "spec", "evidence")} for s in sigs],
                 "weights_version": weights["version"]}
        if pos:
            side = pos["side"]
            d = 1 if side == "LONG" else -1
            move = (price - pos["entry_price"]) / pos["entry_price"] * d
            reason = None
            if move <= -pos["stop_pct"]: reason = "STOP_LOSS"
            elif move >= pos["stop_pct"] * TAKE_MULT: reason = "TAKE_PROFIT"
            elif comp * d <= -ENTRY: reason = "SIGNAL_REVERSAL"
            elif t - pos["opened_ts"] > MAX_HOLD_S: reason = "MAX_HOLD"
            elif w["verdict"] == "CONFLICT": reason = "WITNESS_CONFLICT_EXIT"
            if not reason:
                pos["mark_price"] = price
                log({**base, "event": "HOLD", "side": side, "price": price, "move_pct": round(move * 100, 3),
                     "composite": comp, "top_contributions": comb["contributions"][:4]})
                continue
            oms = oms_route(PaperOrder(desk.lower(), "sell" if d > 0 else "buy", pos["notional_usd"], False), "ELIGIBLE")
            exit_px = price * (1 - slip * d)
            gross = (exit_px - pos["entry_price"]) * pos["qty"] * d
            exit_fee = exit_px * pos["qty"] * fee
            pnl = round(gross - exit_fee - pos["entry_fee_usd"], 4)
            row = {**base, "event": "CLOSE", "side": side, "reason": reason, "quote_price": price,
                   "fill_price": round(exit_px, 6), "entry_price": pos["entry_price"], "qty": pos["qty"],
                   "notional_usd": pos["notional_usd"], "fees_usd": round(exit_fee + pos["entry_fee_usd"], 6),
                   "slippage_pct": slip, "opened_at": pos["opened_at"], "closed_at": _iso(t), "realized_pnl_usd": pnl,
                   "entry_brain": pos.get("entry_brain"), "exit_composite": comp, "oms": oms.state}
            row["ledger_hash"] = ledger.fill(row)
            log(row)
            university_lesson(root, weights, row, (pos.get("entry_brain") or {}).get("contributions") or [])
            equity += pnl
            del positions[sym]
            continue
        side = "LONG" if comp >= ENTRY else "SHORT" if comp <= -ENTRY else None
        why = None
        if halted: why = f"LEDGER_HALT:{halt_reason}"
        elif killed: why = f"KILL_SWITCH:{kill_reason}"
        elif not side: why = "COMPOSITE_BELOW_ENTRY"
        elif higher is not None and (1 if side == "LONG" else -1) != higher: why = "HIGHER_TF_DISAGREES"
        elif newsig and newsig["available"] and newsig["score"] * (1 if side == "LONG" else -1) < -0.5: why = "NEWS_EVENT_RISK"
        elif desk == "CRYPTO" and not next((s["evidence"].get("spread_gate_ok", True) for s in sigs if s["name"] == "order_flow"), True):
            why = "SPREAD_GATE"
        if why:
            log({**base, "event": "NO_TRADE", "reason": why, "price": price, "composite": comp,
                 "top_contributions": comb["contributions"][:5], "regime": regime["regime"]}); continue
        atr = _atr_pct(ohlcv) or MIN_STOP
        stop_pct = max(MIN_STOP, 2 * atr)
        desk_cap = equity * DESK_WEIGHTS[desk] / per_desk_n[desk]
        notional = min(equity * RISK_PER_TRADE / stop_pct * regime["size_mult"], desk_cap * regime["size_mult"])
        open_now = sum(p["notional_usd"] for p in positions.values())
        notional = round(min(notional, MAX_OPEN_NOTIONAL * equity - open_now), 4)
        if notional < 0.5:
            log({**base, "event": "NO_TRADE", "reason": "ALLOCATION_EXHAUSTED", "composite": comp}); continue
        d = 1 if side == "LONG" else -1
        oms = oms_route(PaperOrder(desk.lower(), "buy" if d > 0 else "sell", notional, False), "ELIGIBLE")
        if oms.state != "ACCEPTED_PAPER":
            log({**base, "event": "NO_TRADE", "reason": f"OMS_{oms.state}:{oms.reason}", "composite": comp}); continue
        fill = price * (1 + slip * d)
        qty = notional / fill
        entry_fee = notional * fee
        positions[sym] = {"side": side, "entry_price": round(fill, 6), "qty": qty, "notional_usd": notional,
                          "entry_fee_usd": round(entry_fee, 6), "opened_at": _iso(t), "opened_ts": t, "desk": desk,
                          "stop_pct": round(stop_pct, 5), "entry_brain": brain, "mark_price": price}
        row = {**base, "event": "OPEN", "side": side, "quote_price": price, "fill_price": round(fill, 6), "qty": qty,
               "notional_usd": notional, "fee_usd": round(entry_fee, 6), "slippage_pct": slip, "stop_pct": round(stop_pct, 5),
               "take_pct": round(stop_pct * TAKE_MULT, 5), "equity_at_open_usd": round(equity, 4), "brain": brain,
               "kelly": "OFF (n<30 closed trades, §6)", "oms": "ACCEPTED_PAPER"}
        row["ledger_hash"] = ledger.fill(row)
        log(row)

    unreal = 0.0
    for sym, p in positions.items():
        mp = p.get("mark_price") or p["entry_price"]
        unreal += (mp - p["entry_price"]) * p["qty"] * (1 if p["side"] == "LONG" else -1) - p["entry_fee_usd"]
    _save_json(root / STATE_REL, state)
    acct = paper_account_summary(root)
    trades = load_paper_trades(root)
    status = {
        "updated_at": _iso(t), "paper_only": True, "initial_capital_usd": INITIAL_CAPITAL_USD,
        "realized_equity_usd": acct["current_equity_usd"], "unrealized_pnl_usd": round(unreal, 4),
        "mark_to_market_equity_usd": round(acct["current_equity_usd"] + unreal, 4), "closed_trades": acct["trade_count"],
        "open_positions": {s: {k: v for k, v in p.items() if k != "entry_brain"} | {"top_contributions": (p.get("entry_brain") or {}).get("contributions", [])[:4]}
                           for s, p in positions.items()},
        "per_desk_realized_pnl_usd": acct["per_desk_realized_pnl_usd"], "performance": performance(trades),
        "witness": {s: {k: w[k] for k in ("verdict", "price_a", "price_b", "source_a", "source_b", "gap")} for s, w in wit.items()},
        "halted": halted, "halt_reason": halt_reason, "kill_switch": killed, "kill_reason": kill_reason,
        "ledger_error": ledger.error, "weights_version": weights["version"], "weights": weights["weights"],
        "last_cycle": {"opens": sum(e["event"] == "OPEN" for e in events), "closes": sum(e["event"] == "CLOSE" for e in events),
                       "skips": [f"{e['symbol']}:{e['reason']}" for e in events if e["event"] in ("SKIP", "NO_TRADE")]},
        "news_items": len(news),
        "strategy": "multi-signal composite (MTF trend, candles/wicks, z-score, order flow, large trades, funding/OI, "
                    "stablecoin, macro, news) | two-source witness | vol-sized, compounding | stop max(1%,2xATR1h), take 1.5x",
        "honesty_note": "Paper only. Short record; not evidence of profitability. Closed markets and unverified prices are not traded.",
        "edge_status": EDGE_STATUS, "edge_status_fa": EDGE_STATUS_FA, "edge_evidence": _edge_evidence(root),
        "strategy_switch_version": switch_version,
        "shadow_signals": sorted(k for k, v in live_weights.items() if not v),
    }
    _save_json(root / STATUS_REL, status)
    return status
