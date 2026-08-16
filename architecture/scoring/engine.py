#!/usr/bin/env python3
"""AHOS Evidence-Based Opportunity Scoring Engine (Section VIII).

Strict Stage Separation:
  DATA -> SIGNALS -> EVIDENCE -> FEATURES -> RISK -> OPPORTUNITY -> CONFIDENCE -> INVALIDATION

Principles:
  - Deterministic decision floor: 100% computable without any AI API keys.
  - Provable explainability: Provides structured answers to all 8 canonical questions.
  - Transparent penalties for missing / UNKNOWN data.
  - Non-trading: produces Opportunity Intelligence, NEVER automated trade orders.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any
from ..providers.contracts import NormalizedTokenCandidate, UNKNOWN_VALUE


@dataclass
class EvidenceItem:
    key: str
    description: str
    value: Any
    provider: str
    timestamp: float
    freshness_seconds: float
    status: str                                  # VERIFIED | DERIVED | UNKNOWN | STALE


@dataclass
class RiskItem:
    risk_id: str
    severity: str                                # LOW | MED | HIGH | CRITICAL
    description: str
    penalty_points: float
    evidence_ref: str


@dataclass
class InvalidationCondition:
    condition_id: str
    trigger_description: str
    threshold: str
    is_triggered: bool = False


@dataclass
class OpportunityScoreReport:
    token_address: str
    token_chain: str
    token_symbol: str
    token_name: str
    opportunity_score: float                     # 0.0 to 100.0
    confidence_level: str                        # HIGH | MED | LOW
    risk_level: str                              # LOW | MED | HIGH | CRITICAL
    positive_reasons: list[str]
    risk_deductions: list[RiskItem]
    evidence_items: list[EvidenceItem]
    missing_unknowns: list[str]
    invalidation_conditions: list[InvalidationCondition]
    score_breakdown: dict[str, float]
    computed_at_ts: float = field(default_factory=time.time)
    provenance_sha256: str = ""

    def answer_why_scored(self) -> str:
        return "\n".join(f"+ {r}" for r in self.positive_reasons) if self.positive_reasons else "امتیاز پایه حداقلی"

    def answer_evidence(self) -> list[dict]:
        return [asdict(e) for e in self.evidence_items]

    def answer_missing(self) -> list[str]:
        return self.missing_unknowns

    def answer_risks(self) -> list[dict]:
        return [asdict(r) for r in self.risk_deductions]

    def answer_invalidation(self) -> list[dict]:
        return [asdict(c) for c in self.invalidation_conditions]


class OpportunityScorer:
    """Deterministic opportunity evaluation and evidence synthesizer."""

    def evaluate(self, candidate: NormalizedTokenCandidate,
                 previous_candidate: NormalizedTokenCandidate | None = None,
                 now: float | None = None) -> OpportunityScoreReport:
        ts = time.time() if now is None else now
        m = candidate.metrics
        sec = candidate.security
        evidence: list[EvidenceItem] = []
        risks: list[RiskItem] = []
        reasons: list[str] = []
        unknowns: list[str] = []

        # ---------------- 1. DATA -> EVIDENCE ----------------
        # Liquidity evidence
        if m.liquidity_usd is not None and m.liquidity_usd > 0:
            evidence.append(EvidenceItem(
                key="liquidity_usd",
                description=f"Liquidity depth ${m.liquidity_usd:,.2f}",
                value=m.liquidity_usd,
                provider=candidate.source_provider,
                timestamp=candidate.retrieved_ts,
                freshness_seconds=max(0.0, ts - candidate.retrieved_ts),
                status="VERIFIED"
            ))
        else:
            unknowns.append("نقدینگی استخر (Liquidity USD)")

        # Volume evidence
        if m.volume_1h is not None and m.volume_1h > 0:
            evidence.append(EvidenceItem(
                key="volume_1h",
                description=f"1h Volume ${m.volume_1h:,.2f}",
                value=m.volume_1h,
                provider=candidate.source_provider,
                timestamp=candidate.retrieved_ts,
                freshness_seconds=max(0.0, ts - candidate.retrieved_ts),
                status="VERIFIED"
            ))
        else:
            unknowns.append("حجم معاملات ۱ ساعته")

        # Security evidence
        if sec.is_honeypot is not None:
            evidence.append(EvidenceItem(
                key="is_honeypot",
                description=f"Honeypot check: {sec.is_honeypot}",
                value=sec.is_honeypot,
                provider="security_gate",
                timestamp=candidate.retrieved_ts,
                freshness_seconds=max(0.0, ts - candidate.retrieved_ts),
                status="VERIFIED"
            ))
        else:
            unknowns.append("بررسی Honeypot و امنیت قرارداد")

        if sec.top10_holder_concentration_pct is not None:
            evidence.append(EvidenceItem(
                key="top10_concentration",
                description=f"Top 10 concentration: {sec.top10_holder_concentration_pct:.1f}%",
                value=sec.top10_holder_concentration_pct,
                provider="security_gate",
                timestamp=candidate.retrieved_ts,
                freshness_seconds=max(0.0, ts - candidate.retrieved_ts),
                status="VERIFIED"
            ))
        else:
            unknowns.append("درصد تمرکز ۱۰ هولدر برتر")

        # ---------------- 2. SIGNALS & FEATURES -> BASE SCORE ----------------
        base_score = 0.0

        # Liquidity score (up to 30 pts)
        if m.liquidity_usd is not None:
            if m.liquidity_usd >= 50000:
                base_score += 30.0
                reasons.append(f"عمق نقدینگی بالا (${m.liquidity_usd:,.0f} ≥ $50k)")
            elif m.liquidity_usd >= 10000:
                base_score += 20.0
                reasons.append(f"نقدینگی مناسب (${m.liquidity_usd:,.0f} ≥ $10k)")
            elif m.liquidity_usd >= 2000:
                base_score += 10.0
                reasons.append("نقدینگی اولیه حداقلی")
            else:
                risks.append(RiskItem("LOW_LIQUIDITY", "HIGH", "نقدینگی بسیار اندک (< $2k)", 25.0, "metrics.liquidity_usd"))

        # Volume score (up to 30 pts)
        if m.volume_1h is not None and m.volume_1h > 0:
            if m.volume_1h >= 25000:
                base_score += 30.0
                reasons.append(f"حجم معاملات قوی ۱ ساعته (${m.volume_1h:,.0f})")
            elif m.volume_1h >= 5000:
                base_score += 20.0
                reasons.append(f"فعالیت حجمی فعال (${m.volume_1h:,.0f})")
            elif m.volume_1h >= 1000:
                base_score += 10.0
                reasons.append("حجم معاملات شروع شده")

        # Transaction flow / Buy pressure (up to 20 pts)
        if m.txns_1h_buys is not None and m.txns_1h_sells is not None:
            total_tx = m.txns_1h_buys + m.txns_1h_sells
            if total_tx > 20:
                buy_ratio = m.txns_1h_buys / total_tx
                if buy_ratio >= 0.65:
                    base_score += 20.0
                    reasons.append(f"برتری خریداران ({buy_ratio*100:.0f}% معاملات خرید)")
                elif buy_ratio >= 0.50:
                    base_score += 10.0
                    reasons.append("تعادل مناسب تراکنش‌ها")
                else:
                    risks.append(RiskItem("SELL_PRESSURE", "MED", "فشار فروش غالب در ۱ ساعت گذشته", 10.0, "txns_1h"))

        # Multi-source confirmation (up to 20 pts)
        if len(candidate.social_presence) > 0 or candidate.source_provider in ("dexscreener", "geckoterminal"):
            base_score += 20.0
            reasons.append("تأیید ساختار جفت‌ارز در منابع معتبر")

        # ---------------- 3. RISKS & SECURITY VETOES ----------------
        if sec.is_honeypot is True:
            risks.append(RiskItem("CRITICAL_HONEYPOT", "CRITICAL", "قرارداد به عنوان Honeypot شناسایی شد", 100.0, "security.is_honeypot"))
        if sec.has_mint_authority is True:
            risks.append(RiskItem("MINT_AUTHORITY_ACTIVE", "HIGH", "قابلیت ضرب توکن نامحدود فعال است", 20.0, "security.has_mint_authority"))
        if sec.has_freeze_authority is True:
            risks.append(RiskItem("FREEZE_AUTHORITY_ACTIVE", "HIGH", "قابلیت مسدودسازی کیف‌پول‌ها فعال است", 20.0, "security.has_freeze_authority"))
        if sec.top10_holder_concentration_pct and sec.top10_holder_concentration_pct > 70.0:
            risks.append(RiskItem("HIGH_HOLDER_CONCENTRATION", "HIGH", f"تمرکز شدید هولدرها ({sec.top10_holder_concentration_pct:.1f}%)", 25.0, "security.top10_holder_concentration_pct"))
        if sec.is_contract_verified is False:
            risks.append(RiskItem("UNVERIFIED_CONTRACT", "MED", "سورس کد قرارداد تایید نشده است", 10.0, "security.is_contract_verified"))

        # Penalty for excessive unknowns
        if len(unknowns) >= 3:
            risks.append(RiskItem("HIGH_UNCERTAINTY", "MED", f"عدم قطعیت بالا ({len(unknowns)} فیلد ناشناخته)", len(unknowns) * 3.0, "unknown_fields"))

        # ---------------- 4. OPPORTUNITY SCORE & RISK LEVEL ----------------
        total_penalties = sum(r.penalty_points for r in risks)
        final_score = max(0.0, min(100.0, base_score - total_penalties))

        # Risk level determination
        if any(r.severity == "CRITICAL" for r in risks) or total_penalties >= 50.0:
            risk_level = "CRITICAL"
        elif any(r.severity == "HIGH" for r in risks) or total_penalties >= 25.0:
            risk_level = "HIGH"
        elif any(r.severity == "MED" for r in risks) or total_penalties >= 10.0:
            risk_level = "MED"
        else:
            risk_level = "LOW"

        # Confidence level determination
        if len(unknowns) == 0 and len(evidence) >= 4:
            confidence_level = "HIGH"
        elif len(unknowns) <= 2 and len(evidence) >= 2:
            confidence_level = "MED"
        else:
            confidence_level = "LOW"

        # ---------------- 5. INVALIDATION CONDITIONS ----------------
        invalidation = [
            InvalidationCondition("INV-01", "کاهش نقدینگی به زیر ۲۰٪ سطح فعلی", f"< ${max(m.liquidity_usd or 0, 0)*0.2:,.0f}"),
            InvalidationCondition("INV-02", "افت حجم معاملات ۱ ساعته به زیر ۷۰٪ سطح فعلی", f"< ${max(m.volume_1h or 0, 0)*0.3:,.0f}"),
            InvalidationCondition("INV-03", "فعال شدن سیگنال Honeypot یا قفل ناموفق", "is_honeypot = True"),
            InvalidationCondition("INV-04", "افزایش مالیات خرید/فروش به بالای ۱۰٪", "buy/sell tax > 10%")
        ]

        return OpportunityScoreReport(
            token_address=candidate.address,
            token_chain=candidate.chain,
            token_symbol=candidate.symbol,
            token_name=candidate.name,
            opportunity_score=round(final_score, 1),
            confidence_level=confidence_level,
            risk_level=risk_level,
            positive_reasons=reasons,
            risk_deductions=risks,
            evidence_items=evidence,
            missing_unknowns=unknowns,
            invalidation_conditions=invalidation,
            score_breakdown={
                "base_score": base_score,
                "total_penalties": total_penalties,
                "final_score": final_score
            },
            computed_at_ts=ts
        )
