#!/usr/bin/env python3
"""AHOS Telegram Domain Service — W57 Gateway-only client.

Production path:
  Telegram message -> AHOS_GATEWAY_URL (Conversation Gateway) -> AHOS Core

Without AHOS_GATEWAY_URL:
  EMERGENCY_FALLBACK_ONLY (status message; no scoring / ranking / opportunity decisions).

Mission 9.5 (corrective security): the gateway no longer trusts a client-asserted
`user_id`/`channel`. Every request is signed with AHOS_TELEGRAM_GATEWAY_SECRET
(a server-only value from .env; never printed, never in NEXT_PUBLIC_*) over
`user_id|timestamp|sha256(body)` via HMAC-SHA256, with a short replay window and
a constant-time compare on the gateway side (chat_auth.ts). The bot still sends
AHOS_WEB_API_TOKEN as the API-access bearer; that is transport auth, not identity.
When the signing secret is missing the headers are simply omitted and the gateway
treats the caller as unverified (fail-closed: not the owner).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any

AHOS_GATEWAY_URL = os.environ.get("AHOS_GATEWAY_URL", "").strip()

# Mission 9.5: identity headers verified by chat_auth.ts.
TG_UID_HEADER = "X-AHOS-TG-Uid"
TG_TS_HEADER = "X-AHOS-TG-Ts"
TG_SIG_HEADER = "X-AHOS-TG-Sig"

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
                # Presentation only: optional pre-escaped Telegram HTML from the
                # gateway. The plain `text` stays authoritative for fallback.
                html_out = gw.get("answer_html") or ""
                if not isinstance(html_out, str):
                    html_out = ""
                if html_out and FOOTER_MANDATED not in html_out:
                    html_out = html_out + "\n\n<i>" + FOOTER_MANDATED + "</i>"
                return {
                    "text": text_out,
                    "text_html": html_out or None,
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
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers = {"Content-Type": "application/json; charset=utf-8"}
            # Mirror Lane-B web API gate: send token when configured (fail-closed server-side).
            web_token = (os.environ.get("AHOS_WEB_API_TOKEN") or "").strip()
            if web_token:
                headers["Authorization"] = f"Bearer {web_token}"
            # Mission 9.5: prove the sender identity to the gateway so the owner
            # decision can be made server-side. Fail-closed: without the secret
            # the gateway treats this caller as unverified (not the owner).
            self._sign_identity(headers, payload["user_id"], data)
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

    @staticmethod
    def _sign_identity(headers: dict[str, str], user_id: str, body: bytes) -> None:
        """HMAC-SHA256 over `user_id|timestamp|sha256(body)` with the shared
        server-only secret. Adds the three identity headers, or nothing when the
        secret is absent (gateway then sees an unverified caller)."""
        secret = (os.environ.get("AHOS_TELEGRAM_GATEWAY_SECRET") or "").strip()
        uid = str(user_id or "").strip()
        if not secret or not uid:
            return
        ts = str(int(time.time()))
        body_sha = hashlib.sha256(body).hexdigest()
        sig = hmac.new(secret.encode("utf-8"), f"{uid}|{ts}|{body_sha}".encode("utf-8"), hashlib.sha256).hexdigest()
        headers[TG_UID_HEADER] = uid
        headers[TG_TS_HEADER] = ts
        headers[TG_SIG_HEADER] = sig

    def _require_scorer_forbidden(self) -> None:
        raise RuntimeError("W57_BRAIN_LOCKDOWN: Telegram independent scoring forbidden")

    def _route(self, text: str, user_context: dict | None = None) -> dict[str, Any]:
        """Legacy router retained for import compatibility; not used by handle_message."""
        self._require_scorer_forbidden()
        return {"text": "", "intent": "blocked", "status": "BLOCKED"}
