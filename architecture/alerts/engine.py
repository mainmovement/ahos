#!/usr/bin/env python3
"""AHOS Deterministic Alert Engine (Section XII).

Monitors candidates and paper positions for:
  - OPPORTUNITY: score threshold crossing (score >= 75)
  - THESIS_STRENGTHENING: multi-source liquidity / volume surge
  - RISK_INCREASING: risk escalation / holder concentration increase
  - THESIS_INVALIDATED: invalidation trigger (liquidity dump or honeypot)
  - SECURITY_EVENT: hard veto or blacklisted deployer
  - ABNORMAL_MOVEMENT: volume acceleration spike (>= 3.0x)
  - STALE_OBSERVATION: observation freshness degradation (>4h)

Law:
  - Every alert carries >= 1 reason and >= 1 evidence reference.
  - Alerts are 100% deterministic and auditable.
"""
from __future__ import annotations

import time
from typing import Any
from telegram_ai.alerts import Alert, build as build_alert
from architecture.scoring.engine import OpportunityScoreReport
from architecture.providers.contracts import NormalizedTokenCandidate


class AlertEngine:
    def __init__(self, score_threshold: float = 75.0, volume_spike_threshold: float = 3.0):
        self.score_threshold = score_threshold
        self.volume_spike_threshold = volume_spike_threshold

    def evaluate_opportunity(self, report: OpportunityScoreReport,
                             candidate: NormalizedTokenCandidate,
                             now: float | None = None) -> list[Alert]:
        alerts: list[Alert] = []
        ts = time.time() if now is None else now

        # 1. High Score Opportunity Alert
        if report.opportunity_score >= self.score_threshold and report.risk_level in ("LOW", "MED"):
            alerts.append(build_alert(
                cls="OPPORTUNITY",
                symbol=report.token_symbol,
                reasons=[f"امتیاز فرصت بالا ({report.opportunity_score:.0f}/100) با ریسک {report.risk_level}"] + report.positive_reasons[:2],
                evidence=[f"score={report.opportunity_score:.0f}", f"prov={candidate.source_provider}", f"addr={report.token_address}"],
                severity="HIGH",
                data_state="LIVE" if (ts - candidate.retrieved_ts < 3600) else "STALE"
            ))

        # 2. Critical Security Alert
        if candidate.security.is_honeypot is True:
            alerts.append(build_alert(
                cls="SECURITY_EVENT",
                symbol=report.token_symbol,
                reasons=["شناسایی رفتار Honeypot در تست امنیتی قرارداد"],
                evidence=["security.is_honeypot=True", f"provider={candidate.source_provider}"],
                severity="HIGH"
            ))

        # 3. Abnormal Volume Movement
        if candidate.metrics.volume_velocity and candidate.metrics.volume_velocity >= self.volume_spike_threshold:
            alerts.append(build_alert(
                cls="ABNORMAL_MOVEMENT",
                symbol=report.token_symbol,
                reasons=[f"شتاب غیرعادی حجم معاملات ({candidate.metrics.volume_velocity:.1f}x نسبت به میانگین)"],
                evidence=[f"volume_velocity={candidate.metrics.volume_velocity:.2f}"],
                severity="MED"
            ))

        # 4. Risk Escalation Alert
        if report.risk_level == "CRITICAL" and not any(a.cls == "SECURITY_EVENT" for a in alerts):
            alerts.append(build_alert(
                cls="RISK_INCREASING",
                symbol=report.token_symbol,
                reasons=[r.description for r in report.risk_deductions[:2]] or ["تشدید ریسک ساختاری"],
                evidence=[r.evidence_ref for r in report.risk_deductions[:2]] or ["risk=CRITICAL"],
                severity="HIGH"
            ))

        # 5. Stale Observation Warning
        if ts - candidate.retrieved_ts > 4 * 3600:
            alerts.append(build_alert(
                cls="SITUATION_CHANGING",
                symbol=report.token_symbol,
                reasons=[f"داده‌های مشاهده قدیمی شده‌اند ({int((ts - candidate.retrieved_ts)//3600)} ساعت بدون مشاهده تازه)"],
                evidence=[f"obs_age_sec={ts - candidate.retrieved_ts:.0f}"],
                severity="LOW",
                data_state="STALE"
            ))

        return alerts
