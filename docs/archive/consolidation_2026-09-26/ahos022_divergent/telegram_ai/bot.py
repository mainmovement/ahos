#!/usr/bin/env python3
"""AHOS Telegram Bot Production Runner (Phase XX).

Orchestrates:
  - Inbound update processing (polling / webhook).
  - Security gate authorization & rate limit enforcement.
  - Command routing to domain services.
  - Sanitized Persian response delivery.
"""
from __future__ import annotations

import time
from typing import Any

from .adapter import TelegramBotAdapterInterface, TelegramUpdate, TelegramSecurityGate, MockTelegramAdapter
from .service import TelegramDomainService
from .response_contract import FOOTER_MANDATED


class TelegramBotRunner:
    def __init__(self, adapter: TelegramBotAdapterInterface,
                 service: TelegramDomainService | None = None,
                 gate: TelegramSecurityGate | None = None):
        self.adapter = adapter
        self.service = service or TelegramDomainService()
        self.gate = gate or TelegramSecurityGate()
        self.user_contexts: dict[str, dict[str, Any]] = {}

    def process_update(self, update: TelegramUpdate) -> dict[str, Any]:
        """Processes a single incoming Telegram update and delivers the response."""
        # 1. Authorization check
        if not self.gate.is_authorized(update):
            resp = self.adapter.send_message(
                update.chat_id,
                f"⛔ دسترسی شما به این ربات مجاز نمی‌باشد.\n\n{FOOTER_MANDATED}"
            )
            return {"status": "UNAUTHORIZED", "response": resp}

        # 2. Rate limit check
        if not self.gate.check_rate_limit(update):
            resp = self.adapter.send_message(
                update.chat_id,
                f"⚠️ لطفاً چند لحظه صبر کنید (محدودیت ارسال پیام).\n\n{FOOTER_MANDATED}"
            )
            return {"status": "RATE_LIMITED", "response": resp}

        # 3. Command mapping
        text = update.text.strip()
        if text.startswith("/start") or text.startswith("/help"):
            text = "راهنما"
        elif text.startswith("/top"):
            text = "بهترین فرصت‌های امروز"
        elif text.startswith("/market"):
            text = "آخرین وضعیت بازار چیست؟"

        # 4. Context retrieval & dispatch
        ctx = self.user_contexts.get(str(update.user_id), {})
        result = self.service.handle_message(text, user_context=ctx)

        # 5. Update user context if candidate/token returned
        if "candidate" in result:
            cand = result["candidate"]
            self.user_contexts[str(update.user_id)] = {
                "current_token": {"address": cand.address, "chain": cand.chain}
            }

        # 6. Send response
        send_res = self.adapter.send_message(update.chat_id, result["text"])
        return {"status": "PROCESSED", "intent": result.get("intent"), "send_result": send_res}

    def process_pending_updates(self) -> int:
        """Polls for updates and processes all of them in sequence."""
        updates = self.adapter.poll_updates()
        count = 0
        for up in updates:
            self.process_update(up)
            count += 1
        return count
