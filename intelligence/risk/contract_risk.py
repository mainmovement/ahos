"""
intelligence.risk.contract_risk — Contract risk (honeypot, mint/freeze, unverified)
"""

from __future__ import annotations

import time
from typing import Dict

from core.models.evidence import Evidence
from .base import RiskAnalyzer, RiskResult, RiskLevel


class ContractRiskAnalyzer(RiskAnalyzer):
    analyzer_id = "contract_risk"

    def analyze(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskResult:
        # Evidence-only law: reject raw values
        for k, v in evidence_map.items():
            if not isinstance(v, Evidence):
                raise TypeError(f"Evidence only: {k!r} must be Evidence, got {type(v).__name__}")
        ts = now if now is not None else time.time()
        reasons: list[str] = []
        score = 10
        level = RiskLevel.LOW

        ev_honey = evidence_map.get("is_honeypot")
        ev_mint = evidence_map.get("has_mint_authority")
        ev_freeze = evidence_map.get("has_freeze_authority")
        ev_verified = evidence_map.get("contract_verified")

        refs: list[str] = []
        for ev in [ev_honey, ev_mint, ev_freeze, ev_verified]:
            if ev and isinstance(ev, Evidence):
                refs.append(ev.evidence_id)

        if ev_honey and ev_honey.value is True:
            reasons.append("هانی‌پات تأیید شد — قرارداد اجازه فروش نمی‌دهد")
            score = 100
            level = RiskLevel.CRITICAL
        elif ev_honey and ev_honey.value is None:
            reasons.append("وضعیت هانی‌پات نامشخص — نیازمند بررسی بیشتر")
            score = max(score, 40)
            level = RiskLevel.MEDIUM
        else:
            # Check other contract signals only if not honeypot
            if ev_mint and ev_mint.value is True:
                reasons.append("اختیار ضرب (mint) فعال — عرضه می‌تواند بی‌نهایت افزایش یابد")
                score = max(score, 70)
                level = RiskLevel.HIGH if level != RiskLevel.CRITICAL else level
            if ev_freeze and ev_freeze.value is True:
                reasons.append("اختیار مسدودسازی (freeze) فعال — دارایی قابل قفل شدن است")
                score = max(score, 70)
                level = RiskLevel.HIGH if level != RiskLevel.CRITICAL else level
            if ev_verified and ev_verified.value is False:
                reasons.append("قرارداد تأیید نشده (unverified) — کد قابل بررسی نیست")
                score = max(score, 50)
                if level == RiskLevel.LOW:
                    level = RiskLevel.MEDIUM

        if not reasons:
            reasons.append("ریسک قراردادی پایین — بررسی‌های اولیه مشکلی نشان نداد")
            score = 10
            level = RiskLevel.LOW

        return RiskResult(analyzer=self.analyzer_id, level=level, score=float(score), reasons=reasons, evidence_refs=refs, metadata={"source": "contract"}, computed_at=ts)
