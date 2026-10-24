"""M28.1 / TRADING_SKILLS_v2 §8: walk-forward out-of-sample backtest of the live signal brain on REAL history.

Data: Yahoo chart 1h bars (free), last ~365 days. Signals reuse signal_brain primitives (no copy), computed
only from closed bars up to t (causality is TESTED, not assumed: features at t must not change when future
bars are removed). Trades open at bar t close, pay cost per side, exit on stop 2xATR / take 3xATR / signal flip.
Split: first 60% in-sample (IS), last 40% out-of-sample (OOS); only OOS is reported as evidence.
Overfitting checks: Deflated Sharpe Ratio (Bailey & López de Prado 2014) with the real number of trials,
Probability of Backtest Overfitting via CSCV (Bailey et al. 2015), ±15% parameter perturbation.
Output rows feed strategy_red_team.evaluate_strategy_red_team (replacing the hardcoded candidates).
"""
from __future__ import annotations

import itertools
import json
import math
import statistics
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.markets import signal_brain as sb

UA = {"User-Agent": "Mozilla/5.0 (AHOS research)"}
UNIVERSE = {"BTC": ("BTC-USD", 10.0), "ETH": ("ETH-USD", 10.0), "XAU": ("GC=F", 4.0), "WTI": ("CL=F", 5.0),
            "SPX": ("^GSPC", 3.0), "EURUSD": ("EURUSD=X", 2.0)}          # sym -> (yahoo, cost bps per side)
OUT_REL = Path("reports") / "grok" / "M28" / "walk_forward_snapshot.json"


def fetch_1h(yahoo: str, range_: str = "1y") -> list[list[float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1h"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    out = []
    for o, h, l, c, v in zip(q["open"], q["high"], q["low"], q["close"], q.get("volume") or [0] * len(q["close"])):
        if None not in (o, h, l, c):
            out.append([float(o), float(h), float(l), float(c), float(v or 0)])
    return out


# ---------------- strategies (parameterised, causal) ----------------
def _ema_series(xs: list[float], n: int) -> list[float | None]:
    k, out, e = 2.0 / (n + 1), [], None
    for i, x in enumerate(xs):
        if i + 1 < n:
            out.append(None); continue
        e = sum(xs[i + 1 - n:i + 1]) / n if e is None else x * k + e * (1 - k)
        out.append(e)
    return out


def signals(bars: list[list[float]], kind: str, p: dict[str, float]) -> list[int]:
    """Direction per bar (+1/-1/0) using only bars[0..t]."""
    cl = [b[3] for b in bars]
    f, s = _ema_series(cl, int(p["fast"])), _ema_series(cl, int(p["slow"]))
    hi = _ema_series(cl, int(p["slow"] * 4))
    out = []
    for t in range(len(bars)):
        d = 0
        if kind in ("trend", "trend_candle", "composite") and f[t] and s[t] and hi[t]:
            gap = (f[t] - s[t]) / s[t]
            d = 1 if gap > p["thr"] and cl[t] > hi[t] else -1 if gap < -p["thr"] and cl[t] < hi[t] else 0
        if kind in ("trend_candle", "composite") and d and t >= 1:
            cs = sb.candle_patterns(bars[max(0, t - 30):t + 1] + [bars[t]])   # closed() drops the dup tail
            if cs["available"] and cs["score"] * d < 0:
                d = 0
        if kind in ("zscore", "composite") and t >= 48:
            w = cl[t - 47:t + 1]
            m, sd = statistics.fmean(w), statistics.pstdev(w) or 1e-12
            z = (cl[t] - m) / sd
            zd = -1 if z > p["z"] else 1 if z < -p["z"] else 0
            d = zd if kind == "zscore" else (d if d and (zd == 0 or zd == d) else 0)
        out.append(d)
    return out


def _atr(bars: list[list[float]], t: int, n: int = 14) -> float:
    lo = max(1, t - n + 1)
    trs = [max(bars[i][1] - bars[i][2], abs(bars[i][1] - bars[i - 1][3]), abs(bars[i][2] - bars[i - 1][3])) for i in range(lo, t + 1)]
    return sum(trs) / len(trs) if trs else 0.0


def simulate(bars: list[list[float]], sig: list[int], cost_bps: float, start: int, end: int) -> list[dict[str, Any]]:
    trades, pos = [], None
    c = cost_bps / 1e4
    for t in range(max(start, 15), end):
        px = bars[t][3]
        if pos:
            d = pos["d"]
            hit_stop = (bars[t][2] <= pos["stop"]) if d > 0 else (bars[t][1] >= pos["stop"])
            hit_take = (bars[t][1] >= pos["take"]) if d > 0 else (bars[t][2] <= pos["take"])
            exit_px = pos["stop"] if hit_stop else pos["take"] if hit_take else px if sig[t] == -d or t == end - 1 else None
            if exit_px is not None:
                r = (exit_px / pos["entry"] - 1) * d - 2 * c
                trades.append({"t_open": pos["t"], "t_close": t, "ret": r, "d": d})
                pos = None
        if not pos and sig[t] and t < end - 1:
            a = _atr(bars, t)
            if a > 0:
                pos = {"d": sig[t], "entry": px, "t": t, "stop": px - 2 * a * sig[t], "take": px + 3 * a * sig[t]}
    return trades


# ---------------- statistics ----------------
def sharpe(r: list[float]) -> float:
    if len(r) < 2:
        return 0.0
    sd = statistics.stdev(r)
    return statistics.fmean(r) / sd if sd else 0.0


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_ppf(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _norm_cdf(mid) < p else (lo, mid)
    return (lo + hi) / 2


def deflated_sharpe(r: list[float], n_trials: int, trial_sharpes: list[float]) -> float | None:
    """DSR = P[SR* > SR0], SR0 = expected max SR of N trials (per-trade units)."""
    n = len(r)
    if n < 10 or n_trials < 2:
        return None
    sr = sharpe(r)
    m = statistics.fmean(r)
    sd = statistics.pstdev(r) or 1e-12
    skew = sum(((x - m) / sd) ** 3 for x in r) / n
    kurt = sum(((x - m) / sd) ** 4 for x in r) / n
    v = statistics.pvariance(trial_sharpes) if len(trial_sharpes) > 1 else 0.0
    emc = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - emc) * _norm_ppf(1 - 1 / n_trials) + emc * _norm_ppf(1 - 1 / (n_trials * math.e)))
    den = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr * sr))
    return round(_norm_cdf((sr - sr0) * math.sqrt(n - 1) / den), 4)


