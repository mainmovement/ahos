"""
intelligence.risk.manipulation_risk — Wash / pump / social manipulation risk
"""

from __future__ import annotations

import time
from typing import Dict

from core.models.evidence import Evidence
from .base import RiskAnalyzer, RiskResult, RiskLevel


class ManipulationRiskAnalyzer(RiskAnalyzer):
    analyzer_id = "manipulation_risk"

    def analyze(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskResult:
        for k, v in evidence_map.items():
            if not isinstance(v, Evidence):
                raise TypeError(f"Evidence only: {k!r} must be Evidence, got {type(v).__name__}")
        ts = now if now is not None else time.time()
        reasons: list[str] = []
        refs: list[str] = []

        ev_vol_acc = evidence_map.get("volume_acceleration")
        ev_txn_acc = evidence_map.get("txn_acceleration")
        ev_buys = evidence_map.get("buys_ratio")
        ev_narrative = evidence_map.get("narrative_score")

        for ev in [ev_vol_acc, ev_txn_acc, ev_buys, ev_narrative]:
            if ev:
                refs.append(ev.evidence_id)

        vol_acc = ev_vol_acc.value if ev_vol_acc and isinstance(ev_vol_acc.value, (int, float)) else None
        txn_acc = ev_txn_acc.value if ev_txn_acc and isinstance(ev_txn_acc.value, (int, float)) else None
        buys_ratio = ev_buys.value if ev_buys and isinstance(ev_buys.value, (int, float)) else None

        score = 15
        level = RiskLevel.LOW

        # Wash: volume accelerates far faster than txn count
        if isinstance(vol_acc, (int, float)) and isinstance(txn_acc, (int, float)) and txn_acc > 0:
            try:
                divergence = float(vol_acc) / float(txn_acc)
                if divergence >= 4 and vol_acc >= 5:
                    reasons.append(f"واگرایی حجم/تراکنش {divergence:.1f}× با شتاب حجم {vol_acc:.1f}× — احتمال معاملات صوری")
                    score = max(score, 75)
                    level = RiskLevel.HIGH
                elif divergence >= 2.5 and vol_acc >= 3:
                    reasons.append(f"واگرایی متوسط {divergence:.1f}× — نیازمند احتیاط")
                    score = max(score, 45)
                    if level == RiskLevel.LOW:
                        level = RiskLevel.MEDIUM
            except Exception:
                pass

        # Coordinated buys: 97%+ buys is not organic
        if isinstance(buys_ratio, (int, float)):
            try:
                br = float(buys_ratio)
                if br >= 0.97:
                    reasons.append(f"نسبت خرید {br:.1%} (≥97٪) — الگوی هماهنگ/پامپ محتمل")
                    score = max(score, 70)
                    level = RiskLevel.HIGH if level != RiskLevel.CRITICAL else level
                elif br >= 0.93:
                    reasons.append(f"نسبت خرید بالا {br:.1%}")
                    score = max(score, 40)
            except Exception:
                pass

        # Narrative vs reality gap
        if ev_narrative and isinstance(ev_narrative.value, (int, float)) and float(ev_narrative.value) > 80 and (vol_acc is None or vol_acc < 2):
            reasons.append("امتیاز شبکه اجتماعی بالا اما شتاب حجمی پایین — احتمال تبلیغ بدون تقاضا")
            score = max(score, 35)
            if level == RiskLevel.LOW:
                level = RiskLevel.MEDIUM

        if not reasons:
            reasons.append("الگوی دستکاری خاصی شناسایی نشد — معاملات عادی")
            score = 15
            level = RiskLevel.LOW

        # If no relevant evidence at all, mark UNKNOWN but not critical
        if vol_acc is None and buys_ratio is None and ev_narrative is None:
            return RiskResult(analyzer=self.analyzer_id, level=RiskLevel.UNKNOWN, score=30, reasons=["داده کافی برای تشخیص دستکاری در دسترس نیست"], evidence_refs=refs, metadata={}, computed_at=ts)

        return RiskResult(analyzer=self.analyzer_id, level=level, score=float(score), reasons=reasons, evidence_refs=refs, metadata={"vol_acc": vol_acc, "txn_acc": txn_acc, "buys_ratio": buys_ratio}, computed_at=ts)
