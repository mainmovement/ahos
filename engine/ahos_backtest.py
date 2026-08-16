#!/usr/bin/env python3
"""AHOS Backtest Engine v1.0 — Agent-02 (Strategy) + Agent-08 (Risk) + Agent-09 (QA).
Event-driven, no look-ahead, fixed parameters per STRATEGY_SPEC_v1.0.
Real data only. Deterministic (seeded Monte Carlo)."""
from __future__ import annotations
import json, math
from dataclasses import dataclass, field, asdict
import numpy as np
import pandas as pd

# ---- Fixed parameters (FROZEN — STRATEGY_SPEC_v1.0) ----
P = dict(
    ema_len=20, atr_len=14, vol_sma_len=20, vol_mult=1.2,
    sl_atr=1.5, tp_atr=2.0, time_stop_h=72, leverage=2.0,
    risk_pct=0.02, fee_taker=0.00055, slippage=0.0002,
    max_positions=3, daily_loss_cap=0.10, dd_cap=0.20,
)

def position_size(equity: float, entry: float, sl_distance: float,
                  risk_pct: float | None = None, leverage_cap: float | None = None) -> float:
    """Agent-08 Risk Manager — pure function. Returns allowed notional.
    notional = (risk_pct*equity) / (sl_distance/entry), hard-capped at leverage_cap*equity."""
    rp = P["risk_pct"] if risk_pct is None else risk_pct
    lv = P["leverage"] if leverage_cap is None else leverage_cap
    if equity <= 0 or entry <= 0 or sl_distance <= 0: return 0.0
    return min(rp*equity / (sl_distance/entry), lv*equity)

def leverage_allowed(confidence: float, trend_strong: bool, micro_mode: bool = True) -> float:
    """Leverage ladder from TRADING_INTELLIGENCE_PLAN Section 4 / Risk layer.
    Micro-capital mode ($10-$15): hard 2x. Standard: 5x default; 10x only conf>0.85+trend."""
    if micro_mode: return 2.0
    if confidence > 0.85 and trend_strong: return 10.0
    return 5.0

def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["open","high","low","close"]).reset_index(drop=True)

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema"] = df["close"].ewm(span=P["ema_len"], adjust=False).mean()
    # Wilder ATR
    h,l,c = df["high"], df["low"], df["close"]
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(alpha=1/P["atr_len"], adjust=False).mean()
    df["vol_sma"] = df["volume"].rolling(P["vol_sma_len"]).mean()
    return df

@dataclass
class Position:
    side: str; entry: float; sl: float; tp: float; qty: float; notional: float
    opened_i: int; opened_ts: str

@dataclass
class BacktestResult:
    symbol: str; rows: int; start: str; end: str
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)
    halts: list = field(default_factory=list)

