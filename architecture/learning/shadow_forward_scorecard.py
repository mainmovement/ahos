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
    for s in brain.get("signals") or []:
        if s.get("name") == signal_name and s.get("available"):
            return float(s.get("score") or 0.0)
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
        ret24 = _forward_return(series[sym], t0, 24 * 3600)
        if ret24 is None:
            continue
        pred = 1.0 if score > 0 else -1.0 if score < 0 else 0.0
        if pred == 0.0:
            continue
        preds.append((pred, ret24))
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
        "note_fa": f"سیگنال سایهٔ {signal_name}: {n} نمونهٔ قابل‌سنجش — هنوز ارتقا ممنوع (UNPROVEN_EDGE).",
    }


def build_shadow_forward_scorecard(root: Path) -> dict[str, Any]:
    events = _load_events(root)
    series = _price_timeline(events)
    signals = [_eval_signal(events, series, name, hyp) for name, hyp in SHADOW_SIGNALS]
    best = max(signals, key=lambda s: s["n"])
    summary_fa = (
        f"تورنمنت سیگنال‌های سایه (فقط کاغذی): بهترین نمونه {best['signal']} با n={best['n']} — "
        f"حداقل ۳۰ معاملهٔ بسته و DSR/PBO برای ارتقا لازم است؛ لبهٔ سودآوری اثبات‌نشده."
    )
    payload = {
        "schema": "ahos.shadow_forward_scorecard.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "unproven_edge": True,
        "live_prices_path": str(LIVE_PRICES_REL).replace("\\", "/"),
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
