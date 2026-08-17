#!/usr/bin/env python3
"""AHOS Virality & Attention-Acceleration Tracker.

Answers: "is attention on this token ACCELERATING, and is the acceleration real
or manufactured?"

WHY NOT SCRAPE TWITTER / TIKTOK / INSTAGRAM
-------------------------------------------
Those platforms require paid API tiers or ToS-violating scraping, and are heavily
filtered from Iran. Both violate project law ($0 ceiling, Iran-resilient). Instead
we measure attention through the FOOTPRINT it leaves in free on-chain and DEX data,
which is harder to fake than a follower count:

    transaction acceleration  — txns_5m vs the 1h baseline rate
    volume acceleration       — volume_5m vs the 1h baseline rate
    buy pressure              — buy/sell ratio
    DEX boosts                — paid promotion (a PAID signal, treated as a RISK)
    unique-maker growth       — breadth of participation, not just size

MANUFACTURED-HYPE DETECTION
---------------------------
Wash trading inflates volume while leaving footprints: volume that rises without a
matching rise in transaction COUNT, or transaction count without unique makers.
When volume acceleration massively outruns transaction acceleration, we do NOT
report bullish virality — we raise a WASH_SUSPECTED flag. A pump you cannot exit
is not an opportunity; it is bait.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

# --- Locked thresholds (pre-registered; changing them = a new version) ------
VIRALITY_VERSION = "AHOS-VIRAL-v1"

ACCEL_HOT = 3.0            # >=3x baseline rate == genuinely accelerating
ACCEL_WARM = 1.5           # >=1.5x == building
BUY_PRESSURE_STRONG = 1.6  # buys/sells
BUY_PRESSURE_WEAK = 0.7    # heavy net selling
WASH_DIVERGENCE = 4.0      # volume accel / txn accel above this == suspicious
MIN_TXNS_FOR_SIGNAL = 10   # below this, sample too small to mean anything


@dataclass
class ViralitySignal:
    subject: str
    label: str                      # VIRAL | BUILDING | FLAT | COOLING | UNKNOWN
    score: float                    # [0.0, 100.0]; attention intensity
    txn_acceleration: float | None
    volume_acceleration: float | None
    buy_pressure: float | None
    wash_suspected: bool
    is_paid_promotion: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    computed_ts: float = field(default_factory=time.time)
    version: str = VIRALITY_VERSION

    @property
    def is_known(self) -> bool:
        return self.label != "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject, "label": self.label, "score": self.score,
            "txn_acceleration": self.txn_acceleration,
            "volume_acceleration": self.volume_acceleration,
            "buy_pressure": self.buy_pressure,
            "wash_suspected": self.wash_suspected,
            "is_paid_promotion": self.is_paid_promotion,
            "reasons": self.reasons, "warnings": self.warnings,
            "unknowns": self.unknowns, "computed_ts": self.computed_ts,
            "version": self.version,
        }


class ViralityTracker:
    """Derives attention acceleration from free market microstructure data."""

    def analyze(self, candidate, boost_amount: float | None = None,
                now: float | None = None) -> ViralitySignal:
        """`candidate` is a NormalizedTokenCandidate (duck-typed for testability)."""
        ts = time.time() if now is None else now
        m = candidate.metrics
        symbol = getattr(candidate, "symbol", "?")

        reasons: list[str] = []
        warnings: list[str] = []
        unknowns: list[str] = []

        # ---- 1. Transaction acceleration -----------------------------------
        # 5m window vs the per-5m rate implied by the trailing hour.
        txn_accel: float | None = None
        txns_5m = _sum_opt(m.txns_5m_buys, m.txns_5m_sells)
        txns_1h = _sum_opt(m.txns_1h_buys, m.txns_1h_sells)
        if txns_5m is not None and txns_1h is not None and txns_1h > 0:
            baseline_5m = txns_1h / 12.0
            if baseline_5m > 0:
                txn_accel = txns_5m / baseline_5m
        else:
            unknowns.append("تعداد تراکنش‌ها (txns 5m/1h)")

        # ---- 2. Volume acceleration ----------------------------------------
        vol_accel: float | None = None
        if m.volume_5m is not None and m.volume_1h is not None and m.volume_1h > 0:
            baseline_5m = m.volume_1h / 12.0
            if baseline_5m > 0:
                vol_accel = m.volume_5m / baseline_5m
        else:
            unknowns.append("حجم معاملات (volume 5m/1h)")

        # ---- 3. Buy pressure -------------------------------------------------
        buy_pressure: float | None = None
        if m.txns_5m_buys is not None and m.txns_5m_sells is not None:
            if m.txns_5m_sells > 0:
                buy_pressure = m.txns_5m_buys / m.txns_5m_sells
            elif m.txns_5m_buys > 0:
                buy_pressure = float(m.txns_5m_buys)   # all buys, no sells

        # ---- 4. Wash-trading divergence -------------------------------------
        wash = False
        if txn_accel is not None and vol_accel is not None and txn_accel > 0:
            divergence = vol_accel / txn_accel
            if divergence >= WASH_DIVERGENCE and vol_accel >= ACCEL_WARM:
                wash = True
                warnings.append(
                    f"واگرایی مشکوک: حجم {vol_accel:.1f}× شتاب گرفته ولی تعداد تراکنش فقط "
                    f"{txn_accel:.1f}× — احتمال معاملات صوری (wash trading)"
                )

        # ---- 5. Paid promotion ----------------------------------------------
        paid = bool(boost_amount and boost_amount > 0)
        if paid:
            warnings.append(
                f"این توکن تبلیغ پولی (DEX boost = {boost_amount}) خریده است — "
                "توجه خریداری شده، نه کسب‌شده"
            )

        # ---- 6. Sample-size gate --------------------------------------------
        if txns_5m is not None and txns_5m < MIN_TXNS_FOR_SIGNAL:
            return ViralitySignal(
                subject=symbol, label="UNKNOWN", score=0.0,
                txn_acceleration=txn_accel, volume_acceleration=vol_accel,
                buy_pressure=buy_pressure, wash_suspected=wash, is_paid_promotion=paid,
                reasons=[], warnings=warnings,
                unknowns=unknowns + [f"نمونه بسیار کوچک ({txns_5m} تراکنش در ۵ دقیقه)"],
                computed_ts=ts,
            )

        if txn_accel is None and vol_accel is None:
            return ViralitySignal(
                subject=symbol, label="UNKNOWN", score=0.0,
                txn_acceleration=None, volume_acceleration=None,
                buy_pressure=buy_pressure, wash_suspected=False, is_paid_promotion=paid,
                reasons=[], warnings=warnings, unknowns=unknowns, computed_ts=ts,
            )

        # ---- 7. Compose the score -------------------------------------------
        score = 0.0
        accel = max(txn_accel or 0.0, 0.0)
        vaccel = max(vol_accel or 0.0, 0.0)
        effective = txn_accel if txn_accel is not None else vaccel

        if effective >= ACCEL_HOT:
            score += 45.0
            reasons.append(f"شتاب فعالیت {effective:.1f} برابر میانگین ساعت گذشته")
        elif effective >= ACCEL_WARM:
            score += 25.0
            reasons.append(f"فعالیت در حال افزایش ({effective:.1f}× میانگین)")
        elif effective < 0.5:
            reasons.append(f"فعالیت در حال سرد شدن ({effective:.1f}× میانگین)")

        if vol_accel is not None and vol_accel >= ACCEL_HOT and not wash:
            score += 25.0
            reasons.append(f"شتاب حجم معاملات {vol_accel:.1f} برابر")

        if buy_pressure is not None:
            if buy_pressure >= BUY_PRESSURE_STRONG:
                score += 20.0
                reasons.append(f"فشار خرید قوی (نسبت خرید/فروش = {buy_pressure:.2f})")
            elif buy_pressure <= BUY_PRESSURE_WEAK:
                score -= 10.0
                warnings.append(f"فشار فروش غالب (نسبت خرید/فروش = {buy_pressure:.2f})")

        # Penalties: manufactured attention is worth less than earned attention.
        if wash:
            score *= 0.4
        if paid:
            score *= 0.75

        score = max(0.0, min(100.0, score))

        if wash:
            label = "UNKNOWN"        # refuse to call manufactured volume "viral"
        elif score >= 60.0:
            label = "VIRAL"
        elif score >= 30.0:
            label = "BUILDING"
        elif effective < 0.5:
            label = "COOLING"
        else:
            label = "FLAT"

        return ViralitySignal(
            subject=symbol, label=label, score=round(score, 2),
            txn_acceleration=round(txn_accel, 3) if txn_accel is not None else None,
            volume_acceleration=round(vol_accel, 3) if vol_accel is not None else None,
            buy_pressure=round(buy_pressure, 3) if buy_pressure is not None else None,
            wash_suspected=wash, is_paid_promotion=paid,
            reasons=reasons, warnings=warnings, unknowns=unknowns, computed_ts=ts,
        )


def _sum_opt(a: int | None, b: int | None) -> int | None:
    """Sum two optionals; UNKNOWN if either is missing (never coerce None to 0)."""
    if a is None or b is None:
        return None
    return a + b
