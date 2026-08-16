"""AHOS Lab — candidate signal generators. CAUSAL ONLY (no look-ahead):
all series at index i depend exclusively on rows[0..i]. Entry fires on NEXT bar open."""
from __future__ import annotations
import numpy as np
import pandas as pd

def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def sma(s, n): return s.rolling(n).mean()
def atr(df, n=14):
    h,l,c = df.high, df.low, df.close
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()
def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0); dn = -d.clip(upper=0)
    rs = up.ewm(alpha=1/n, adjust=False).mean() / dn.ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100/(1+rs)
def adx(df, n=14):
    h,l,c = df.high, df.low, df.close
    up = h.diff(); dn = -l.diff()
    pdm = np.where((up>dn)&(up>0), up, 0.0); mdm = np.where((dn>up)&(dn>0), dn, 0.0)
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    a = tr.ewm(alpha=1/n, adjust=False).mean()
    pdi = 100*pd.Series(pdm,index=df.index).ewm(alpha=1/n,adjust=False).mean()/a
    mdi = 100*pd.Series(mdm,index=df.index).ewm(alpha=1/n,adjust=False).mean()/a
    dx = 100*(pdi-mdi).abs()/(pdi+mdi)
    return dx.ewm(alpha=1/n, adjust=False).mean()

# Each generator returns (entries: Series in {+1,-1,0}, exits: dict)
def gen_H1(df):
    hi55 = df.close.rolling(55).max().shift(1); lo55 = df.close.rolling(55).min().shift(1)
    hi20 = df.close.rolling(20).max().shift(1); lo20 = df.close.rolling(20).min().shift(1)
    e = pd.Series(0, index=df.index)
    e[df.close > hi55] = 1; e[df.close < lo55] = -1
    ex = dict(sl_atr=2.0, tp_atr=None, time_h=20*24,
              exit_long=df.close < lo20, exit_short=df.close > hi20)
    return e, ex

def gen_H2(df):
    m = sma(df.close,20); sd = df.close.rolling(20).std()
    z = (df.close-m)/sd
    e = pd.Series(0, index=df.index)
    e[z <= -2] = 1; e[z >= 2] = -1
    ex = dict(sl_atr=2.0, tp_atr=None, time_h=72, exit_long=z >= 0, exit_short=z <= 0)
    return e, ex

def gen_H3(df):
    a = atr(df); squeeze = a/sma(a,100) < 0.8
    hi20 = df.high.rolling(20).max().shift(1); lo20 = df.low.rolling(20).min().shift(1)
    e = pd.Series(0, index=df.index)
    e[squeeze & (df.close > hi20)] = 1; e[squeeze & (df.close < lo20)] = -1
    return e, dict(sl_atr=1.5, tp_atr=3.0, time_h=48, exit_long=None, exit_short=None)

def gen_H4(df):
    ax = adx(df); e50 = ema(df.close,50); e20 = ema(df.close,20)
    e = pd.Series(0, index=df.index)
    e[(ax>25)&(df.close>e50)&(df.low<=e20)] = 1
    e[(ax>25)&(df.close<e50)&(df.high>=e20)] = -1
    return e, dict(sl_atr=1.5, tp_atr=2.5, time_h=96, exit_long=None, exit_short=None)

def gen_H5(df):  # needs df['funding'] already merged (backward fill from known values ONLY)
    f = df["funding"]; a = atr(df); sm = sma(df.close,200)
    e = pd.Series(0, index=df.index)
    e[(f <= -0.0001)&(df.close > sm)] = 1
    e[(f >=  0.0001)&(df.close < sm)] = -1
    ex = dict(sl_atr=2.0, tp_atr=None, time_h=96, exit_long=f >= 0, exit_short=f <= 0)
    return e, ex

def gen_H6(df):  # needs df['oi_chg'] (daily OI pct change, backward-known only)
    r24 = df.close.pct_change(24)
    e = pd.Series(0, index=df.index)
    e[(df.oi_chg > 0.05)&(r24 > 0.02)] = 1
    e[(df.oi_chg > 0.05)&(r24 < -0.02)] = -1
    return e, dict(sl_atr=1.5, tp_atr=2.0, time_h=72, exit_long=None, exit_short=None)

