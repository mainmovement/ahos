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
from architecture.markets.second_source import (FUTURES, fetch_second_sources, fetch_third_sources,
                                                 third_source_needed, witness)
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
    "UNI": ("PB_TOKEN", 0.0015, 0.0010),
    "XAU": ("GOLD", 0.0004, 0.0003),
    "WTI": ("OIL", 0.0005, 0.0004), "BRENT": ("OIL", 0.0005, 0.0004),
    "SPX": ("US_EQUITIES", 0.0003, 0.0002), "QQQ": ("US_EQUITIES", 0.0003, 0.0002),
    "DAX": ("EU_EQUITIES", 0.0004, 0.0003),
    "N225": ("ASIA_EQUITIES", 0.0004, 0.0003), "HSI": ("ASIA_EQUITIES", 0.0004, 0.0003),
    "EURUSD": ("FOREX", 0.0002, 0.0001), "USDJPY": ("FOREX", 0.0002, 0.0001),
}
DESK_WEIGHTS = {"CRYPTO": 0.25, "PB_TOKEN": 0.05, "GOLD": 0.15, "OIL": 0.15, "US_EQUITIES": 0.15,
                "EU_EQUITIES": 0.10, "ASIA_EQUITIES": 0.10, "FOREX": 0.10}
CLUSTER_OF_DESK = {
    "CRYPTO": "crypto", "PB_TOKEN": "crypto",
    "GOLD": "metals", "OIL": "energy",
    "US_EQUITIES": "equities", "EU_EQUITIES": "equities", "ASIA_EQUITIES": "equities",
    "FOREX": "fx",
}
CLUSTER_CAPS = {"crypto": 0.35, "metals": 0.20, "energy": 0.20, "equities": 0.40, "fx": 0.15}


def logged_witness(witness: dict) -> dict:
    """Copy the fields the paper log is allowed to keep.

    Tolerance and pair are copied only when the witness already has them.
    A pair that carries an address is left off the log. The exit rule does
    not read this copy.
    """
    out = {k: witness[k] for k in ("verdict", "source_b", "price_b", "gap")}
    for key in ("tolerance", "pair"):
        value = witness.get(key)
        if value is None:
            continue
        if key == "pair" and isinstance(value, str) and ("0x" in value.lower() or "pool32:" in value):
            continue
        out[key] = value
    return out


def logged_source(source: object) -> str | None:
    """Keep the venue label. A source that carries an address is reduced to that label."""
    if source is None:
        return None
    text = str(source)
    if "0x" in text.lower() or "pool32:" in text.lower():
        kind = text.split(":", 1)[0]
        if not kind or "0x" in kind.lower():
            return None
        return kind
    return text


MAX_TRADE_AGE_S = 20 * 60
ENTRY = 0.25
RISK_PER_TRADE = 0.005
MIN_STOP, TAKE_MULT = 0.010, 1.5
MAX_HOLD_S = 24 * 3600
CHANDELIER_ATR_MULT = 3.0
PARTIAL_FRACTION = 0.5
TIME_STOP_HOLD_FRAC = 0.5
TIME_STOP_MOVE_FRAC = 0.25
DAILY_LOSS_LIMIT, WEEKLY_LOSS_LIMIT = 0.03, 0.06
MAX_OPEN_NOTIONAL = 1.0          # 1x equity in total, no leverage
EXIT_REASONS = (
    "STOP_LOSS", "TAKE_PROFIT", "PARTIAL_TAKE_PROFIT", "CHANDELIER_STOP",
    "SIGNAL_REVERSAL", "TIME_STOP", "MAX_HOLD", "WITNESS_CONFLICT_EXIT",
)
LESSON_COUNTERFACTUAL = "no trade (flat) = 0 USD; the trade sign is not a count of signal votes"


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
                         counterfactual=LESSON_COUNTERFACTUAL,
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
            "promotion_gate": "NOT_ELIGIBLE (needs >= 30 closed trades, CI lower bound > 0, DSR > 0.95)"}



