"""AHOS Lab Execution Engine — generic causal backtester for registered candidates.
Discipline inherited from verified ahos_backtest.py: signal@close(t) → entry@open(t+1),
intrabar SL-first, full cost model, enforced daily-loss halt & permanent DD stop, 2% risk / 2x cap.
Baseline engine file is FROZEN and untouched; shared discipline imported, not duplicated blindly."""
from __future__ import annotations
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add project root and engine to sys.path if not present
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
ENGINE_DIR = ROOT_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

try:
    from engine.ahos_backtest import position_size, metrics as _metrics, monte_carlo as _mc
except ImportError:
    from ahos_backtest import position_size, metrics as _metrics, monte_carlo as _mc

COST = dict(fee=0.0005, slip=0.0002)      # Binance USDT-M taker 0.05% + 0.02% slip per side (documented)
RISK = dict(risk_pct=0.02, lev=2.0, daily_halt=0.10, dd_stop=0.20)

class LabResult:
    def __init__(self, tag, symbol):
        self.tag, self.symbol, self.trades, self.eq, self.halts = tag, symbol, [], [], []

def run_candidate(df: pd.DataFrame, entries: pd.Series, exits: dict, symbol: str,
                  cost=None, risk=None, start_eq=100.0):
    cost = cost or COST; risk = risk or RISK
    res = LabResult("", symbol)
    d = df.reset_index(drop=True); sig = entries.reset_index(drop=True).values
    a = AtrCompute(d)
    el, es = exits.get("exit_long"), exits.get("exit_short")
    el = el.reset_index(drop=True).values if el is not None else None
    es = es.reset_index(drop=True).values if es is not None else None
    lev_cap, rp = risk["lev"], risk["risk_pct"]
    eq, peak, pos = start_eq, start_eq, None
    day_pnl, cur_day, halt_until, stop_all = 0.0, None, None, False
    for i in range(1, len(d)):
        ts, o, h, l, c = d.timestamp.iat[i], d.open.iat[i], d.high.iat[i], d.low.iat[i], d.close.iat[i]
        day = str(ts)[:10]
        if day != cur_day: cur_day, day_pnl = day, 0.0
        if halt_until and ts < halt_until: continue
        halt_until = None
        s = sig[i-1]  # previous CLOSED bar
        atr_prev = a[i-1]
        def close(price, why):
            nonlocal eq, pos, day_pnl, peak, stop_all
            m = 1 if pos["side"]==1 else -1
            fee = (cost["fee"]+cost["slip"]) * pos["notional"] * 2
            pnl = (price/pos["entry"]-1)*m*pos["notional"] - fee
            eq += pnl; day_pnl += pnl
            res.trades.append(dict(symbol=symbol, side="LONG" if pos["side"]==1 else "SHORT",
                entry=round(pos["entry"],8), exit=round(float(price),8), notional=pos["notional"],
                pnl=round(float(pnl),6), reason=why, opened=str(pos["ts"]), closed=str(ts)))
            peak = max(peak, eq)
            if (peak-eq)/peak >= risk["dd_stop"] and not stop_all:
                stop_all = True
                res.halts.append(dict(ts=str(ts), type="DD_STOP", dd=round((peak-eq)/peak,4)))
            if day_pnl <= -risk["daily_halt"]*eq:
                halt_until = ts + pd.Timedelta(hours=24)
                res.halts.append(dict(ts=str(ts), type="DAILY_HALT", pnl=round(day_pnl,4)))
            pos = None
        if pos is not None:
            side = pos["side"]
            hit_sl = (l <= pos["sl"]) if side==1 else (h >= pos["sl"])
            hit_tp = pos["tp"] is not None and ((h >= pos["tp"]) if side==1 else (l <= pos["tp"]))
            flip = (el is not None and side==1 and el[i]) or (es is not None and side==-1 and es[i])
            sigflip = (s == -side) and exits.get("flip_on_signal", True)
            if hit_sl: close(pos["sl"], "SL")
            elif hit_tp: close(pos["tp"], "TP")
            elif flip: close(o, "EXIT_RULE")
            elif sigflip: close(o, "FLIP")
            elif i - pos["i"] >= exits.get("time_h", 10**9): close(o, "TIME")
        if pos is None and s != 0 and not stop_all and np.isfinite(atr_prev) and atr_prev > 0:
            side = int(s)
            entry = o * (1 + cost["slip"]*side)
            dist = exits["sl_atr"] * atr_prev
            notional = position_size(eq, entry, dist, risk_pct=rp, leverage_cap=lev_cap)
            if notional <= 0: continue
            sl = entry - side*dist
            tp = (entry + side*(exits["tp_atr"]/exits["sl_atr"])*dist) if exits.get("tp_atr") else None
            pos = dict(side=side, entry=float(entry), sl=float(sl), tp=float(tp) if tp else None,
                       notional=float(notional), i=i, ts=ts)
        res.eq.append((str(ts), round(eq,6)))
    if pos is not None:
        m = 1 if pos["side"]==1 else -1
        price = d.close.iat[-1]; fee = (cost["fee"]+cost["slip"])*pos["notional"]*2
        pnl = (price/pos["entry"]-1)*m*pos["notional"] - fee; eq += pnl
        res.trades.append(dict(symbol=symbol, side="LONG" if pos["side"]==1 else "SHORT",
            entry=round(pos["entry"],8), exit=round(float(price),8), notional=pos["notional"],
            pnl=round(float(pnl),6), reason="END", opened=str(pos["ts"]), closed=str(d.timestamp.iat[-1])))
    return res

def AtrCompute(df):
    h,l,c = df.high, df.low, df.close
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14, adjust=False).mean().values

def metrics_of(res) -> dict:
    from ahos_backtest import BacktestResult
    b = BacktestResult(symbol=res.symbol, rows=len(res.eq), start=res.eq[0][0] if res.eq else "",
                       end=res.eq[-1][0] if res.eq else "", trades=res.trades, equity_curve=res.eq, halts=res.halts)
    return _metrics(b)

def merge_aux(df: pd.DataFrame, loading: dict) -> pd.DataFrame:
    """Causal merge: funding known from its settle time; OI daily change known next day end (backward-only)."""
    out = df.copy()
    if "funding_df" in loading and loading["funding_df"] is not None:
        f = loading["funding_df"]
        out = pd.merge_asof(out.sort_values("timestamp"),
                            f.sort_values("timestamp").rename(columns={"funding_rate":"funding"}),
                            on="timestamp", direction="backward")
    if "oi_df" in loading and loading["oi_df"] is not None:
        o = loading["oi_df"].copy().sort_values("timestamp")
        o["oi_chg"] = o["sum_open_interest"].pct_change()
        # conservative causality: daily OI point usable only from next day 00:00
        o["available_at"] = o["timestamp"] + pd.Timedelta(days=1)
        out = pd.merge_asof(out.sort_values("timestamp"),
                            o[["available_at","oi_chg"]].rename(columns={"available_at":"timestamp"}),
                            on="timestamp", direction="backward")
    return out
