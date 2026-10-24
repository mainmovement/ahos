"""MAP-Elites archive and the four Batch-6 composites (H29–H32).

Pre-registered in strategy_lab/hypotheses.py ``_B6`` at 2026-10-24 18:18 Tehran, before any run.
An out-of-sample trial is spent only after the in-sample screens (active share, pairwise |rho|).
A screened hypothesis is written down and is not counted in ``trials_counted_in_dsr``.
The walk-forward arithmetic stays in architecture.learning.walk_forward.
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from architecture.learning.walk_forward import (
    B5_OUT_REL, DAILY, _bar_day, _cand5, _day, _grid, _regime_pnl, _ts,
    deflated_sharpe, deflated_sharpe_annualized, fetch_1h_v, fetch_daily_v, ledoit_wolf,
    sharpe, time_aligned_pbo,
)
from architecture.markets.walk_forward import (
    apply_portfolio_l1_gate, apply_weight_hysteresis, atr_normalized_return, clears_cost_hurdle,
    portfolio_l1_turnover, safe_simple_return, wilder_atr,
)

B6_OUT_REL = Path("reports") / "grok" / "M28" / "batch6_research.json"
GRID_REL = Path("reports") / "grok" / "M28" / "map_elites_grid.json"
HORIZONS = ("intraday", "swing_2_5d", "macro_weekly")
REGIMES = ("trend_breakout", "vol_compression_carry", "crisis_defensive")
RHO_MAX = 0.65
CELLS = {
    "H29": ("macro_weekly", "vol_compression_carry"),
    "H30": ("macro_weekly", "trend_breakout"),
    "H31": ("swing_2_5d", "trend_breakout"),
    "H32": ("macro_weekly", "crisis_defensive"),
}
ACTIVE_MIN = {"H29": 0.30, "H30": 0.25, "H31": 0.25, "H32": 0.25,
              "H33": 0.25, "H34": 0.25, "H35": 0.25, "H36": 0.25}
CELLS.update({
    "H33": ("macro_weekly", "vol_compression_carry"),
    "H34": ("swing_2_5d", "trend_breakout"),
    "H35": ("macro_weekly", "crisis_defensive"),
    "H36": ("swing_2_5d", "vol_compression_carry"),
    "H37": ("macro_weekly", "vol_compression_carry"),
    "H38": ("intraday", "trend_breakout"),
    "H39": ("intraday", "vol_compression_carry"),
    "H40": ("intraday", "crisis_defensive"),
})
ACTIVE_MIN.update({"H37": 0.25, "H38": 0.25, "H39": 0.25, "H40": 0.25})
B8_OUT_REL = Path("reports") / "grok" / "M28" / "batch8_research.json"
TAU_L1 = 0.25
HOUR_ASSETS = ("BTC", "ETH", "SPX", "QQQ", "XAU")
HOUR_YAHOO = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SPX": "^GSPC", "QQQ": "QQQ", "XAU": "GC=F"}
B7_OUT_REL = Path("reports") / "grok" / "M28" / "batch7_research.json"
TAU_REBAL = 0.05
HURDLE = 2.5
B7_COST_BPS = 15.0
BL_ASSETS = ("BTC", "ETH", "XAU", "WTI", "SPX", "DAX", "N225", "EURUSD")
H31_SKIP = ("EURUSD", "USDJPY")
PRIOR_THROUGH_BATCH5 = 89


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 30:
        return None
    a, b = xs[:n], ys[:n]
    mx, my = statistics.fmean(a), statistics.fmean(b)
    vx = sum((x - mx) ** 2 for x in a)
    vy = sum((y - my) ** 2 for y in b)
    if vx <= 0 or vy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(a, b)) / math.sqrt(vx * vy)


def active_share(weights: list[float]) -> float:
    """Cremers active share against equal weight, on gross-normalized weights (sum |w| = 1)."""
    gross = sum(abs(w) for w in weights)
    if gross <= 0:
        return 0.0
    n = len(weights)
    w = [x / gross for x in weights]
    return 0.5 * sum(abs(x - 1.0 / n) for x in w)


def screen_book(is_returns: list[float], baselines: dict[str, list[float]], siblings: dict[str, list[float]],
                share: float, min_share: float, rho_max: float = RHO_MAX) -> tuple[bool, str]:
    """In-sample only. Failure refuses the out-of-sample trial."""
    if share < min_share:
        return False, f"active_share {share:.3f} < {min_share}"
    if len(is_returns) < 30:
        return False, f"is_observations {len(is_returns)} < 30"
    for name, series in {**baselines, **siblings}.items():
        rho = pearson(is_returns, series)
        if rho is not None and abs(rho) >= rho_max:
            return False, f"|rho|={abs(rho):.3f} vs {name} >= {rho_max}"
    return True, "ADMITTED"


def _closes(daily: dict, assets: tuple[str, ...]) -> tuple[list[str], np.ndarray]:
    days, series, _ = _grid(daily, assets, ref=assets[0], max_stale=5)
    mat = np.array([[np.nan if series[a][t] is None else float(series[a][t]) for a in assets] for t in range(len(days))],
                   dtype=float)
    return days, mat


def _g(C: np.ndarray, t: int, step: int) -> np.ndarray:
    out = np.full(C.shape[1], np.nan)
    for i in range(C.shape[1]):
        r = _fwd(float(C[t, i]), float(C[t + step, i]))
        if r is not None:
            out[i] = r
    return out


def _fwd(p0: float, p1: float) -> float | None:
    if not (math.isfinite(p0) and math.isfinite(p1)):
        return None
    return safe_simple_return(p0, p1)


def _trade(days: list[str], t: int, step: int, ret: float, w: np.ndarray, assets: tuple[str, ...], ew: float) -> dict:
    return {"ts_open": _ts(days[t]), "ts_close": _ts(days[min(t + step, len(days) - 1)]), "ret": float(ret),
            "d": 1, "weights": {a: round(float(w[i]), 4) for i, a in enumerate(assets)}, "ew_ret": float(ew)}


def _renorm(w: np.ndarray, good: np.ndarray) -> np.ndarray | None:
    ww = w.copy()
    ww[~good] = 0.0
    gross = np.abs(ww).sum()
    if gross <= 0:
        return None
    return ww / gross


def h29_book(daily: dict, *, lb: int = 252, vol_lb: int = 63, step: int = 5, cost_bps: float = 15.0,
             until_ts: int | None = None) -> list[dict]:
    assets = tuple(DAILY)
    days, C = _closes(daily, assets)
    n, k = C.shape
    trades, w_prev = [], np.zeros(k)
    cost = cost_bps / 1e4
    for t in range(lb, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        score = []
        vol = np.full(k, np.nan)
        for i in range(k):
            mom = _fwd(C[t - lb, i], C[t, i])
            rets = [r for r in (_fwd(C[j - 1, i], C[j, i]) for j in range(t - vol_lb + 1, t + 1)) if r is not None]
            if mom is None or len(rets) < 20 or statistics.pstdev(rets) <= 0:
                continue
            vol[i] = statistics.pstdev(rets)
            score.append((i, mom / vol[i]))
        if len(score) < 6:
            continue
        score.sort(key=lambda x: x[1])
        third = max(1, len(score) // 3)
        raw = np.zeros(k)
        for i, _s in score[:third]:
            raw[i] = -1.0 / vol[i]
        for i, _s in score[-third:]:
            raw[i] = 1.0 / vol[i]
        g = _g(C, t, step)
        good = np.isfinite(g)
        w = _renorm(raw, good)
        if w is None:
            continue
        turn = 0.5 * float(np.abs(w - w_prev).sum())
        trades.append(_trade(days, t, step, float(np.nansum(w * g)) - turn * cost, w, assets, float(np.nanmean(g))))
        w_prev = w
    return trades


def h30_book(daily: dict, *, lb: int = 252, step: int = 21, tau: float = 0.05, delta: float = 2.5,
             until_ts: int | None = None) -> list[dict]:
    assets = BL_ASSETS
    days, C = _closes(daily, assets)
    n, k = C.shape
    cost = np.array([DAILY[a][1] for a in assets]) / 1e4
    trades, w_prev, past = [], np.zeros(k), []
    for t in range(lb, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        rows = []
        for j in range(t - lb + 1, t + 1):
            row = [_fwd(C[j - 1, i], C[j, i]) for i in range(k)]
            if None not in row:
                rows.append(row)
        if len(rows) < lb // 2:
            continue
        R = np.array(rows, dtype=float)
        sig, _sh = ledoit_wolf(R)
        weq = np.ones(k) / k
        mom = np.array([_fwd(C[t - lb, i], C[t, i]) or 0.0 for i in range(k)])
        sign = np.sign(mom)
        ic = _trailing_ic(past)
        conf = min(0.99, abs(ic)) if ic is not None else 0.0
        if conf >= 0.02:
            sd = np.sqrt(np.clip(np.diag(sig), 1e-12, None))
            pi = delta * sig @ weq
            om = tau * sd ** 2 / conf
            q = sign * 0.05 * sd
            ts_inv = np.linalg.inv(tau * sig)
            mu = np.linalg.solve(ts_inv + np.diag(1.0 / om), ts_inv @ pi + q / om)
            w = np.linalg.solve(delta * sig, mu)
            w = w / (np.abs(w).sum() or 1.0)
        else:
            w = weq.copy()
        g = _g(C, t, step)
        good = np.isfinite(g)
        ww = _renorm(w, good)
        if ww is None:
            continue
        ret = float(np.nansum(ww * g) - np.abs(ww - w_prev) @ cost)
        ew = float(np.nanmean(g))
        trades.append(_trade(days, t, step, ret, ww, assets, ew))
        past.append((sign, np.array([x if x is not None else 0.0 for x in g])))
        w_prev = ww
    return trades


def _trailing_ic(past: list[tuple[np.ndarray, np.ndarray]]) -> float | None:
    if len(past) < 8:
        return None
    xs, ys = [], []
    for sign, realized in past:
        xs.extend(float(s) for s in sign)
        ys.extend(float(r) for r in realized)
    return pearson(xs, ys)


def _causal_high_prob(closes: np.ndarray) -> list[float | None]:
    """Forward-only 3-state vol filter. Emission scales use trailing absolute returns, never the future.
    Full-sample PELT is deliberately not used: its penalty is fit on the whole path."""
    trans = ((0.90, 0.09, 0.01), (0.06, 0.88, 0.06), (0.02, 0.10, 0.88))
    probs = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
    hist: list[float] = []
    out: list[float | None] = [None]
    for i in range(1, len(closes)):
        r = _fwd(closes[i - 1], closes[i])
        if r is None:
            out.append(None)
            continue
        past = hist[-252:] or [1e-4]
        mean_abs = sum(past) / len(past) or 1e-4
        scales = (0.5 * mean_abs, mean_abs, 2.2 * mean_abs)
        pred = [sum(probs[a] * trans[a][b] for a in range(3)) for b in range(3)]
        lik = [math.exp(-0.5 * min(50.0, (r / scales[b]) ** 2)) / scales[b] for b in range(3)]
        post = [pred[b] * lik[b] for b in range(3)]
        s = sum(post) or 1.0
        probs = [p / s for p in post]
        hist.append(abs(r))
        out.append(pred[2])
    return out


def h31_book(daily: dict, *, wick: float = 2.2, comp: float = 0.8, hold: int = 3, until_ts: int | None = None) -> list[dict]:
    assets = tuple(a for a in DAILY if a not in H31_SKIP)
    days, C = _closes(daily, assets)
    ohlc = {a: {_bar_day(b[0]): b for b in daily.get(a) or []} for a in assets}
    high_p = [_causal_high_prob(C[:, i]) for i in range(len(assets))]
    trades, busy = [], -1
    for t in range(40, len(days) - hold):
        if t < busy or (until_ts is not None and _ts(days[t]) >= until_ts):
            continue
        fired = []
        for i, a in enumerate(assets):
            bar = ohlc[a].get(days[t])
            if bar is None or high_p[i][t] is None or high_p[i][t] >= 0.5:
                continue
            rets = [r for r in (_fwd(C[j - 1, i], C[j, i]) for j in range(t - 19, t + 1)) if r is not None]
            if len(rets) < 20:
                continue
            if statistics.pstdev(rets[-5:]) >= comp * statistics.pstdev(rets):
                continue
            o, h, l, c = bar[1], bar[2], bar[3], bar[4]
            body = abs(c - o) or 1e-12
            lower, upper = min(o, c) - l, h - max(o, c)
            if lower >= wick * body and lower > upper:
                fired.append((i, 1.0))
            elif upper >= wick * body and upper > lower:
                fired.append((i, -1.0))
        if not fired:
            continue
        w = np.zeros(len(assets))
        for i, d in fired:
            w[i] = d
        g = _g(C, t, hold)
        good = np.isfinite(g) & (w != 0)
        ww = _renorm(w, good)
        if ww is None:
            continue
        cost = statistics.fmean(DAILY[a][1] for a in assets) / 1e4
        ret = float(np.nansum(ww * g)) - 2 * cost
        ew = float(np.nanmean(g))
        trades.append(_trade(days, t, hold, ret, ww, assets, ew))
        busy = t + hold
    return trades


def h32_book(daily: dict, *, vol_lb: int = 20, med_lb: int = 252, mom_lb: int = 63, step: int = 5,
             cost_bps: float = 15.0, until_ts: int | None = None) -> list[dict]:
    assets = ("XAU", "DXY", "BTC", "ETH", "SPX")
    panel = {**daily}
    days, C = _closes(panel, assets)
    ix = {a: i for i, a in enumerate(assets)}
    trades, w_prev = [], np.zeros(len(assets))
    cost = cost_bps / 1e4
    spx = ix["SPX"]
    for t in range(med_lb + vol_lb, len(days) - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        vols = []
        for j in range(t - med_lb, t + 1):
            window = [r for r in (_fwd(C[u - 1, spx], C[u, spx]) for u in range(j - vol_lb + 1, j + 1)) if r is not None]
            if len(window) >= vol_lb // 2:
                vols.append(statistics.pstdev(window))
        if len(vols) < med_lb // 2:
            continue
        high = vols[-1] > statistics.median(vols[:-1])
        raw = np.zeros(len(assets))
        if high:
            raw[ix["XAU"]] = 0.5
            raw[ix["DXY"]] = 0.5
        else:
            risk = []
            for a in ("BTC", "ETH", "SPX"):
                mom = _fwd(C[t - mom_lb, ix[a]], C[t, ix[a]])
                if mom is not None and mom > 0:
                    risk.append(ix[a])
            if risk:
                for i in risk:
                    raw[i] = 1.0 / len(risk)
        g = _g(C, t, step)
        good = np.isfinite(g)
        w = _renorm(raw, good) if raw.sum() > 0 else None
        if w is None:
            trades.append(_trade(days, t, step, 0.0, np.zeros(len(assets)), assets, float(np.nanmean(g))))
            w_prev = np.zeros(len(assets))
            continue
        turn = 0.5 * float(np.abs(w - w_prev).sum())
        ret = float(np.nansum(w * g)) - turn * cost
        trades.append(_trade(days, t, step, ret, w, assets, float(np.nanmean(g))))
        w_prev = w
    return trades


def _mean_share(trades: list[dict]) -> float:
    shares = [active_share(list(t["weights"].values())) for t in trades if any(t["weights"].values())]
    return statistics.fmean(shares) if shares else 0.0


def _split_of(days: list[str]) -> int:
    return _ts(days[int(len(days) * 0.6)])


def _baselines(daily: dict, until_ts: int) -> dict[str, list[float]]:
    """Equal-weight and 12-month time-series momentum, in-sample only. Not trials."""
    assets = tuple(DAILY)
    days, C = _closes(daily, assets)
    ew, mom = [], []
    for t in range(252, len(days) - 5, 5):
        if _ts(days[t]) >= until_ts:
            break
        g = [_fwd(C[t, i], C[t + 5, i]) for i in range(C.shape[1])]
        good = [x for x in g if x is not None]
        if len(good) < 6:
            continue
        ew.append(statistics.fmean(good))
        signs = []
        for i, r in enumerate(g):
            m = _fwd(C[t - 252, i], C[t, i])
            if r is not None and m is not None and m != 0:
                signs.append((1.0 if m > 0 else -1.0) * r)
        if signs:
            mom.append(statistics.fmean(signs))
    return {"equal_weight": ew, "tsmom_12m": mom}


def _atr_sharpe(daily: dict, trades: list[dict], split_ts: int) -> float | None:
    cache: dict[str, tuple[dict[str, int], list]] = {}
    rets = []
    for t in trades:
        if t["ts_open"] < split_ts:
            continue
        acc = 0.0
        for sym, w in t["weights"].items():
            if abs(w) < 1e-12 or sym not in daily:
                continue
            if sym not in cache:
                bars = daily[sym]
                cache[sym] = ({_bar_day(b[0]): i for i, b in enumerate(bars)}, wilder_atr(bars))
            idx, atrs = cache[sym]
            bars = daily[sym]
            i0, i1 = idx.get(_bar_day(t["ts_open"])), idx.get(_bar_day(t["ts_close"]))
            if i0 is None or i1 is None:
                continue
            r = atr_normalized_return(bars[i0][4], bars[i1][4], atrs[i0])
            if r is not None:
                acc += w * r
        rets.append(acc)
    return round(sharpe(rets), 4) if len(rets) >= 5 else None


BUILDERS = {"H29": h29_book, "H30": h30_book, "H31": h31_book, "H32": h32_book}
TITLES = {
    "H29": "Cross-sectional momentum, inverse-vol, 15 bps turnover",
    "H30": "Black-Litterman momentum view, omega inverse to trailing IC",
    "H31": "Wick fade under vol compression, causal vol-state gate",
    "H32": "Gold/USD in high vol, crypto/equity momentum in low vol",
}


def _to_candidate(hid: str, trades: list[dict], split_ts: int, daily: dict) -> dict[str, Any]:
    end_ts = max(t["ts_close"] for t in trades)
    step = {"H29": 5, "H30": 21, "H31": 3, "H32": 5}[hid]
    c = _cand5(hid, "BOOK", TITLES[hid], trades, split_ts, 15.0, "yahoo_daily_price_safe",
               obs_per_year=252.0 / step, end_ts=end_ts, unit="rebalance")
    c["strategy_id"] = f"b6-{hid}-BOOK"
    oos_ew = [t["ew_ret"] for t in trades if t["ts_open"] >= split_ts]
    c["equal_weight_oos_sharpe"] = round(sharpe(oos_ew), 4)
    c["excess_vs_equal_weight_oos_sharpe"] = round(c["oos_sharpe"] - c["equal_weight_oos_sharpe"], 4)
    c["is_active_share"] = round(_mean_share([t for t in trades if t["ts_open"] < split_ts]), 4)
    c["atr_oos_sharpe"] = _atr_sharpe(daily, trades, split_ts)
    c["atr_sign_disagrees"] = bool(c["atr_oos_sharpe"] is not None and c["oos_sharpe"] != 0
                                   and (c["atr_oos_sharpe"] > 0) != (c["oos_sharpe"] > 0))
    c["map_elites_cell"] = {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}
    c["return_method"] = "percent, non-positive price days dropped per asset; ATR series is a receipt not a trial"
    _regime_pnl(c, daily.get("SPX") or [])
    return c


def evaluate_batch6(daily: dict) -> dict[str, Any]:
    """Screen on the in-sample date split, then spend an OOS trial only for admitted books."""
    ref_days, _ = _closes(daily, tuple(DAILY))
    split_ts = _split_of(ref_days)
    baselines = _baselines(daily, split_ts)
    admitted: list[dict[str, Any]] = []
    screened: list[dict[str, Any]] = []
    sibling_is: dict[str, list[float]] = {}
    for hid in ("H29", "H30", "H31", "H32"):
        probe = BUILDERS[hid](daily, until_ts=split_ts)
        is_rets = [t["ret"] for t in probe]
        share = _mean_share(probe)
        ok, reason = screen_book(is_rets, baselines, sibling_is, share, ACTIVE_MIN[hid])
        if not ok:
            screened.append({"hypothesis_id": hid, "strategy_id": f"b6-{hid}-BOOK", "counted_in_dsr": False,
                             "screen": reason, "is_observations": len(is_rets), "is_active_share": round(share, 4),
                             "cell": {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}})
            continue
        full = BUILDERS[hid](daily)
        cand = _to_candidate(hid, full, split_ts, daily)
        cand["screen"] = reason
        admitted.append(cand)
        sibling_is[hid] = is_rets
    return {"admitted": admitted, "screened": screened, "split_ts": split_ts,
            "nonpositive_days": _nonpositive_days(daily)}


def _nonpositive_days(daily: dict) -> dict[str, int]:
    out = {}
    for sym, bars in daily.items():
        n = sum(1 for b in bars if b[4] <= 0)
        if n:
            out[sym] = n
    return out


def _prior(root: Path) -> tuple[int, list[tuple[float, float]]]:
    n, rows = PRIOR_THROUGH_BATCH5, []
    try:
        b5 = json.loads((root / B5_OUT_REL).read_text(encoding="utf-8"))
        n = int(b5.get("n_trials_counted_in_dsr") or n)
        for c in b5.get("candidates") or []:
            opy = c.get("obs_per_year") or 1.0
            rows.append((c["oos_sharpe"], c["oos_sharpe"] * math.sqrt(max(1.0, opy))))
    except (OSError, ValueError, KeyError):
        pass
    return n, rows


def _score(cands: list[dict], root: Path) -> dict[str, Any]:
    n_prior, prior = _prior(root)
    n_trials = n_prior + len(cands)
    if cands:
        tr_obs = [c["oos_sharpe"] for c in cands] + [p[0] for p in prior]
        tr_ann = [c["oos_sharpe"] * math.sqrt(max(1.0, c["obs_per_year"])) for c in cands] + [p[1] for p in prior]
        for c in cands:
            v1 = deflated_sharpe(c["returns"], n_trials, tr_obs)
            v2 = deflated_sharpe_annualized(c["returns"], c["obs_per_year"], n_trials, tr_ann)
            c["dsr_per_observation"], c["dsr_annualized"] = v1, v2
            c["deflated_sharpe"] = min(v1, v2) if v1 is not None and v2 is not None else None
    pbo = time_aligned_pbo(cands) if len(cands) >= 2 else {"pbo": None, "included": [], "blocks": 16}
    for c in cands:
        ok = c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo["pbo"] is not None and pbo["pbo"] < 0.5
        c["gate"] = "PASS_STATS" if ok else "FAIL"
        c["gate_detail"] = f"oos_n={c['oos_trades']} DSR={c.get('deflated_sharpe')} PBO={pbo['pbo']}"
        c["param_perturbation_sharpe_retention"] = _perturb_retention(c, root)
    return {"n_prior": n_prior, "n_trials": n_trials, "pbo": pbo}


def _measured_retention(hid: str, daily: dict, split_ts: int, base: float) -> float | None:
    """+/-15% on the pre-registered lookback. A diagnostic rerun, not an additional counted trial."""
    if base <= 0:
        return None
    if hid == "H29":
        alt = h29_book(daily, lb=int(252 * 1.15))
    elif hid == "H30":
        alt = h30_book(daily, lb=int(252 * 1.15))
    elif hid == "H31":
        alt = h31_book(daily, wick=2.2 * 1.15)
    else:
        alt = h32_book(daily, vol_lb=int(20 * 1.15))
    alt_s = sharpe([t["ret"] for t in alt if t["ts_open"] >= split_ts])
    return round(min(alt_s, base) / base, 3)


def _perturb_retention(cand: dict, root: Path) -> float | None:
    return cand.get("param_perturbation_sharpe_retention")


def map_elites_grid(admitted: list[dict], screened: list[dict]) -> dict[str, Any]:
    cells = {h: {r: None for r in REGIMES} for h in HORIZONS}
    for c in admitted:
        cell = c["map_elites_cell"]
        slot = cells[cell["horizon"]][cell["regime"]]
        quality = c.get("is_sharpe") or 0.0
        if slot is None or quality > slot["is_sharpe"]:
            cells[cell["horizon"]][cell["regime"]] = {
                "strategy_id": c["strategy_id"], "hypothesis_id": c["hypothesis_id"],
                "is_sharpe": quality, "oos_sharpe": c["oos_sharpe"], "gate": c["gate"],
                "quality_definition": "IS Sharpe (admission). OOS Sharpe is reported and is not the archive key.",
            }
    occupied = sum(1 for h in cells.values() for v in h.values() if v)
    return {"schema": "ahos.map_elites_grid.v1", "paper_only": True,
            "descriptors": {"horizon": list(HORIZONS), "regime": list(REGIMES)},
            "cells_occupied": occupied, "cells_total": len(HORIZONS) * len(REGIMES),
            "empty_cells_mean": "no admitted strategy, not a zero-quality strategy",
            "grid": cells, "screened": screened}


def run_batch6(root: Path, daily: dict | None = None) -> dict[str, Any]:
    root = Path(root)
    errors: dict[str, str] = {}
    if daily is None:
        daily = {}
        for sym, (yahoo, _c) in {**DAILY, "DXY": ("DX-Y.NYB", 2.0)}.items():
            try:
                daily[sym] = fetch_daily_v(yahoo)
            except Exception as exc:  # noqa: BLE001 - a missing series is recorded, the book skips it
                errors[sym] = repr(exc)[:160]
    cache = {sym: {_bar_day(b[0]): b[4] for b in bars if b[4] > 0}
             for sym, bars in daily.items() if sym in ("SPX", "XAU", "BTC", "WTI")}
    cp = root / "reports" / "grok" / "M28" / "daily_close_cache.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"schema": "ahos.daily_close_cache.v1", "paper_only": True, "closes": cache}), encoding="utf-8")
    ev = evaluate_batch6(daily)
    for c in ev["admitted"]:
        c["param_perturbation_sharpe_retention"] = _measured_retention(c["hypothesis_id"], daily, ev["split_ts"], c["oos_sharpe"])
    scored = _score(ev["admitted"], root)
    # Retention needs a second causal run. It is not counted. None leaves the red-team vector failing closed.
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in ev["admitted"]]
    for c in clean:
        c.pop("weights", None)
    snap = {"schema": "ahos.strategy_lab.batch6.v1",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True,
            "pre_registered": "strategy_lab/hypotheses.py _B6 @ 2026-10-24 18:18 Tehran (before first run)",
            "return_method": "percent returns; a day with price <= 0 is dropped for that asset and weights are "
                             "renormalized. ATR-normalized dollar changes are reported as atr_oos_sharpe and are not a second trial.",
            "nonpositive_price_days": ev["nonpositive_days"],
            "screens": {"rho_max": RHO_MAX, "active_share_min": ACTIVE_MIN,
                        "rule": "screened hypotheses are not counted in n_trials_counted_in_dsr"},
            "n_trials_this_batch": len(clean), "n_trials_prior": scored["n_prior"],
            "n_trials_counted_in_dsr": scored["n_trials"],
            "pbo_cscv": scored["pbo"].get("pbo"), "pbo_detail": scored["pbo"],
            "screened": ev["screened"], "errors": errors, "candidates": clean,
            "promotion_rule": "OOS obs>=30 AND DSR>0.95 (89 prior + this batch's admitted trials) AND PBO<0.5 "
                              "AND excess over equal weight > 0 AND survives strategy_red_team"}
    out = root / B6_OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    grid = map_elites_grid(clean, ev["screened"])
    grid["generated_at"] = snap["generated_at"]
    gp = root / GRID_REL
    gp.write_text(json.dumps(grid, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _trail_port(C: np.ndarray, w: np.ndarray, t: int, lb: int) -> float:
    """Compounded portfolio return over the `lb` sessions ending at t, using only those sessions."""
    eq = 1.0
    for j in range(max(1, t - lb + 1), t + 1):
        day, ok = 0.0, False
        for i in range(len(w)):
            if w[i] == 0:
                continue
            r = _fwd(float(C[j - 1, i]), float(C[j, i]))
            if r is None:
                continue
            day += float(w[i]) * r
            ok = True
        if ok:
            eq *= 1.0 + day
    return eq - 1.0


def _gated_weights(previous: np.ndarray, proposed: np.ndarray, edge: float, *, tau: float, hurdle: float,
                   cost_bps: float) -> tuple[np.ndarray, float]:
    held = np.array(apply_weight_hysteresis(previous.tolist(), proposed.tolist(), tau), dtype=float)
    turn = 0.5 * float(np.abs(held - previous).sum())
    if not clears_cost_hurdle(edge, turn, cost_bps, multiple=hurdle):
        return previous, 0.0
    gross = float(np.abs(held).sum())
    return (held / gross if gross > 0 else previous), turn


def h33_book(daily: dict, *, step: int = 5, tau: float = TAU_REBAL, hurdle: float = HURDLE,
             until_ts: int | None = None) -> list[dict]:
    assets = ("SPX", "QQQ", "BTC", "ETH", "XAU")
    days, C = _closes(daily, assets)
    n, k = C.shape
    trades, w_prev = [], np.zeros(k)
    cost = B7_COST_BPS / 1e4
    ix = {a: i for i, a in enumerate(assets)}
    high_p = _causal_high_prob(C[:, ix["SPX"]])
    for t in range(252, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        raw = np.zeros(k)
        inv = []
        rets20 = []
        for i in range(k):
            window = [r for r in (_fwd(float(C[j - 1, i]), float(C[j, i])) for j in range(t - 19, t + 1)) if r is not None]
            if len(window) >= 15:
                rets20.append(window)
            mom = _fwd(float(C[t - 63, i]), float(C[t, i]))
            vol = statistics.pstdev(window) if len(window) >= 15 else 0.0
            if mom is not None and mom > 0 and vol > 0:
                inv.append((i, 1.0 / vol))
        crisis = False
        spx_20 = _fwd(float(C[t - 20, ix["SPX"]]), float(C[t, ix["SPX"]]))
        if spx_20 is not None and spx_20 < -0.08:
            crisis = True
        if high_p[t] is not None and high_p[t] >= 0.5:
            crisis = True
        if len(rets20) >= 3:
            m = np.array([r[-15:] for r in rets20])
            if m.shape[1] >= 15:
                c = np.corrcoef(m)
                if np.isfinite(c).all():
                    upper = c[np.triu_indices(len(c), 1)]
                    if len(upper) and float(np.mean(upper)) > 0.55:
                        crisis = True
        if crisis and math.isfinite(C[t, ix["XAU"]]):
            raw[ix["XAU"]] = 1.0
        elif inv:
            s = sum(v for _, v in inv)
            for i, v in inv:
                raw[i] = v / s
        proposed = raw if raw.sum() > 0 else w_prev
        edge = _trail_port(C, proposed, t, 20) - _trail_port(C, w_prev, t, 20)
        held, turn = _gated_weights(w_prev, proposed, edge, tau=tau, hurdle=hurdle, cost_bps=B7_COST_BPS)
        g = _g(C, t, step)
        w = _renorm(held, np.isfinite(g))
        if w is None:
            continue
        ret = float(np.nansum(w * g)) - turn * cost
        trades.append(_trade(days, t, step, ret, w, assets, float(np.nanmean(g))))
        trades[-1]["turnover"] = turn
        w_prev = w
    return trades


def h34_book(daily: dict, *, hurdle: float = HURDLE, until_ts: int | None = None) -> list[dict]:
    assets = tuple(a for a in DAILY if a not in H31_SKIP)
    days, C = _closes(daily, assets)
    ohlc = {a: {_bar_day(b[0]): b for b in daily.get(a) or []} for a in assets}
    atr = {a: {_bar_day(b[0]): v for b, v in zip(daily.get(a) or [], wilder_atr(daily.get(a) or []))} for a in assets}
    open_pos: dict[str, dict] = {}
    trades: list[dict] = []
    for t in range(60, len(days)):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        for i, a in enumerate(assets):
            bar = ohlc[a].get(days[t])
            if bar is None:
                continue
            pos = open_pos.get(a)
            if pos is not None:
                pos["peak"] = max(pos["peak"], bar[4])
                a_tr = atr[a].get(days[t])
                if a_tr and bar[4] < pos["peak"] - 3.0 * a_tr and t > pos["t"]:
                    ret = _fwd(pos["entry"], bar[4])
                    if ret is not None:
                        cost = 2.0 * DAILY[a][1] / 1e4
                        window = _g(C, pos["t"], t - pos["t"])
                        ew = float(np.nanmean(window)) if np.isfinite(window).any() else 0.0
                        w = np.zeros(len(assets))
                        w[i] = 1.0
                        trades.append(_trade(days, pos["t"], t - pos["t"], ret - cost, w, assets, ew))
                        trades[-1]["turnover"] = 1.0
                    del open_pos[a]
                continue
            highs20, highs55, vols = [], [], []
            for j in range(t - 55, t):
                b = ohlc[a].get(days[j])
                if b is None:
                    continue
                if j >= t - 20:
                    highs20.append(b[2])
                    vols.append(b[5])
                highs55.append(b[2])
            if len(highs20) < 15 or len(highs55) < 40:
                continue
            channel = max(max(highs20), max(highs55))
            a_tr = atr[a].get(days[t])
            if not a_tr or channel <= 0 or bar[4] <= channel:
                continue
            if (bar[2] - bar[3]) < 1.2 * a_tr:
                continue
            vol_mean = statistics.fmean(vols) if vols else 0.0
            if vol_mean > 0 and bar[5] <= vol_mean:
                continue
            distance = bar[4] / channel - 1.0
            round_trip = 2.0 * DAILY[a][1] / 1e4
            if distance <= hurdle * round_trip:
                continue
            open_pos[a] = {"t": t, "entry": bar[4], "peak": bar[4]}
    return trades


def h35_book(daily: dict, *, step: int = 21, tau: float = TAU_REBAL, hurdle: float = HURDLE,
             until_ts: int | None = None) -> list[dict]:
    assets = ("SPX", "QQQ", "DAX", "N225", "XAU", "BRENT", "BTC", "ETH")
    days, C = _closes(daily, assets)
    n, k = C.shape
    trades, w_prev = [], np.zeros(k)
    cost = B7_COST_BPS / 1e4
    xau = assets.index("XAU")
    for t in range(252, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        scored = []
        for i in range(k):
            mom = _fwd(float(C[t - 252, i]), float(C[t, i]))
            if mom is not None and mom > 0:
                scored.append((mom, i))
        scored.sort(reverse=True)
        raw = np.zeros(k)
        picks = [i for _, i in scored[:2]]
        if picks:
            for i in picks:
                raw[i] = 1.0 / len(picks)
        elif math.isfinite(C[t, xau]):
            raw[xau] = 1.0
        edge = _trail_port(C, raw if raw.sum() else w_prev, t, 63) - _trail_port(C, w_prev, t, 63)
        held, turn = _gated_weights(w_prev, raw if raw.sum() else w_prev, edge, tau=tau, hurdle=hurdle, cost_bps=B7_COST_BPS)
        g = _g(C, t, step)
        w = _renorm(held, np.isfinite(g))
        if w is None:
            continue
        ret = float(np.nansum(w * g)) - turn * cost
        trades.append(_trade(days, t, step, ret, w, assets, float(np.nanmean(g))))
        trades[-1]["turnover"] = turn
        w_prev = w
    return trades


def h36_book(daily: dict, *, step: int = 5, tau: float = TAU_REBAL, hurdle: float = HURDLE,
             until_ts: int | None = None) -> list[dict]:
    assets = ("BTC", "ETH", "XAU", "SPX", "QQQ")
    days, C = _closes(daily, assets)
    n, k = C.shape
    trades, w_prev = [], np.ones(k) / k
    cost = B7_COST_BPS / 1e4
    spx = assets.index("SPX")
    for t in range(252, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        short = [r for r in (_fwd(float(C[j - 1, spx]), float(C[j, spx])) for j in range(t - 4, t + 1)) if r is not None]
        long = [r for r in (_fwd(float(C[j - 1, spx]), float(C[j, spx])) for j in range(t - 19, t + 1)) if r is not None]
        compressed = len(short) >= 4 and len(long) >= 15 and statistics.pstdev(short) < 0.8 * statistics.pstdev(long)
        raw = np.ones(k) / k
        if compressed:
            agree = []
            for i in range(k):
                signs = []
                for lb in (21, 63, 252):
                    m = _fwd(float(C[t - lb, i]), float(C[t, i]))
                    signs.append(0 if m is None or m == 0 else (1 if m > 0 else -1))
                if signs[0] != 0 and len(set(signs)) == 1:
                    agree.append((i, signs[0]))
            if sum(1 for _, s in agree if s != 0) >= 2:
                raw = np.zeros(k)
                for i, s in agree:
                    raw[i] = 2.0 if s > 0 else 0.0
                for i in range(k):
                    if all(i != a for a, _ in agree):
                        raw[i] = 1.0
        edge = _trail_port(C, raw, t, 20) - _trail_port(C, w_prev, t, 20)
        held, turn = _gated_weights(w_prev, raw, edge, tau=tau, hurdle=hurdle, cost_bps=B7_COST_BPS)
        g = _g(C, t, step)
        w = _renorm(held, np.isfinite(g))
        if w is None:
            continue
        ret = float(np.nansum(w * g)) - turn * cost
        trades.append(_trade(days, t, step, ret, w, assets, float(np.nanmean(g))))
        trades[-1]["turnover"] = turn
        w_prev = w
    return trades


B7_BUILDERS = {"H33": h33_book, "H34": h34_book, "H35": h35_book, "H36": h36_book}
B7_TITLES = {
    "H33": "Low-turnover vol-scaled core, cost-gated crash sleeve",
    "H34": "Donchian breakout, chandelier stop, cost deadband",
    "H35": "Monthly dual momentum, cost deadband",
    "H36": "Equal-weight tilt only when three horizons agree in compressed vol",
}


def _to_candidate7(hid: str, trades: list[dict], split_ts: int, daily: dict) -> dict[str, Any]:
    end_ts = max(t["ts_close"] for t in trades)
    step = {"H33": 5, "H34": 10, "H35": 21, "H36": 5}[hid]
    c = _cand5(hid, "BOOK", B7_TITLES[hid], trades, split_ts, B7_COST_BPS, "yahoo_daily_price_safe",
               obs_per_year=252.0 / step, end_ts=end_ts, unit="rebalance" if hid != "H34" else "completed_breakout")
    c["strategy_id"] = f"b7-{hid}-BOOK"
    oos = [t for t in trades if t["ts_open"] >= split_ts]
    oos_ew = [t["ew_ret"] for t in oos]
    c["equal_weight_oos_sharpe"] = round(sharpe(oos_ew), 4)
    c["excess_vs_equal_weight_oos_sharpe"] = round(c["oos_sharpe"] - c["equal_weight_oos_sharpe"], 4)
    c["is_active_share"] = round(_mean_share([t for t in trades if t["ts_open"] < split_ts]), 4)
    c["rebalance_count"] = sum(1 for t in trades if t.get("turnover", 0) > 0)
    c["mean_turnover"] = round(statistics.fmean([t.get("turnover", 0.0) for t in trades]), 4) if trades else 0.0
    c["map_elites_cell"] = {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}
    c["return_method"] = "percent; deadband 0.05 and 2.5x round-trip cost hurdle; ATR is not a second trial"
    c["atr_oos_sharpe"] = None
    _regime_pnl(c, daily.get("SPX") or [])
    return c


def _batch6_is_paths(daily: dict, split_ts: int) -> dict[str, list[float]]:
    """In-sample paths of the already-counted batch-6 books. Not new trials."""
    out = {}
    for hid, fn in BUILDERS.items():
        out[hid] = [t["ret"] for t in fn(daily, until_ts=split_ts)]
    return out


def evaluate_batch7(daily: dict) -> dict[str, Any]:
    ref_days, _ = _closes(daily, tuple(DAILY))
    split_ts = _split_of(ref_days)
    baselines = {**_baselines(daily, split_ts), **_batch6_is_paths(daily, split_ts)}
    admitted, screened, sibling = [], [], {}
    for hid in ("H33", "H34", "H35", "H36"):
        probe = B7_BUILDERS[hid](daily, until_ts=split_ts)
        is_rets = [t["ret"] for t in probe]
        share = _mean_share(probe)
        ok, reason = screen_book(is_rets, baselines, sibling, share, ACTIVE_MIN[hid])
        if not ok:
            screened.append({"hypothesis_id": hid, "strategy_id": f"b7-{hid}-BOOK", "counted_in_dsr": False,
                             "screen": reason, "is_observations": len(is_rets), "is_active_share": round(share, 4),
                             "cell": {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}})
            continue
        full = B7_BUILDERS[hid](daily)
        cand = _to_candidate7(hid, full, split_ts, daily)
        cand["screen"] = reason
        admitted.append(cand)
        sibling[hid] = is_rets
    return {"admitted": admitted, "screened": screened, "split_ts": split_ts}


def _prior7(root: Path) -> tuple[int, list[tuple[float, float]]]:
    n, rows = 93, []
    for rel in (B5_OUT_REL, B6_OUT_REL):
        try:
            doc = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if rel == B6_OUT_REL:
            n = int(doc.get("n_trials_counted_in_dsr") or n)
        for c in doc.get("candidates") or []:
            opy = c.get("obs_per_year") or 1.0
            rows.append((float(c["oos_sharpe"]), float(c["oos_sharpe"]) * math.sqrt(max(1.0, opy))))
    return n, rows


def _score7(cands: list[dict], root: Path) -> dict[str, Any]:
    n_prior, prior = _prior7(root)
    n_trials = n_prior + len(cands)
    if cands:
        tr_obs = [c["oos_sharpe"] for c in cands] + [p[0] for p in prior]
        tr_ann = [c["oos_sharpe"] * math.sqrt(max(1.0, c["obs_per_year"])) for c in cands] + [p[1] for p in prior]
        for c in cands:
            v1 = deflated_sharpe(c["returns"], n_trials, tr_obs)
            v2 = deflated_sharpe_annualized(c["returns"], c["obs_per_year"], n_trials, tr_ann)
            c["dsr_per_observation"], c["dsr_annualized"] = v1, v2
            c["deflated_sharpe"] = min(v1, v2) if v1 is not None and v2 is not None else None
    legacy = []
    pbo_note = "PBO uses this batch's admitted paths only"
    pbo = time_aligned_pbo(cands) if len(cands) >= 2 else {"pbo": None, "included": [], "blocks": 16}
    pbo["scope"] = "batch7_admitted_only"
    pbo["note"] = pbo_note
    for c in cands:
        ok = (c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo.get("pbo") is not None
              and pbo["pbo"] < 0.5 and (c.get("excess_vs_equal_weight_oos_sharpe") or 0) > 0)
        c["gate"] = "PASS_STATS" if ok else "FAIL"
        c["gate_detail"] = f"oos_n={c['oos_trades']} DSR={c.get('deflated_sharpe')} PBO={pbo.get('pbo')} excess={c.get('excess_vs_equal_weight_oos_sharpe')}"
    return {"n_prior": n_prior, "n_trials": n_trials, "pbo": pbo, "legacy_unused": len(legacy),
            "trial_sharpes_used": len(prior) + len(cands),
            "trial_sharpe_note": "SR0 uses the counted trial total. The variance uses stored OOS Sharpes from batches 5 and 6 plus this batch, which is fewer than the counted total."}


def merge_map_elites_grid(prior_rows: list[dict], new_rows: list[dict], screened: list[dict]) -> dict[str, Any]:
    cells: dict[str, dict[str, Any]] = {h: {r: None for r in REGIMES} for h in HORIZONS}
    challengers = []
    for c in prior_rows + new_rows:
        cell = c.get("map_elites_cell") or {}
        h, r = cell.get("horizon"), cell.get("regime")
        if h not in cells or r not in cells[h]:
            continue
        quality = float(c.get("is_sharpe") or 0.0)
        slot = cells[h][r]
        row = {"strategy_id": c["strategy_id"], "hypothesis_id": c["hypothesis_id"], "is_sharpe": quality,
               "oos_sharpe": c.get("oos_sharpe"), "gate": c.get("gate"),
               "quality_definition": "IS Sharpe (admission). OOS Sharpe is reported and is not the archive key."}
        if slot is None or quality > float(slot["is_sharpe"]):
            if slot is not None:
                challengers.append({"cell": {"horizon": h, "regime": r}, "kept": c["hypothesis_id"], "displaced": slot["hypothesis_id"]})
            cells[h][r] = row
        else:
            challengers.append({"cell": {"horizon": h, "regime": r}, "kept": slot["hypothesis_id"], "challenger": c["hypothesis_id"],
                                "challenger_is_sharpe": quality})
    occupied = sum(1 for h in cells.values() for v in h.values() if v)
    return {"schema": "ahos.map_elites_grid.v1", "paper_only": True,
            "descriptors": {"horizon": list(HORIZONS), "regime": list(REGIMES)},
            "cells_occupied": occupied, "cells_total": 9,
            "empty_cells_mean": "no admitted strategy, not a zero-quality strategy",
            "intraday_empty_reason": "daily bars have no intraday session; those three cells stay empty",
            "grid": cells, "screened": screened, "challengers": challengers}


def run_batch7(root: Path, daily: dict | None = None) -> dict[str, Any]:
    root = Path(root)
    errors: dict[str, str] = {}
    if daily is None:
        import time
        daily = {}
        symbols = {**DAILY, "DXY": ("DX-Y.NYB", 2.0)}
        for _attempt in range(3):
            errors = {}
            for sym, (yahoo, _c) in symbols.items():
                if sym in daily:
                    continue
                try:
                    daily[sym] = fetch_daily_v(yahoo)
                except Exception as exc:  # noqa: BLE001
                    errors[sym] = repr(exc)[:160]
            if not errors:
                break
            time.sleep(2)
    ev = evaluate_batch7(daily)
    for c in ev["admitted"]:
        base = c["oos_sharpe"]
        alt = B7_BUILDERS[c["hypothesis_id"]](daily, hurdle=HURDLE * 1.15)
        alt_s = sharpe([t["ret"] for t in alt if t["ts_open"] >= ev["split_ts"]])
        c["param_perturbation_sharpe_retention"] = None if base <= 0 else round(min(alt_s, base) / base, 3)
    scored = _score7(ev["admitted"], root)
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in ev["admitted"]]
    for c in clean:
        c.pop("weights", None)
    snap = {"schema": "ahos.strategy_lab.batch7.v1",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True,
            "pre_registered": "strategy_lab/hypotheses.py _B7 @ 2026-10-24 19:45 Tehran (before first run)",
            "deadband": {"tau": TAU_REBAL, "cost_hurdle_multiple": HURDLE, "cost_bps": B7_COST_BPS},
            "cell_note": "H33-H35 use their pre-registered cells even where batch 6 already sits. H36 is swing_2_5d x vol_compression_carry. Intraday cells stay empty.",
            "n_trials_this_batch": len(clean), "n_trials_prior": scored["n_prior"],
            "n_trials_counted_in_dsr": scored["n_trials"],
            "trial_sharpes_used": scored["trial_sharpes_used"], "trial_sharpe_note": scored["trial_sharpe_note"],
            "pbo_cscv": scored["pbo"].get("pbo"), "pbo_detail": scored["pbo"],
            "screened": ev["screened"], "errors": errors, "candidates": clean,
            "promotion_rule": "OOS obs>=30 AND DSR>0.95 AND PBO<0.5 AND excess over equal weight > 0 AND survives strategy_red_team"}
    out = root / B7_OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    prior_rows, b6s = [], []
    try:
        b6 = json.loads((root / B6_OUT_REL).read_text(encoding="utf-8"))
        prior_rows = b6.get("candidates") or []
        b6s = b6.get("screened") or []
    except (OSError, ValueError):
        pass
    grid = merge_map_elites_grid(prior_rows, clean, list(b6s) + ev["screened"])
    grid["generated_at"] = snap["generated_at"]
    (root / GRID_REL).write_text(json.dumps(grid, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _l1_gate(previous: np.ndarray, proposed: np.ndarray, edge: float, tau_l1: float, hurdle: float):
    """Hold the whole book unless portfolio L1 turnover clears tau_l1 and the cost hurdle."""
    held = np.array(apply_portfolio_l1_gate(previous.tolist(), proposed.tolist(), tau_l1), dtype=float)
    turn = portfolio_l1_turnover(previous.tolist(), held.tolist())
    if not clears_cost_hurdle(edge, turn, B7_COST_BPS, multiple=hurdle):
        return previous, 0.0
    gross = float(np.abs(held).sum())
    return (held / gross if gross > 0 else previous), turn


def _htrade(ts_open: int, ts_close: int, ret: float, w: np.ndarray, assets: tuple[str, ...], ew: float) -> dict:
    return {"ts_open": int(ts_open), "ts_close": int(ts_close), "ret": float(ret), "d": 1,
            "weights": {a: round(float(w[i]), 4) for i, a in enumerate(assets)}, "ew_ret": float(ew),
            "bar_interval": "1h"}


def align_hours(hourly: dict, assets: tuple[str, ...] = HOUR_ASSETS) -> dict | None:
    """Intersection of hour stamps. A missing name yields None. Daily bars are not accepted here."""
    maps = {}
    for a in assets:
        bucket = {}
        for b in hourly.get(a) or []:
            if len(b) < 6:
                continue
            bucket[int(b[0] // 3600) * 3600] = b
        maps[a] = bucket
    if any(len(maps[a]) < 100 for a in assets):
        return None
    keys = set.intersection(*(set(maps[a]) for a in assets))
    ts = sorted(keys)
    if len(ts) < 400:
        return None
    k, n = len(assets), len(ts)
    C, H, L = (np.full((n, k), np.nan) for _ in range(3))
    V = np.zeros((n, k))
    series = {a: [] for a in assets}
    for t, stamp in enumerate(ts):
        for i, a in enumerate(assets):
            b = maps[a][stamp]
            H[t, i], L[t, i], C[t, i], V[t, i] = b[2], b[3], b[4], b[5]
            series[a].append(b)
    return {"ts": ts, "C": C, "H": H, "L": L, "V": V, "atr": {a: wilder_atr(series[a]) for a in assets},
            "assets": assets, "span_utc": (_day(ts[0]), _day(ts[-1]))}


def h37_book(daily: dict, *, step: int = 5, tau_l1: float = TAU_L1, hurdle: float = HURDLE,
             until_ts: int | None = None) -> list[dict]:
    """H33 core plus a 25% Donchian satellite. The gate is portfolio L1, not a per-asset band."""
    assets = ("SPX", "QQQ", "BTC", "ETH", "XAU")
    if any(a not in daily or len(daily.get(a) or []) < 300 for a in assets):
        return []
    days, C = _closes(daily, assets)
    n, k = C.shape
    trades, w_prev = [], np.zeros(k)
    cost = B7_COST_BPS / 1e4
    ix = {a: i for i, a in enumerate(assets)}
    high_p = _causal_high_prob(C[:, ix["SPX"]])
    ohlc = {a: {_bar_day(b[0]): b for b in daily[a]} for a in assets}
    atr = {a: {_bar_day(b[0]): v for b, v in zip(daily[a], wilder_atr(daily[a]))} for a in assets}
    for t in range(252, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        raw = np.zeros(k)
        inv, rets20 = [], []
        for i in range(k):
            window = [r for r in (_fwd(float(C[j - 1, i]), float(C[j, i])) for j in range(t - 19, t + 1)) if r is not None]
            if len(window) >= 15:
                rets20.append(window)
            mom = _fwd(float(C[t - 63, i]), float(C[t, i]))
            vol = statistics.pstdev(window) if len(window) >= 15 else 0.0
            if mom is not None and mom > 0 and vol > 0:
                inv.append((i, 1.0 / vol))
        crisis = False
        spx_20 = _fwd(float(C[t - 20, ix["SPX"]]), float(C[t, ix["SPX"]]))
        if spx_20 is not None and spx_20 < -0.08:
            crisis = True
        if high_p[t] is not None and high_p[t] >= 0.5:
            crisis = True
        if len(rets20) >= 3:
            m = np.array([r[-15:] for r in rets20])
            if m.shape[1] >= 15:
                corr = np.corrcoef(m)
                if np.isfinite(corr).all():
                    upper = corr[np.triu_indices(len(corr), 1)]
                    if len(upper) and float(np.mean(upper)) > 0.55:
                        crisis = True
        if crisis and math.isfinite(C[t, ix["XAU"]]):
            raw[ix["XAU"]] = 1.0
        elif inv:
            s = sum(v for _, v in inv)
            for i, v in inv:
                raw[i] = v / s
            best_i, best_dist = None, 0.0
            for i, a in enumerate(assets):
                bar, a_tr = ohlc[a].get(days[t]), atr[a].get(days[t])
                prior = [ohlc[a][days[j]][2] for j in range(t - 20, t) if days[j] in ohlc[a]]
                if not bar or not a_tr or a_tr <= 0 or len(prior) < 15:
                    continue
                hi = max(prior)
                if hi > 0 and bar[4] > hi and (bar[2] - bar[3]) > 1.2 * a_tr:
                    dist = bar[4] / hi - 1.0
                    if dist > best_dist:
                        best_i, best_dist = i, dist
            if best_i is not None:
                raw = raw * 0.75
                raw[best_i] += 0.25
                raw = raw / raw.sum()
        proposed = raw if raw.sum() > 0 else w_prev
        edge = _trail_port(C, proposed, t, 20) - _trail_port(C, w_prev, t, 20)
        held, turn = _l1_gate(w_prev, proposed, edge, tau_l1, hurdle)
        g = _g(C, t, step)
        w = _renorm(held, np.isfinite(g))
        if w is None:
            continue
        ret = float(np.nansum(w * g)) - turn * cost
        trades.append(_trade(days, t, step, ret, w, assets, float(np.nanmean(g))))
        trades[-1]["turnover"] = turn
        trades[-1]["bar_interval"] = "1d"
        w_prev = w
    return trades


def h38_book(hourly: dict, *, hurdle: float = HURDLE, until_ts: int | None = None) -> list[dict]:
    """Completed 1h breakouts only. Hold is at least 4 hours and at most 12. Flat time is not a cash return."""
    panel = align_hours(hourly)
    if panel is None:
        return []
    ts, C, H, L, V, atr = panel["ts"], panel["C"], panel["H"], panel["L"], panel["V"], panel["atr"]
    assets, trades, open_pos = HOUR_ASSETS, [], {}
    for t in range(60, len(ts)):
        if until_ts is not None and ts[t] >= until_ts:
            break
        for i, a in enumerate(assets):
            a_tr = atr[a][t]
            pos = open_pos.get(i)
            if pos is not None:
                pos["peak"] = max(pos["peak"], float(C[t, i]))
                held_h = t - pos["t"]
                if a_tr and held_h >= 4 and (held_h >= 12 or float(C[t, i]) < pos["peak"] - 3.0 * a_tr):
                    ret = _fwd(pos["entry"], float(C[t, i]))
                    if ret is not None:
                        w = np.zeros(len(assets))
                        w[i] = 1.0
                        window = _g(C, pos["t"], held_h)
                        ew = float(np.nanmean(window)) if np.isfinite(window).any() else 0.0
                        trades.append(_htrade(ts[pos["t"]], ts[t], ret - 2.0 * B7_COST_BPS / 1e4, w, assets, ew))
                        trades[-1]["turnover"] = 1.0
                    del open_pos[i]
                continue
            if not a_tr or a_tr <= 0:
                continue
            hi = float(np.nanmax(H[t - 55:t, i]))
            vol_avg = float(np.mean(V[t - 20:t, i]))
            dist = float(C[t, i]) / hi - 1.0 if hi > 0 else 0.0
            if (hi > 0 and float(C[t, i]) > hi and (H[t, i] - L[t, i]) > 1.2 * a_tr
                    and (vol_avg <= 0 or V[t, i] > vol_avg)
                    and clears_cost_hurdle(dist, 1.0, B7_COST_BPS, multiple=hurdle)):
                open_pos[i] = {"t": t, "entry": float(C[t, i]), "peak": float(C[t, i])}
    return trades


def _hour_weights(C: np.ndarray, t: int, compressed: bool) -> np.ndarray:
    k = C.shape[1]
    raw = np.zeros(k)
    vols = []
    for i in range(k):
        window = [r for r in (_fwd(float(C[j - 1, i]), float(C[j, i])) for j in range(t - 11, t + 1)) if r is not None]
        vol = statistics.pstdev(window) if len(window) >= 8 else 0.0
        mom = _fwd(float(C[t - 24, i]), float(C[t, i]))
        if vol > 0:
            vols.append((vol, i))
        if compressed and mom is not None and mom > 0 and vol > 0:
            raw[i] = 1.0 / vol
    if raw.sum() > 0:
        return raw / raw.sum()
    if vols:
        raw[min(vols)[1]] = 1.0
    return raw


def h39_book(hourly: dict, *, step: int = 6, tau_l1: float = TAU_L1, hurdle: float = HURDLE,
             until_ts: int | None = None) -> list[dict]:
    panel = align_hours(hourly)
    if panel is None:
        return []
    ts, C, assets = panel["ts"], panel["C"], HOUR_ASSETS
    trades, w_prev, cost = [], np.zeros(C.shape[1]), B7_COST_BPS / 1e4
    spx = assets.index("SPX")
    for t in range(48, len(ts) - step, step):
        if until_ts is not None and ts[t] >= until_ts:
            break
        spx_w = [r for r in (_fwd(float(C[j - 1, spx]), float(C[j, spx])) for j in range(t - 47, t + 1)) if r is not None]
        vol_s = statistics.pstdev(spx_w[-12:]) if len(spx_w) >= 12 else 0.0
        vol_l = statistics.pstdev(spx_w) if len(spx_w) >= 24 else 0.0
        proposed = _hour_weights(C, t, bool(vol_l > 0 and vol_s < 0.8 * vol_l))
        if proposed.sum() <= 0:
            proposed = w_prev
        edge = _trail_port(C, proposed, t, 12) - _trail_port(C, w_prev, t, 12)
        held, turn = _l1_gate(w_prev, proposed, edge, tau_l1, hurdle)
        g = _g(C, t, step)
        w = _renorm(held, np.isfinite(g))
        if w is None:
            continue
        trades.append(_htrade(ts[t], ts[min(t + step, len(ts) - 1)], float(np.nansum(w * g)) - turn * cost, w, assets, float(np.nanmean(g))))
        trades[-1]["turnover"] = turn
        w_prev = w
    return trades


def h40_book(hourly: dict, *, step: int = 8, tau_l1: float = TAU_L1, hurdle: float = HURDLE,
             until_ts: int | None = None) -> list[dict]:
    panel = align_hours(hourly)
    if panel is None:
        return []
    ts, C, assets = panel["ts"], panel["C"], HOUR_ASSETS
    trades, w_prev, cost = [], np.zeros(C.shape[1]), B7_COST_BPS / 1e4
    k = C.shape[1]
    xau = assets.index("XAU")
    for t in range(48, len(ts) - step, step):
        if until_ts is not None and ts[t] >= until_ts:
            break
        last6 = [_fwd(float(C[t - 6, i]), float(C[t, i])) for i in range(k)]
        last6 = [r for r in last6 if r is not None]
        crisis = bool(last6) and float(np.mean(last6)) < -0.015
        if not crisis:
            mats = []
            for i in range(k):
                window = [r for r in (_fwd(float(C[j - 1, i]), float(C[j, i])) for j in range(t - 11, t + 1)) if r is not None]
                if len(window) >= 8:
                    mats.append(window[-8:])
            if len(mats) >= 3:
                corr = np.corrcoef(np.array(mats))
                if np.isfinite(corr).all():
                    upper = corr[np.triu_indices(len(corr), 1)]
                    crisis = bool(len(upper) and float(np.mean(upper)) > 0.55)
        raw = np.zeros(k)
        if crisis and math.isfinite(C[t, xau]):
            raw[xau] = 1.0
        else:
            for i in range(k):
                mom = _fwd(float(C[t - 24, i]), float(C[t, i]))
                if mom is not None and mom > 0:
                    raw[i] = 1.0
            if raw.sum() > 0:
                raw = raw / raw.sum()
        proposed = raw if raw.sum() > 0 else w_prev
        edge = _trail_port(C, proposed, t, 12) - _trail_port(C, w_prev, t, 12)
        held, turn = _l1_gate(w_prev, proposed, edge, tau_l1, hurdle)
        g = _g(C, t, step)
        w = _renorm(held, np.isfinite(g))
        if w is None:
            continue
        trades.append(_htrade(ts[t], ts[min(t + step, len(ts) - 1)], float(np.nansum(w * g)) - turn * cost, w, assets, float(np.nanmean(g))))
        trades[-1]["turnover"] = turn
        w_prev = w
    return trades


B8_BUILDERS = {"H37": h37_book, "H38": h38_book, "H39": h39_book, "H40": h40_book}
B8_TITLES = {
    "H37": "Core plus Donchian satellite, portfolio L1 gate",
    "H38": "Hourly Donchian breakout, 4h to 12h hold",
    "H39": "Hourly vol-compression carry, portfolio L1 gate",
    "H40": "Hourly stress sleeve into XAU, portfolio L1 gate",
}


def _batch7_is_paths(daily: dict, split_ts: int) -> dict[str, list[float]]:
    """In-sample paths of the already-counted batch-7 books. Not new trials."""
    return {hid: [t["ret"] for t in fn(daily, until_ts=split_ts)] for hid, fn in B7_BUILDERS.items()}


def _to_candidate8(hid: str, trades: list[dict], split_ts: int, regime_bars) -> dict[str, Any]:
    step = {"H37": 5, "H38": 8, "H39": 6, "H40": 8}[hid]
    session_hours = 6.5 if hid != "H37" else None
    obs = 252.0 / step if hid == "H37" else (252.0 * session_hours) / step
    end_ts = max(t["ts_close"] for t in trades)
    c = _cand5(hid, "BOOK", B8_TITLES[hid], trades, split_ts, B7_COST_BPS, "yahoo_1h" if hid != "H37" else "yahoo_daily_price_safe",
               obs_per_year=obs, end_ts=end_ts, unit="completed_breakout" if hid == "H38" else "rebalance")
    c["strategy_id"] = f"b8-{hid}-BOOK"
    oos = [t for t in trades if t["ts_open"] >= split_ts]
    oos_ew = [t["ew_ret"] for t in oos]
    c["equal_weight_oos_sharpe"] = round(sharpe(oos_ew), 4)
    c["excess_vs_equal_weight_oos_sharpe"] = round(c["oos_sharpe"] - c["equal_weight_oos_sharpe"], 4)
    c["is_active_share"] = round(_mean_share([t for t in trades if t["ts_open"] < split_ts]), 4)
    c["rebalance_count"] = sum(1 for t in trades if t.get("turnover", 0) > 0)
    c["mark_count"] = len(trades)
    c["mean_turnover"] = round(statistics.fmean([t.get("turnover", 0.0) for t in trades]), 4) if trades else 0.0
    c["map_elites_cell"] = {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}
    c["bar_interval"] = "1d" if hid == "H37" else "1h"
    c["gate_method"] = "completed_breakout" if hid == "H38" else "portfolio_l1"
    c["tau_l1"] = None if hid == "H38" else TAU_L1
    c["return_method"] = "percent; portfolio L1 gate 0.25 and 2.5x cost hurdle; 1h books use Yahoo 1h bars"
    c["atr_oos_sharpe"] = None
    _regime_pnl(c, regime_bars or [])
    return c


def evaluate_batch8(daily: dict, hourly: dict) -> dict[str, Any]:
    ref_days, _ = _closes(daily, tuple(DAILY))
    split_daily = _split_of(ref_days)
    baselines = {**_baselines(daily, split_daily), **_batch6_is_paths(daily, split_daily), **_batch7_is_paths(daily, split_daily)}
    admitted, screened, sibling = [], [], {}
    probe = h37_book(daily, until_ts=split_daily)
    share = _mean_share(probe)
    ok, reason = screen_book([t["ret"] for t in probe], baselines, sibling, share, ACTIVE_MIN["H37"])
    if not ok:
        screened.append({"hypothesis_id": "H37", "strategy_id": "b8-H37-BOOK", "counted_in_dsr": False,
                         "screen": reason, "is_observations": len(probe), "is_active_share": round(share, 4),
                         "cell": {"horizon": "macro_weekly", "regime": "vol_compression_carry"}, "bar_interval": "1d"})
    else:
        full = h37_book(daily)
        cand = _to_candidate8("H37", full, split_daily, daily.get("SPX") or [])
        cand["screen"] = reason
        admitted.append(cand)
        sibling["H37"] = [t["ret"] for t in probe]
    panel = align_hours(hourly)
    split_h = panel["ts"][int(len(panel["ts"]) * 0.6)] if panel else None
    hour_siblings: dict[str, list[float]] = {}
    for hid, fn in (("H38", h38_book), ("H39", h39_book), ("H40", h40_book)):
        if panel is None:
            screened.append({"hypothesis_id": hid, "strategy_id": f"b8-{hid}-BOOK", "counted_in_dsr": False,
                             "screen": "incomplete_1h_universe", "is_observations": 0, "is_active_share": 0.0,
                             "cell": {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}, "bar_interval": "1h"})
            continue
        probe_h = fn(hourly, until_ts=split_h)
        share_h = _mean_share(probe_h)
        # Hourly IS paths are not correlated with daily books: the observation unit is different.
        ok_h, reason_h = screen_book([t["ret"] for t in probe_h], {}, hour_siblings, share_h, ACTIVE_MIN[hid])
        if not ok_h:
            screened.append({"hypothesis_id": hid, "strategy_id": f"b8-{hid}-BOOK", "counted_in_dsr": False,
                             "screen": reason_h, "is_observations": len(probe_h), "is_active_share": round(share_h, 4),
                             "cell": {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}, "bar_interval": "1h"})
            continue
        full_h = fn(hourly)
        cand = _to_candidate8(hid, full_h, split_h, hourly.get("SPX") or [])
        cand["screen"] = reason_h
        cand["hour_span_utc"] = list(panel["span_utc"])
        admitted.append(cand)
        hour_siblings[hid] = [t["ret"] for t in probe_h]
    return {"admitted": admitted, "screened": screened, "split_daily": split_daily, "split_h": split_h,
            "hour_span": None if panel is None else list(panel["span_utc"])}


def _prior8(root: Path) -> tuple[int, list[tuple[float, float]]]:
    n, rows = 96, []
    for rel in (B5_OUT_REL, B6_OUT_REL, B7_OUT_REL):
        try:
            doc = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if rel == B7_OUT_REL:
            n = int(doc.get("n_trials_counted_in_dsr") or n)
        for c in doc.get("candidates") or []:
            opy = c.get("obs_per_year") or 1.0
            rows.append((float(c["oos_sharpe"]), float(c["oos_sharpe"]) * math.sqrt(max(1.0, opy))))
    return n, rows


def _score8(cands: list[dict], root: Path) -> dict[str, Any]:
    n_prior, prior = _prior8(root)
    n_trials = n_prior + len(cands)
    if cands:
        tr_obs = [c["oos_sharpe"] for c in cands] + [p[0] for p in prior]
        tr_ann = [c["oos_sharpe"] * math.sqrt(max(1.0, c["obs_per_year"])) for c in cands] + [p[1] for p in prior]
        for c in cands:
            v1 = deflated_sharpe(c["returns"], n_trials, tr_obs)
            v2 = deflated_sharpe_annualized(c["returns"], c["obs_per_year"], n_trials, tr_ann)
            c["dsr_per_observation"], c["dsr_annualized"] = v1, v2
            c["deflated_sharpe"] = min(v1, v2) if v1 is not None and v2 is not None else None
    pbo = time_aligned_pbo(cands) if len(cands) >= 2 else {"pbo": None, "included": [], "blocks": 16}
    pbo["scope"] = "batch8_admitted_only"
    pbo["note"] = "PBO uses this batch's admitted paths only. Rebuilding earlier paths would not be a new trial and was not done."
    for c in cands:
        ok = (c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo.get("pbo") is not None
              and pbo["pbo"] < 0.5 and (c.get("excess_vs_equal_weight_oos_sharpe") or 0) > 0)
        c["gate"] = "PASS_STATS" if ok else "FAIL"
    return {"n_prior": n_prior, "n_trials": n_trials, "pbo": pbo, "trial_sharpes_used": len(prior) + len(cands),
            "trial_sharpe_note": "SR0 uses the counted trial total. The variance uses stored OOS Sharpes from batches 5, 6 and 7 plus this batch, which is fewer than the counted total."}


def _fetch_retry(symbols: dict[str, str], fetcher) -> tuple[dict, dict]:
    import time
    got, errors = {}, {}
    for _attempt in range(3):
        errors = {}
        for sym, yahoo in symbols.items():
            if sym in got:
                continue
            try:
                got[sym] = fetcher(yahoo)
            except Exception as exc:  # noqa: BLE001
                errors[sym] = repr(exc)[:160]
        if not errors:
            break
        time.sleep(2)
    return got, errors


def run_batch8(root: Path, daily: dict | None = None, hourly: dict | None = None) -> dict[str, Any]:
    root = Path(root)
    if daily is None:
        daily, daily_errors = _fetch_retry({s: y for s, (y, _c) in {**DAILY, "DXY": ("DX-Y.NYB", 2.0)}.items()}, fetch_daily_v)
    else:
        daily_errors = {}
    if hourly is None:
        hourly, hour_errors = _fetch_retry(HOUR_YAHOO, fetch_1h_v)
    else:
        hour_errors = {}
    ev = evaluate_batch8(daily, hourly)
    for c in ev["admitted"]:
        base = c["oos_sharpe"]
        hid = c["hypothesis_id"]
        alt = B8_BUILDERS[hid](hourly if hid != "H37" else daily, hurdle=HURDLE * 1.15)
        split = ev["split_h"] if hid != "H37" else ev["split_daily"]
        alt_s = sharpe([t["ret"] for t in alt if split is not None and t["ts_open"] >= split])
        c["param_perturbation_sharpe_retention"] = None if base <= 0 or split is None else round(min(alt_s, base) / base, 3)
    scored = _score8(ev["admitted"], root)
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in ev["admitted"]]
    for c in clean:
        c.pop("weights", None)
    snap = {"schema": "ahos.strategy_lab.batch8.v1",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True,
            "pre_registered": "strategy_lab/hypotheses.py _B8 @ 2026-10-24 21:20 Tehran (before first run)",
            "tau_l1": TAU_L1, "cost_hurdle_multiple": HURDLE, "cost_bps": B7_COST_BPS,
            "hour_span_utc": ev["hour_span"],
            "hour_note": "Intraday cells use Yahoo 1h bars (about 730 days). A daily bar is not labeled intraday. An empty intraday cell means no admitted 1h book.",
            "n_trials_this_batch": len(clean), "n_trials_prior": scored["n_prior"],
            "n_trials_counted_in_dsr": scored["n_trials"],
            "trial_sharpes_used": scored["trial_sharpes_used"], "trial_sharpe_note": scored["trial_sharpe_note"],
            "pbo_cscv": scored["pbo"].get("pbo"), "pbo_detail": scored["pbo"],
            "screened": ev["screened"], "errors": {"daily": daily_errors, "hourly": hour_errors},
            "candidates": clean,
            "promotion_rule": "OOS obs>=30 AND DSR>0.95 AND PBO<0.5 AND excess over equal weight > 0 AND survives strategy_red_team"}
    out = root / B8_OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    prior_rows, screened_prior = [], []
    for rel in (B6_OUT_REL, B7_OUT_REL):
        try:
            doc = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        prior_rows += doc.get("candidates") or []
        screened_prior += doc.get("screened") or []
    grid = merge_map_elites_grid(prior_rows, clean, screened_prior + ev["screened"])
    for c in clean:
        cell = c.get("map_elites_cell") or {}
        slot = ((grid.get("grid") or {}).get(cell.get("horizon")) or {}).get(cell.get("regime"))
        if isinstance(slot, dict) and slot.get("hypothesis_id") == c["hypothesis_id"]:
            slot["bar_interval"] = c["bar_interval"]
    intra = (grid.get("grid") or {}).get("intraday") or {}
    empty_intra = [name for name, slot in intra.items() if not slot]
    grid["intraday_provenance"] = "yahoo_chart_interval_1h_range_730d"
    grid["intraday_empty_reason"] = None if not empty_intra else (
        "These intraday cells have no admitted 1h book: " + ", ".join(empty_intra)
        + ". Daily bars were not used to fill them.")
    grid["generated_at"] = snap["generated_at"]
    (root / GRID_REL).write_text(json.dumps(grid, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