def gen_H7(df):
    a = atr(df); vs = sma(df.volume,20)
    shock = (df.volume > 2.5*vs) & ((df.high-df.low) > 1.5*a)
    e = pd.Series(0, index=df.index)
    e[shock & (df.close > df.open)] = 1; e[shock & (df.close < df.open)] = -1
    return e, dict(sl_atr=1.2, tp_atr=1.8, time_h=24, exit_long=None, exit_short=None)

def gen_H9(df):
    e50 = ema(df.close,50); r = rsi(df.close); vs = sma(df.volume,20)
    m = sma(df.close,20); sd = df.close.rolling(20).std(); z20 = (df.close-m)/sd
    fterm = np.tanh(-df.get("funding", pd.Series(0.0, index=df.index))/0.0005)
    v_safe = np.maximum(df.volume, 1e-6) / np.maximum(vs, 1e-6)
    S = (0.35*np.tanh(40*(df.close/e50-1)) + 0.20*np.tanh((r-50)/12)
         + 0.15*np.tanh(np.log(v_safe)-0.05) - 0.15*np.tanh(z20/2) + 0.15*fterm)
    e = pd.Series(0, index=df.index)
    e[S >= 0.5] = 1; e[S <= -0.5] = -1
    ex = dict(sl_atr=1.5, tp_atr=2.0, time_h=96, exit_long=S < 0, exit_short=S > 0)
    return e, ex

def gen_H10(df):  # OI expansion gated by HIGH realized-vol tercile (batch 2 — registered 2026-08-10)
    rv = np.log(df.close/df.close.shift()).rolling(20).std()
    hi_thr = rv.rolling(500).quantile(2/3)
    high_state = rv > hi_thr
    r24 = df.close.pct_change(24)
    e = pd.Series(0, index=df.index)
    e[high_state & (df.oi_chg > 0.05) & (r24 > 0.02)] = 1
    e[high_state & (df.oi_chg > 0.05) & (r24 < -0.02)] = -1
    return e, dict(sl_atr=1.5, tp_atr=2.0, time_h=72, exit_long=None, exit_short=None)

def gen_H11(df):  # composite conviction-extremes (batch 2)
    e50 = ema(df.close,50); r = rsi(df.close); vs = sma(df.volume,20)
    m = sma(df.close,20); sd = df.close.rolling(20).std(); z20 = (df.close-m)/sd
    fterm = np.tanh(-df.get("funding", pd.Series(0.0, index=df.index))/0.0005)
    v_safe = np.maximum(df.volume, 1e-6) / np.maximum(vs, 1e-6)
    S = (0.35*np.tanh(40*(df.close/e50-1)) + 0.20*np.tanh((r-50)/12)
         + 0.15*np.tanh(np.log(v_safe)-0.05) - 0.15*np.tanh(z20/2) + 0.15*fterm)
    e = pd.Series(0, index=df.index)
    e[S >= 0.8] = 1; e[S <= -0.8] = -1
    ex = dict(sl_atr=1.5, tp_atr=2.5, time_h=72,
              exit_long=S.abs() < 0.2, exit_short=S.abs() < 0.2)
    return e, ex

def gen_H12(df):  # RV 3-state gating of 20h Donchian breaks (batch 2)
    rv = np.log(df.close/df.close.shift()).rolling(20).std()
    hi_thr = rv.rolling(500).quantile(2/3)
    high = rv > hi_thr
    hi20 = df.high.rolling(20).max().shift(1); lo20 = df.low.rolling(20).min().shift(1)
    e = pd.Series(0, index=df.index)
    e[high & (df.close > hi20)] = 1; e[high & (df.close < lo20)] = -1
    ex = dict(sl_atr=2.0, tp_atr=None, time_h=10*24,
              exit_long=df.close < lo20, exit_short=df.close > hi20)
    return e, ex

def gen_H13(df):  # identical mechanism to H10 (parameters frozen since H10); scope=BTC; 7y sample
    return gen_H10(df)

GENERATORS = {k[4:]: v for k, v in list(globals().items()) if k.startswith("gen_H")}
