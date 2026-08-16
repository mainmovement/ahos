#!/usr/bin/env python3
"""AHOS Telegram Production Adapter & Bot API Abstraction Layer (Phase XX).

Features:
  - Abstract Bot API Interface for both Webhook and Polling modes.
  - Mock Adapter for $0 / keyless testing environments.
  - Production Adapter with automatic secret sanitization.
  - User Permission Gate & Chat Authorization.
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Any

from architecture.security import sanitize_secrets, sanitize_dict


@dataclass
class TelegramUpdate:
    update_id: int
    chat_id: int | str
    user_id: int | str
    username: str | None
    text: str
    is_command: bool
    timestamp: float = field(default_factory=time.time)


class TelegramSecurityGate:
    def __init__(self, allowed_chat_ids: list[int | str] | None = None,
                 admin_user_ids: list[int | str] | None = None,
                 rate_limit_user_rps: float = 1.0):
        self.allowed_chat_ids = set(str(cid) for cid in (allowed_chat_ids or []))
        self.admin_user_ids = set(str(uid) for uid in (admin_user_ids or []))
        self.rate_limit_user_rps = rate_limit_user_rps
        self._user_last_msg_ts: dict[str, float] = {}

    def is_authorized(self, update: TelegramUpdate) -> bool:
        if not self.allowed_chat_ids:
            return True  # Open access mode if no restriction configured
        return str(update.chat_id) in self.allowed_chat_ids or str(update.user_id) in self.admin_user_ids

    def is_admin(self, update: TelegramUpdate) -> bool:
        return str(update.user_id) in self.admin_user_ids

    def check_rate_limit(self, update: TelegramUpdate) -> bool:
        uid = str(update.user_id)
        now = time.time()
        last = self._user_last_msg_ts.get(uid, 0.0)
        min_interval = 1.0 / max(self.rate_limit_user_rps, 0.1)
        if now - last < min_interval:
            return False
        self._user_last_msg_ts[uid] = now
        return True


class TelegramBotAdapterInterface(ABC):
    @abstractmethod
    def send_message(self, chat_id: int | str, text: str, parse_mode: str = "HTML") -> dict[str, Any]:
        pass

    @abstractmethod
    def poll_updates(self, offset: int | None = None, timeout: int = 10) -> list[TelegramUpdate]:
        pass

    @abstractmethod
    def set_webhook(self, url: str) -> bool:
        pass


class MockTelegramAdapter(TelegramBotAdapterInterface):
    """In-memory mock adapter for tests and token-less operation."""
    def __init__(self):
        self.sent_messages: list[dict[str, Any]] = []
        self.incoming_updates: list[TelegramUpdate] = []
        self.webhook_url: str | None = None

    def inject_update(self, chat_id: int | str, text: str, user_id: int | str = 12345, username: str = "testuser"):
        up = TelegramUpdate(
            update_id=len(self.incoming_updates) + 1,
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            text=text,
            is_command=text.startswith("/")
        )
        self.incoming_updates.append(up)
        return up

    def send_message(self, chat_id: int | str, text: str, parse_mode: str = "HTML") -> dict[str, Any]:
        msg = {
            "chat_id": chat_id,
            "text": sanitize_secrets(text),
            "parse_mode": parse_mode,
            "timestamp": time.time()
        }
        self.sent_messages.append(msg)
        return {"ok": True, "result": msg}

    def poll_updates(self, offset: int | None = None, timeout: int = 10) -> list[TelegramUpdate]:
        updates = list(self.incoming_updates)
        self.incoming_updates.clear()
        return updates

    def set_webhook(self, url: str) -> bool:
        self.webhook_url = url
        return True


class ProductionTelegramAdapter(TelegramBotAdapterInterface):
    """Production HTTP adapter connecting to Telegram Bot API."""
    def __init__(self, bot_token: str, transport: Callable = urllib.request.urlopen):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.transport = transport

    def send_message(self, chat_id: int | str, text: str, parse_mode: str = "HTML") -> dict[str, Any]:
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": sanitize_secrets(text),
            "parse_mode": parse_mode
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with self.transport(req, timeout=10.0) as resp:
                raw = resp.read()
            return json.loads(raw)
        except Exception as e:
            return {"ok": False, "error": sanitize_secrets(str(e))}

    def poll_updates(self, offset: int | None = None, timeout: int = 10) -> list[TelegramUpdate]:
        url = f"{self.base_url}/getUpdates?timeout={timeout}"
        if offset is not None:
            url += f"&offset={offset}"
        req = urllib.request.Request(url)
        updates: list[TelegramUpdate] = []
        try:
            with self.transport(req, timeout=timeout + 5) as resp:
                data = json.loads(resp.read())
            for item in data.get("result", []):
                msg = item.get("message", {})
                chat = msg.get("chat", {})
                from_user = msg.get("from", {})
                txt = msg.get("text", "")
                updates.append(TelegramUpdate(
                    update_id=item.get("update_id", 0),
                    chat_id=chat.get("id", ""),
                    user_id=from_user.get("id", ""),
                    username=from_user.get("username"),
                    text=txt,
                    is_command=txt.startswith("/")
                ))
        except Exception:
            pass
        return updates

    def set_webhook(self, url: str) -> bool:
        req_url = f"{self.base_url}/setWebhook?url={url}"
        req = urllib.request.Request(req_url)
        try:
            with self.transport(req, timeout=10.0) as resp:
                data = json.loads(resp.read())
                return data.get("ok", False)
        except Exception:
            return False
