#!/usr/bin/env python3
"""Telegram must not ship hardcoded operational census; watch/alert are paper-only."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED
from telegram_ai import intent as I


SOL = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


def test_system_health_has_no_hardcoded_w25_census():
    srv = TelegramDomainService()
    res = srv.handle_message("وضعیت سامانه چطوره؟")
    assert res["intent"] == "SYSTEM_HEALTH"
    assert FOOTER_MANDATED in res["text"]
    assert "۹۵۲" not in res["text"]
    assert "۴۹۳" not in res["text"]
    assert "۱۱ پوزیشن" not in res["text"]


def test_watch_token_records_paper_watch(tmp_path):
    srv = TelegramDomainService(ledger_db_path=str(tmp_path / "ledger.sqlite"))
    ctx = {"current_token": {"address": SOL, "chain": "solana"}}
    parsed_intent = I.parse("این توکن رو زیر نظر بگیر", context_token=ctx["current_token"])
    assert parsed_intent.intent == "WATCH_TOKEN"
    res = srv.handle_message("این توکن رو زیر نظر بگیر", user_context=ctx)
    assert res["status"] == "RECORDED"
    assert res.get("watch_id")
    assert "کاغذی" in res["text"] or "محلی" in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_alert_set_does_not_trade(tmp_path):
    srv = TelegramDomainService(ledger_db_path=str(tmp_path / "ledger.sqlite"))
    ctx = {"current_token": {"address": SOL, "chain": "solana"}}
    res = srv.handle_message("اگر شرایط خراب شد بهم خبر بده", user_context=ctx)
    assert res["intent"] == "ALERT_SET"
    assert res["status"] == "RECORDED"
    assert "معامله" in res["text"] or "کاغذی" in res["text"]


def test_sell_advice_without_position_is_not_found(tmp_path):
    srv = TelegramDomainService(ledger_db_path=str(tmp_path / "ledger.sqlite"))
    ctx = {"current_token": {"address": SOL, "chain": "solana"}}
    res = srv.handle_message("کی بفروشم؟", user_context=ctx)
    assert res["intent"] == "SELL_ADVICE_QUERY"
    assert res["status"] == "NOT_FOUND"
    assert FOOTER_MANDATED in res["text"]


def test_ai_router_floor_does_not_invent_confidence():
    from architecture.ai.router import AIProviderRouter
    r = AIProviderRouter(ollama_url="http://127.0.0.1:9")
    out = r.generate_completion("x")
    assert out["tier"] == "TIER_3_DETERMINISTIC_HEURISTIC"
    assert out["data"]["recommendation"] == "INSUFFICIENT_EVIDENCE"
    assert out["data"]["confidence"] is None
