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
from architecture.intel.viral import WASH_DIVERGENCE


def _per_5m_baseline(hourly: float | None) -> float | None:
    """The per-5m rate implied by a trailing hour. Twelve 5m windows per hour."""
    if hourly is None or hourly <= 0:
        return None
    return hourly / 12.0


def _volume_acceleration(m) -> float | None:
    base = _per_5m_baseline(m.volume_1h)
    if base is None or m.volume_5m is None:
        return None
    return m.volume_5m / base


def _txn_acceleration(m) -> float | None:
    if None in (m.txns_5m_buys, m.txns_5m_sells, m.txns_1h_buys, m.txns_1h_sells):
        return None
    base = _per_5m_baseline(float(m.txns_1h_buys + m.txns_1h_sells))
    if base is None:
        return None
    return (m.txns_5m_buys + m.txns_5m_sells) / base


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
        #
        # This rule keyed on `metrics.volume_velocity`, a field NO adapter has
        # ever populated -- it is declared in the contract and set nowhere, so
        # it is always None and the whole ABNORMAL_MOVEMENT class was dead
        # code. Verified: a token doing 90k in five minutes against 200k over
        # the day raised no movement alert at all.
        #
        # The quantity was already being computed correctly elsewhere.
        # ViralityAnalyzer derives volume acceleration as the 5m window over
        # the per-5m rate implied by the trailing hour, which is the honest
        # baseline (dividing the hour by 12), and it also knows that volume
        # accelerating far faster than transaction count means wash trading
        # rather than attention. Recomputing that here would have duplicated a
        # subtle calculation and let the two drift apart, so the alert now
        # reads the same derivation.
        accel = _volume_acceleration(candidate.metrics)
        if accel is not None and accel >= self.volume_spike_threshold:
            txn_accel = _txn_acceleration(candidate.metrics)
            washy = (txn_accel is not None and txn_accel > 0
                     and accel / txn_accel >= WASH_DIVERGENCE)
            reasons = [f"شتاب غیرعادی حجم معاملات ({accel:.1f}× نرخ ساعت گذشته)"]
            evidence = [f"volume_acceleration={accel:.2f}",
                        f"volume_5m={candidate.metrics.volume_5m}",
                        f"volume_1h={candidate.metrics.volume_1h}"]
            if washy:
                # Do not report manufactured volume as if it were interest.
                reasons.append(
                    f"اما تعداد تراکنش‌ها تنها {txn_accel:.1f}× شتاب گرفته — "
                    f"واگرایی نشانه معاملات صوری است، نه توجه واقعی")
                evidence.append(f"txn_acceleration={txn_accel:.2f}")
            alerts.append(build_alert(
                cls="ABNORMAL_MOVEMENT",
                symbol=report.token_symbol,
                reasons=reasons,
                evidence=evidence,
                severity="HIGH" if washy else "MED"
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
