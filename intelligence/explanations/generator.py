"""
intelligence.explanations.generator — Human-readable explanation generator

Converts ScoreResult + RiskEngineResult + evidence audit into a
Persian-first, evidence-cited explanation. No LLM, no network, deterministic.

Output contract:
  Explanation.text — fully formatted Persian block for Telegram / docs
  Explanation.brief — one-line summary
  Explanation.bullets — why scored + risks + evidence + invalidation
  Explanation.evidence_citations — list of evidence_ids cited
  Explanation.confidence — HIGH/MEDIUM/LOW/UNKNOWN
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from core.models.evidence import Confidence

ADVISORY_FOOTER = "تصمیم نهایی با کاربر است — این یک توضیح تحلیلی است، نه دستور معامله."


@dataclass(frozen=True)
class Explanation:
    brief: str
    text: str
    bullets: Dict[str, List[str]]
    evidence_citations: List[str]
    confidence: str
    score: float
    risk_level: str
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExplanationGenerator:
    """
    Deterministic explanation builder.
    Input: ScoreResult, RiskEngineResult (or compatible dict), evidence audit.
    Output: Explanation (Persian, evidence-cited, no hallucination).
    """

    def generate(
        self,
        score_result: Any,
        risk_result: Any = None,
        evidence_audit: Dict[str, Any] | None = None,
        now: float | None = None,
    ) -> Explanation:
        ts = now if now is not None else time.time()

        # Normalize score_result (supports ScoreResult or dict)
        if hasattr(score_result, "to_dict"):
            score_dict = score_result.to_dict()
        elif isinstance(score_result, dict):
            score_dict = dict(score_result)
        else:
            raise ValueError("score_result must be ScoreResult or dict")

        total = float(score_dict.get("total_score", score_dict.get("score", 0)))
        conf = str(score_dict.get("confidence", Confidence.UNKNOWN))
        breakdown = score_dict.get("breakdown", {}) or {}
        evidence_refs = score_dict.get("evidence_refs", []) or []

        # Risk
        risk_level = RiskLevelFallback = "UNKNOWN"
        risk_score = 0.0
        risk_reasons: List[str] = []
        if risk_result is not None:
            if hasattr(risk_result, "to_dict"):
                risk_dict = risk_result.to_dict()
            elif isinstance(risk_result, dict):
                risk_dict = dict(risk_result)
            else:
                risk_dict = {}
            risk_level = str(risk_dict.get("aggregate_level", risk_dict.get("level", "UNKNOWN")))
            risk_score = float(risk_dict.get("aggregate_score", risk_dict.get("score", 0)))
            risk_reasons = list(risk_dict.get("highest_reasons", risk_dict.get("reasons", [])) or [])
            # Merge evidence refs
            for eid in risk_dict.get("evidence_refs", []):
                if eid not in evidence_refs:
                    evidence_refs.append(eid)
        else:
            risk_level = str(score_dict.get("risk_level", "UNKNOWN"))

        # Evidence audit
        evidence_citations = list(evidence_refs[:8])
        coverage_note = ""
        if evidence_audit:
            total_cnt = evidence_audit.get("total")
            elig = evidence_audit.get("eligible")
            if total_cnt is not None and elig is not None:
                coverage_note = f"پوشش شواهد: {elig}/{total_cnt} مورد واجد شرایط"

        # Build Persian text
        icon = self._icon(total, risk_level, conf)
        header = f"{icon} امتیاز {total:.0f}/100 — اعتماد {conf} — ریسک {risk_level}"

        # Why bullets (positive drivers)
        why: List[str] = []
        for k in ("market_score", "security_score", "liquidity_score", "whale_score", "social_score"):
            v = breakdown.get(k)
            if isinstance(v, (int, float)):
                label = {
                    "market_score": "بازار",
                    "security_score": "امنیت",
                    "liquidity_score": "نقدینگی",
                    "whale_score": "نهنگ/تمرکز",
                    "social_score": "اجتماعی/وایرال",
                }.get(k, k)
                why.append(f"{label}: {v:.0f}/100")

        # Risk bullets
        risk_bullets: List[str] = []
        if risk_reasons:
            risk_bullets = risk_reasons[:4]
        elif float(breakdown.get("risk_penalty", 0)) > 0:
            risk_bullets.append(f"جریمه ریسک: {breakdown.get('risk_penalty', 0):.0f}")

        # Evidence bullets
        evidence_bullets: List[str] = []
        if evidence_citations:
            evidence_bullets.append(f"ارجاع شواهد: {', '.join(c[:8] for c in evidence_citations)}")
        if coverage_note:
            evidence_bullets.append(coverage_note)

        # Invalidation / next steps
        invalidation: List[str] = []
        if risk_level in ("CRITICAL", "HIGH"):
            invalidation.append("ابطال در صورت تأیید ریسک‌های فوق — ورود توصیه نمی‌شود")
        elif conf in (Confidence.LOW, Confidence.UNKNOWN):
            invalidation.append("نیازمند شواهد بیشتر — تصمیم با داده ناقص پرهیز")
        else:
            invalidation.append("پایش نقدینگی و تمرکز قبل از هر اقدام")

        # Assemble text
        lines: List[str] = [header, ""]
        if why:
            lines.append("چرا این امتیاز:")
            lines.extend(f"  • {b}" for b in why)
            lines.append("")
        if risk_bullets:
            lines.append("ریسک‌ها:")
            lines.extend(f"  • {b}" for b in risk_bullets)
            lines.append("")
        if evidence_bullets:
            lines.append("شواهد:")
            lines.extend(f"  • {b}" for b in evidence_bullets)
            lines.append("")
        if invalidation:
            lines.append("ابطال/گام بعد:")
            lines.extend(f"  • {b}" for b in invalidation)
            lines.append("")
        lines.append(ADVISORY_FOOTER)

        text = "\n".join(lines)
        brief = f"امتیاز {total:.0f} ({conf}) — ریسک {risk_level} — {why[0] if why else ''}"

        return Explanation(
            brief=brief.strip(),
            text=text,
            bullets={"why": why, "risks": risk_bullets, "evidence": evidence_bullets, "invalidation": invalidation},
            evidence_citations=evidence_citations,
            confidence=conf,
            score=total,
            risk_level=risk_level,
            computed_at=ts,
        )

    def _icon(self, score: float, risk_level: str, confidence: str) -> str:
        if risk_level == "CRITICAL":
            return "🔴"
        if risk_level == "HIGH":
            return "🟠"
        if confidence == Confidence.UNKNOWN or confidence == Confidence.LOW:
            return "⚪"
        if score >= 70:
            return "🟢"
        if score >= 50:
            return "🟡"
        return "⚪"
