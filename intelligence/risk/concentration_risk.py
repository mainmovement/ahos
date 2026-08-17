"""
intelligence.risk.concentration_risk — Holder / whale concentration risk
"""

from __future__ import annotations

import time
from typing import Dict

from core.models.evidence import Evidence
from .base import RiskAnalyzer, RiskResult, RiskLevel


class ConcentrationRiskAnalyzer(RiskAnalyzer):
    analyzer_id = "concentration_risk"

    def analyze(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskResult:
        for k, v in evidence_map.items():
            if not isinstance(v, Evidence):
                raise TypeError(f"Evidence only: {k!r} must be Evidence, got {type(v).__name__}")
        ts = now if now is not None else time.time()
        refs: list[str] = []
        reasons: list[str] = []

        ev_top10 = evidence_map.get("top10_share")
        ev_top20 = evidence_map.get("top20_share")
        ev_holders = evidence_map.get("holders_count")
        for ev in [ev_top10, ev_top20, ev_holders]:
            if ev:
                refs.append(ev.evidence_id)

        top10 = ev_top10.value if ev_top10 and isinstance(ev_top10.value, (int, float)) else None

        if top10 is None:
            return RiskResult(analyzer=self.analyzer_id, level=RiskLevel.UNKNOWN, score=40, reasons=["تمرکز مالکیت نامشخص — توزیع هولدرها در دسترس نیست"], evidence_refs=refs, metadata={"top10": None}, computed_at=ts)

        try:
            v = float(top10)
            # Normalize if 0-1 vs 0-100
            if 0 <= v <= 1:
                v = v * 100
        except Exception:
            return RiskResult(analyzer=self.analyzer_id, level=RiskLevel.UNKNOWN, score=40, reasons=["تمرکز نامعتبر"], evidence_refs=refs, metadata={}, computed_at=ts)

        if v > 80:
            level, score, reason = RiskLevel.CRITICAL, 90, f"تمرکز بسیار بالا: ۱۰ هولدر برتر {v:.1f}٪ — ریسک دامپ شدید"
        elif v > 70:
            level, score, reason = RiskLevel.HIGH, 75, f"تمرکز بالا: ده هولدر {v:.1f}٪"
        elif v > 50:
            level, score, reason = RiskLevel.MEDIUM, 50, f"تمرکز متوسط: {v:.1f}٪"
        elif v > 30:
            level, score, reason = RiskLevel.MEDIUM, 30, f"تمرکز قابل قبول: {v:.1f}٪"
        else:
            level, score, reason = RiskLevel.LOW, 15, f"توزیع مناسب: {v:.1f}٪"

        reasons.append(reason)

        # Holder count as secondary signal
        if ev_holders and isinstance(ev_holders.value, (int, float)):
            try:
                hc = int(ev_holders.value)
                if hc < 20:
                    reasons.append(f"تعداد هولدرها بسیار کم ({hc}) — نقدشوندگی اجتماعی پایین")
                    score = max(score, 60)
                    if level == RiskLevel.LOW:
                        level = RiskLevel.MEDIUM
            except Exception:
                pass

        return RiskResult(analyzer=self.analyzer_id, level=level, score=float(score), reasons=reasons, evidence_refs=refs, metadata={"top10": v}, computed_at=ts)
