#!/usr/bin/env python3
"""Multi-factor ranking — not highest-score-wins; anti-hype is structural."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.scoring.ranker import classify, rank_reports  # noqa: E402


@dataclass
class _Ev:
    key: str
    value: Any
    status: str = "VERIFIED"


@dataclass
class _Risk:
    risk_id: str
    severity: str = "HIGH"
    description: str = ""
    penalty_points: float = 0.0
    evidence_ref: str = ""


@dataclass
class _Report:
    token_address: str
    token_symbol: str
    token_chain: str = "solana"
    opportunity_score: float = 0.0
    confidence_level: str = "LOW"
    risk_level: str = "LOW"
    evidence_items: list = field(default_factory=list)
    intel_evidence_items: list = field(default_factory=list)
    missing_unknowns: list = field(default_factory=list)
    risk_deductions: list = field(default_factory=list)
    computed_at_ts: float = 1_000.0


def _viral(label, wash=None, paid=None):
    items = [{"key": "virality_label", "value": label, "status": "DERIVED"}]
    if wash is not None:
        items.append({"key": "wash_suspected", "value": wash, "status": "DERIVED"})
    if paid is not None:
        items.append({"key": "is_paid_promotion", "value": paid, "status": "DERIVED"})
    return items


def test_high_virality_plus_high_security_risk_is_rejected():
    r = _Report(
        token_address="hype", token_symbol="HYPE",
        opportunity_score=95.0, confidence_level="HIGH", risk_level="HIGH",
        evidence_items=[_Ev("is_honeypot", False), _Ev("liquidity_usd", 80_000.0)],
        intel_evidence_items=_viral("VIRAL"),
    )
    row = classify(r)
    assert row.disposition == "REJECT"
    assert any("HIGH VIRALITY" in x and "REJECT" in x for x in row.why_not_selected)


def test_viral_unknown_security_is_not_auto_selected():
    r = _Report(
        token_address="unk", token_symbol="UNK",
        opportunity_score=88.0, confidence_level="MED", risk_level="MED",
        evidence_items=[_Ev("liquidity_usd", 40_000.0)],
        intel_evidence_items=_viral("VIRAL"),
        missing_unknowns=["honeypot"],
    )
    row = classify(r)
    assert row.disposition != "SELECT"
    assert "is_honeypot" in row.unknown_factors


def test_low_virality_high_fundamentals_investigates_or_selects():
    r = _Report(
        token_address="fund", token_symbol="FUND",
        opportunity_score=72.0, confidence_level="HIGH", risk_level="LOW",
        evidence_items=[
            _Ev("liquidity_usd", 80_000.0),
            _Ev("volume_1h", 40_000.0),
            _Ev("is_honeypot", False),
            _Ev("top10_concentration", 20.0),
        ],
        intel_evidence_items=_viral("FLAT") + [
            {"key": "exit_verdict", "value": "EXITABLE", "status": "DERIVED"},
        ],
    )
    row = classify(r)
    assert row.disposition in ("SELECT", "INVESTIGATE")
    assert row.why_selected


def test_highest_score_does_not_beat_security_veto():
    safe = _Report(
        token_address="safe", token_symbol="SAFE",
        opportunity_score=55.0, confidence_level="HIGH", risk_level="LOW",
        evidence_items=[
            _Ev("liquidity_usd", 60_000.0),
            _Ev("is_honeypot", False),
            _Ev("volume_1h", 20_000.0),
            _Ev("top10_concentration", 15.0),
        ],
    )
    hype = _Report(
        token_address="hype", token_symbol="HYPE",
        opportunity_score=99.0, confidence_level="HIGH", risk_level="CRITICAL",
        evidence_items=[_Ev("is_honeypot", True), _Ev("liquidity_usd", 90_000.0)],
        intel_evidence_items=_viral("VIRAL", wash=True),
    )
    ranked = rank_reports([hype, safe])
    assert ranked[0].token_symbol == "SAFE"
    assert ranked[-1].disposition == "REJECT"
    assert ranked[-1].token_symbol == "HYPE"


def test_unknown_liquidity_is_not_sorted_as_zero():
    known = _Report(
        token_address="k", token_symbol="K",
        opportunity_score=40.0, confidence_level="MED", risk_level="LOW",
        evidence_items=[_Ev("liquidity_usd", 5_000.0), _Ev("is_honeypot", False)],
    )
    unknown = _Report(
        token_address="u", token_symbol="U",
        opportunity_score=40.0, confidence_level="MED", risk_level="LOW",
        evidence_items=[_Ev("is_honeypot", False)],
        missing_unknowns=["نقدینگی"],
    )
    ranked = rank_reports([unknown, known])
    assert ranked[0].token_symbol == "K"
    assert ranked[1].liquidity_usd is None


def test_ranking_is_deterministic():
    a = _Report(token_address="a", token_symbol="A", opportunity_score=10.0)
    b = _Report(token_address="b", token_symbol="B", opportunity_score=10.0)
    r1 = [row.token_address for row in rank_reports([b, a])]
    r2 = [row.token_address for row in rank_reports([a, b])]
    assert r1 == r2


def test_manufactured_hype_rejected():
    r = _Report(
        token_address="wash", token_symbol="WASH",
        opportunity_score=80.0, confidence_level="MED", risk_level="MED",
        evidence_items=[_Ev("is_honeypot", False), _Ev("liquidity_usd", 20_000.0)],
        intel_evidence_items=_viral("VIRAL", wash=True),
    )
    assert classify(r).disposition == "REJECT"
