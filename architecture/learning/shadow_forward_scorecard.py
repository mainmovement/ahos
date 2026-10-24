"""M28/M56/M58 — Shadow signal forward-test scorecard (PAPER_ONLY, no promotion)."""
from __future__ import annotations

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
    ("whale_mempool", "H17"),
    ("macro_event", "H18"),
    ("mtf_trend", "hmm_pelt_regime"),
    ("council_debate", "soroush_bl_view"),
)
HORIZONS_H = (1, 4, 24)
PRIMARY_EVAL_H = 1
SIGNAL_ALIASES: dict[str, tuple[str, ...]] = {
    "stablecoin_impulse": ("stablecoin_impulse", "stablecoin"),
    "exchange_netflow": ("exchange_netflow",),
    "whale_mempool": ("whale_mempool",),
    "macro_event": ("macro_event", "news", "macro"),
    "mtf_trend": ("mtf_trend",),
    "council_debate": ("council_debate",),
}
BAR_SECONDS_LIVE_HISTORY = 300


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
    quotes = payload.get("quotes") or {}
    out = dict(series)
    for sym, pts in list(out.items()):
        q = quotes.get(sym) or {}
        hist = q.get("history") or []
        if not hist:
            continue
        extra: list[tuple[float, float]] = []
        for i, price in enumerate(hist):
            if not isinstance(price, (int, float)):
                continue
            t = fetched - (len(hist) - 1 - i) * BAR_SECONDS_LIVE_HISTORY
            extra.append((t, float(price)))
        merged = sorted({(t, p) for t, p in (pts + extra)}, key=lambda x: x[0])
        out[sym] = merged
    return out


def _price_timeline(events: list[dict[str, Any]]) -> dict[str, list[tuple[float, float]]]:
    series: dict[str, list[tuple[float, float]]] = {}
    for row in events:
        sym = str(row["symbol"])
        t = _parse_ts(str(row["ts"]))
        price = row.get("price") or row.get("quote_price") or row.get("fill_price")
        if t is None or not isinstance(price, (int, float)):
            continue
        series.setdefault(sym, []).append((t, float(price)))
    for sym in series:
        series[sym].sort(key=lambda x: x[0])
    return series


def _forward_return(series: list[tuple[float, float]], t0: float, horizon_s: float) -> float | None:
    p0 = next((p for t, p in series if t == t0), None)
    if p0 is None or p0 <= 0:
        for t, p in series:
            if abs(t - t0) < 1.0:
                p0 = p
                break
    if p0 is None or p0 <= 0:
        return None
    target = t0 + horizon_s
    p1 = None
    for t, p in series:
        if t >= target:
            p1 = p
            break
    if p1 is None:
        return None
    return (p1 - p0) / p0


def _signal_score(row: dict[str, Any], signal_name: str) -> float | None:
    brain = row.get("brain") or row.get("entry_brain") or {}
    if signal_name == "council_debate":
        cd = brain.get("council_debate") or {}
        bull = float(cd.get("bull_prob") or 0.5)
        bear = float(cd.get("bear_prob") or 0.5)
        return bull - bear
    if signal_name == "mtf_trend":
        regime = brain.get("regime") or {}
        if isinstance(regime, dict) and regime.get("regime") == "HIGH_VOL":
            return -0.3
        for s in brain.get("signals") or []:
            if s.get("name") == "mtf_trend" and s.get("available"):
                return float(s.get("score") or 0.0)
        return None
    names = SIGNAL_ALIASES.get(signal_name, (signal_name,))
    for alias in names:
        for s in brain.get("signals") or []:
            if s.get("name") == alias and s.get("available"):
                return float(s.get("score") or 0.0)
    if signal_name == "council_debate":
        comp = brain.get("composite")
        if isinstance(comp, (int, float)):
            return float(comp)
    return None


