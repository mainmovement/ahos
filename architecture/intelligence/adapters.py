#!/usr/bin/env python3
"""Convert existing AHOS intel signals into Evidence objects.

These adapters are the integration seam between Lane-A intel
(`architecture/intel`) and the Phase 4 intelligence engine. They never pass
raw candidate metrics through — only already-computed, provenance-bearing
signal fields become Evidence.
"""
from __future__ import annotations

from typing import Any, Iterable

from .evidence import Evidence, _digest


def _ev(key: str, description: str, value: Any, *, provider: str,
        timestamp: float, source_field: str, status: str = "DERIVED") -> Evidence:
    known = value is not None and status != "UNKNOWN"
    return Evidence(
        key=key,
        description=description,
        value=value,
        provider=provider,
        timestamp=timestamp,
        freshness_seconds=0.0,
        status="VERIFIED" if known and status == "VERIFIED" else (status if known else "UNKNOWN"),
        source_field=source_field,
        sha256=_digest(key, value, provider, timestamp),
    )


def evidence_from_narrative(signal: Any) -> list[Evidence]:
    """NarrativeSignal → Evidence. Narrative is never proof."""
    if signal is None:
        return []
    ts = float(getattr(signal, "computed_ts", 0.0) or 0.0)
    label = getattr(signal, "label", "UNKNOWN")
    status = "DERIVED" if getattr(signal, "is_known", False) else "UNKNOWN"
    items = [
        _ev("narrative_label", "Narrative label", label,
            provider="intel.news", timestamp=ts, source_field="narrative.label", status=status),
        _ev("narrative_sentiment", "Narrative sentiment [-1,1]",
            getattr(signal, "sentiment", None),
            provider="intel.news", timestamp=ts, source_field="narrative.sentiment", status=status),
        _ev("narrative_mentions", "Narrative mention count",
            getattr(signal, "mention_count", None),
            provider="intel.news", timestamp=ts, source_field="narrative.mention_count", status=status),
    ]
    for i, ev in enumerate(getattr(signal, "evidence", None) or []):
        if isinstance(ev, dict) and ev.get("sha256"):
            items.append(_ev(
                f"narrative_cite_{i}",
                ev.get("title") or "narrative citation",
                ev.get("sha256"),
                provider=str(ev.get("source") or "intel.news"),
                timestamp=ts,
                source_field="narrative.evidence",
                status="VERIFIED",
            ))
    return items


def evidence_from_virality(signal: Any, *,
                           boost_seen: bool | None = None,
                           txns_seen: bool | None = None) -> list[Evidence]:
    """Convert a ViralitySignal into evidence atoms with honest statuses.

    The raw signal uses False-on-missing for `wash_suspected` and
    `is_paid_promotion`; emitting that False as a known fact would fabricate
    a negative ("no promotion" / "no wash") out of absent data. Callers must
    pass `boost_seen` / `txns_seen` so the atoms are DERIVED only when the
    underlying data was actually observed; otherwise the atom carries None
    with status UNKNOWN. `None` (unspecified) is treated as not observed —
    the conservative, never-fabricating default.
    """
    if signal is None:
        return []
    ts = float(getattr(signal, "computed_ts", 0.0) or 0.0)
    status = "DERIVED" if getattr(signal, "is_known", False) else "UNKNOWN"
    wash_value = getattr(signal, "wash_suspected", None) if txns_seen else None
    paid_value = getattr(signal, "is_paid_promotion", None) if boost_seen else None
    return [
        _ev("virality_label", "Virality label", getattr(signal, "label", None),
            provider="intel.viral", timestamp=ts, source_field="virality.label", status=status),
        _ev("virality_score", "Virality score", getattr(signal, "score", None),
            provider="intel.viral", timestamp=ts, source_field="virality.score", status=status),
        _ev("wash_suspected", "Wash-trading suspected", wash_value,
            provider="intel.viral", timestamp=ts, source_field="virality.wash_suspected",
            status="DERIVED" if txns_seen else "UNKNOWN"),
        _ev("is_paid_promotion", "Paid DEX promotion", paid_value,
            provider="intel.viral", timestamp=ts, source_field="virality.is_paid_promotion",
            status="DERIVED" if boost_seen else "UNKNOWN"),
    ]


