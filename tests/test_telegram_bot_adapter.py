#!/usr/bin/env python3
"""Tests for Telegram Bot Production Adapter & Security Gate (Phase XX)."""
import sys, json, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from telegram_ai.adapter import (
    TelegramUpdate, TelegramSecurityGate, MockTelegramAdapter, ProductionTelegramAdapter
)
from telegram_ai.bot import TelegramBotRunner
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED


def test_telegram_security_gate_open_access():
    gate = TelegramSecurityGate()
    up = TelegramUpdate(1, chat_id=100, user_id=200, username="user", text="سلام", is_command=False)
    assert gate.is_authorized(up) is True
    assert gate.is_admin(up) is False


def test_telegram_security_gate_restricted_chat():
    gate = TelegramSecurityGate(allowed_chat_ids=[100, 200], admin_user_ids=[999])
    up_allowed = TelegramUpdate(1, chat_id=100, user_id=50, username="user", text="سلام", is_command=False)
    up_forbidden = TelegramUpdate(2, chat_id=300, user_id=50, username="user", text="سلام", is_command=False)
    up_admin = TelegramUpdate(3, chat_id=300, user_id=999, username="admin", text="سلام", is_command=False)

    assert gate.is_authorized(up_allowed) is True
    assert gate.is_authorized(up_forbidden) is False
    assert gate.is_authorized(up_admin) is True
    assert gate.is_admin(up_admin) is True


def test_telegram_security_gate_user_rate_limit():
    gate = TelegramSecurityGate(rate_limit_user_rps=2.0)  # max 2 per sec (0.5s interval)
    up = TelegramUpdate(1, chat_id=100, user_id=50, username="user", text="1", is_command=False)
    assert gate.check_rate_limit(up) is True
    # Immediate next message rejected
    assert gate.check_rate_limit(up) is False
    # After sleep
    time.sleep(0.55)
    assert gate.check_rate_limit(up) is True


def test_mock_telegram_adapter_send_and_poll():
    adapter = MockTelegramAdapter()
    adapter.send_message(chat_id=100, text="سلام تست")
    assert len(adapter.sent_messages) == 1
    assert adapter.sent_messages[0]["text"] == "سلام تست"

    adapter.inject_update(chat_id=100, text="راهنما")
    updates = adapter.poll_updates()
    assert len(updates) == 1
    assert updates[0].text == "راهنما"

    # Polling clears pending
    assert len(adapter.poll_updates()) == 0


def test_production_telegram_adapter_mock_transport():
    mock_sent = []

    def mock_transport(req, timeout=None):
        data = json.loads(req.data.decode("utf-8"))
        mock_sent.append(data)

        class MockResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"ok": True, "result": {"message_id": 1}}).encode("utf-8")
        return MockResp()

    adapter = ProductionTelegramAdapter(bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567", transport=mock_transport)
    res = adapter.send_message(chat_id=100, text="تست آداپتور لایو")
    assert res["ok"] is True
    assert len(mock_sent) == 1
    assert mock_sent[0]["chat_id"] == 100
    assert mock_sent[0]["text"] == "تست آداپتور لایو"


def test_telegram_bot_runner_full_cycle(tmp_path):
    adapter = MockTelegramAdapter()
    service = TelegramDomainService(ledger_db_path=str(tmp_path / "test_ledger.sqlite"))
    gate = TelegramSecurityGate(allowed_chat_ids=[100])
    runner = TelegramBotRunner(adapter, service=service, gate=gate)

    # 1. Authorized message — W57 emergency fallback when gateway URL unset
    adapter.inject_update(chat_id=100, text="/help")
    count = runner.process_pending_updates()
    assert count == 1
    assert len(adapter.sent_messages) == 1
    assert "EMERGENCY_FALLBACK_ONLY" in adapter.sent_messages[0]["text"]
    assert FOOTER_MANDATED in adapter.sent_messages[0]["text"]

    # 2. Unauthorized message
    adapter.inject_update(chat_id=999, text="/help")
    runner.process_pending_updates()
    assert len(adapter.sent_messages) == 2
    assert "دسترسی شما به این ربات مجاز نمی‌باشد" in adapter.sent_messages[1]["text"]
