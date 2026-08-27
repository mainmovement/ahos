"""Wave-25 conversational NLU + W57 gateway-only Telegram surface.

Two layers are pinned here:

1. Intent parsing (`telegram_ai.intent`) remains the Persian NLU grammar.
   It is used by the Conversation Gateway / Web path; Telegram no longer
   executes independent scoring through `_route`.

2. `TelegramDomainService.handle_message` is W57 gateway-only:
   - With AHOS_GATEWAY_URL → POST Conversation Gateway → Core
   - Without gateway → EMERGENCY_FALLBACK_ONLY (no independent scoring)

Pre-W57 expectations that assumed in-process GREETING/NEWS/COUNCIL replies
from TelegramDomainService are intentionally retired.
"""
from __future__ import annotations

import json
from io import BytesIO
from urllib.error import URLError

import pytest

import telegram_ai.intent as I
import telegram_ai.service as svc_mod
from telegram_ai.service import TelegramDomainService, TOKEN_SCOPED_INTENTS
from telegram_ai.response_contract import FOOTER_MANDATED

SOL = "So11111111111111111111111111111111111111112"
CTX = {"current_token": {"address": SOL, "chain": "solana"}}


@pytest.fixture(scope="module")
def svc():
    return TelegramDomainService()


@pytest.fixture(autouse=True)
def _no_gateway(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "")


# ----------------------------------------------------------------- routing --

@pytest.mark.parametrize("text,intent", [
    ("سلام", "GREETING"),
    ("درود", "GREETING"),
    ("چطوری", "GREETING"),
    ("امروز چه خبر؟", "NEWS_DIGEST"),
    ("اخبار کریپتو رو بگو", "NEWS_DIGEST"),
    ("چی بخرم؟", "WHAT_TO_BUY"),
    ("کدوم توکن رو بخرم", "WHAT_TO_BUY"),
    ("کی وارد بشم؟", "ENTRY_TIMING"),
    ("نقدشوندگی این چطوره؟", "EXITABILITY_QUERY"),
    ("نهنگ ها چیکار میکنن؟", "WHALE_QUERY"),
    ("این وایرال شده؟", "VIRALITY_QUERY"),
    ("نظر هوش مصنوعی ها چیه؟", "COUNCIL_OPINION"),
    ("اشتباهاتت رو مرور کن", "SELF_REVIEW"),
    ("عملکرد گذشته چطور بوده؟", "SELF_REVIEW"),
    ("چه درسی گرفتی؟", "SELF_REVIEW"),
    ("شورای تحلیلی چی میگه؟", "PANEL_ANALYSIS"),
    ("۱۰۰ نابغه چی میگن", "PANEL_ANALYSIS"),
])
def test_conversational_intents_route(text, intent):
    assert I.parse(text).intent == intent


def test_existing_intents_are_not_shadowed():
    """The new rules must not steal traffic from the deterministic command layer."""
    assert I.parse("۵ میلیون تومان خریدم").intent == "BUY_LOG"
    assert I.parse("کی بفروشم؟").intent == "SELL_ADVICE_QUERY"
    assert I.parse("چند درصد سود دارم؟").intent == "PNL_QUERY"
    assert I.parse("وضعیت سیستم چطوره؟").intent == "SYSTEM_HEALTH"
    assert I.parse("بهترین فرصت های امروز").intent == "TOP_OPPORTUNITIES"


def test_leading_question_is_not_answered_as_data_query():
    """«حتماً پامپ میشه نه؟» seeks agreement. Agreeing would be the whole failure."""
    assert I.parse("حتماً پامپ میشه نه؟").intent == "UNKNOWN"
    assert I.parse("قطعا ترند میشه؟").intent == "UNKNOWN"


# -------------------------------------------------------------------- laws --