def evidence_from_whales(signal: Any) -> list[Evidence]:
    if signal is None:
        return []
    ts = float(getattr(signal, "computed_ts", 0.0) or 0.0)
    status = "DERIVED" if getattr(signal, "is_known", False) else "UNKNOWN"
    return [
        _ev("whale_top10_share", "Whale top-10 share",
            getattr(signal, "top10_share_pct", None),
            provider="intel.whales", timestamp=ts, source_field="whales.top10_share_pct",
            status=status),
        _ev("whale_risk_penalty", "Whale risk penalty",
            getattr(signal, "risk_penalty", None),
            provider="intel.whales", timestamp=ts, source_field="whales.risk_penalty",
            status=status),
        _ev("whale_label", "Lane-A whale label",
            getattr(signal, "label", None),
            provider="intel.whales", timestamp=ts, source_field="whales.label",
            status=status),
        _ev("top1_concentration", "Lane-A top-1 share",
            getattr(signal, "top1_share_pct", None),
            provider="intel.whales", timestamp=ts, source_field="whales.top1_share_pct",
            status=status),
        _ev("previous_top10_concentration", "Lane-A prior top-10 share",
            _previous_top10(signal),
            provider="intel.whales", timestamp=ts, source_field="whales.previous_top10",
            status=status),
    ]


def evidence_from_exitability(report: Any) -> list[Evidence]:
    if report is None:
        return []
    ts = float(getattr(report, "computed_ts", 0.0) or 0.0)
    return [
        _ev("exit_verdict", "Exitability verdict", getattr(report, "verdict", None),
            provider="intel.exitability", timestamp=ts, source_field="exitability.verdict",
            status="DERIVED"),
        _ev("realizable_fraction", "Realizable exit fraction",
            getattr(report, "realizable_fraction", None),
            provider="intel.exitability", timestamp=ts, source_field="exitability.realizable_fraction",
            status="DERIVED" if getattr(report, "realizable_fraction", None) is not None else "UNKNOWN"),
    ]


def evidence_from_social(report: Any) -> list[Evidence]:
    """SocialIntelligenceReport → Evidence. Social is never a buy signal."""
    if report is None:
        return []
    ts = float(getattr(report, "computed_ts", 0.0) or 0.0)
    velocity = getattr(report, "mention_velocity_1h", None)
    propagation = getattr(report, "cross_source_propagation", None)
    wash = getattr(report, "bot_wash", None) or {}
    recycled = wash.get("recycled_content") if isinstance(wash, dict) else None
    paid = wash.get("paid_promo_markers") if isinstance(wash, dict) else None
    return [
        _ev("social_mention_velocity_1h", "Social mention velocity (1h)",
            velocity, provider="intel.social", timestamp=ts,
            source_field="social.mention_velocity_1h",
            status="DERIVED" if velocity is not None else "UNKNOWN"),
        _ev("social_cross_source_propagation", "Distinct social sources with a match",
            propagation, provider="intel.social", timestamp=ts,
            source_field="social.cross_source_propagation",
            status="DERIVED" if propagation is not None else "UNKNOWN"),
        _ev("social_recycled_content", "Recycled-content heuristic",
            recycled, provider="intel.social", timestamp=ts,
            source_field="social.bot_wash.recycled_content",
            status="DERIVED" if recycled is not None else "UNKNOWN"),
        _ev("social_paid_promo_markers", "Paid-promo phrase-bank hit",
            paid, provider="intel.social", timestamp=ts,
            source_field="social.bot_wash.paid_promo_markers",
            status="DERIVED" if paid is not None else "UNKNOWN"),
        _ev("social_decision_floor", "Social cannot create an opportunity",
            getattr(report, "decision_floor", "SOCIAL_IS_EVIDENCE_NOT_PROOF"),
            provider="intel.social", timestamp=ts,
            source_field="social.decision_floor", status="VERIFIED"),
    ]


def collect_intel_evidence(*, narrative: Any = None, virality: Any = None,
                           whales: Any = None, exitability: Any = None,
                           social: Any = None,
                           boost_seen: bool | None = None,
                           txns_seen: bool | None = None) -> list[Evidence]:
    """Bundle optional Lane-A intel signals as extra Evidence.

    `boost_seen`/`txns_seen` are forwarded to `evidence_from_virality` so the
    wash/paid-promotion atoms are DERIVED only when the underlying data was
    observed; the conservative default (None) yields UNKNOWN, never a
    fabricated negative.
    """
    items: list[Evidence] = []
    for group in (
        evidence_from_narrative(narrative),
        evidence_from_virality(virality, boost_seen=boost_seen, txns_seen=txns_seen),
        evidence_from_whales(whales),
        evidence_from_exitability(exitability),
        evidence_from_social(social),
    ):
        items.extend(group)
    return items


def as_evidence_sequence(items: Iterable[Any]) -> list[Evidence]:
    return [i for i in items if isinstance(i, Evidence)]


def _previous_top10(signal: Any) -> float | None:
    top = getattr(signal, "top10_share_pct", None)
    delta = getattr(signal, "delta_pct_points", None)
    if top is None or delta is None:
        return None
    try:
        return float(top) - float(delta)
    except (TypeError, ValueError):
        return None
