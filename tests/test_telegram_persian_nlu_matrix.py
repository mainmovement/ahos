#!/usr/bin/env python3
"""Exhaustive Persian NLU Phrasing & Natural Language Matrix Tests (Phase XX)."""
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from telegram_ai import intent as I
from telegram_ai.response_contract import (
    format_opportunity_response, format_market_overview, FOOTER_MANDATED
)
from architecture.scoring.engine import OpportunityScoreReport, InvalidationCondition
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics

EVM_ADDR = "0x" + "11" * 20
SOL_ADDR = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


# ---------------- Exhaustive Phrasing Matrix for All 9 Canonical Queries ----------------
@pytest.mark.parametrize("text,expected_intent", [
    # 1. NEW_OPPORTUNITIES
    ("فرصت‌های جدید چی داریم؟", "NEW_OPPORTUNITIES"),
    ("فرصت های تازه رو نشون بده", "NEW_OPPORTUNITIES"),
    ("فرصت نو چی هست؟", "NEW_OPPORTUNITIES"),

    # 2. TOP_OPPORTUNITIES
    ("بهترین فرصت امروز چیه؟", "TOP_OPPORTUNITIES"),
    ("بهترین توکن های امروز", "TOP_OPPORTUNITIES"),
    ("بهترین فرصت ها رو بده", "TOP_OPPORTUNITIES"),

    # 3. WHY_SCORED
    ("این توکن چرا امتیاز گرفته؟", "WHY_SCORED"),
    ("چرا این اسکور بالا گرفته؟", "WHY_SCORED"),
    ("علت نمره این توکن چیه؟", "WHY_SCORED"),

    # 4. RISK_ANALYSIS
    ("ریسک این توکن چیست؟", "RISK_ANALYSIS"),
    ("این چقدر ریسک داره؟", "RISK_ANALYSIS"),
    ("ریسک این چیه؟", "RISK_ANALYSIS"),

    # 5. WHAT_IS_UNKNOWN
    ("چه چیزی نامعلوم است؟", "WHAT_IS_UNKNOWN"),
    ("چه فیلدهایی نامشخص است؟", "WHAT_IS_UNKNOWN"),
    ("چی ناشناخته است در این توکن؟", "WHAT_IS_UNKNOWN"),

    # 6. POSITION_STATUS
    ("وضعیت این پوزیشن چیست؟", "POSITION_STATUS"),
    ("شرایط پوزیشن من چطوره؟", "POSITION_STATUS"),
    ("وضعیت معامله من", "POSITION_STATUS"),

    # 7. WHY_ALERTED
    ("چرا هشدار صادر شد؟", "WHY_ALERTED"),
    ("علت این آلرت چی بود؟", "WHY_ALERTED"),
    ("چرا اخطار دادی؟", "WHY_ALERTED"),

    # 8. INVALIDATION_CONDITIONS
    ("چه چیزی این فرصت را invalid می‌کند؟", "INVALIDATION_CONDITIONS"),
    ("شرایط ابطال این فرصت چیست؟", "INVALIDATION_CONDITIONS"),
    ("چه شرطی این را باطل میکند؟", "INVALIDATION_CONDITIONS"),

    # 9. MARKET_OVERVIEW
    ("آخرین وضعیت بازار چیست؟", "MARKET_OVERVIEW"),
    ("وضعیت کلی بازار چطوره؟", "MARKET_OVERVIEW"),
    ("خلاصه مارکت رو بگو", "MARKET_OVERVIEW"),
])
def test_persian_nlu_canonical_queries(text, expected_intent):
    res = I.parse(text)
    assert res.intent == expected_intent
    assert res.confidence == "HIGH"


# ---------------- Persian Digits & Currency Normalization ----------------
@pytest.mark.parametrize("text,expected_val,expected_cur", [
    ("من ۵ میلیون تومان خریدم", 5_000_000, "IRT"),
    ("من ۵ میلیون تومن خریدم", 5_000_000, "IRT"),
    ("خرید ۵۰ میلیون ریال", 5_000_000, "IRT"),     # ریال -> تومان conversion
    ("من ۲.۵ اتریوم خریدم", 2.5, "ETH"),
    ("من ۱۰ سولانا خریدم", 10.0, "SOL"),
    ("من ۱۰۰۰ تتر خریدم", 1000.0, "USDT"),
    ("من ۵۰۰ دلار خریدم", 500.0, "USD"),
])
def test_persian_currency_and_digits_parsing(text, expected_val, expected_cur):
    res = I.parse(text)
    assert res.intent == "BUY_LOG"
    assert res.slots["amount"] == pytest.approx(expected_val)
    assert res.slots["currency"] == expected_cur


# ---------------- Anaphora Resolution ----------------
def test_anaphora_resolution_with_and_without_context():
    # Without context -> needs_context = True
    r1 = I.parse("این توکن رو بررسی کن")
    assert r1.needs_context is True
    assert r1.slots.get("token") is None

    # With context -> resolved
    ctx = {"address": SOL_ADDR, "chain": "solana"}
    r2 = I.parse("این توکن رو بررسی کن", context_token=ctx)
    assert r2.needs_context is False
    assert r2.slots["token"] == ctx


# ---------------- Response Contract Formatting Invariants ----------------
def test_response_contract_mandatory_footer():
    rep = OpportunityScoreReport(
        token_address=SOL_ADDR,
        token_chain="solana",
        token_symbol="TEST",
        token_name="Test",
        opportunity_score=80.0,
        confidence_level="HIGH",
        risk_level="LOW",
        positive_reasons=["نقدینگی بالا"],
        risk_deductions=[],
        evidence_items=[],
        missing_unknowns=[],
        invalidation_conditions=[InvalidationCondition("INV", "افت نقدینگی", "< $10k")],
        score_breakdown={}
    )
    txt = format_opportunity_response(rep)
    assert FOOTER_MANDATED in txt
    assert "🎯 فرصت: 80/100" in txt
    assert "دلایل مثبت" in txt
    assert "شرط‌های ابطال" in txt

    overview_txt = format_market_overview(100, 20, 80, [rep])
    assert FOOTER_MANDATED in overview_txt