def _eval_signal(events: list[dict[str, Any]], series: dict[str, list[tuple[float, float]]], signal_name: str, hyp: str) -> dict[str, Any]:
    preds: list[tuple[float, float]] = []
    for row in events:
        if row.get("event") not in ("OPEN", "NO_TRADE", "HOLD", "SKIP"):
            continue
        score = _signal_score(row, signal_name)
        sym = str(row["symbol"])
        t0 = _parse_ts(str(row["ts"]))
        if score is None or t0 is None or sym not in series:
            continue
        ret_primary = _forward_return(series[sym], t0, PRIMARY_EVAL_H * 3600)
        if ret_primary is None:
            continue
        pred = 1.0 if score > 0 else -1.0 if score < 0 else 0.0
        if pred == 0.0:
            continue
        preds.append((pred, ret_primary))
    n = len(preds)
    if n == 0:
        return {
            "signal": signal_name,
            "hypothesis_id": hyp,
            "n": 0,
            "hit_rate": None,
            "rolling_ic": None,
            "brier": None,
            "horizons": {f"{h}h": {"n": 0, "hit_rate": None} for h in HORIZONS_H},
            "trades_remaining_to_gate": 30,
            "promotion_eligible": False,
            "primary_horizon_h": PRIMARY_EVAL_H,
            "note_fa": f"سیگنال سایهٔ {signal_name}: هنوز نمونهٔ کافی برای بازدهٔ {PRIMARY_EVAL_H}h نیست — ارتقا ممنوع.",
        }
    hits = sum(1 for p, r in preds if (p > 0 and r > 0) or (p < 0 and r < 0))
    hit_rate = hits / n
    mean_p = sum(p for p, _ in preds) / n
    mean_r = sum(r for _, r in preds) / n
    cov = sum((p - mean_p) * (r - mean_r) for p, r in preds)
    var_p = sum((p - mean_p) ** 2 for p, r in preds) or 1e-9
    var_r = sum((r - mean_r) ** 2 for p, r in preds) or 1e-9
    ic = cov / math.sqrt(var_p * var_r)
    brier = sum((max(0.0, min(1.0, 0.5 + 0.5 * p)) - (1.0 if r > 0 else 0.0)) ** 2 for p, r in preds) / n
    horizons: dict[str, Any] = {}
    for h in HORIZONS_H:
        hp: list[tuple[float, float]] = []
        for row in events:
            score = _signal_score(row, signal_name)
            sym = str(row["symbol"])
            t0 = _parse_ts(str(row["ts"]))
            if score is None or t0 is None or sym not in series:
                continue
            fr = _forward_return(series[sym], t0, h * 3600)
            if fr is None:
                continue
            pred = 1.0 if score > 0 else -1.0 if score < 0 else 0.0
            if pred != 0.0:
                hp.append((pred, fr))
        hn = len(hp)
        hh = sum(1 for p, r in hp if (p > 0 and r > 0) or (p < 0 and r < 0)) / hn if hn else None
        horizons[f"{h}h"] = {"n": hn, "hit_rate": round(hh, 4) if hh is not None else None}
    return {
        "signal": signal_name,
        "hypothesis_id": hyp,
        "n": n,
        "hit_rate": round(hit_rate, 4),
        "rolling_ic": round(ic, 4),
        "brier": round(brier, 4),
        "horizons": horizons,
        "trades_remaining_to_gate": max(0, 30 - n),
        "promotion_eligible": False,
        "primary_horizon_h": PRIMARY_EVAL_H,
        "note_fa": (
            f"سیگنال سایهٔ {signal_name}: {n} نمونهٔ {PRIMARY_EVAL_H}h (فقط کاغذی) — "
            f"حداقل ۳۰ معاملهٔ بسته برای ارتقا؛ لبهٔ سودآوری اثبات‌نشده."
        ),
    }


def build_shadow_forward_scorecard(root: Path) -> dict[str, Any]:
    events = _load_events(root)
    series = _enrich_series_from_live_prices(root, _price_timeline(events))
    signals = [_eval_signal(events, series, name, hyp) for name, hyp in SHADOW_SIGNALS]
    best = max(signals, key=lambda s: s["n"])
    best_ic = next((s for s in sorted(signals, key=lambda x: -(x.get("rolling_ic") or -9)) if s["n"] > 0), best)
    summary_fa = (
        f"تورنمنت سیگنال‌های سایه (فقط کاغذی، بازدهٔ {PRIMARY_EVAL_H}h): "
        f"بیشترین نمونه {best['signal']} با n={best['n']}"
        + (f" · IC≈{best_ic.get('rolling_ic')}" if best_ic.get("rolling_ic") is not None else "")
        + " — هنوز ارتقا ممنوع (UNPROVEN_EDGE؛ نه ۳۰ معاملهٔ بسته)."
    )
    payload = {
        "schema": "ahos.shadow_forward_scorecard.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "unproven_edge": True,
        "live_prices_path": str(LIVE_PRICES_REL).replace("\\", "/"),
        "primary_eval_horizon_h": PRIMARY_EVAL_H,
        "price_series_source": "paper_trades.jsonl+live_market_prices.history",
        "events_scanned": len(events),
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
