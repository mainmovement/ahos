#!/usr/bin/env python3
"""Tests for Telegram Service — W57 Gateway-only lockdown."""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
import telegram_ai.service as svc_mod
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED

SOL_ADDR = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


@pytest.fixture
def service(tmp_path):
    return TelegramDomainService(
        discovery_db_path=str(ROOT_DIR / "data" / "e01_discovery.sqlite"),
        ledger_db_path=str(tmp_path / "test_local.sqlite"),
    )


@pytest.fixture(autouse=True)
def _no_gateway(monkeypatch):
    """Without AHOS_GATEWAY_URL, production path must be EMERGENCY_FALLBACK_ONLY."""
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "")


def test_scorer_is_none(service):
    assert service.scorer is None


def test_telegram_service_help_query(service):
    res = service.handle_message("راهنما")
    assert res["source"] == "EMERGENCY_FALLBACK_ONLY"
    assert res["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert FOOTER_MANDATED in res["text"]
    assert "scoring" in res["text"].lower() or "هسته" in res["text"] or "EMERGENCY" in res["text"]


def test_telegram_service_market_overview(service):
    res = service.handle_message("آخرین وضعیت بازار چیست؟")
    assert res["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert res["source"] == "EMERGENCY_FALLBACK_ONLY"
    assert FOOTER_MANDATED in res["text"]


def test_telegram_service_buy_logging_paper(service):
    res = service.handle_message(
        "من ۵ میلیون تومان از این خریدم",
        user_context={"current_token": {"address": SOL_ADDR, "chain": "solana"}},
    )
    assert res["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert res["source"] == "EMERGENCY_FALLBACK_ONLY"
    assert FOOTER_MANDATED in res["text"]


def test_telegram_service_token_scoring_query(service):
    res = service.handle_message(f"این توکن رو بررسی کن {SOL_ADDR}")
    assert res["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert res["source"] == "EMERGENCY_FALLBACK_ONLY"
    assert FOOTER_MANDATED in res["text"]
    assert "تحلیل فرصت" not in res["text"]


def test_telegram_service_unknown_message(service):
    res = service.handle_message("یک متن نامربوط و عجیب و غریب")
    assert res["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert FOOTER_MANDATED in res["text"]


def test_require_scorer_forbidden(service):
    with pytest.raises(RuntimeError, match="W57"):
        service._require_scorer_forbidden()


def test_gateway_reply_has_no_forced_footer_and_long_timeout(monkeypatch, service):
    import telegram_ai.service as svc
    assert svc.GATEWAY_TIMEOUT_S >= 25
    monkeypatch.setattr(type(service), "_call_conversation_gateway",
                        lambda self, t, c, u: {"reply": "سلام، طلا الان ۲۴۰۰ دلار است.", "intent": "agent"})
    res = service.handle_message("طلا چنده؟")
    assert res["source"] == "conversation_gateway"
    assert FOOTER_MANDATED not in res["text"]
    assert res["footer_injected"] is False


def test_operating_question_ignores_a_gateway_that_says_the_engine_is_off(monkeypatch, service):
    monkeypatch.setattr(
        type(service),
        "_call_conversation_gateway",
        lambda self, t, c, u: {"reply": "✅ موتور تحلیل خاموش شد."},
    )
    monkeypatch.setattr(
        "telegram_ai.service.answer_question",
        lambda root, text, **_k: {
            "text": "معامله‌های کاغذی فعال است؛ کلید پول واقعی عمداً خاموش است.",
            "source": "world_state",
            "error_class": None,
        },
    )
    res = service.handle_message("آهوس چیکار میکنه")
    assert res["source"] == "world_state"
    assert "موتور تحلیل خاموش" not in res["text"]
    assert "معامله‌های کاغذی فعال است؛ کلید پول واقعی عمداً خاموش است." in res["text"]


def test_status_question_uses_the_paper_file_when_the_gateway_is_down(monkeypatch, service):
    monkeypatch.setattr(type(service), "_call_conversation_gateway", lambda self, t, c, u: None)
    monkeypatch.setattr(
        "telegram_ai.service.answer_question",
        lambda root, text, **_k: {
            "text": "شرط صادقانه: 30 fresh closes + DSR>0.95 + PBO<0.5",
            "source": "world_state",
            "error_class": "timeout",
        },
    )
    res = service.handle_message("چقدر مونده سودده بشه؟")
    assert res["source"] == "llm_fallback"
    assert "30 fresh closes + DSR>0.95 + PBO<0.5" in res["text"]


def test_bare_menu_uses_the_paper_fallback(monkeypatch, service):
    monkeypatch.setattr(
        type(service),
        "_call_conversation_gateway",
        lambda self, t, c, u: {"reply": "این سؤال را دقیق متوجه نشدم. یکی از این‌ها را امتحان کن:"},
    )
    monkeypatch.setattr(
        "telegram_ai.service.answer_question",
        lambda root, text, **_k: {
            "text": "سود کاغذی هنوز پایدار نشده است.\nشرط صادقانه: 30 fresh closes + DSR>0.95 + PBO<0.5",
            "source": "world_state",
            "error_class": "quota_429",
        },
    )
    res = service.handle_message("چقدر مونده سودده بشه؟")
    assert res["source"] == "llm_fallback"
    assert "دقیق متوجه نشدم" not in res["text"]
    assert "30 fresh closes + DSR>0.95 + PBO<0.5" in res["text"]