def mc_risk_of_ruin(trades: list[dict[str, Any]], equity: float = 100.0, *, ruin_dd: float = 0.20, paths: int = 1000, horizon_trades: int = 50, seed: int = 42) -> dict[str, Any]:
    """TS-12 & M21: 1,000-path block-bootstrap Monte Carlo risk-of-ruin estimator."""
    pnls = [float(t.get("realized_pnl_usd", 0.0)) for t in trades]
    # When n < 5 closed trades, use conservative per-trade risk distribution (±0.5% equity stop)
    sample = pnls if len(pnls) >= 5 else [-0.50, -0.45, 0.55, -0.48, 0.65, -0.50, 0.60, -0.42]
    rnd = random.Random(seed)
    ruin_floor = equity * (1.0 - ruin_dd)
    ruined = 0
    max_dds: list[float] = []
    for _ in range(paths):
        eq = equity
        peak = equity
        mdd = 0.0
        hit_ruin = False
        for _ in range(horizon_trades):
            eq += rnd.choice(sample)
            if eq > peak:
                peak = eq
            dd = (peak - eq) / max(1e-6, peak)
            if dd > mdd:
                mdd = dd
            if eq <= ruin_floor:
                hit_ruin = True
                break
        if hit_ruin:
            ruined += 1
        max_dds.append(mdd)
    max_dds.sort()
    p95_dd = max_dds[int(0.95 * len(max_dds))] if max_dds else 0.0
    return {
        "paths": paths,
        "horizon_trades": horizon_trades,
        "ruin_drawdown_threshold_pct": round(ruin_dd * 100, 1),
        "ruin_probability": round(ruined / max(1, paths), 4),
        "p95_max_drawdown_pct": round(p95_dd * 100, 2),
        "empirical_trades_used": len(pnls),
        "empirical": len(pnls) >= 5,
        "basis": "EMPIRICAL_CLOSED_TRADES" if len(pnls) >= 5 else
                 "POLICY_STRESS_PRIOR (±0.5% equity stop per RISK_PER_TRADE; not observed trades)",
    }


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


def _mark_excursion(pos: dict[str, Any], price: float, atr_pct: float) -> float:
    """Update the path high-water and the chandelier. The stop only tightens."""
    entry = float(pos["entry_price"])
    d = 1 if pos["side"] == "LONG" else -1
    move = (price - entry) / entry * d
    pos["mfe"] = move if pos.get("mfe") is None else max(float(pos["mfe"]), move)
    pos["mae"] = move if pos.get("mae") is None else min(float(pos["mae"]), move)
    pos["path_points"] = int(pos.get("path_points") or 0) + 1
    stop_pct = float(pos["stop_pct"])
    atr_abs = max(0.0, float(atr_pct)) * price
    if pos["side"] == "LONG":
        pos["peak_price"] = max(float(pos.get("peak_price") or price), price)
        hard = entry * (1.0 - stop_pct)
        trail = float(pos["peak_price"]) - CHANDELIER_ATR_MULT * atr_abs
        pos["chandelier_stop"] = max(hard, trail)
    else:
        pos["trough_price"] = min(float(pos.get("trough_price") or price), price)
        hard = entry * (1.0 + stop_pct)
        trail = float(pos["trough_price"]) + CHANDELIER_ATR_MULT * atr_abs
        pos["chandelier_stop"] = min(hard, trail)
    return move


def _chandelier_hit(pos: dict[str, Any], price: float) -> bool:
    stop = pos.get("chandelier_stop")
    if not isinstance(stop, (int, float)):
        return False
    entry = float(pos["entry_price"])
    stop_pct = float(pos["stop_pct"])
    if pos["side"] == "LONG":
        hard = entry * (1.0 - stop_pct)
        return price <= float(stop) and float(stop) > hard + 1e-12
    hard = entry * (1.0 + stop_pct)
    return price >= float(stop) and float(stop) < hard - 1e-12


def gather_witness(quotes: dict[str, Any], *, fetch_b: Callable[[], dict[str, Any]] | None = None,
                   fetch_c: Callable[[list[str]], dict[str, Any]] | None = None,
                   symbols: set[str] | None = None) -> dict[str, dict[str, Any]]:
    """A (execution feed) vs B (same contract month) vs lazy C (independent vendor) -> witness per symbol."""
    syms = symbols or (set(INSTRUMENTS) | {"DXY", "US10Y"})
    if fetch_b is not None:
        second = fetch_b()
    else:
        months = {s: (quotes.get(s) or {}).get("contract_month") for s in FUTURES}
        second = fetch_second_sources(contract_months={s: m for s, m in months.items() if m})
    pre = {s: witness(s, quotes.get(s), second.get(s)) for s in syms}
    if fetch_c is not None:
        third = fetch_c(third_source_needed(pre))
    elif fetch_b is None:
        third = fetch_third_sources(third_source_needed(pre))
    else:
        third = {}
    return {s: (witness(s, quotes.get(s), second.get(s), third.get(s)) if s in third else pre[s]) for s in syms}


