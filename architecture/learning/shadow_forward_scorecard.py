"""M28/M56/M58 — Shadow signal forward-test scorecard (PAPER_ONLY, no promotion).

Per signal x horizon (15m/1h/4h/24h): n (all scored observations), n_eff (non-overlapping per symbol: the next
observation is used only after the previous horizon elapsed), accuracy, Spearman rank IC and Brier skill score
against the sample's own up-move base rate, all computed on the NON-OVERLAPPING subset. A forward price must land
within max(10 min, horizon/2) of the target; stale-session prices (exactly zero forward move) are excluded.
The promotion gate counts CLOSED paper trades (ledger CLOSE rows), never signal observations."""
from __future__ import annotations

import bisect
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_account import LEDGER_REL

OUT_REL = Path("reports") / "grok" / "M28" / "shadow_forward_scorecard.json"
LIVE_PRICES_REL = Path("reports") / "grok" / "M19" / "live_market_prices.json"

SHADOW_SIGNALS: tuple[tuple[str, str], ...] = (
    ("stablecoin_impulse", "H15"),
    ("exchange_netflow", "H14"),
    ("whale_mempool", "LIVE_ONLY_NO_BACKTEST"),
    ("macro_event", "H16"),
    ("event_shock", "H26"),
    ("news", "H22"),
    ("mtf_trend", "M28.1"),
    ("council_debate", "H27"),
)
HORIZONS: tuple[tuple[str, int], ...] = (("15m", 900), ("1h", 3600), ("4h", 14400), ("24h", 86400))
HORIZONS_H = (0.25, 1, 4, 24)
PRIMARY_EVAL_H = 1
PRIMARY_KEY = "1h"
PROMOTION_CLOSED_TRADES = 30
SIGNAL_ALIASES: dict[str, tuple[str, ...]] = {
    "stablecoin_impulse": ("stablecoin_impulse", "stablecoin"),
}
BAR_SECONDS_LIVE_HISTORY = 300
STALE_SKIP_REASONS = ("MARKET_CLOSED_OR_STALE",)


def _parse_ts(ts: str) -> float | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _load_events(root: Path) -> list[dict[str, Any]]:
    p = root / LEDGER_REL
    if not p.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("symbol") and row.get("ts"):
            out.append(row)
    out.sort(key=lambda r: _parse_ts(str(r["ts"])) or 0.0)
    return out


def _enrich_series_from_live_prices(root: Path, series: dict[str, list[tuple[float, float]]]) -> dict[str, list[tuple[float, float]]]:
    path = root / LIVE_PRICES_REL
    if not path.is_file():
        return series
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return series
    fetched = _parse_ts(str(payload.get("generated_at") or ""))
    if fetched is None:
        return series
    out = dict(series)
    for sym, q in (payload.get("quotes") or {}).items():
        hist = (q or {}).get("history") or []
        extra = [(fetched - (len(hist) - 1 - i) * BAR_SECONDS_LIVE_HISTORY, float(p))
                 for i, p in enumerate(hist) if isinstance(p, (int, float)) and p > 0]
        if extra:
            out[sym] = sorted(set(out.get(sym, []) + extra))
    return out


def _price_timeline(events: list[dict[str, Any]]) -> dict[str, list[tuple[float, float]]]:
    series: dict[str, list[tuple[float, float]]] = {}
    for row in events:
        if row.get("event") == "SKIP" and row.get("reason") in STALE_SKIP_REASONS:
            continue
        t = _parse_ts(str(row["ts"]))
        price = row.get("price") or row.get("quote_price") or row.get("fill_price")
        if t is None or not isinstance(price, (int, float)) or price <= 0:
            continue
        series.setdefault(str(row["symbol"]), []).append((t, float(price)))
    return {s: sorted(v) for s, v in series.items()}


