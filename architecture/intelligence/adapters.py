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


def evidence_from_virality(signal: Any) -> list[Evidence]:
    if signal is None:
        return []
    ts = float(getattr(signal, "computed_ts", 0.0) or 0.0)
    status = "DERIVED" if getattr(signal, "is_known", False) else "UNKNOWN"
    return [
        _ev("virality_label", "Virality label", getattr(signal, "label", None),
            provider="intel.viral", timestamp=ts, source_field="virality.label", status=status),
        _ev("virality_score", "Virality score", getattr(signal, "score", None),
            provider="intel.viral", timestamp=ts, source_field="virality.score", status=status),
        _ev("wash_suspected", "Wash-trading suspected", getattr(signal, "wash_suspected", None),
            provider="intel.viral", timestamp=ts, source_field="virality.wash_suspected",
            status="DERIVED"),
        _ev("is_paid_promotion", "Paid DEX promotion", getattr(signal, "is_paid_promotion", None),
            provider="intel.viral", timestamp=ts, source_field="virality.is_paid_promotion",
            status="DERIVED"),
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


def collect_intel_evidence(*, narrative: Any = None, virality: Any = None,
                           whales: Any = None, exitability: Any = None) -> list[Evidence]:
    """Bundle optional Lane-A intel signals as extra Evidence."""
    items: list[Evidence] = []
    for group in (
        evidence_from_narrative(narrative),
        evidence_from_virality(virality),
        evidence_from_whales(whales),
        evidence_from_exitability(exitability),
    ):
        items.extend(group)
    return items


def as_evidence_sequence(items: Iterable[Any]) -> list[Evidence]:
    return [i for i in items if isinstance(i, Evidence)]