def test_all_conversational_intents_are_info_only():
    convo = {"NEWS_DIGEST", "WHAT_TO_BUY", "ENTRY_TIMING", "EXITABILITY_QUERY",
             "WHALE_QUERY", "VIRALITY_QUERY", "COUNCIL_OPINION", "GREETING",
             "SELF_REVIEW", "PANEL_ANALYSIS"}
    assert convo <= I.INFO_ONLY_INTENTS
    assert not (convo & I.LEDGER_MUTATING_INTENTS)


def test_ledger_mutation_remains_a_single_deterministic_intent():
    """Conversation expanded; the write surface did not."""
    assert I.LEDGER_MUTATING_INTENTS == {"BUY_LOG"}


def test_inheritance_is_limited_to_token_scoped_intents():
    """A session token must not silently narrow market-wide questions."""
    assert "NEWS_DIGEST" not in TOKEN_SCOPED_INTENTS
    assert "WHAT_TO_BUY" not in TOKEN_SCOPED_INTENTS
    assert "GREETING" not in TOKEN_SCOPED_INTENTS


# ------------------------------------------- W57 gateway-only service path --

@pytest.mark.parametrize("text", [
    "سلام", "امروز چه خبر؟", "چی بخرم؟", "راهنما",
    "نقدشوندگی این چطوره؟", "نهنگ ها چیکار میکنن؟",
    "این وایرال شده؟", "نظر هوش مصنوعی ها چیه؟",
    "اشتباهاتت رو مرور کن", "شورای تحلیلی چی میگه؟",
    "asdkjh qwerty",
])
def test_without_gateway_handle_message_is_emergency_fallback(svc, text):
    r = svc.handle_message(text, user_context=CTX)
    assert r["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert r["source"] == "EMERGENCY_FALLBACK_ONLY"
    assert r["intent"] == "gateway_unavailable"
    assert "scoring" in r["text"].lower() or "هسته" in r["text"]
    assert FOOTER_MANDATED in r["text"]


def test_legacy_route_is_hard_locked(svc):
    with pytest.raises(RuntimeError, match="W57"):
        svc._route("سلام")


def test_scorer_slot_remains_none(svc):
    assert svc.scorer is None


def test_gateway_success_path_uses_conversation_core(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "text": "پاسخ هسته از gateway",
                "intent": "GREETING",
                "focus_token": None,
                "evidence": {},
            }).encode("utf-8")

    monkeypatch.setattr(
        svc_mod.urllib.request, "urlopen", lambda *a, **k: _Resp())
    r = TelegramDomainService().handle_message("سلام")
    assert r["status"] == "OK"
    assert r["source"] == "conversation_gateway"
    assert r["intent"] == "GREETING"
    assert "پاسخ هسته" in r["text"]
    assert FOOTER_MANDATED in r["text"]


def test_gateway_transport_failure_falls_back_honestly(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")

    def _boom(*a, **k):
        raise URLError("connection refused")

    monkeypatch.setattr(svc_mod.urllib.request, "urlopen", _boom)
    r = TelegramDomainService().handle_message("سلام")
    assert r["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert r["intent"] == "gateway_unavailable"
    assert FOOTER_MANDATED in r["text"]


@pytest.mark.parametrize("probe", [
    "آخرین وضعیت بازار چیست؟", "بهترین فرصت های امروز", "فرصت های جدید",
    "این توکن رو بررسی کن", "سلام", "امروز چه خبر؟", "چی بخرم؟",
    "نقدشوندگی این چطوره؟", "نهنگ ها چیکار میکنن؟", "این وایرال شده؟",
    "نظر هوش مصنوعی ها چیه؟", "شورای تحلیلی چی میگه؟", "اشتباهاتت رو مرور کن",
    "وضعیت سیستم چطوره؟", "چند درصد سود دارم؟", "کی بفروشم؟", "راهنما",
    "asdkjh qwerty",
])
def test_every_reachable_probe_carries_footer_under_lockdown(probe):
    fresh = TelegramDomainService()
    r = fresh.handle_message(probe, user_context=CTX)
    assert FOOTER_MANDATED in r["text"], f"{probe} -> {r.get('intent')}"
