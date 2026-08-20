#!/usr/bin/env python3
"""AHOS multi-factor candidate ranking (production pipeline).

Lane-A `discovery/ranker.py` stays frozen (rank-first, no numeric score).
This module ranks *already-scored* OpportunityScoreReports for the
production pipeline. Ranking is NOT "highest score wins".

Dimensions (all honest; UNKNOWN never coerced to a midpoint):

    opportunity · confidence · evidence quality · liquidity · security
    · exitability · novelty · regime · risk · uncertainty · virality

Anti-hype law
-------------
HIGH VIRALITY + HIGH SECURITY RISK  →  REJECT
LOW  VIRALITY + HIGH FUNDAMENTALS + HIGH EXITABILITY  →  INVESTIGATE

A viral / volume-spike / whale-buy token is never auto-selected.
Social evidence cannot create a SELECT disposition.

This module does not change opportunity_score. It only orders and labels.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Sequence

CONFIDENCE_RANK = {"HIGH": 2, "MED": 1, "LOW": 0}
RISK_RANK = {"LOW": 0, "MED": 1, "HIGH": 2, "CRITICAL": 3}
DISPOSITION_RANK = {"SELECT": 3, "INVESTIGATE": 2, "HOLD": 1, "REJECT": 0}

VIRAL_LABELS = {"VIRAL", "BUILDING"}
SECURITY_VETO_IDS = {
    "HONEYPOT", "HONEYPOT_DETECTED", "CRITICAL_SECURITY",
    "MINT_AUTHORITY", "FREEZE_AUTHORITY",
}


@dataclass
class RankedCandidate:
    token_address: str
    token_symbol: str
    token_chain: str
    rank: int
    disposition: str                 # SELECT | INVESTIGATE | HOLD | REJECT
    opportunity_score: float
    confidence_level: str
    risk_level: str
    evidence_quality: float | None   # known canonical / 4; None if unscored
    liquidity_usd: float | None
    novelty_hours: float | None
    virality_label: str | None
    exit_verdict: str | None
    unknown_count: int
    reasons: list[str] = field(default_factory=list)
    why_selected: list[str] = field(default_factory=list)
    why_not_selected: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    unknown_factors: list[str] = field(default_factory=list)
    dimensions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _report_value(report: Any, key: str) -> Any:
    """Read an intel-evidence atom or a score-report field. Missing → None."""
    for item in getattr(report, "intel_evidence_items", None) or []:
        if isinstance(item, dict) and item.get("key") == key:
            if item.get("status") == "UNKNOWN":
                return None
            return item.get("value")
    for item in getattr(report, "evidence_items", None) or []:
        k = getattr(item, "key", None) if not isinstance(item, dict) else item.get("key")
        if k == key:
            status = getattr(item, "status", None) if not isinstance(item, dict) else item.get("status")
            value = getattr(item, "value", None) if not isinstance(item, dict) else item.get("value")
            if status == "UNKNOWN":
                return None
            return value
    return None


def _numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _canonical_known_count(report: Any) -> tuple[int, int]:
    """(known, total=4) over the frozen four-item evidence contract."""
    keys = ("liquidity_usd", "volume_1h", "is_honeypot", "top10_concentration")
    known = 0
    items = list(getattr(report, "evidence_items", None) or [])
    have: set[str] = set()
    for item in items:
        k = getattr(item, "key", None) if not isinstance(item, dict) else item.get("key")
        v = getattr(item, "value", None) if not isinstance(item, dict) else item.get("value")
        if k in keys and v is not None:
            have.add(k)
    known = len(have)
    # missing_unknowns is the legacy Persian-label list for the same 4 keys
    missing = list(getattr(report, "missing_unknowns", None) or [])
    if not items and missing:
        known = max(0, 4 - len(missing))
    return known, 4


def classify(report: Any) -> RankedCandidate:
    """Disposition + explainability for one scored report. Pure, deterministic."""
    score = float(getattr(report, "opportunity_score", 0.0) or 0.0)
    confidence = str(getattr(report, "confidence_level", "LOW") or "LOW")
    risk = str(getattr(report, "risk_level", "LOW") or "LOW")
    liq = _numeric(_report_value(report, "liquidity_usd"))
    if liq is None:
        # the frozen evidence_items contract uses the same key
        for item in getattr(report, "evidence_items", None) or []:
            k = getattr(item, "key", None) if not isinstance(item, dict) else item.get("key")
            if k == "liquidity_usd":
                liq = _numeric(getattr(item, "value", None) if not isinstance(item, dict) else item.get("value"))
                break
    honeypot = _report_value(report, "is_honeypot")
    virality = _report_value(report, "virality_label")
    wash = _report_value(report, "wash_suspected")
    paid = _report_value(report, "is_paid_promotion")
    exit_verdict = _report_value(report, "exit_verdict")
    pair_created = _numeric(_report_value(report, "pair_created_ts"))
    retrieved = getattr(report, "computed_at_ts", None)
    novelty_hours: float | None = None
    if pair_created is not None and retrieved is not None:
        novelty_hours = max(0.0, (float(retrieved) - pair_created) / 3600.0)

    known, total = _canonical_known_count(report)
    evidence_quality = round(known / total, 3) if total else None
    unknowns = list(getattr(report, "missing_unknowns", None) or [])
    unknown_count = len(unknowns)

    findings = list(getattr(report, "risk_deductions", None) or [])
    finding_ids = {
        (getattr(f, "risk_id", None) if not isinstance(f, dict) else f.get("risk_id"))
        for f in findings
    }
    finding_ids.discard(None)
    risk_factors = [
        (getattr(f, "description", None) if not isinstance(f, dict) else f.get("description"))
        or (getattr(f, "risk_id", None) if not isinstance(f, dict) else f.get("risk_id"))
        for f in findings
    ]

    reasons: list[str] = []
    why_sel: list[str] = []
    why_not: list[str] = []
    unknown_factors = list(unknowns)

    security_veto = bool(honeypot is True) or bool(finding_ids & SECURITY_VETO_IDS) \
        or risk == "CRITICAL"
    viral = isinstance(virality, str) and virality.upper() in VIRAL_LABELS
    high_security_risk = risk in ("HIGH", "CRITICAL") or honeypot is True or wash is True

    disposition = "HOLD"
    if security_veto:
        disposition = "REJECT"
        why_not.append("security veto / CRITICAL risk — not selectable")
        reasons.append("SECURITY_VETO")
    elif viral and high_security_risk:
        disposition = "REJECT"
        why_not.append("HIGH VIRALITY BUT HIGH SECURITY RISK → REJECT")
        reasons.append("ANTI_HYPE_REJECT")
    elif viral and (wash is True or paid is True):
        disposition = "REJECT"
        why_not.append("viral attention is manufactured (wash/paid) → REJECT")
        reasons.append("MANUFACTURED_HYPE_REJECT")
    elif viral and honeypot is None:
        # virality without a security reading is not an opportunity
        disposition = "HOLD"
        why_not.append("HIGH VIRALITY with UNKNOWN security — not auto-selected")
        unknown_factors.append("is_honeypot")
        reasons.append("HYPE_WITHOUT_SECURITY")
    else:
        fundamentals = (
            liq is not None and liq >= 10000
            and score >= 50.0
            and confidence in ("HIGH", "MED")
            and risk in ("LOW", "MED")
        )
        exit_ok = exit_verdict in ("EXITABLE", "PARTIAL", None)  # None = UNKNOWN, not a bonus
        low_virality = (virality is None) or (str(virality).upper() in ("FLAT", "COOLING", "UNKNOWN"))
        if fundamentals and low_virality and honeypot is False and risk == "LOW":
            if exit_verdict in ("UNEXITABLE", "TRAPPED"):
                disposition = "REJECT"
                why_not.append("fundamentals present but exitability failed")
                reasons.append("UNEXITABLE")
            elif exit_verdict in ("EXITABLE",) or (exit_verdict is None and liq is not None and liq >= 50000):
                disposition = "SELECT"
                why_sel.append("fundamentals + security clear; virality not required")
                if low_virality and virality is not None:
                    why_sel.append("LOW VIRALITY + HIGH FUNDAMENTALS + EXITABILITY → INVESTIGATE/SELECT")
                reasons.append("FUNDAMENTALS")
            else:
                disposition = "INVESTIGATE"
                why_sel.append("LOW VIRALITY + HIGH FUNDAMENTALS → INVESTIGATE")
                if exit_verdict is None:
                    unknown_factors.append("exit_verdict")
                reasons.append("INVESTIGATE_FUNDAMENTALS")
        elif score >= 70.0 and confidence == "HIGH" and risk == "LOW" and honeypot is False:
            disposition = "SELECT"
            why_sel.append("high score, high confidence, low risk, honeypot clear")
            reasons.append("HIGH_QUALITY")
        elif score <= 0.0 or risk in ("HIGH", "CRITICAL"):
            disposition = "HOLD" if not security_veto else "REJECT"
            why_not.append("score/risk do not support selection")
            reasons.append("WEAK")
        else:
            disposition = "HOLD"
            why_not.append("insufficient combined evidence for SELECT")
            reasons.append("INSUFFICIENT_COMBINED_EVIDENCE")

    if honeypot is None:
        unknown_factors.append("is_honeypot")
    if virality is None:
        unknown_factors.append("virality_label")
    if liq is None:
        unknown_factors.append("liquidity_usd")

    # de-dupe unknown factors while preserving order
    seen: set[str] = set()
    unknown_factors = [u for u in unknown_factors if not (u in seen or seen.add(u))]  # type: ignore[func-returns-value]

    return RankedCandidate(
        token_address=str(getattr(report, "token_address", "") or ""),
        token_symbol=str(getattr(report, "token_symbol", "") or ""),
        token_chain=str(getattr(report, "token_chain", "") or ""),
        rank=0,
        disposition=disposition,
        opportunity_score=score,
        confidence_level=confidence,
        risk_level=risk,
        evidence_quality=evidence_quality,
        liquidity_usd=liq,
        novelty_hours=novelty_hours,
        virality_label=str(virality) if virality is not None else None,
        exit_verdict=str(exit_verdict) if exit_verdict is not None else None,
        unknown_count=unknown_count,
        reasons=reasons,
        why_selected=why_sel,
        why_not_selected=why_not,
        risk_factors=[r for r in risk_factors if r],
        unknown_factors=unknown_factors,
        dimensions={
            "opportunity_score": score,
            "confidence": confidence,
            "evidence_quality": evidence_quality,
            "liquidity_usd": liq,
            "security_risk": risk,
            "exitability": exit_verdict,
            "novelty_hours": novelty_hours,
            "virality": virality,
            "uncertainty": unknown_count,
            "wash_suspected": wash,
            "is_paid_promotion": paid,
            "honeypot": honeypot,
        },
    )


def _sort_key(row: RankedCandidate) -> tuple:
    """Deterministic lexicographic key. Missing numerics sort last, never as 0."""
    disp = DISPOSITION_RANK.get(row.disposition, 0)
    conf = CONFIDENCE_RANK.get(row.confidence_level, 0)
    risk = RISK_RANK.get(row.risk_level, 0)
    eq = row.evidence_quality if row.evidence_quality is not None else -1.0
    liq = row.liquidity_usd if row.liquidity_usd is not None else -1.0
    # novelty: unknown last; very new is not a bonus (sniper window is risk)
    return (
        -disp,
        -row.opportunity_score,
        -conf,
        -eq,
        -liq,
        risk,                          # lower risk first
        row.unknown_count,             # fewer unknowns first
        row.token_address,
    )


def rank_reports(reports: Sequence[Any]) -> list[RankedCandidate]:
    """Order scored reports by the multi-factor key. Empty in → empty out."""
    rows = [classify(r) for r in reports]
    rows.sort(key=_sort_key)
    for i, row in enumerate(rows, start=1):
        row.rank = i
    return rows


def rank_paired(paired: Iterable[tuple[Any, Any]]) -> list[tuple[Any, Any, RankedCandidate]]:
    """Preserve (candidate, report) pairing while ranking.

    Returns list of (candidate, report, rank_row) in rank order.
    """
    items = list(paired)
    decorated = [(classify(rep), cand, rep) for cand, rep in items]
    decorated.sort(key=lambda t: _sort_key(t[0]))
    out: list[tuple[Any, Any, RankedCandidate]] = []
    for i, (row, cand, rep) in enumerate(decorated, start=1):
        row.rank = i
        out.append((cand, rep, row))
    return out
