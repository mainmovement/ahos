#!/usr/bin/env python3
"""AHOS Market Structure Analyzer (Lane B intel — P1-1).

Derives auditable microstructure features from *observed* market metrics only.
Never fabricates depth books, order-flow, or pool fragmentation that was not
supplied by a provider.

Signals (when evidence exists):
  - liquidity_quality        thin / adequate / deep
  - vol_liq_ratio            volume_1h / liquidity (abnormal volume flag)
  - buy_sell_imbalance       (buys-sells)/(buys+sells) over 1h
  - short_horizon_pressure   5m vs 1h buy pressure divergence
  - activity_quality         txn count vs volume consistency

Missing inputs → UNKNOWN atoms. Structure findings never override security veto.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

MARKET_STRUCTURE_VERSION = "AHOS-MSTRUCT-v1"

THIN_LIQ = 5_000.0
ADEQUATE_LIQ = 25_000.0
DEEP_LIQ = 100_000.0
ABNORMAL_VOL_LIQ = 5.0          # 1h volume >> liquidity → exitability concern
MIN_TXNS = 10


@dataclass
class MarketStructureSignal:
    subject: str
    label: str                              # HEALTHY | FRAGILE | ABNORMAL | UNKNOWN
    liquidity_quality: str | None           # THIN | ADEQUATE | DEEP | None
    vol_liq_ratio: float | None
    buy_sell_imbalance: float | None        # [-1, +1]
    short_horizon_imbalance: float | None
    activity_quality: str | None            # CONSISTENT | DIVERGENT | SPARSE | None
    reasons: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    computed_ts: float = field(default_factory=time.time)
    version: str = MARKET_STRUCTURE_VERSION

    @property
    def is_known(self) -> bool:
        return self.label != "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "label": self.label,
            "liquidity_quality": self.liquidity_quality,
            "vol_liq_ratio": self.vol_liq_ratio,
            "buy_sell_imbalance": self.buy_sell_imbalance,
            "short_horizon_imbalance": self.short_horizon_imbalance,
            "activity_quality": self.activity_quality,
            "reasons": self.reasons,
            "unknowns": self.unknowns,
            "computed_ts": self.computed_ts,
            "version": self.version,
        }


def _imbalance(buys: float | None, sells: float | None) -> float | None:
    if buys is None or sells is None:
        return None
    total = buys + sells
    if total <= 0:
        return None
    return (buys - sells) / total


class MarketStructureAnalyzer:
    """Deterministic microstructure view from NormalizedTokenCandidate metrics."""

    def analyze(self, candidate: Any, *, now: float | None = None) -> MarketStructureSignal:
        ts = time.time() if now is None else now
        symbol = str(getattr(candidate, "symbol", "") or "UNKNOWN")
        metrics = getattr(candidate, "metrics", None)
        unknowns: list[str] = []
        reasons: list[str] = []

        liq = getattr(metrics, "liquidity_usd", None) if metrics else None
        vol_1h = getattr(metrics, "volume_1h", None) if metrics else None
        vol_5m = getattr(metrics, "volume_5m", None) if metrics else None
        b1 = getattr(metrics, "txns_1h_buys", None) if metrics else None
        s1 = getattr(metrics, "txns_1h_sells", None) if metrics else None
        b5 = getattr(metrics, "txns_5m_buys", None) if metrics else None
        s5 = getattr(metrics, "txns_5m_sells", None) if metrics else None

        if liq is None:
            unknowns.append("liquidity_usd")
        if vol_1h is None:
            unknowns.append("volume_1h")
        if b1 is None or s1 is None:
            unknowns.append("txns_1h")

        liq_q = None
        if liq is not None:
            if liq < THIN_LIQ:
                liq_q = "THIN"
                reasons.append(f"thin liquidity ${liq:,.0f}")
            elif liq < ADEQUATE_LIQ:
                liq_q = "ADEQUATE"
            elif liq >= DEEP_LIQ:
                liq_q = "DEEP"
                reasons.append(f"deep liquidity ${liq:,.0f}")
            else:
                liq_q = "ADEQUATE"

        vlr = None
        if liq is not None and liq > 0 and vol_1h is not None:
            vlr = vol_1h / liq
            if vlr >= ABNORMAL_VOL_LIQ:
                reasons.append(f"abnormal vol/liq ratio {vlr:.2f}")

        imb_1h = _imbalance(
            float(b1) if b1 is not None else None,
            float(s1) if s1 is not None else None,
        )
        imb_5m = _imbalance(
            float(b5) if b5 is not None else None,
            float(s5) if s5 is not None else None,
        )

        activity = None
        txn_total = None
        if b1 is not None and s1 is not None:
            txn_total = float(b1) + float(s1)
            if txn_total < MIN_TXNS:
                activity = "SPARSE"
                unknowns.append("sparse_txns")
            elif vol_1h is not None and vol_1h > 0 and txn_total > 0:
                # crude consistency: very high volume with tiny txns → divergent
                per_txn = vol_1h / txn_total
                if per_txn > 50_000:
                    activity = "DIVERGENT"
                    reasons.append("volume dwarfs txn count (possible wash/outlier)")
                else:
                    activity = "CONSISTENT"
            else:
                activity = "SPARSE" if txn_total < MIN_TXNS else "CONSISTENT"

        # Label synthesis — UNKNOWN only when we lack core liquidity+flow evidence.
        if liq is None and imb_1h is None and vlr is None:
            label = "UNKNOWN"
        elif (liq_q == "THIN") or (vlr is not None and vlr >= ABNORMAL_VOL_LIQ) or activity == "DIVERGENT":
            label = "ABNORMAL" if (vlr is not None and vlr >= ABNORMAL_VOL_LIQ) or activity == "DIVERGENT" else "FRAGILE"
        elif liq_q in ("ADEQUATE", "DEEP") and activity in (None, "CONSISTENT", "SPARSE"):
            label = "HEALTHY" if liq_q == "DEEP" or (imb_1h is not None and imb_1h >= -0.2) else "FRAGILE"
        else:
            label = "FRAGILE"

        return MarketStructureSignal(
            subject=symbol,
            label=label,
            liquidity_quality=liq_q,
            vol_liq_ratio=round(vlr, 4) if vlr is not None else None,
            buy_sell_imbalance=round(imb_1h, 4) if imb_1h is not None else None,
            short_horizon_imbalance=round(imb_5m, 4) if imb_5m is not None else None,
            activity_quality=activity,
            reasons=reasons,
            unknowns=unknowns,
            computed_ts=ts,
        )