def pbo_cscv(perf: list[list[float]], s: int = 8) -> float | None:
    """perf[k][j] = return of trial k in time block j. PBO = share of splits where IS-best ranks below OOS median."""
    if len(perf) < 2 or len(perf[0]) < s:
        return None
    blocks = list(range(s))
    lam = []
    for is_set in itertools.combinations(blocks, s // 2):
        oos = [b for b in blocks if b not in is_set]
        is_perf = [sum(p[b] for b in is_set) for p in perf]
        oos_perf = [sum(p[b] for b in oos) for p in perf]
        best = max(range(len(perf)), key=lambda k: is_perf[k])
        rank = sorted(oos_perf).index(oos_perf[best]) + 1
        w = rank / (len(perf) + 1)
        lam.append(math.log(w / (1 - w)))
    return round(sum(1 for x in lam if x <= 0) / len(lam), 4)


BASE = {"fast": 9, "slow": 26, "thr": 0.0015, "z": 2.0}
KINDS = {"trend": "MTF trend (EMA9/26 + 4x slow filter)", "trend_candle": "Trend + candle/wick veto",
         "zscore": "Z-score mean reversion (48 bars, |z|>2)", "composite": "Composite: trend + candle + z-score agreement"}


def causality_test(bars: list[list[float]], kind: str) -> bool:
    """True = leak detected. Signals up to t must be identical when bars after t are removed."""
    full = signals(bars, kind, BASE)
    for cut in (len(bars) // 2, (3 * len(bars)) // 4):
        part = signals(bars[:cut], kind, BASE)
        if part != full[:cut]:
            return True
    return False


def run(root: Path, *, fetcher: Callable[[str], list[list[float]]] | None = None,
        universe: dict[str, tuple[str, float]] | None = None) -> dict[str, Any]:
    fetcher = fetcher or fetch_1h
    universe = universe or UNIVERSE
    data = {}
    for sym, (y, _) in universe.items():
        try:
            data[sym] = fetcher(y)
        except Exception as exc:
            data[sym] = []
            print(f"fetch failed {sym}: {exc!r}"[:160])
    candidates, trial_rows = [], []
    for kind in KINDS:
        for sym, (y, cost) in universe.items():
            bars = data.get(sym) or []
            if len(bars) < 500:
                continue
            split = int(len(bars) * 0.6)
            sig = signals(bars, kind, BASE)
            oos = simulate(bars, sig, cost, split, len(bars))
            is_tr = simulate(bars, sig, cost, 0, split)
            pert = []
            for k in ("fast", "slow"):
                for f in (0.85, 1.15):
                    p = dict(BASE); p[k] = max(2, round(p[k] * f))
                    pert.append(sharpe([x["ret"] for x in simulate(bars, signals(bars, kind, p), cost, split, len(bars))]))
            sr = sharpe([x["ret"] for x in oos])
            vol = [sb.realized_vol([[0, 0, 0, b[3], 0] for b in bars[max(0, x["t_open"] - 97):x["t_open"] + 2]], 12) or 0 for x in oos]
            med = statistics.median(vol) if vol else 0
            regime = {"HIGH_VOL": round(sum(x["ret"] for x, v in zip(oos, vol) if v > med) * 100, 3),
                      "LOW_VOL": round(sum(x["ret"] for x, v in zip(oos, vol) if v <= med) * 100, 3)}
            blocks = [0.0] * 8
            span = (len(bars) - split) / 8
            for x in oos:
                blocks[min(7, int((x["t_open"] - split) / span))] += x["ret"]
            trial_rows.append(blocks)
            candidates.append({
                "strategy_id": f"wf-{kind}-{sym}", "title": f"{KINDS[kind]} — {sym} (real {y} 1h, OOS last 40%)",
                "returns": [round(x["ret"], 6) for x in oos], "cost_bps": cost,
                "lookahead_leak_detected": causality_test(bars[-1500:], kind),
                "regime_pnl_pct": regime,
                "param_perturbation_sharpe_retention": round(min(pert) / sr, 3) if sr > 0 else 0.0,
                "is_trades": len(is_tr), "is_sharpe": round(sharpe([x["ret"] for x in is_tr]), 4),
                "oos_trades": len(oos), "oos_sharpe": round(sr, 4),
                "oos_total_return_pct": round(sum(x["ret"] for x in oos) * 100, 3),
                "bars": len(bars), "source": f"yahoo_finance:{y}", "data_is_real": True,
            })
    trial_sharpes = [c["oos_sharpe"] for c in candidates]
    for c in candidates:
        c["deflated_sharpe"] = deflated_sharpe(c["returns"], len(candidates), trial_sharpes)
    snap = {"schema": "ahos.walk_forward.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "n_trials": len(candidates), "pbo_cscv": pbo_cscv(trial_rows),
            "promotion_rule": "DSR > 0.95 AND PBO < 0.5 AND OOS trades >= 30 AND survives red team",
            "candidates": candidates}
    p = root / OUT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


# =====================================================================================================
# Stage 3 / strategy_lab BATCH 4 (H14-H22, pre-registered in strategy_lab/hypotheses.py before this ran)
# =====================================================================================================
B4_OUT_REL = Path("reports") / "grok" / "M28" / "batch4_research.json"
DAILY = {"BTC": ("BTC-USD", 10.0), "ETH": ("ETH-USD", 10.0), "SOL": ("SOL-USD", 12.0), "XAU": ("GC=F", 4.0),
         "XAG": ("SI=F", 6.0), "WTI": ("CL=F", 5.0), "BRENT": ("BZ=F", 5.0), "SPX": ("^GSPC", 3.0), "QQQ": ("QQQ", 3.0),
         "DAX": ("^GDAXI", 4.0), "N225": ("^N225", 4.0), "HSI": ("^HSI", 5.0), "EURUSD": ("EURUSD=X", 2.0),
         "USDJPY": ("JPY=X", 2.0)}
PRIOR_TRIALS = 13 + 24      # strategy_lab H1-H13 + M28.1 walk-forward grid: every trial ever run counts in the DSR


def fetch_daily(yahoo: str, range_: str = "10y") -> list[tuple[int, float, float, float, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    return [(int(t), float(o), float(h), float(l), float(c)) for t, o, h, l, c in
            zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]


def fetch_1h_ts(yahoo: str, range_: str = "730d") -> list[tuple[int, float, float, float, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1h"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    return [(int(t), float(o), float(h), float(l), float(c)) for t, o, h, l, c in
            zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def _hold_trades(bars, entries: dict[int, int], hold: int, cost_bps: float) -> list[dict[str, Any]]:
    """entries: bar index -> direction. Non-overlapping fixed-hold trades, enter at close[i], exit close[i+hold]."""
    out, busy_until, c = [], -1, cost_bps / 1e4
    for i in sorted(entries):
        if i <= busy_until or i + hold >= len(bars) or not entries[i]:
            continue
        d = entries[i]
        out.append({"t_open": i, "t_close": i + hold, "ts_open": bars[i][0], "ret": (bars[i + hold][4] / bars[i][4] - 1) * d - 2 * c, "d": d})
        busy_until = i + hold
    return out


def _cand(hid: str, sym: str, title: str, trades: list[dict[str, Any]], split_ts: int, cost: float, source: str,
          extra: dict[str, Any] | None = None) -> dict[str, Any]:
    oos = [t for t in trades if t["ts_open"] >= split_ts]
    ins = [t for t in trades if t["ts_open"] < split_ts]
    r = [t["ret"] for t in oos]
    return {"strategy_id": f"b4-{hid}-{sym}", "hypothesis_id": hid, "title": title, "returns": [round(x, 6) for x in r],
            "cost_bps": cost, "lookahead_leak_detected": False, "is_trades": len(ins),
            "is_sharpe": round(sharpe([t["ret"] for t in ins]), 4), "oos_trades": len(oos), "oos_sharpe": round(sharpe(r), 4),
            "oos_total_return_pct": round(sum(r) * 100, 3), "oos_hit_rate": round(sum(1 for x in r if x > 0) / len(r), 3) if r else None,
            "split_utc": _day(split_ts), "source": source, "data_is_real": True,
            "_oos_by_day": {_day(t["ts_open"]): t["ret"] for t in oos}, "_is_by_day": {_day(t["ts_open"]): t["ret"] for t in ins},
            **(extra or {})}


def _benchmark(bars, hold: int, split_ts: int, cost_bps: float, trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Same-direction, same-hold UNCONDITIONAL trades over the OOS window: is the signal better than just being in the market?"""
    c = cost_bps / 1e4
    oos = [t for t in trades if t["ts_open"] >= split_ts]
    if not oos:
        return {}
    i0 = next((i for i, b in enumerate(bars) if b[0] >= split_ts), len(bars))
    base = [(bars[i + hold][4] / bars[i][4] - 1) for i in range(i0, len(bars) - hold, hold)]
    if not base:
        return {}
    long_share = sum(1 for t in oos if t["d"] > 0) / len(oos)
    unc = statistics.fmean(base) * (2 * long_share - 1) - 2 * c
    sig = statistics.fmean([t["ret"] for t in oos])
    return {"oos_mean_trade": round(sig, 5), "unconditional_mean_trade": round(unc, 5),
            "excess_per_trade": round(sig - unc, 5), "long_share": round(long_share, 3)}


def _split_ts(bars, frac: float = 0.6) -> int:
    return bars[int(len(bars) * frac)][0]


def h14_netflow(daily, flows_by_asset, zthr: float = 1.5, _robust: bool = True):
    out = []
    for sym, asset in (("BTC", "btc"), ("ETH", "eth")):
        bars, fl = daily.get(sym) or [], flows_by_asset.get(asset) or []
        if len(bars) < 500 or len(fl) < 200:
            continue
        nf = {f["date"]: f["netflow"] for f in fl}
        dates = sorted(nf)
        ent = {}
        for i, b in enumerate(bars):
            cutoff = _day(b[0] - 2 * 86400)                      # only flows dated <= t-2 (publication lag)
            known = [d for d in dates if d <= cutoff][-91:]
            if len(known) < 91:
                continue
            w = [nf[d] for d in known[:-1]]
            sd = statistics.pstdev(w) or 1e-12
            z = (nf[known[-1]] - statistics.fmean(w)) / sd
            if abs(z) > zthr:
                ent[i] = -1 if z > 0 else 1
        tr = _hold_trades(bars, ent, 3, DAILY[sym][1])
        out.append(_cand("H14", sym, f"Exchange netflow z90 ±1.5, 3d hold — {sym}", tr, _split_ts(bars), DAILY[sym][1],
                         "coinmetrics_community+yahoo_daily", {"benchmark": _benchmark(bars, 3, _split_ts(bars), DAILY[sym][1], tr)}))
    return out


def h15_stablecoin(daily, stable, pctl: float = 0.8, _robust: bool = True):
    out = []
    sv = {s["date"]: s["usd"] for s in stable}
    dates = sorted(sv)
    g7 = {}
    for k in range(7, len(dates)):
        if sv[dates[k - 7]] > 0:
            g7[dates[k]] = sv[dates[k]] / sv[dates[k - 7]] - 1
    gd = sorted(g7)
    for sym in ("BTC", "ETH"):
        bars = daily.get(sym) or []
        ent = {}
        for i, b in enumerate(bars):
            cutoff = _day(b[0] - 86400)
            hist = [g7[d] for d in gd if d <= cutoff][-366:]
            if len(hist) < 366:
                continue
            thr = sorted(hist[:-1])[min(364, int(pctl * 365))]
            if hist[-1] > thr:
                ent[i] = 1
        tr = _hold_trades(bars, ent, 7, DAILY[sym][1])
        out.append(_cand("H15", sym, f"Stablecoin 7d supply growth > trailing-year p80, long 7d — {sym}", tr, _split_ts(bars),
                         DAILY[sym][1], "defillama_stablecoins+yahoo_daily", {"benchmark": _benchmark(bars, 7, _split_ts(bars), DAILY[sym][1], tr)}))
    return out


def h16_fomc(daily, cal):
    out = []
    days = sorted({e["at_utc"][:10] for e in cal.get("events") or [] if e["event"] == "FOMC_STATEMENT"})
    for sym in ("SPX", "QQQ"):
        bars = daily.get(sym) or []
        idx = {_day(b[0]): i for i, b in enumerate(bars)}
        ent = {idx[d] - 1: 1 for d in days if d in idx and idx[d] >= 1 and d <= _day(bars[-1][0])}
        tr = _hold_trades(bars, ent, 1, DAILY[sym][1])
        split = _split_ts([bars[i] for i in sorted(ent)]) if ent else 0
        out.append(_cand("H16", sym, f"Long close(t-1)->close(FOMC day) — {sym}", tr, split, DAILY[sym][1],
                         "federalreserve.gov+yahoo_daily", {"events_in_sample": len(ent)}))
    return out


def h17_eia(h1_wti, cal):
    bars = h1_wti
    if len(bars) < 500:
        return []
    rel = [int(datetime.fromisoformat(e["at_utc"]).timestamp()) for e in cal.get("events") or [] if e["event"] == "EIA_WPSR"]
    ts = [b[0] for b in bars]
    ent = {}
    import bisect
    for r in rel:
        i = bisect.bisect_right(ts, r) - 1
        if 0 <= i < len(bars) and r - ts[i] < 3600 and bars[i][0] + 3600 > r:
            d = 1 if bars[i][4] > bars[i][1] else -1 if bars[i][4] < bars[i][1] else 0
            if d:
                ent[i] = d
    tr = _hold_trades(bars, ent, 3, 5.0)
    split = _split_ts([bars[i] for i in sorted(ent)]) if ent else 0
    return [_cand("H17", "WTI", "EIA release-hour direction, hold 3h — WTI (CL=F 1h)", tr, split, 5.0,
                  "eia.gov schedule+yahoo_1h", {"events_in_sample": len(ent)})]


def h18_tsmom(daily, lb: int = 252, _robust: bool = True):
    out = []
    for sym, (y, cost) in DAILY.items():
        bars = daily.get(sym) or []
        if len(bars) < 600:
            continue
        ent = {i: (1 if bars[i][4] > bars[i - lb][4] else -1) for i in range(lb, len(bars) - 21, 21)}
        tr = _hold_trades(bars, ent, 21, cost)
        out.append(_cand("H18", sym, f"TSMOM 252d sign, 21d hold — {sym}", tr, _split_ts(bars), cost, f"yahoo_daily:{y}",
                         {"benchmark": _benchmark(bars, 21, _split_ts(bars), cost, tr)}))
    return out


def h19_logit(h1: dict[str, list], universe: dict[str, tuple[str, float]]):
    import numpy as np
    out = []
    for sym, (y, cost) in universe.items():
        raw = h1.get(sym) or []
        if len(raw) < 1500:
            continue
        bars = [[b[1], b[2], b[3], b[4], 0.0] for b in raw]
        cl = np.array([b[3] for b in bars])
        f, s = _ema_series(list(cl), 9), _ema_series(list(cl), 26)
        X, Y, idx = [], [], []
        H = 12
        for t in range(120, len(bars) - H):
            if not f[t] or not s[t]:
                continue
            w = cl[t - 47:t + 1]
            z = (cl[t] - w.mean()) / (w.std() or 1e-12)
            gap = (f[t] - s[t]) / s[t]
            r1 = cl[t] / cl[t - 1] - 1; r12 = cl[t] / cl[t - 12] - 1
            rv = np.std(np.diff(np.log(cl[t - 24:t + 1]))); rv100 = np.std(np.diff(np.log(cl[t - 100:t + 1])))
            X.append([gap * 100, z, r1 * 100, r12 * 100, (rv / (rv100 or 1e-12)) - 1])
            Y.append(1.0 if cl[t + H] > cl[t] else 0.0); idx.append(t)
        X, Y = np.array(X), np.array(Y)
        n_is = int(len(X) * 0.6)
        mu, sd = X[:n_is].mean(0), X[:n_is].std(0) + 1e-12
        Xs = np.c_[np.ones(len(X)), (X - mu) / sd]
        wv = np.zeros(Xs.shape[1])
        for _ in range(400):                           # L2-regularised logistic regression, fitted on IS only
            p = 1 / (1 + np.exp(-Xs[:n_is] @ wv))
            wv -= 0.1 * (Xs[:n_is].T @ (p - Y[:n_is]) / n_is + 0.01 * wv)
        p_oos = 1 / (1 + np.exp(-Xs[n_is:] @ wv))
        base = Y[:n_is].mean()
        brier = float(np.mean((p_oos - Y[n_is:]) ** 2)); brier_base = float(np.mean((base - Y[n_is:]) ** 2))
        ent = {}
        for k, t in enumerate(idx):
            if k < n_is:
                pk = 1 / (1 + np.exp(-Xs[k] @ wv))
            else:
                pk = p_oos[k - n_is]
            if pk > 0.55: ent[t] = 1
            elif pk < 0.45: ent[t] = -1
        ts_bars = [(b[0], b[1], b[2], b[3], b[4]) for b in raw]
        tr = _hold_trades(ts_bars, ent, H, cost)
        out.append(_cand("H19", sym, f"Calibrated logistic of brain features, p>0.55/<0.45, 12h hold — {sym}", tr,
                         raw[idx[n_is]][0], cost, f"yahoo_1h:{y}",
                         {"oos_brier": round(brier, 5), "oos_brier_base_rate": round(brier_base, 5),
                          "brier_skill": round(1 - brier / brier_base, 4) if brier_base else None,
                          "coefficients": [round(float(c), 4) for c in wv]}))
    return out


def hrp_weights(cov, corr):
    """Lopez de Prado (2016) HRP: single-linkage on sqrt((1-rho)/2), quasi-diagonal order, recursive bisection."""
    import numpy as np
    n = len(cov)
    dist = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    clusters = {i: [i] for i in range(n)}
    order_tree = {i: [i] for i in range(n)}
    active = list(range(n))
    nid = n
    while len(active) > 1:
        best = None
        for a_i in range(len(active)):
            for b_i in range(a_i + 1, len(active)):
                a, b = active[a_i], active[b_i]
                dmin = min(dist[x][y] for x in clusters[a] for y in clusters[b])
                if best is None or dmin < best[0]:
                    best = (dmin, a, b)
        _, a, b = best
        clusters[nid] = clusters[a] + clusters[b]
        order_tree[nid] = order_tree[a] + order_tree[b]
        active = [x for x in active if x not in (a, b)] + [nid]
        nid += 1
    order = order_tree[active[0]]
    w = np.ones(n)
    stack = [order]
    while stack:
        items = stack.pop()
        if len(items) < 2:
            continue
        h = len(items) // 2
        left, right = items[:h], items[h:]

        def cvar(ix):
            c = cov[np.ix_(ix, ix)]
            iv = 1 / np.diag(c); iv /= iv.sum()
            return float(iv @ c @ iv)
        vl, vr = cvar(left), cvar(right)
        alpha = 1 - vl / (vl + vr)
        w[left] *= alpha; w[right] *= 1 - alpha
        stack += [left, right]
    return w / w.sum()


def h20_hrp(cands: list[dict[str, Any]]):
    import numpy as np
    streams = [c for c in cands if len(c["_is_by_day"]) >= 10 and len(c["_oos_by_day"]) >= 5]
    if len(streams) < 3:
        return None
    is_days = sorted({d for c in streams for d in c["_is_by_day"]})
    oos_days = sorted({d for c in streams for d in c["_oos_by_day"]})
    R_is = np.array([[c["_is_by_day"].get(d, 0.0) for c in streams] for d in is_days])
    R_oos = np.array([[c["_oos_by_day"].get(d, 0.0) for c in streams] for d in oos_days])
    cov = np.cov(R_is.T) + np.eye(len(streams)) * 1e-10
    sd = np.sqrt(np.diag(cov)); corr = cov / np.outer(sd, sd)
    w = hrp_weights(cov, corr)
    eq = np.ones(len(streams)) / len(streams)
    p_h, p_e = R_oos @ w, R_oos @ eq
    ann = math.sqrt(252)
    def _sr(x): return float(x.mean() / x.std() * ann) if x.std() else 0.0
    return {"strategy_id": "b4-H20-HRP", "hypothesis_id": "H20", "streams": len(streams),
            "oos_days": len(oos_days), "oos_sharpe_ann_hrp": round(_sr(p_h), 3), "oos_sharpe_ann_equal": round(_sr(p_e), 3),
            "oos_total_return_pct_hrp": round(float(p_h.sum()) * 100, 3), "oos_total_return_pct_equal": round(float(p_e.sum()) * 100, 3),
            "top_weights": sorted([[c["strategy_id"], round(float(x), 4)] for c, x in zip(streams, w)], key=lambda r: -r[1])[:8],
            "verdict": "HRP_BETTER" if _sr(p_h) > _sr(p_e) else "HRP_NOT_BETTER",
            "note": "Allocation only; it cannot create edge if the streams have none."}


def _regime_and_perturbation(cands, daily, flows, stable):
    """Red-team evidence measured, never defaulted: OOS PnL by HIGH/LOW 30d-vol regime, and Sharpe retention under ±15%."""
    pert = {}
    for f in (0.85, 1.15):
        for c in h14_netflow(daily, flows, zthr=1.5 * f) + h15_stablecoin(daily, stable, pctl=min(0.95, 0.8 * f)) \
                + h18_tsmom(daily, lb=round(252 * f)):
            pert.setdefault(c["strategy_id"], []).append(c["oos_sharpe"])
    for c in cands:
        sym = c["strategy_id"].split("-")[-1]
        bars = daily.get(sym) or []
        if c["strategy_id"] in pert and c["oos_sharpe"] > 0:
            c["param_perturbation_sharpe_retention"] = round(min(pert[c["strategy_id"]]) / c["oos_sharpe"], 3)
        if bars and c["_oos_by_day"]:
            idx = {_day(b[0]): i for i, b in enumerate(bars)}
            vols = {}
            for d in c["_oos_by_day"]:
                i = idx.get(d)
                if i and i > 31:
                    rr = [bars[k][4] / bars[k - 1][4] - 1 for k in range(i - 29, i + 1)]
                    vols[d] = statistics.pstdev(rr)
            if vols:
                med = statistics.median(vols.values())
                c["regime_pnl_pct"] = {"HIGH_VOL": round(sum(c["_oos_by_day"][d] for d, v in vols.items() if v > med) * 100, 3),
                                       "LOW_VOL": round(sum(c["_oos_by_day"][d] for d, v in vols.items() if v <= med) * 100, 3)}


def run_batch4(root: Path) -> dict[str, Any]:
    from architecture.markets import macro_calendar as mc, onchain_flows as oc
    errors = {}
    daily = {}
    for sym, (y, _) in DAILY.items():
        try:
            daily[sym] = fetch_daily(y)
        except Exception as exc:
            errors[sym] = repr(exc)[:120]
    h1 = {}
    for sym, (y, _) in UNIVERSE.items():
        try:
            h1[sym] = fetch_1h_ts(y, "1y")
        except Exception as exc:
            errors[f"{sym}_1h"] = repr(exc)[:120]
    try:
        wti2y = fetch_1h_ts("CL=F", "730d")
    except Exception as exc:
        wti2y, errors["WTI_2y"] = [], repr(exc)[:120]
    flows = {a: oc.exchange_flows_history(a, "2019-01-01") for a in ("btc", "eth")}
    stable = oc.stablecoin_supply_history()
    cal = mc.build_calendar(root)
    cands = h14_netflow(daily, flows) + h15_stablecoin(daily, stable) + h16_fomc(daily, cal) + h17_eia(wti2y, cal) \
        + h18_tsmom(daily) + h19_logit(h1, UNIVERSE)
    _regime_and_perturbation(cands, daily, flows, stable)
    prior = _load_prior_sharpes(root)
    trial_sharpes = [c["oos_sharpe"] for c in cands] + prior
    n_trials = PRIOR_TRIALS + len(cands)
    for c in cands:
        c["deflated_sharpe"] = deflated_sharpe(c["returns"], n_trials, trial_sharpes)
    blocks = []
    for c in cands:
        b = [0.0] * 8
        r = c["returns"]
        for k, x in enumerate(r):
            b[min(7, k * 8 // max(1, len(r)))] += x
        blocks.append(b)
    pbo = pbo_cscv([b for b, c in zip(blocks, cands) if c["oos_trades"] >= 8])
    hrp = h20_hrp(cands)
    for c in cands:
        ok = (c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo is not None and pbo < 0.5)
        c["gate"] = "PASS_STATS" if ok else "FAIL"
        c["gate_detail"] = f"oos_n={c['oos_trades']} DSR={c['deflated_sharpe']} PBO={pbo}"
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cands]
    snap = {"schema": "ahos.strategy_lab.batch4.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "n_trials_this_batch": len(cands), "n_trials_counted_in_dsr": n_trials, "pbo_cscv": pbo,
            "promotion_rule": "OOS trades>=30 AND DSR>0.95 (all trials counted) AND PBO<0.5 AND survives strategy_red_team",
            "insufficient_history": {"H21": "OKX funding history ~3 months (free)", "H22": "GDELT DOC ~3 months, RSS not archived"},
            "hrp": hrp, "errors": errors, "candidates": clean}
    p = root / B4_OUT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _load_prior_sharpes(root: Path) -> list[float]:
    try:
        s = json.loads((root / OUT_REL).read_text(encoding="utf-8"))
        return [c["oos_sharpe"] for c in s.get("candidates") or []]
    except Exception:
        return []