def _forward_return(series: list[tuple[float, float]], t0: float, horizon_s: float, times: list[float] | None = None) -> float | None:
    ts = times if times is not None else [t for t, _ in series]
    i = bisect.bisect_left(ts, t0 - 60)
    if i >= len(ts) or abs(ts[i] - t0) > 60:
        return None
    p0 = series[i][1]
    j = bisect.bisect_left(ts, t0 + horizon_s)
    if j >= len(ts) or ts[j] - (t0 + horizon_s) > max(600.0, horizon_s / 2):
        return None
    return (series[j][1] - p0) / p0 if p0 > 0 else None


def _signal_score(row: dict[str, Any], signal_name: str) -> float | None:
    brain = row.get("brain") or row.get("entry_brain") or {}
    if signal_name == "council_debate":
        cd = brain.get("council_debate") or {}
        if not cd:
            return None
        return float(cd.get("bull_prob") or 0.5) - float(cd.get("bear_prob") or 0.5)
    names = SIGNAL_ALIASES.get(signal_name, (signal_name,))
    flat = row.get("signal_scores") or {}
    for alias in names:
        if isinstance(flat.get(alias), (int, float)):
            return float(flat[alias])
        for s in brain.get("signals") or []:
            if s.get("name") == alias and s.get("available"):
                return float(s.get("score") or 0.0)
    return None


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda k: xs[k])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3:
        return None
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va, vb = sum((x - ma) ** 2 for x in ra), sum((y - mb) ** 2 for y in rb)
    return cov / math.sqrt(va * vb) if va > 0 and vb > 0 else None


def brier_skill(scores: list[float], rets: list[float]) -> tuple[float | None, float | None]:
    """p(up) = 0.5 + 0.5*clip(score); BSS = 1 - Brier / Brier(base rate of up moves in the same sample)."""
    if not scores:
        return None, None
    o = [1.0 if r > 0 else 0.0 for r in rets]
    p = [0.5 + 0.5 * max(-1.0, min(1.0, s)) for s in scores]
    brier = sum((pi - oi) ** 2 for pi, oi in zip(p, o)) / len(o)
    base = sum(o) / len(o)
    ref = sum((base - oi) ** 2 for oi in o) / len(o)
    return brier, (1 - brier / ref) if ref > 0 else None


def _non_overlapping(obs: list[tuple[str, float, float, float]], horizon_s: int) -> list[tuple[str, float, float, float]]:
    last: dict[str, float] = {}
    keep = []
    for sym, t0, s, r in sorted(obs, key=lambda x: x[1]):
        if t0 >= last.get(sym, -1e18) + horizon_s:
            keep.append((sym, t0, s, r))
            last[sym] = t0
    return keep


def _horizon_stats(obs: list[tuple[str, float, float, float]], horizon_s: int) -> dict[str, Any]:
    ne = _non_overlapping(obs, horizon_s)
    directional = [(s, r) for _, _, s, r in ne if s != 0]
    hits = sum(1 for s, r in directional if (s > 0) == (r > 0))
    brier, bss = brier_skill([s for _, _, s, _ in ne], [r for _, _, _, r in ne])
    ic = spearman([s for _, _, s, _ in ne], [r for _, _, _, r in ne])
    return {"n": len(obs), "n_eff": len(ne), "n_directional": len(directional),
            "accuracy": round(hits / len(directional), 4) if directional else None,
            "hit_rate": round(hits / len(directional), 4) if directional else None,
            "rank_ic": round(ic, 4) if ic is not None else None,
            "brier": round(brier, 4) if brier is not None else None,
            "brier_skill": round(bss, 4) if bss is not None else None}


