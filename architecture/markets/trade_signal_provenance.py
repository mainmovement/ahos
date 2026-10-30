"""Categorize paper-trade signals for logging and Persian Kian explanations (PAPER_ONLY, advisory)."""
from __future__ import annotations

from typing import Any

# Maps signal `name` -> human bucket (honest: unlisted names -> other)
SIGNAL_CATEGORY: dict[str, str] = {
    "news": "news",
    "macro": "macro_central_bank",
    "macro_event": "macro_central_bank",
    "event_shock": "macro_central_bank",
    "candles": "candles_wicks",
    "mtf_trend": "mtf_trend",
    "zscore_mr": "candles_wicks",
    "large_trades": "whales_flow",
    "order_flow": "whales_flow",
    "exchange_netflow": "whales_flow",
    "whale_mempool": "whales_flow",
    "cftc_cot": "whales_flow",
    "funding_oi": "whales_flow",
    "stablecoin": "whales_flow",
    "stablecoin_impulse": "whales_flow",
    "vol_regime": "research_risk",
    "research_overlay": "research",
}

CATEGORY_FA: dict[str, str] = {
    "news": "اخبار (RSS دو منبع)",
    "macro_central_bank": "ماکرو / بانک مرکزی / DXY-بازده",
    "candles_wicks": "کندل و سایه",
    "mtf_trend": "روند چندبازه (به‌تنهایی رأی مستقل نیست)",
    "whales_flow": "جریان نهنگ / عمق / funding",
    "research": "پژوهش / فرضیه strategy-lab",
    "research_risk": "رژیم نوسان (سایز، نه جهت)",
    "other": "سایر",
}


def _brain_signals(brain: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(brain, dict):
        return []
    raw = brain.get("signals")
    if isinstance(raw, list):
        return [s for s in raw if isinstance(s, dict)]
    return []


def build_signal_provenance(brain: dict[str, Any] | None) -> dict[str, Any]:
    """Summarize which signal families drove the entry (from logged brain snapshot)."""
    signals = _brain_signals(brain)
    contributions = []
    if isinstance(brain, dict):
        contributions = [c for c in (brain.get("contributions") or []) if isinstance(c, dict)]

    by_category: dict[str, list[dict[str, Any]]] = {}
    drivers: list[dict[str, Any]] = []
    for s in signals:
        name = str(s.get("name") or "unknown")
        cat = SIGNAL_CATEGORY.get(name, "other")
        if not s.get("available"):
            entry = {"signal": name, "category": cat, "available": False, "score": None, "source": s.get("source")}
        else:
            entry = {
                "signal": name,
                "category": cat,
                "available": True,
                "score": s.get("score"),
                "source": s.get("source"),
                "spec": s.get("spec"),
            }
        by_category.setdefault(cat, []).append(entry)
        if s.get("available") and abs(float(s.get("score") or 0)) >= 0.05:
            drivers.append(entry)

    top_contrib = sorted(
        contributions,
        key=lambda c: -abs(float(c.get("contribution") or 0) * float(c.get("weight") or 0)),
    )[:5]

    missing_families = []
    for fam, cat in (
        ("news", "news"),
        ("whales", "whales_flow"),
        ("central_banks", "macro_central_bank"),
        ("candle_wicks", "candles_wicks"),
        ("research", "research"),
    ):
        items = by_category.get(cat) or []
        if not any(i.get("available") for i in items):
            missing_families.append(fam)

    switch_v = brain.get("switch_version") if isinstance(brain, dict) else None
    research_note = None
    for s in signals:
        if s.get("name") != "research_overlay":
            continue
        ev = s.get("evidence") if isinstance(s.get("evidence"), dict) else {}
        bits: list[str] = []
        srcs = ev.get("weighted_sources")
        if isinstance(srcs, list) and srcs:
            bits.append("وزن‌دار=" + ",".join(str(x) for x in srcs))
        shadow = ev.get("shadow_forward_logged")
        if isinstance(shadow, list) and shadow:
            bits.append("سایه-فقط-لاگ=" + ",".join(str(x) for x in shadow[:6]))
        if bits:
            research_note = " · ".join(bits) + " (فقط مشاوره؛ بدون ارتقا)"
            break
    if research_note is None and switch_v is not None and int(switch_v or 0) > 0:
        research_note = f"strategy_switch_version={switch_v} (overlay only; not promotion)"

    return {
        "schema": "ahos.trade_signal_provenance.v1",
        "by_category": by_category,
        "top_contributions": top_contrib,
        "drivers": drivers[:8],
        "missing_families": missing_families,
        "research_note": research_note,
        "paper_only": True,
    }


def explain_paper_trade_fa(
    *,
    symbol: str,
    side: str,
    desk: str,
    brain: dict[str, Any] | None,
    composite: float | None = None,
) -> str:
    """Short Persian explanation for Kian/Telegram (presentation only)."""
    prov = build_signal_provenance(brain)
    side_fa = "خرید" if side == "LONG" else "فروش" if side == "SHORT" else side
    lines = [
        f"معامله کاغذی {symbol} ({desk}): جهت {side_fa}.",
        "این توضیح از سیگنال‌های ثبت‌شده روی لاگ می‌آید؛ تضمین سود نیست.",
    ]
    if composite is not None:
        lines.append(f"امتیاز ترکیبی ورود: {composite:.3f}.")
    if prov["top_contributions"]:
        parts = []
        for c in prov["top_contributions"][:3]:
            parts.append(f"{c.get('signal')} (وزن×امتیاز={float(c.get('contribution') or 0):.3f})")
        lines.append("مهم‌ترین سهم‌ها: " + "، ".join(parts) + ".")
    cats_used = []
    for cat, items in prov["by_category"].items():
        active = [i for i in items if i.get("available")]
        if not active:
            continue
        names = ", ".join(f"{i['signal']}({i['score']})" for i in active[:3])
        cats_used.append(f"{CATEGORY_FA.get(cat, cat)}: {names}")
    if cats_used:
        lines.append("خانواده سیگنال: " + " | ".join(cats_used) + ".")
    if prov["missing_families"]:
        lines.append(
            "ثبت نشده این دور: "
            + "، ".join(prov["missing_families"])
            + " (UNKNOWN > ساختگی؛ بدون عدد جعل‌شده)."
        )
    if prov.get("research_note"):
        lines.append(str(prov["research_note"]))
    if isinstance(brain, dict) and brain.get("desk_notional_mult") is not None:
        src = brain.get("desk_notional_mult_source") or ""
        lines.append(
            f"سیاست اندازه میز (کاغذی): ضریب {float(brain['desk_notional_mult']):.3f}"
            + (f" ({src})" if src else "")
            + "."
        )
    lines.append("وضعیت لبه: UNPROVEN_EDGE — گیت ارتقا (DSR/PBO/expectancy) پاس نشده؛ این متن حکم معامله نیست.")
    return "\n".join(lines)
