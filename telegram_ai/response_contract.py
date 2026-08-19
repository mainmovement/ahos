#!/usr/bin/env python3
"""AHOS Telegram Response Contract Formatter (Section X).

Law:
  - Every response is strictly grounded in real stored evidence.
  - Never fabricate numbers, scores or reasons.
  - Persian-first with clear structural markers:
      فرصت: XX/100
      اعتماد: [بالا|متوسط|پایین]
      ریسک: [کم|متوسط|بالا|بحرانی]
      دلایل: (+ ...)
      ریسک: (- ...)
      نامعلوم: (...)
      شرط invalidation: (...)
  - Always concludes with the invariant Persian footer:
      «تصمیم نهایی با کاربر است.»
"""
from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any
from architecture.scoring.engine import OpportunityScoreReport
from architecture.providers.contracts import NormalizedTokenCandidate

FOOTER_MANDATED = "تصمیم نهایی با کاربر است."


def esc(value: Any) -> str:
    """Escape a value for Telegram's HTML parse mode.

    Token names and symbols are attacker-controlled: whoever deploys a token
    picks its name. Messages go out with parse_mode="HTML", so a token called
    `Bull & Bear` produces an unescaped ampersand and Telegram rejects the
    whole send with 400 "can't parse entities" -- the alert never arrives, and
    the exception is swallowed by the send guard. A name containing a stray
    `<` can likewise swallow the rest of the card, including the address.

    Escaping at the point of interpolation is the only reliable fix: the
    surrounding template keeps its own intentional <code> markup.
    """
    return html.escape(str(value), quote=False)

_CONFIDENCE_FA = {
    "HIGH": "بالا",
    "MED": "متوسط",
    "LOW": "پایین"
}

_RISK_FA = {
    "LOW": "کم",
    "MED": "متوسط",
    "HIGH": "بالا",
    "CRITICAL": "بحرانی / خطرناک"
}


def format_opportunity_response(report: OpportunityScoreReport,
                                candidate: NormalizedTokenCandidate | None = None) -> str:
    """Renders the canonical Section X opportunity card in Persian."""
    lines: list[str] = []

    # Title & Identity
    lines.append(f"📊 تحلیل فرصت — {esc(report.token_symbol)} ({esc(report.token_name)})")
    lines.append(f"🌐 شبکه: {esc(report.token_chain.upper())} | "
                 f"آدرس: <code>{esc(report.token_address)}</code>")
    lines.append("──────────────────────")

    # Score, Confidence, Risk
    lines.append(f"🎯 فرصت: {report.opportunity_score:.0f}/100")
    lines.append(f"🔍 اعتماد به داده: {_CONFIDENCE_FA.get(report.confidence_level, report.confidence_level)}")
    lines.append(f"⚠️ سطح ریسک: {_RISK_FA.get(report.risk_level, report.risk_level)}")
    lines.append("")

    # Reasons (+)
    lines.append("دلایل مثبت (+):")
    if report.positive_reasons:
        for r in report.positive_reasons:
            lines.append(f" + {esc(r)}")
    else:
        lines.append(" • دلیل مثبتی در مشاهدات فعلی ثبت نشد")
    lines.append("")

    # Risks (-)
    lines.append("ریسک‌ها (-):")
    if report.risk_deductions:
        for risk in report.risk_deductions:
            lines.append(f" - {esc(risk.description)} [{esc(risk.severity)}]")
    else:
        lines.append(" • ریسک ساختاری حادی شناسایی نشد")
    lines.append("")

    # Missing / Unknowns
    lines.append("نامعلوم / فاقد مشاهده:")
    if report.missing_unknowns:
        for unk in report.missing_unknowns:
            lines.append(f" ? {esc(unk)}")
    else:
        lines.append(" • تمامی اقلام ضروری مورد مشاهده قرار گرفت")
    lines.append("")

    # Invalidation Conditions
    lines.append("شرط‌های ابطال فرصت (Invalidation):")
    for inv in report.invalidation_conditions:
        lines.append(f" ❌ {esc(inv.trigger_description)} ({esc(inv.threshold)})")
    lines.append("")

    # Market & Provenance Details (if candidate provided)
    if candidate:
        m = candidate.metrics
        lines.append("مشخصات بازار و منبع:")
        if m.liquidity_usd is not None:
            lines.append(f" • نقدینگی: ${m.liquidity_usd:,.2f}")
        if m.volume_1h is not None:
            lines.append(f" • حجم ۱ ساعته: ${m.volume_1h:,.2f}")
        if m.price_usd is not None:
            lines.append(f" • قیمت لحظه‌ای: ${m.price_usd:.8f}".rstrip("0").rstrip("."))
        lines.append(f" • منبع داده: {esc(candidate.source_provider)}")
        obs_utc = datetime.fromtimestamp(candidate.retrieved_ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f" • زمان آخرین مشاهده: {obs_utc}")
        lines.append("")

    # Mandated Footer
    lines.append(FOOTER_MANDATED)
    return "\n".join(lines)


def format_market_overview(tokens_count: int, resolved_count: int,
                           dead_count: int, top_opportunities: list[OpportunityScoreReport]) -> str:
    """Renders general market & pipeline status in Persian."""
    lines = [
        "🌐 وضعیت کلی بازار و پایپ‌لاین کشف AHOS",
        "──────────────────────",
        f"• کل توکن‌های تحت رصد: {tokens_count:,}",
        f"• توکن‌های تکمیل‌شده (RESOLVED): {resolved_count:,}",
        f"• توکن‌های غیرفعال/منقضی (DEAD): {dead_count:,}",
        "",
        "🏆 برترین فرصت‌های شناسایی‌شده با داده معتبر:"
    ]
    if top_opportunities:
        for i, opp in enumerate(top_opportunities[:5], 1):
            lines.append(
                f"{i}. {esc(opp.token_symbol)} | امتیاز: {opp.opportunity_score:.0f}/100 "
                f"| ریسک: {esc(_RISK_FA.get(opp.risk_level, opp.risk_level))}")
    else:
        lines.append("• در حال حاضر فرصتی با امتیاز بالای آستانه ثبت نشده است.")
    lines.append("")
    lines.append(FOOTER_MANDATED)
    return "\n".join(lines)
