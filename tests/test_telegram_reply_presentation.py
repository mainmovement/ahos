"""Phase 5: Telegram reply presentation (HTML with plain fallback, 4096 limit).

Presentation only: no decision/authority logic. Offline: the gateway call and
Telegram adapter are stubbed. Self-test, not independent verification.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import telegram_ai.service as svc_mod
from telegram_ai.adapter import MockTelegramAdapter, TelegramSecurityGate
from telegram_ai.bot import TELEGRAM_MAX_CHARS, TelegramBotRunner, clamp_telegram_text
from telegram_ai.response_contract import FOOTER_MANDATED
from telegram_ai.service import TelegramDomainService


def _service(tmp_path, monkeypatch, gw_response):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")
    svc = TelegramDomainService(ledger_db_path=str(tmp_path / "l.sqlite"))
    monkeypatch.setattr(svc, "_call_conversation_gateway", lambda text, ctx: gw_response)
    return svc


def _runner(svc, adapter=None):
    adapter = adapter or MockTelegramAdapter()
    gate = TelegramSecurityGate(allowed_chat_ids=[100], rate_limit_user_rps=1000.0)
    return TelegramBotRunner(adapter, service=svc, gate=gate), adapter


GW = {
    "answer": "📊 وضعیت بازار\n• بیت‌کوین: ۶۵٬۴۳۲ دلار\n\n— " + FOOTER_MANDATED,
    "answer_html": "<b>📊 وضعیت بازار</b>\n• بیت‌کوین: ۶۵٬۴۳۲ دلار\n\n<i>— " + FOOTER_MANDATED + "</i>",
    "intent": "market",
}


def test_service_passes_html_and_keeps_plain(tmp_path, monkeypatch):
    res = _service(tmp_path, monkeypatch, dict(GW)).handle_message("بازار چه خبر؟")
    assert res["text_html"] == GW["answer_html"]
    assert res["text"] == GW["answer"]
    assert res["text"].count(FOOTER_MANDATED) == 1
    assert res["text_html"].count(FOOTER_MANDATED) == 1


def test_service_adds_footer_to_html_once_when_missing(tmp_path, monkeypatch):
    gw = {"answer": "x", "answer_html": "<b>x</b>", "intent": "general"}
    res = _service(tmp_path, monkeypatch, gw).handle_message("x")
    assert res["text_html"].count(FOOTER_MANDATED) == 1
    assert res["text"].count(FOOTER_MANDATED) == 1


def test_service_without_html_is_plain_only(tmp_path, monkeypatch):
    res = _service(tmp_path, monkeypatch, {"answer": "سلام", "intent": "greeting"}).handle_message("سلام")
    assert res["text_html"] is None
    gw_bad = {"answer": "سلام", "answer_html": {"not": "a string"}, "intent": "greeting"}
    assert _service(tmp_path, monkeypatch, gw_bad).handle_message("سلام")["text_html"] is None


def test_bot_sends_html_when_available(tmp_path, monkeypatch):
    runner, adapter = _runner(_service(tmp_path, monkeypatch, dict(GW)))
    adapter.inject_update(chat_id=100, text="بازار چه خبر؟")
    runner.process_pending_updates()
    assert len(adapter.sent_messages) == 1
    sent = adapter.sent_messages[0]
    assert sent["parse_mode"] == "HTML"
    assert sent["text"].startswith("<b>📊 وضعیت بازار</b>")


class _RejectHtmlAdapter(MockTelegramAdapter):
    """Simulates Telegram returning HTTP 400 (can't parse entities) for HTML."""

    def send_message(self, chat_id, text, parse_mode="HTML"):
        if parse_mode == "HTML":
            return {"ok": False, "error": "HTTP Error 400: Bad Request"}
        return super().send_message(chat_id, text, parse_mode=parse_mode)


def test_bot_falls_back_to_plain_when_html_rejected(tmp_path, monkeypatch):
    runner, adapter = _runner(_service(tmp_path, monkeypatch, dict(GW)), _RejectHtmlAdapter())
    adapter.inject_update(chat_id=100, text="بازار چه خبر؟")
    runner.process_pending_updates()
    assert len(adapter.sent_messages) == 1
    sent = adapter.sent_messages[0]
    assert "parse_mode" not in sent
    assert sent["text"] == GW["answer"]
    assert "<b>" not in sent["text"]


def test_bot_plain_fallback_when_html_too_long(tmp_path, monkeypatch):
    gw = {"answer": "a" * 5000, "answer_html": "<b>" + "a" * 5000 + "</b>", "intent": "news"}
    runner, adapter = _runner(_service(tmp_path, monkeypatch, gw))
    adapter.inject_update(chat_id=100, text="اخبار")
    runner.process_pending_updates()
    sent = adapter.sent_messages[0]
    assert "parse_mode" not in sent
    assert len(sent["text"]) <= TELEGRAM_MAX_CHARS
    assert sent["text"].endswith(FOOTER_MANDATED)


def test_clamp_keeps_short_text_and_footer():
    assert clamp_telegram_text("سلام") == "سلام"
    long = clamp_telegram_text("ب" * 10000)
    assert len(long) <= TELEGRAM_MAX_CHARS
    assert long.count(FOOTER_MANDATED) == 1


def test_gateway_unavailable_path_unchanged_plain(tmp_path, monkeypatch):
    runner, adapter = _runner(_service(tmp_path, monkeypatch, None))
    adapter.inject_update(chat_id=100, text="بازار چه خبر؟")
    runner.process_pending_updates()
    sent = adapter.sent_messages[0]
    assert "parse_mode" not in sent
    assert "EMERGENCY_FALLBACK_ONLY" in sent["text"]


def test_chat_ts_user_text_has_no_internal_ids():
    """Static scan of the reply builders' string literals (user-facing text)."""
    for rel in ("chat_replies.ts", "chat.ts"):
        src = (ROOT / rel).read_text(encoding="utf-8")
        literals = re.findall(r'"([^"\n]*[\u0600-\u06FF][^"\n]*)"|`([^`]*[\u0600-\u06FF][^`]*)`', src)
        # Drop ${...} interpolations: identifiers are code, not user text.
        texts = [re.sub(r"\$\{[^}]*\}", "", a or b) for a, b in literals]
        assert texts, rel
        for t in texts:
            assert not re.search(r"GM-\d", t), (rel, t)
            assert "کانونیکال" not in t, (rel, t)
            assert not re.search(r"canonical", t, re.I), (rel, t)
            assert "فهمیدم چی گفتی" not in t, (rel, t)
    gate = (ROOT / "chat_control_gate.ts").read_text(encoding="utf-8")
    refuse = gate[gate.index("const REFUSE_FA"):gate.index("};", gate.index("const REFUSE_FA"))]
    assert "GM-" not in refuse
    assert "هیچ تغییری اعمال نشد" in refuse


def test_engine_notice_not_unconditional():
    src = (ROOT / "chat.ts").read_text(encoding="utf-8")
    assert "engineNoticeRelevant(intent, text)" in src
    assert "(کنترل موتور از گفتگو غیرفعال است — GM-04)" not in src
    assert src.count("FINAL_USER_LINE") >= 2  # footer still applied (once per reply)


def test_single_shared_composer_for_all_chat_surfaces():
    """Dashboard chat (`reply`) and Telegram (`answer_html`) come from one composer."""
    chat = (ROOT / "chat.ts").read_text(encoding="utf-8")
    assert 'from "./response_composer"' in chat
    # normal replies + one locked helper (refusals, proposals, confirmations; Phase 7b)
    assert chat.count("finalizeReply(") == 2 and "async function lockedReply" in chat
    assert "renderPlain(" not in chat and "renderTelegramHtml(" not in chat
    assert "locked: true" in chat
    comp = (ROOT / "response_composer.ts").read_text(encoding="utf-8")
    assert "export interface ReplyPhraser" in comp
    assert "validatePhrased" in comp
    assert "fetch(" not in comp and "process.env" not in comp  # no LLM wired today
