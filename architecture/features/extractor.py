#!/usr/bin/env python3
"""AHOS Feature Extractor (Phase 4).

Consumes EvidenceBundle ONLY. Produces a FeatureVector whose point contributions
match the deterministic floor historically computed inside OpportunityScorer.

No raw candidate, dict-of-metrics, or database row is accepted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence.evidence import (
    EvidenceBundle,
    mapping_value,
    numeric_value,
    require_evidence_bundle,
    text_value,
)


@dataclass(frozen=True)
class Feature:
    key: str
    value: float | None
    points: float
    reason: str | None
    evidence_key: str
    status: str                                  # KNOWN | UNKNOWN


@dataclass
class FeatureVector:
    features: dict[str, Feature] = field(default_factory=dict)
    base_score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)

    def get(self, key: str) -> Feature | None:
        return self.features.get(key)


class FeatureExtractor:
    """DATA/EVIDENCE → FEATURES. Pure function of an EvidenceBundle."""

    CONSUMER = "FeatureExtractor.extract"

    def extract(self, evidence: EvidenceBundle) -> FeatureVector:
        require_evidence_bundle(evidence, self.CONSUMER)

        features: dict[str, Feature] = {}
        reasons: list[str] = []
        refs: list[str] = []
        base = 0.0

        liq = numeric_value(evidence.get("liquidity_usd"))
        if liq is not None:
            if liq >= 50000:
                pts, reason = 30.0, f"عمق نقدینگی بالا (${liq:,.0f} ≥ $50k)"
            elif liq >= 10000:
                pts, reason = 20.0, f"نقدینگی مناسب (${liq:,.0f} ≥ $10k)"
            elif liq >= 2000:
                pts, reason = 10.0, "نقدینگی اولیه حداقلی"
            else:
                pts, reason = 0.0, None
            features["liquidity"] = Feature(
                "liquidity", liq, pts, reason, "liquidity_usd", "KNOWN"
            )
            base += pts
            if reason:
                reasons.append(reason)
            refs.append("liquidity_usd")
        else:
            features["liquidity"] = Feature(
                "liquidity", None, 0.0, None, "liquidity_usd", "UNKNOWN"
            )

        vol = numeric_value(evidence.get("volume_1h"))
        if vol is not None and vol > 0:
            if vol >= 25000:
                pts, reason = 30.0, f"حجم معاملات قوی ۱ ساعته (${vol:,.0f})"
            elif vol >= 5000:
                pts, reason = 20.0, f"فعالیت حجمی فعال (${vol:,.0f})"
            elif vol >= 1000:
                pts, reason = 10.0, "حجم معاملات شروع شده"
            else:
                pts, reason = 0.0, None
            features["volume_1h"] = Feature(
                "volume_1h", vol, pts, reason, "volume_1h", "KNOWN"
            )
            base += pts
            if reason:
                reasons.append(reason)
            refs.append("volume_1h")
        else:
            features["volume_1h"] = Feature(
                "volume_1h", vol, 0.0, None, "volume_1h", "UNKNOWN"
            )

        buys = numeric_value(evidence.get("txns_1h_buys"))
        sells = numeric_value(evidence.get("txns_1h_sells"))
        if buys is not None and sells is not None:
            total_tx = buys + sells
            buy_ratio = (buys / total_tx) if total_tx > 0 else 0.0
            pts, reason = 0.0, None
            if total_tx > 20:
                if buy_ratio >= 0.65:
                    pts, reason = 20.0, f"برتری خریداران ({buy_ratio * 100:.0f}% معاملات خرید)"
                elif buy_ratio >= 0.50:
                    pts, reason = 10.0, "تعادل مناسب تراکنش‌ها"
            features["buy_pressure"] = Feature(
                "buy_pressure", buy_ratio, pts, reason, "txns_1h_buys", "KNOWN"
            )
            base += pts
            if reason:
                reasons.append(reason)
            refs.extend(["txns_1h_buys", "txns_1h_sells"])
        else:
            features["buy_pressure"] = Feature(
                "buy_pressure", None, 0.0, None, "txns_1h_buys", "UNKNOWN"
            )

        social = mapping_value(evidence.get("social_presence"))
        provider = text_value(evidence.get("source_provider")) or evidence.identity.source_provider
        multi = bool(social) or provider in ("dexscreener", "geckoterminal")
        if multi:
            pts, reason = 20.0, "تأیید ساختار جفت‌ارز در منابع معتبر"
            features["multi_source"] = Feature(
                "multi_source", 1.0, pts, reason, "source_provider", "KNOWN"
            )
            base += pts
            reasons.append(reason)
            refs.append("source_provider")
        else:
            features["multi_source"] = Feature(
                "multi_source", 0.0, 0.0, None, "source_provider", "KNOWN"
            )

        return FeatureVector(
            features=features,
            base_score=base,
            reasons=reasons,
            evidence_refs=refs,
        )
