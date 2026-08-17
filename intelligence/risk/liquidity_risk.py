"""
intelligence.risk.liquidity_risk — Liquidity / exit feasibility risk
"""

from __future__ import annotations

import time
from typing import Dict

from core.models.evidence import Evidence
from .base import RiskAnalyzer, RiskResult, RiskLevel


class LiquidityRiskAnalyzer(RiskAnalyzer):
    analyzer_id = "liquidity_risk"

    def analyze(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskResult:
        for k, v in evidence_map.items():
            if not isinstance(v, Evidence):
                raise TypeError(f"Evidence only: {k!r} must be Evidence, got {type(v).__name__}")
        ts = now if now is not None else time.time()
        reasons: list[str] = []
        refs: list[str] = []

        ev_liq = evidence_map.get("liquidity_usd")
        ev_fdv = evidence_map.get("fdv_usd")
        if ev_liq:
            refs.append(ev_liq.evidence_id)
        if ev_fdv:
            refs.append(ev_fdv.evidence_id)

        liq = ev_liq.value if ev_liq and isinstance(ev_liq.value, (int, float)) else None
        fdv = ev_fdv.value if ev_fdv and isinstance(ev_fdv.value, (int, float)) else None

        if liq is None:
            return RiskResult(analyzer=self.analyzer_id, level=RiskLevel.UNKNOWN, score=50, reasons=["نقدینگی نامشخص — امکان خروج قابل تأیید نیست"], evidence_refs=refs, metadata={"liq": None}, computed_at=ts)

        try:
            liq_f = float(liq)
        except Exception:
            liq_f = 0

        if liq_f < 500:
            return RiskResult(analyzer=self.analyzer_id, level=RiskLevel.CRITICAL, score=95, reasons=[f"نقدینگی بسیار اندک (${liq_f:,.0f} < $500) — خروج عملاً غیرممکن"], evidence_refs=refs, metadata={"liq": liq_f}, computed_at=ts)
        if liq_f < 2000:
            level, score, reason = RiskLevel.HIGH, 80, f"نقدینگی اندک (${liq_f:,.0f} < $2k) — لغزش بالا و خروج سخت"
        elif liq_f < 10000:
            level, score, reason = RiskLevel.MEDIUM, 50, f"نقدینگی محدود (${liq_f:,.0f}) — برای مبالغ کوچک مناسب"
        elif liq_f < 50000:
            level, score, reason = RiskLevel.MEDIUM, 30, f"نقدینگی متوسط (${liq_f:,.0f})"
        else:
            level, score, reason = RiskLevel.LOW, 15, f"نقدینگی کافی (${liq_f:,.0f})"

        reasons.append(reason)

        # FDV/liquidity dilution check
        if fdv is not None and liq_f > 0:
            try:
                ratio = float(fdv) / liq_f
                if ratio > 400:
                    reasons.append(f"نسبت FDV/نقدینگی {ratio:.0f}× — رقیق‌سازی شدید (400×+)")
                    score = max(score, 70)
                    if level not in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                        level = RiskLevel.HIGH
                elif ratio > 120:
                    reasons.append(f"نسبت FDV/نقدینگی {ratio:.0f}× — رقیق‌سازی متوسط")
                    score = max(score, 45)
            except Exception:
                pass

        return RiskResult(analyzer=self.analyzer_id, level=level, score=float(score), reasons=reasons, evidence_refs=refs, metadata={"liq": liq_f, "fdv": fdv}, computed_at=ts)