def _eval_signal(events: list[dict[str, Any]], series: dict[str, list[tuple[float, float]]], signal_name: str, hyp: str,
                 times: dict[str, list[float]] | None = None, closed: int = 0) -> dict[str, Any]:
    times = times or {s: [t for t, _ in v] for s, v in series.items()}
    horizons: dict[str, Any] = {}
    for key, hs in HORIZONS:
        obs = []
        for row in events:
            if row.get("event") not in ("OPEN", "NO_TRADE", "HOLD", "SKIP"):
                continue
            score = _signal_score(row, signal_name)
            sym = str(row["symbol"])
            t0 = _parse_ts(str(row["ts"]))
            if score is None or t0 is None or sym not in series:
                continue
            fr = _forward_return(series[sym], t0, hs, times[sym])
            if fr is None or fr == 0.0:
                continue
            obs.append((sym, t0, score, fr))
        horizons[key] = _horizon_stats(obs, hs)
    p = horizons[PRIMARY_KEY]
    return {
        "signal": signal_name,
        "hypothesis_id": hyp,
        "n": p["n"],
        "n_eff": p["n_eff"],
        "hit_rate": p["accuracy"],
        "accuracy": p["accuracy"],
        "rolling_ic": p["rank_ic"],
        "rank_ic": p["rank_ic"],
        "brier": p["brier"],
        "brier_skill": p["brier_skill"],
        "horizons": horizons,
        "trades_remaining_to_gate": max(0, PROMOTION_CLOSED_TRADES - closed),
        "promotion_eligible": False,
        "primary_horizon_h": PRIMARY_EVAL_H,
        "note_fa": (
            f"سیگنال سایهٔ {signal_name}: {p['n_eff']} مشاهدهٔ غیرهم‌پوشان {PRIMARY_KEY} (از {p['n']}) — فقط کاغذی؛ "
            f"ارتقا فقط با ۳۰ معاملهٔ بستهٔ واقعی و DSR/PBO؛ لبهٔ سودآوری اثبات‌نشده."
        ),
    }


def build_shadow_forward_scorecard(root: Path) -> dict[str, Any]:
    events = _load_events(root)
    series = _enrich_series_from_live_prices(root, _price_timeline(events))
    times = {s: [t for t, _ in v] for s, v in series.items()}
    closed = sum(1 for e in events if e.get("event") == "CLOSE")
    signals = [_eval_signal(events, series, name, hyp, times, closed) for name, hyp in SHADOW_SIGNALS]
    best = max(signals, key=lambda s: s["n_eff"])
    ranked = [s for s in signals if s["n_eff"] >= 10 and s["rank_ic"] is not None]
    best_ic = max(ranked, key=lambda s: s["rank_ic"]) if ranked else None
    remaining = max(0, PROMOTION_CLOSED_TRADES - closed)
    summary_fa = (
        f"تورنمنت سیگنال‌های سایه (فقط کاغذی، افق اصلی {PRIMARY_KEY}): بیشترین نمونهٔ غیرهم‌پوشان {best['signal']} "
        f"با n_eff={best['n_eff']}"
        + (f" · بهترین Rank IC={best_ic['rank_ic']} ({best_ic['signal']})" if best_ic else " · هنوز هیچ سیگنالی ۱۰ مشاهدهٔ غیرهم‌پوشان ندارد")
        + f" — معاملات بسته {closed}/{PROMOTION_CLOSED_TRADES}؛ {remaining} معاملهٔ دیگر تا دروازه (UNPROVEN_EDGE)."
    )
    payload = {
        "schema": "ahos.shadow_forward_scorecard.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "unproven_edge": True,
        "live_prices_path": str(LIVE_PRICES_REL).replace("\\", "/"),
        "primary_eval_horizon_h": PRIMARY_EVAL_H,
        "horizons": [k for k, _ in HORIZONS],
        "metrics": "accuracy, Spearman rank IC, Brier skill vs sample base rate — on non-overlapping observations",
        "price_series_source": "paper_trades.jsonl (stale-session SKIP rows excluded)+live_market_prices.history",
        "events_scanned": len(events),
        "closed_trades_count": closed,
        "trades_remaining_to_30_gate": remaining,
        "signals": signals,
        "summary_fa": summary_fa,
    }
    out = root / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def export_shadow_forward_scorecard(root: Path | None = None) -> dict[str, Any]:
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    return build_shadow_forward_scorecard(repo)
