#!/usr/bin/env python3
"""AHOS Telegram Domain Service — W57 Gateway-only client.

Production path:
  Telegram message -> AHOS_GATEWAY_URL (Conversation Gateway) -> AHOS Core

Without AHOS_GATEWAY_URL:
  EMERGENCY_FALLBACK_ONLY (status message; no scoring / ranking / opportunity decisions).
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any

AHOS_GATEWAY_URL = os.environ.get("AHOS_GATEWAY_URL", "").strip()

from .intent import parse, ParseResult, INFO_ONLY_INTENTS, LEDGER_MUTATING_INTENTS
from .response_contract import FOOTER_MANDATED
from .positions import open_ledger, log_buy, positions_for_token, latest_observed_value
from config.paths import connect_sqlite_ro, get_discovery_db_path, get_local_db_path

TOKEN_SCOPED_INTENTS = {
    "EXITABILITY_QUERY", "WHALE_QUERY", "VIRALITY_QUERY", "COUNCIL_OPINION", "PANEL_ANALYSIS",
}


class TelegramDomainService:
    def __init__(self, discovery_db_path: str | None = None, ledger_db_path: str | None = None):
        self.discovery_db_path = discovery_db_path or get_discovery_db_path()
        self.ledger_db_path = ledger_db_path or get_local_db_path()
        self.scorer = None  # W57: no independent scorer

    def _open_discovery(self) -> sqlite3.Connection:
        c = connect_sqlite_ro(self.discovery_db_path)
        c.row_factory = sqlite3.Row
        return c

    def _open_ledger(self) -> sqlite3.Connection:
        Path(self.ledger_db_path).parent.mkdir(parents=True, exist_ok=True)
        return open_ledger(self.ledger_db_path)

    def handle_message(self, text: str, user_context: dict | None = None) -> dict[str, Any]:
        """Telegram -> Gateway -> Core only. No independent scoring."""
        if AHOS_GATEWAY_URL:
            gw = self._call_conversation_gateway(text, user_context or {})
            if gw is not None:
                text_out = gw.get("text") or gw.get("answer") or gw.get("reply") or ""
                if text_out and FOOTER_MANDATED not in text_out:
                    text_out = text_out + "\n\n" + FOOTER_MANDATED
                return {
                    "text": text_out,
                    "intent": gw.get("intent", "gateway"),
                    "status": "OK",
                    "source": "conversation_gateway",
                    "focus_token": gw.get("focus_token") or gw.get("focusToken"),
                    "evidence": gw.get("evidence", {}),
                    "footer_injected": True,
                }
        return {
            "text": (
                "هسته تصمیم‌گیری در دسترس نیست. وضعیت: EMERGENCY_FALLBACK_ONLY — "
                "هیچ scoring مستقلی انجام نشد.\n\n" + FOOTER_MANDATED
            ),
            "intent": "gateway_unavailable",
            "status": "EMERGENCY_FALLBACK_ONLY",
            "source": "EMERGENCY_FALLBACK_ONLY",
            "footer_injected": True,
        }

    def _call_conversation_gateway(self, text: str, user_context: dict) -> dict[str, Any] | None:
        try:
            payload = {
                "message": text,
                "channel": "telegram",
                "focus_token": user_context.get("current_token") or user_context.get("focus_token"),
                "history": user_context.get("history") or [],
                "user_id": str(user_context.get("user_id") or ""),
            }
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            # Mirror Lane-B web API gate: send token when configured (fail-closed server-side).
            web_token = (os.environ.get("AHOS_WEB_API_TOKEN") or "").strip()
            if web_token:
                headers["Authorization"] = f"Bearer {web_token}"
            req = urllib.request.Request(
                AHOS_GATEWAY_URL,
                data=data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body if isinstance(body, dict) else None
        except Exception:
            return None

    def _require_scorer_forbidden(self) -> None:
        raise RuntimeError("W57_BRAIN_LOCKDOWN: Telegram independent scoring forbidden")

    def _route(self, text: str, user_context: dict | None = None) -> dict[str, Any]:
        """Legacy router retained for import compatibility; not used by handle_message."""
        self._require_scorer_forbidden()
        return {"text": "", "intent": "blocked", "status": "BLOCKED"}
