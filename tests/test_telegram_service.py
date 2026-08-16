#!/usr/bin/env python3
"""Tests for Telegram Service & Persian NLU (Sections IX & X)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED, format_opportunity_response
from architecture.scoring.engine import OpportunityScorer
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics

SOL_ADDR = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


@pytest.fixture
def service(tmp_path):
    # Use real e01 sqlite for read-only or empty db for test
    return TelegramDomainService(
        discovery_db_path=str(ROOT_DIR / "data" / "e01_discovery.sqlite"),
        ledger_db_path=str(tmp_path / "test_local.sqlite")
    )


def test_telegram_service_help_query(service):
    res = service.handle_message("راهنما")
    assert res["status"] == "OK"
    assert "راهنمای دستیار هوشمند AHOS" in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_telegram_service_market_overview(service):
    res = service.handle_message("آخرین وضعیت بازار چیست؟")
    assert res["status"] == "OK"
    assert "وضعیت کلی بازار" in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_telegram_service_buy_logging_paper(service):
    res = service.handle_message(f"من ۵ میلیون تومان از این خریدم", user_context={"current_token": {"address": SOL_ADDR, "chain": "solana"}})
    assert res["status"] == "RECORDED"
    assert res["entry_id"] is not None
    assert "پوزیشن خرید کاغذی با موفقیت ثبت شد" in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_telegram_service_token_scoring_query(service):
    res = service.handle_message(f"این توکن رو بررسی کن {SOL_ADDR}")
    assert res["status"] == "OK"
    assert "تحلیل فرصت" in res["text"]
    assert "فرصت:" in res["text"]
    assert "دلایل مثبت" in res["text"]
    assert "شرط‌های ابطال فرصت" in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_telegram_service_unknown_message(service):
    res = service.handle_message("یک متن نامربوط و عجیب و غریب")
    assert res["status"] == "UNRECOGNIZED"
    assert "متوجه منظور شما نشدم" in res["text"]
    assert FOOTER_MANDATED in res["text"]
