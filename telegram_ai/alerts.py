#!/usr/bin/env python3
"""AHOS alert builder — WHY-MANDATED by construction (Wave-7 directive §18).

Law:
  - Every alert MUST carry >=1 reason string AND >=1 evidence reference
    (observation id / feature key / probe id / security verdict id). build()
    raises otherwise — a meaningless alert is a TYPE ERROR, not a style issue.
  - Alert quality > alert quantity: per-class minimum-severity metadata lives
    here so callers cannot invent spam classes.
  - Persian rendering ends with the mandated footer on decisional classes:
    «تصمیم نهایی با کاربر است.»
"""
from __future__ import annotations

from dataclasses import dataclass, field

FOOTER = "تصمیم نهایی با کاربر است."

ALERT_CLASSES = {
    "OPPORTUNITY":          {"emoji": "🚨", "min_severity": "HIGH",   "decisional": True},
    "THESIS_STRENGTHENING": {"emoji": "🟢", "min_severity": "MED",    "decisional": True},
    "SITUATION_CHANGING":   {"emoji": "🟡", "min_severity": "LOW",    "decisional": True},
    "RISK_INCREASING":      {"emoji": "🟠", "min_severity": "MED",    "decisional": True},
    "THESIS_INVALIDATED":   {"emoji": "🔴", "min_severity": "HIGH",   "decisional": True},
    "SECURITY_EVENT":       {"emoji": "🚨", "min_severity": "HIGH",   "decisional": True},
    "ABNORMAL_MOVEMENT":    {"emoji": "🚀", "min_severity": "MED",    "decisional": False},
}

_TITLE_FA = {
    "OPPORTUNITY": "فرصت شناسایی شد",
    "THESIS_STRENGTHENING": "تقویت تز",
    "SITUATION_CHANGING": "تغییر وضعیت",
    "RISK_INCREASING": "افزایش ریسک",
    "THESIS_INVALIDATED": "ابطال تز",
    "SECURITY_EVENT": "رویداد امنیتی",
    "ABNORMAL_MOVEMENT": "حرکت غیرعادی",
}


@dataclass
class Alert:
    cls: str
    symbol: str
    reasons: list[str]
    evidence: list[str]
    severity: str
    data_state: str = "LIVE"   # LIVE | STALE | UNKNOWN — staleness is never hidden
    meta: dict = field(default_factory=dict)


def build(cls: str, symbol: str, reasons: list[str], evidence: list[str],
          severity: str = "MED", data_state: str = "LIVE", meta: dict | None = None) -> Alert:
    if cls not in ALERT_CLASSES:
        raise ValueError(f"unknown alert class: {cls}")
    reasons = [r for r in (reasons or []) if isinstance(r, str) and r.strip()]
    evidence = [e for e in (evidence or []) if isinstance(e, str) and e.strip()]
    if not reasons:
        raise ValueError("WHY-law: alert requires >=1 reason")
    if not evidence:
        raise ValueError("WHY-law: alert requires >=1 evidence reference")
    if not symbol:
        raise ValueError("alert requires a subject (symbol/token ref)")
    return Alert(cls, symbol, reasons, evidence, severity, data_state, meta or {})


def render_fa(a: Alert) -> str:
    spec = ALERT_CLASSES[a.cls]
    lines = [f"{spec['emoji']} {_TITLE_FA[a.cls]} — {a.symbol}", ""]
    lines.append("چرا:")
    lines.extend(f"• {r}" for r in a.reasons)
    lines.append("")
    lines.append("شواهد:")
    lines.extend(f"‹{e}›" for e in a.evidence)
    if a.data_state != "LIVE":
        lines.append("")
        lines.append(f"⚠️ وضعیت داده: {a.data_state}")
    lines.append("")
    if spec["decisional"]:
        lines.append(FOOTER)
    return "\n".join(lines).strip()
