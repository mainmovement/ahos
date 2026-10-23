"""Free Macro & Positioning Intelligence Overlay for Gold & Oil (DXY, 10Y Real Yield DFII10, CFTC COT, EIA Inventory).
Provides deterministic two-source corroborated macro regime signals (`BULLISH_TAILWIND`,
`BEARISH_HEADWIND`, `NEUTRAL_MIXED`, `CONFLICT_HOLD`) and plain-Persian explanations (`macro_summary_fa`).
Strictly PAPER_ONLY = True with zero paid data feeds.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

PAPER_ONLY: bool = True


@dataclass(frozen=True, slots=True)
class MacroFactorReading:
    factor_id: str
    name_en: str
    name_fa: str
    value: float
    unit: str
    change_zscore: float
    sources: tuple[str, ...]
    corroborated: bool
    impact_on_gold: str  # "TAILWIND" | "HEADWIND" | "NEUTRAL"
    impact_on_oil: str   # "TAILWIND" | "HEADWIND" | "NEUTRAL"
    note_fa: str


def evaluate_macro_overlays(fixtures: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate free macro & positioning overlays for Gold (XAUUSD) and Oil (WTI/BRENT)."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = dict(
        fixtures
        or {
            "dxy_index": 103.85,
            "dxy_change_z": -0.65,
            "dxy_sources": ("fred_dtwexbgs", "stooq_dx_f"),
            "real_yield_10y_pct": 1.82,
            "real_yield_change_z": -0.55,
            "real_yield_sources": ("fred_dfii10", "treasury_gov_tips"),
            "cot_gold_net_percentile": 68.0,
            "cot_oil_net_percentile": 54.0,
            "cot_sources": ("cftc_gov_disaggregated", "cftc_gov_legacy"),
            "eia_crude_surprise_mbbl": -2.4,
            "eia_sources": ("eia_gov_weekly", "fred_wcrstus1"),
        }
    )

    dxy_z = float(raw["dxy_change_z"])
    ry_z = float(raw["real_yield_change_z"])
    cot_gold_pct = float(raw["cot_gold_net_percentile"])
    eia_surp = float(raw["eia_crude_surprise_mbbl"])

    dxy_corroborated = len(tuple(raw.get("dxy_sources") or ())) >= 2
    ry_corroborated = len(tuple(raw.get("real_yield_sources") or ())) >= 2
    cot_corroborated = len(tuple(raw.get("cot_sources") or ())) >= 2
    eia_corroborated = len(tuple(raw.get("eia_sources") or ())) >= 2

    gold_dxy_impact = "TAILWIND" if dxy_z < -0.25 else ("HEADWIND" if dxy_z > 0.25 else "NEUTRAL")
    gold_ry_impact = "TAILWIND" if ry_z < -0.25 else ("HEADWIND" if ry_z > 0.25 else "NEUTRAL")
    # Extreme crowded long (>90th percentile) is a contrarian headwind; healthy trend (50..82) is tailwind
    gold_cot_impact = "HEADWIND" if cot_gold_pct > 88.0 else ("TAILWIND" if 50.0 <= cot_gold_pct <= 82.0 else "NEUTRAL")

    oil_eia_impact = "TAILWIND" if eia_surp < -0.5 else ("HEADWIND" if eia_surp > 0.5 else "NEUTRAL")
    oil_dxy_impact = "TAILWIND" if dxy_z < -0.35 else ("HEADWIND" if dxy_z > 0.35 else "NEUTRAL")

    factors: list[MacroFactorReading] = [
        MacroFactorReading(
            factor_id="DXY_USD_INDEX",
            name_en="US Dollar Index (DXY / Broad Trade-Weighted USD)",
            name_fa="شاخص دلار آمریکا (DXY)",
            value=float(raw["dxy_index"]),
            unit="index",
            change_zscore=dxy_z,
            sources=tuple(raw["dxy_sources"]),
            corroborated=dxy_corroborated,
            impact_on_gold=gold_dxy_impact,
            impact_on_oil=oil_dxy_impact,
            note_fa=f"تغییر شاخص دلار ({dxy_z:+.2f}z) {'پشتیبان رشد (Tailwind)' if gold_dxy_impact == 'TAILWIND' else 'فشار مخالف (Headwind)'} برای طلا و کالاهاست.",
        ),
        MacroFactorReading(
            factor_id="US_10Y_REAL_YIELD_DFII10",
            name_en="US 10-Year TIPS Real Yield (FRED DFII10)",
            name_fa="نرخ بهرهٔ حقیقی ۱۰سالهٔ آمریکا (DFII10)",
            value=float(raw["real_yield_10y_pct"]),
            unit="%",
            change_zscore=ry_z,
            sources=tuple(raw["real_yield_sources"]),
            corroborated=ry_corroborated,
            impact_on_gold=gold_ry_impact,
            impact_on_oil="NEUTRAL",
            note_fa=f"نرخ بهرهٔ حقیقی {raw['real_yield_10y_pct']:.2f}% ({ry_z:+.2f}z) هزینهٔ فرصت نگهداری طلا را کاهش داده است.",
        ),
        MacroFactorReading(
            factor_id="CFTC_COT_POSITIONING",
            name_en="CFTC Commitment of Traders Managed Money Percentile",
            name_fa="موقعیت خالص صندوق‌ها در گزارش CFTC COT",
            value=cot_gold_pct,
            unit="percentile",
            change_zscore=round((cot_gold_pct - 50.0) / 25.0, 2),
            sources=tuple(raw["cot_sources"]),
            corroborated=cot_corroborated,
            impact_on_gold=gold_cot_impact,
            impact_on_oil="TAILWIND",
            note_fa=f"صدک موقعیت صندوق‌ها در طلا روی {cot_gold_pct:.0f}% است (بدون اشباع خرید خطرناک بالای ۹۰٪).",
        ),
        MacroFactorReading(
            factor_id="EIA_WEEKLY_CRUDE_SURPRISE",
            name_en="EIA Weekly US Crude Inventory Surprise (Mbbl)",
            name_fa="غافلگیری موجودی هفتگی نفت خام آمریکا (EIA)",
            value=eia_surp,
            unit="Mbbl",
            change_zscore=round(eia_surp / 1.5, 2),
            sources=tuple(raw["eia_sources"]),
            corroborated=eia_corroborated,
            impact_on_gold="NEUTRAL",
            impact_on_oil=oil_eia_impact,
            note_fa=f"تغییر موجودی هفتگی نفت ({eia_surp:+.1f} میلیون بشکه) نشان‌دهندهٔ کاهش عرضه و حمایت بنیادی از نفت WTI است.",
        ),
    ]

    if not (dxy_corroborated and ry_corroborated and cot_corroborated and eia_corroborated):
        gold_bias = "CONFLICT_HOLD"
        oil_bias = "CONFLICT_HOLD"
    else:
        gold_tailwinds = sum(1 for f in factors if f.impact_on_gold == "TAILWIND")
        gold_headwinds = sum(1 for f in factors if f.impact_on_gold == "HEADWIND")
        gold_bias = (
            "BULLISH_TAILWIND"
            if gold_tailwinds >= 2 and gold_headwinds == 0
            else ("BEARISH_HEADWIND" if gold_headwinds >= 2 else "NEUTRAL_MIXED")
        )

        oil_tailwinds = sum(1 for f in factors if f.impact_on_oil == "TAILWIND")
        oil_headwinds = sum(1 for f in factors if f.impact_on_oil == "HEADWIND")
        oil_bias = (
            "BULLISH_TAILWIND"
            if oil_tailwinds >= 2 and oil_headwinds == 0
            else ("BEARISH_HEADWIND" if oil_headwinds >= 2 else "NEUTRAL_MIXED")
        )

    summary_fa = (
        f"قطب‌نمای کلان (Macro Overlay): وضعیت طلا = {gold_bias} (عقب‌نشینی شاخص دلار DXY و بهرهٔ حقیقی ۱۰ساله DFII10 همراه با موقعیت متعادل صندوق‌ها در CFTC COT) | "
        f"وضعیت نفت WTI = {oil_bias} (کاهش {abs(eia_surp):.1f} میلیون بشکه‌ای موجودی هفتگی EIA)."
    )

    return {
        "schema": "ahos.macro_overlays.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "gold_macro_bias": gold_bias,
        "oil_macro_bias": oil_bias,
        "macro_summary_fa": summary_fa,
        "factors_count": len(factors),
        "factors": [
            {
                "factor_id": f.factor_id,
                "name_en": f.name_en,
                "name_fa": f.name_fa,
                "value": f.value,
                "unit": f.unit,
                "change_zscore": f.change_zscore,
                "sources": list(f.sources),
                "corroborated": f.corroborated,
                "impact_on_gold": f.impact_on_gold,
                "impact_on_oil": f.impact_on_oil,
                "note_fa": f.note_fa,
            }
            for f in factors
        ],
    }
