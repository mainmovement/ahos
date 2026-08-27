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


def evidence_from_market_structure(signal: Any) -> list[Evidence]:
    """MarketStructureSignal → Evidence. Missing metrics stay UNKNOWN."""
    if signal is None:
        return []
    ts = float(getattr(signal, "computed_ts", 0.0) or 0.0)
    status = "DERIVED" if getattr(signal, "is_known", False) else "UNKNOWN"
    return [
        _ev("mstruct_label", "Market structure label",
            getattr(signal, "label", "UNKNOWN"),
            provider="intel.market_structure", timestamp=ts,
            source_field="market_structure.label", status=status),
        _ev("mstruct_liquidity_quality", "Liquidity quality band",
            getattr(signal, "liquidity_quality", None),
            provider="intel.market_structure", timestamp=ts,
            source_field="market_structure.liquidity_quality",
            status="DERIVED" if getattr(signal, "liquidity_quality", None) else "UNKNOWN"),
        _ev("mstruct_vol_liq_ratio", "Volume/liquidity ratio (1h)",
            getattr(signal, "vol_liq_ratio", None),
            provider="intel.market_structure", timestamp=ts,
            source_field="market_structure.vol_liq_ratio",
            status="DERIVED" if getattr(signal, "vol_liq_ratio", None) is not None else "UNKNOWN"),
        _ev("mstruct_buy_sell_imbalance", "Buy/sell imbalance [-1,1]",
            getattr(signal, "buy_sell_imbalance", None),
            provider="intel.market_structure", timestamp=ts,
            source_field="market_structure.buy_sell_imbalance",
            status="DERIVED" if getattr(signal, "buy_sell_imbalance", None) is not None else "UNKNOWN"),
        _ev("mstruct_activity_quality", "Activity quality",
            getattr(signal, "activity_quality", None),
            provider="intel.market_structure", timestamp=ts,
            source_field="market_structure.activity_quality",
            status="DERIVED" if getattr(signal, "activity_quality", None) else "UNKNOWN"),
    ]


def evidence_from_tokenomics(signal: Any) -> list[Evidence]:
    if signal is None:
        return []
    ts = float(getattr(signal, "computed_ts", 0.0) or 0.0)
    status = "DERIVED" if getattr(signal, "is_known", False) else "UNKNOWN"
    items = [
        _ev("tokenomics_label", "Tokenomics label",
            getattr(signal, "label", "UNKNOWN"),
            provider="intel.tokenomics", timestamp=ts,
            source_field="tokenomics.label", status=status),
        _ev("tokenomics_circ_to_fdv", "Circulating/FDV ratio",
            getattr(signal, "circ_to_fdv_ratio", None),
            provider="intel.tokenomics", timestamp=ts,
            source_field="tokenomics.circ_to_fdv_ratio",
            status="DERIVED" if getattr(signal, "circ_to_fdv_ratio", None) is not None else "UNKNOWN"),
        _ev("tokenomics_mint_authority", "Mint authority active",
            getattr(signal, "has_mint_authority", None),
            provider="intel.tokenomics", timestamp=ts,
            source_field="tokenomics.has_mint_authority",
            status="DERIVED" if getattr(signal, "has_mint_authority", None) is not None else "UNKNOWN"),
        _ev("tokenomics_freeze_authority", "Freeze authority active",
            getattr(signal, "has_freeze_authority", None),
            provider="intel.tokenomics", timestamp=ts,
            source_field="tokenomics.has_freeze_authority",
            status="DERIVED" if getattr(signal, "has_freeze_authority", None) is not None else "UNKNOWN"),
        _ev("tokenomics_unlock_vesting", "Unlock/vesting schedule status",
            getattr(signal, "unlock_vesting_status", "UNKNOWN"),
            provider="intel.tokenomics", timestamp=ts,
            source_field="tokenomics.unlock_vesting_status",
            status="UNKNOWN"),  # never fabricated as known
    ]
    return items


def evidence_from_catalysts(report: Any) -> list[Evidence]:
    if report is None:
        return []
    ts = float(getattr(report, "computed_ts", 0.0) or 0.0)
    status_raw = getattr(report, "status", "UNKNOWN")
    atom_status = "DERIVED" if status_raw in ("FOUND", "NONE") else "UNKNOWN"
    items = [
        _ev("catalyst_status", "Catalyst catalog status",
            status_raw,
            provider="intel.catalyst", timestamp=ts,
            source_field="catalyst.status", status=atom_status),
        _ev("catalyst_count", "Catalyst event count",
            len(getattr(report, "events", None) or []),
            provider="intel.catalyst", timestamp=ts,
            source_field="catalyst.count",
            status=atom_status if status_raw != "UNKNOWN" else "UNKNOWN"),
    ]
    for i, ev in enumerate(getattr(report, "events", None) or []):
        if not isinstance(ev, dict):
            ev = ev.to_dict() if hasattr(ev, "to_dict") else {}
        items.append(_ev(
            f"catalyst_{i}_{ev.get('kind', 'EVENT')}",
            ev.get("title") or "catalyst",
            ev.get("evidence_sha16") or ev.get("kind"),
            provider=str(ev.get("source") or "intel.catalyst"),
            timestamp=float(ev["timestamp"]) if ev.get("timestamp") is not None else ts,
            source_field="catalyst.event",
            status="VERIFIED" if ev.get("evidence_sha16") else "DERIVED",
        ))
    return items


def collect_intel_evidence(*, narrative: Any = None, virality: Any = None,
                           whales: Any = None, exitability: Any = None,
                           market_structure: Any = None,
                           tokenomics: Any = None,
                           catalysts: Any = None,
                           boost_seen: bool | None = None,
                           txns_seen: bool | None = None) -> list[Evidence]:
    """Bundle optional Lane-B intel signals as extra Evidence.

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
        evidence_from_market_structure(market_structure),
        evidence_from_tokenomics(tokenomics),
        evidence_from_catalysts(catalysts),
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