DEX_FEE, DEX_SLIP = 0.0030, 0.0020   # AMM pool fee + conservative slippage per side


def live_dex_feed(root: Path, positions: dict[str, Any]) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    """M33 -> PB_TOKEN: fresh vetted tokens with a distinct-pool witness, plus every open DEX position (exit path)."""
    from architecture.markets import token_safety_live as tsl
    want = {f"DEX_{t['symbol']}": t for t in tsl.load_eligible_paper_tokens(root)}
    for sym, p in positions.items():
        if sym.startswith("DEX_") and p.get("token_address") and p.get("dex_pool"):
            want.setdefault(sym, {"symbol": sym[4:], "address": p["token_address"], "pool": p["dex_pool"]})
    out = {}
    for sym, tok in want.items():
        try:
            out[sym] = tsl.dex_paper_quote(tok)
        except Exception:
            continue
    return out


def run_cycle(root: Path, *, fetch: Callable[[], dict[str, Any]] | None = None,
              fetch_b: Callable[[], dict[str, Any]] | None = None, signals_fn: Callable[..., list[dict[str, Any]]] | None = None,
              now: Callable[[], float] = time.time, use_ledger: bool = True,
              fetch_c: Callable[[list[str]], dict[str, Any]] | None = None,
              dex_feed: Callable[[Path, dict[str, Any]], dict[str, tuple[dict[str, Any], dict[str, Any]]]] | None = None) -> dict[str, Any]:
    if fetch is None:
        from architecture.markets.live_price_feed import fetch_live_market_prices as fetch
    t = now()
    quotes = (fetch() or {}).get("quotes") or {}
    wit = gather_witness(quotes, fetch_b=fetch_b, fetch_c=fetch_c)
    state = _load(root / STATE_REL, {})
    state.setdefault("positions", {})
    state.setdefault("brain", {})
    if dex_feed is None and fetch_b is None and signals_fn is None:
        dex_feed = live_dex_feed
    dex = dex_feed(root, state["positions"]) if dex_feed else {}
    for sym, (dq, dw) in dex.items():
        quotes[sym], wit[sym] = dq, dw
    instruments = {**INSTRUMENTS, **{s: ("PB_TOKEN", DEX_FEE, DEX_SLIP) for s in dex}}
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
    per_desk_n = {d: max(1, sum(1 for v in instruments.values() if v[0] == d)) for d in DESK_WEIGHTS}
    events: list[dict[str, Any]] = []

    def log(row: dict[str, Any]) -> None:
        _append(root, LEDGER_REL, row)
        events.append(row)

    for sym, (desk, fee, slip) in instruments.items():
        q = quotes.get(sym) or {}
        price = q.get("price")
        w = wit[sym]
        base = {"ts": _iso(t), "symbol": sym, "desk": desk, "paper_only": True, "source": logged_source(q.get("source")),
                "market_time": q.get("market_time"), "witness": logged_witness(w)}
        mt = _parse(q.get("market_time"))
        pos = positions.get(sym)
        if not isinstance(price, (int, float)) or price <= 0:
            log({**base, "event": "SKIP", "reason": "PRICE_UNAVAILABLE"}); continue
        age = None if mt is None else t - mt
        if age is None or age > MAX_TRADE_AGE_S or age < 0:
            from architecture.markets.weekday_session_gate import symbol_session
            gate = symbol_session(sym, datetime.fromtimestamp(t, tz=timezone.utc))
            opened = gate.get("open")
            session_state = "OPEN" if opened is True else "CLOSED" if opened is False else "UNKNOWN"
            ahead = age is not None and age < 0
            log({**base, "event": "SKIP", "reason": "QUOTE_TIME_AHEAD" if ahead else "MARKET_CLOSED_OR_STALE",
                 "price": price, "freshness": "UNKNOWN" if age is None or ahead else "STALE",
                 "session_state": session_state})
            continue
        if w["verdict"] != "VERIFIED" and not pos:
            log({**base, "event": "SKIP", "reason": f"WITNESS_{w['verdict']}", "price": price}); continue
        ohlcv = q.get("ohlcv_5m") or []
        if signals_fn:
            sigs = signals_fn(sym, desk, q)
        else:
            sigs = [sb.mtf_trend(ohlcv), sb.candle_patterns(ohlcv), sb.zscore_mr(ohlcv), sb.news_signal(desk, news),
                    sb.macro_pressure(desk, quotes, wit), sb.macro_event(desk, root), sb.event_shock(desk, sym, root)]
            if desk == "CRYPTO":
                fund_hist = state["brain"].setdefault("funding_history", {}).setdefault(sym, [])
                sigs += [sb.order_flow(sym), sb.large_trades(sym), sb.funding_oi(sym, fund_hist), sb.stablecoin_flow(state["brain"]),
                         sb.exchange_netflow(sym), sb.whale_mempool(sym), sb.stablecoin_impulse(sym)]
        regime = sb.vol_regime(ohlcv)
        oflow = next((s for s in sigs if s["name"] == "order_flow"), None)
        if oflow and (oflow.get("evidence") or {}).get("depth_disagreement"):
            regime["size_mult"] = round(float(regime.get("size_mult") or 1.0) * 0.5, 4)
            regime["depth_disagreement_haircut"] = True
        comb = sb.combine(sigs, live_weights)
        comp = comb["composite"]
        mtf = next((s for s in sigs if s["name"] == "mtf_trend"), None)
        higher = (mtf or {}).get("evidence", {}).get("higher_tf_sign")
        newsig = next((s for s in sigs if s["name"] == "news"), None)
        brain = {"composite": comp, "contributions": comb["contributions"], "regime": regime,
                 "signals": [{k: s[k] for k in ("name", "score", "available", "source", "spec", "evidence")} for s in sigs],
                 "weights_version": weights["version"]}
        scores = {s["name"]: round(float(s["score"]), 4) for s in sigs if s.get("available")}
        if pos:
            side = pos["side"]
            d = 1 if side == "LONG" else -1
            atr_pct = _atr_pct(ohlcv) or float(pos["stop_pct"]) / 2.0
            move = _mark_excursion(pos, price, atr_pct)
            held_s = t - pos["opened_ts"]
            reason = None
            partial = False
            if move <= -pos["stop_pct"]:
                reason = "STOP_LOSS"
            elif move >= pos["stop_pct"] * TAKE_MULT:
                reason = "TAKE_PROFIT"
            elif not pos.get("partial_taken") and move >= pos["stop_pct"]:
                reason = "PARTIAL_TAKE_PROFIT"
                partial = True
            elif _chandelier_hit(pos, price):
                reason = "CHANDELIER_STOP"
            elif comp * d <= -ENTRY:
                reason = "SIGNAL_REVERSAL"
            elif held_s > MAX_HOLD_S * TIME_STOP_HOLD_FRAC and abs(move) < TIME_STOP_MOVE_FRAC * pos["stop_pct"]:
                reason = "TIME_STOP"
            elif held_s > MAX_HOLD_S:
                reason = "MAX_HOLD"
            elif w["verdict"] == "CONFLICT":
                reason = "WITNESS_CONFLICT_EXIT"
            if not reason:
                pos["mark_price"] = price
                log({**base, "event": "HOLD", "side": side, "price": price, "move_pct": round(move * 100, 3),
                     "composite": comp, "top_contributions": comb["contributions"][:4], "signal_scores": scores,
                     "chandelier_stop": pos.get("chandelier_stop"), "mfe": pos.get("mfe"), "mae": pos.get("mae")})
                continue
            fraction = PARTIAL_FRACTION if partial else 1.0
            oms = oms_route(PaperOrder(desk.lower(), "sell" if d > 0 else "buy", pos["notional_usd"] * fraction, False), "ELIGIBLE")
            exit_px = price * (1 - slip * d)
            qty_close = pos["qty"] * fraction
            gross = (exit_px - pos["entry_price"]) * qty_close * d
            exit_fee = exit_px * qty_close * fee
            entry_fee_part = pos["entry_fee_usd"] * fraction
            pnl = round(gross - exit_fee - entry_fee_part, 4)
            row = {**base, "event": "CLOSE", "side": side, "reason": reason, "partial": partial, "quote_price": price,
                   "fill_price": round(exit_px, 6), "entry_price": pos["entry_price"], "qty": qty_close,
                   "notional_usd": round(pos["notional_usd"] * fraction, 4),
                   "fees_usd": round(exit_fee + entry_fee_part, 6),
                   "slippage_pct": slip, "opened_at": pos["opened_at"], "closed_at": _iso(t), "realized_pnl_usd": pnl,
                   "mae": None if pos.get("mae") is None else round(float(pos["mae"]), 6),
                   "mfe": None if pos.get("mfe") is None else round(float(pos["mfe"]), 6),
                   "path_points": int(pos.get("path_points") or 0),
                   "entry_brain": pos.get("entry_brain"), "exit_composite": comp, "oms": oms.state}
            row["ledger_hash"] = ledger.fill(row)
            log(row)
            university_lesson(root, weights, row, (pos.get("entry_brain") or {}).get("contributions") or [])
            equity += pnl
            if partial:
                pos["qty"] = pos["qty"] - qty_close
                pos["notional_usd"] = round(pos["notional_usd"] * (1.0 - fraction), 4)
                pos["entry_fee_usd"] = round(pos["entry_fee_usd"] - entry_fee_part, 6)
                pos["partial_taken"] = True
                pos["mark_price"] = price
            else:
                del positions[sym]
            continue
        from architecture.markets.weekday_session_gate import CASH_DESKS, symbol_session
        moment = datetime.fromtimestamp(t, tz=timezone.utc)
        gate = symbol_session(sym, moment)
        session_gate = {"evaluated": True, "venue": gate.get("venue"), "open": gate.get("open") is True}
        if desk in CASH_DESKS and session_gate["open"] is not True:
            age = None if mt is None else t - mt
            if age is None or age < 0:
                freshness = "UNKNOWN"
            elif age > MAX_TRADE_AGE_S:
                freshness = "STALE"
            else:
                freshness = "FRESH"
            log({**base, "event": "SKIP", "reason": "SESSION_CLOSED", "session_gate": session_gate,
                 "freshness": freshness, "session_state": "CLOSED"})
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
        elif desk == "CRYPTO":
            fund = next((s for s in sigs if s["name"] == "funding_oi"), None)
            z = ((fund or {}).get("evidence") or {}).get("funding_z")
            if isinstance(z, (int, float)) and ((side == "LONG" and z >= 2.0) or (side == "SHORT" and z <= -2.0)):
                why = "FUNDING_CROWDING"
        elif desk == "PB_TOKEN" and signals_fn is None:
            from architecture.markets.token_safety_live import veto_check as _tok_veto
            tv = _tok_veto(sym[4:] if sym.startswith("DEX_") else sym, q.get("token_address"),
                           strict=bool(q.get("token_address")))
            brain["token_safety_veto"] = {k: tv.get(k) for k in ("verdict", "allowed", "sources_verified", "reasons")}
            if not tv.get("allowed"):
                why = f"TOKEN_SAFETY_VETO:{','.join(tv.get('reasons') or ['fail_closed'])}"
        if why:
            log({**base, "event": "NO_TRADE", "reason": why, "price": price, "composite": comp,
                 "top_contributions": comb["contributions"][:5], "regime": regime["regime"], "signal_scores": scores}); continue
        atr = _atr_pct(ohlcv) or MIN_STOP
        stop_pct = max(MIN_STOP, 2 * atr)
        desk_cap = equity * DESK_WEIGHTS[desk] / per_desk_n[desk]
        shock = next((s for s in sigs if s["name"] == "event_shock"), None)
        event_size = min(1.0, float(((shock or {}).get("evidence") or {}).get("size_mult") or 1.0))
        brain["event_size_mult"] = event_size
        notional = min(equity * RISK_PER_TRADE / stop_pct * regime["size_mult"], desk_cap * regime["size_mult"]) * event_size
        cluster = CLUSTER_OF_DESK.get(desk, "other")
        cluster_open = sum(p["notional_usd"] for p in positions.values() if CLUSTER_OF_DESK.get(p.get("desk", ""), "") == cluster)
        cluster_rem = max(0.0, CLUSTER_CAPS.get(cluster, 0.35) * equity - cluster_open)
        open_now = sum(p["notional_usd"] for p in positions.values())
        notional = round(min(notional, cluster_rem, MAX_OPEN_NOTIONAL * equity - open_now), 4)
        adv_chk = sb.adv_cap_check(notional, q, ohlcv)
        brain["adv_cap"] = adv_chk
        if not adv_chk["allowed"]:
            notional = round(min(notional, adv_chk["cap_1pct_usd"]), 4)
        if notional < 0.5:
            log({**base, "event": "NO_TRADE", "reason": "ALLOCATION_EXHAUSTED", "composite": comp}); continue
        try:
            from architecture.markets.council_gate import soroush_blind_debate_and_bl
            brain["council_debate"] = soroush_blind_debate_and_bl(
                symbol=sym,
                bull_prob=max(0.05, min(0.95, 0.5 + 0.4 * comp)),
                bear_prob=max(0.05, min(0.95, 0.5 - 0.4 * comp)),
                bull_evidence_refs=[f"{s['name']}:{s['source']}" for s in sigs if s["available"] and s["score"] > 0] or [f"witness:{w['source_a']}"],
                bear_evidence_refs=[f"{s['name']}:{s['source']}" for s in sigs if s["available"] and s["score"] < 0] or [f"witness:{w['source_b']}"],
                devils_advocate_dissent=f"Counter-case for {side} {sym}: macro/regime reversal or spread widening beyond {stop_pct:.2%} stop",
            )
        except Exception:
            pass
        d = 1 if side == "LONG" else -1
        oms = oms_route(PaperOrder(desk.lower(), "buy" if d > 0 else "sell", notional, False), "ELIGIBLE")
        if oms.state != "ACCEPTED_PAPER":
            log({**base, "event": "NO_TRADE", "reason": f"OMS_{oms.state}:{oms.reason}", "composite": comp}); continue
        fill = price * (1 + slip * d)
        qty = notional / fill
        entry_fee = notional * fee
        positions[sym] = {"side": side, "entry_price": round(fill, 6), "qty": qty, "notional_usd": notional,
                          "entry_fee_usd": round(entry_fee, 6), "opened_at": _iso(t), "opened_ts": t, "desk": desk,
                          "stop_pct": round(stop_pct, 5), "entry_brain": brain, "mark_price": price,
                          **({"token_address": q["token_address"], "dex_pool": q.get("dex_pool")} if q.get("token_address") else {})}
        row = {**base, "event": "OPEN", "side": side, "quote_price": price, "fill_price": round(fill, 6), "qty": qty,
               "notional_usd": notional, "fee_usd": round(entry_fee, 6), "slippage_pct": slip, "stop_pct": round(stop_pct, 5),
               "take_pct": round(stop_pct * TAKE_MULT, 5), "equity_at_open_usd": round(equity, 4), "brain": brain,
               "kelly": "OFF (a close count does not switch Kelly on)", "oms": "ACCEPTED_PAPER",
               "session_gate": session_gate}
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
        "witness": {s: {k: w.get(k) for k in ("verdict", "price_a", "price_b", "source_a", "source_b", "gap", "price_c",
                                               "source_c", "pair", "n_sources", "contract_month_a", "diagnostics")}
                    for s, w in wit.items()},
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
        "risk_of_ruin_mc": mc_risk_of_ruin(trades, acct["current_equity_usd"]),
        "cluster_exposure_usd": {
            cl: round(sum(p["notional_usd"] for p in positions.values() if CLUSTER_OF_DESK.get(p.get("desk", ""), "") == cl), 4)
            for cl in CLUSTER_CAPS
        },
    }
    _save_json(root / STATUS_REL, status)
    if signals_fn is None and any(e["event"] in ("OPEN", "CLOSE") for e in events):
        try:
            from architecture.markets.paper_trade_audit import export_paper_trade_audit_snapshot
            from architecture.learning.shadow_forward_scorecard import export_shadow_forward_scorecard
            from architecture.health.unification_audit import export_unification_audit
            export_paper_trade_audit_snapshot(root)
            export_shadow_forward_scorecard(root)
            export_unification_audit(root)
        except Exception:
            pass
    return status