def run_backtest(df: pd.DataFrame, symbol: str, start_equity: float = 100.0):
    """start_equity=100 USDT normalized (capital path-agnostic %; micro $10 scenario scales linearly)."""
    df = add_indicators(df)
    bt = BacktestResult(symbol=symbol, rows=len(df),
                        start=str(df.timestamp.iloc[0]), end=str(df.timestamp.iloc[-1]))
    eq = start_equity; peak = start_equity
    pos: Position | None = None
    day_pnl = 0.0; cur_day = None; halted_until = None
    halted_permanent = False  # Agent-08: DD-cap breach = full stop (was record-only before audit fix)

    for i in range(1, len(df)):
        ts = df.timestamp.iloc[i]; o,h,l,c = (df.iloc[i][k] for k in ("open","high","low","close"))
        atr = df.atr.iloc[i-1]; ema = df.ema.iloc[i-1]; vsma = df.vol_sma.iloc[i-1]
        pc = df.close.iloc[i-1]; pv = df.volume.iloc[i-1]  # previous CLOSED candle for signals
        day = str(ts)[:10]
        if day != cur_day: cur_day, day_pnl = day, 0.0
        if halted_until and ts < halted_until: continue
        halted_until = None

        sig_long  = (pc > ema) and (pv > P["vol_mult"]*vsma) and np.isfinite(atr) and atr>0
        sig_short = (pc < ema) and (pv > P["vol_mult"]*vsma) and np.isfinite(atr) and atr>0

        def close_pos(price, reason):
            nonlocal eq, pos, day_pnl, peak, halted_permanent
            side_mult = 1 if pos.side=="LONG" else -1
            raw = (price/pos.entry - 1) * side_mult
            fee = (P["fee_taker"]+P["slippage"]) * pos.notional * 2  # entry+exit cost
            pnl = raw * pos.notional - fee
            eq += pnl; day_pnl += pnl
            bt.trades.append(dict(symbol=symbol, side=pos.side, entry=pos.entry, exit=round(float(price),8),
                qty=pos.qty, notional=pos.notional, pnl=round(float(pnl),6),
                pnl_pct_on_margin=round(float(pnl/(pos.notional/P["leverage"]))*100,4),
                reason=reason, opened=pos.opened_ts, closed=str(ts), bars=i-pos.opened_i))
            peak = max(peak, eq)
            if (peak-eq)/peak >= P["dd_cap"] and not halted_permanent:
                halted_permanent = True
                bt.halts.append(dict(ts=str(ts), type="MAX_DRAWDOWN_HALT", dd=round((peak-eq)/peak,4),
                                     effect="NO NEW POSITIONS for remainder of run (DD cap breached)"))
            if day_pnl <= -P["daily_loss_cap"] * eq:
                halted_until = ts + pd.Timedelta(hours=24)
                bt.halts.append(dict(ts=str(ts), type="DAILY_LOSS_HALT", day_pnl=round(day_pnl,4)))
            pos = None

        # manage open position (intrabar conservative: SL first)
        if pos:
            side_mult = 1 if pos.side=="LONG" else -1
            hit_sl = (l <= pos.sl) if pos.side=="LONG" else (h >= pos.sl)
            hit_tp = (h >= pos.tp) if pos.side=="LONG" else (l <= pos.tp)
            price, reason = None, None
            if hit_sl: price, reason = pos.sl, "SL"
            elif hit_tp: price, reason = pos.tp, "TP"
            elif i - pos.opened_i >= P["time_stop_h"]: price, reason = o, "TIME"
            elif (sig_short and pos.side=="LONG") or (sig_long and pos.side=="SHORT"):
                price, reason = o, "FLIP"
            if price is not None: close_pos(price, reason)

        # new entry at bar open (no open position, daily halt inactive, DD-stop inactive)
        if pos is None and (sig_long or sig_short) and not halted_permanent:
            side = "LONG" if sig_long else "SHORT"
            entry = o * (1 + P["slippage"]*(1 if side=="LONG" else -1))
            dist = P["sl_atr"] * atr
            if dist <= 0: continue
            # Risk sizing via Agent-08 pure function (single source of truth)
            notional = position_size(eq, entry, dist)
            if notional <= 0: continue
            qty = notional / entry
            sl = entry - dist if side=="LONG" else entry + dist
            tp = entry + (P["tp_atr"]/P["sl_atr"])*dist if side=="LONG" else entry - (P["tp_atr"]/P["sl_atr"])*dist
            pos = Position(side, float(entry), float(sl), float(tp), float(qty), float(notional), i, str(ts))
        bt.equity_curve.append((str(ts), round(eq,6)))
    # force close at end
    if pos:
        ts = df.timestamp.iloc[-1]
        side_mult = 1 if pos.side=="LONG" else -1
        price = df.close.iloc[-1]; fee = (P["fee_taker"]+P["slippage"])*pos.notional*2
        pnl = (price/pos.entry-1)*side_mult*pos.notional - fee; eq += pnl
        bt.trades.append(dict(symbol=symbol, side=pos.side, entry=pos.entry, exit=float(price),
            qty=pos.qty, notional=pos.notional, pnl=round(float(pnl),6),
            pnl_pct_on_margin=round(float(pnl/(pos.notional/P["leverage"]))*100,4),
            reason="END", opened=pos.opened_ts, closed=str(ts), bars=len(df)-1-pos.opened_i))
    return bt

def metrics(bt: BacktestResult) -> dict:
    tr = bt.trades
    if not tr: return {"symbol": bt.symbol, "trades": 0}
    wins = [t for t in tr if t["pnl"] > 0]; losses = [t for t in tr if t["pnl"] <= 0]
    gw = sum(t["pnl"] for t in wins); gl = -sum(t["pnl"] for t in losses)
    eqs = pd.Series([e for _,e in bt.equity_curve]) if bt.equity_curve else pd.Series([100.0])
    rets = eqs.pct_change().dropna()
    peak = eqs.cummax(); dd = ((peak-eqs)/peak).max()
    sharpe = float(rets.mean()/rets.std()*math.sqrt(24*365)) if len(rets)>2 and rets.std()>0 else None
    return dict(symbol=bt.symbol, rows=bt.rows, start=bt.start, end=bt.end,
        trades=len(tr), win_rate=round(len(wins)/len(tr)*100,2),
        avg_win=round(float(np.mean([t["pnl"] for t in wins])),4) if wins else 0.0,
        avg_loss=round(float(np.mean([t["pnl"] for t in losses])),4) if losses else 0.0,
        profit_factor=round(gw/gl,3) if gl>0 else None,
        expectancy=round(float(np.mean([t["pnl"] for t in tr])),5),
        total_pnl=round(sum(t["pnl"] for t in tr),4),
        total_return_pct=round((eqs.iloc[-1]/100-1)*100,3) if len(eqs) else 0.0,
        max_drawdown_pct=round(float(dd)*100,2), sharpe_annualized=round(sharpe,3) if sharpe else None,
        halts=bt.halts)

def monte_carlo(trades, n=1000, seed=42):
    rng = np.random.default_rng(seed)
    pnls = np.array([t["pnl"] for t in trades])
    finals, maxdds = [], []
    for _ in range(n):
        seq = rng.choice(pnls, size=len(pnls), replace=True)
        curve = 100 + np.cumsum(seq)
        finals.append(curve[-1]-100)
        maxdds.append(float((np.maximum.accumulate(curve)-curve).max()))
    finals, maxdds = np.array(finals), np.array(maxdds)
    return dict(simulations=n, positive_outcomes_pct=round(float((finals>0).mean())*100,2),
        p5_pnl=round(float(np.percentile(finals,5)),3), median_pnl=round(float(np.median(finals)),3),
        p95_pnl=round(float(np.percentile(finals,95)),3),
        p95_maxdd=round(float(np.percentile(maxdds,95)),3), prob_dd_gt_20pct=round(float((maxdds>20).mean())*100,2))

def walk_forward(df, symbol, train=960, test=240, step=240):
    """train 40d / test 10d rolling (adapted to 83-day availability — documented limitation)."""
    windows, i = [], 0
    while i + train + test <= len(df):
        tr = df.iloc[i:i+train]; te = df.iloc[i+train:i+train+test]
        m_tr = metrics(run_backtest(tr, symbol)); m_te = metrics(run_backtest(pd.concat([tr.tail(60), te]), symbol))
        windows.append(dict(window=len(windows)+1, train=f"{tr.timestamp.iloc[0]}→{tr.timestamp.iloc[-1]}",
            test=f"{te.timestamp.iloc[0]}→{te.timestamp.iloc[-1]}",
            train_wr=m_tr.get("win_rate"), train_pf=m_tr.get("profit_factor"),
            test_wr=m_te.get("win_rate"), test_pf=m_te.get("profit_factor"),
            test_trades=m_te.get("trades")))
        i += step
    return windows
