#!/usr/bin/env python3
"""Static + Telegram wiring checks for Lane-B web API auth gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import telegram_ai.service as svc_mod
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED

API_ROUTES = sorted((ROOT / "app" / "api").glob("*/route.ts"))


def test_all_api_routes_call_authorize_web_api():
    assert API_ROUTES, "expected app/api/*/route.ts"
    for path in API_ROUTES:
        text = path.read_text(encoding="utf-8")
        assert "authorizeWebApi" in text, f"{path.name} missing authorizeWebApi"
        assert "from \"@/web_api_auth\"" in text or "from '@/web_api_auth'" in text


def test_command_center_uses_web_api_client():
    text = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")
    assert "webApiFetch" in text
    assert 'fetch("/api/' not in text


def test_package_json_binds_next_to_loopback():
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "--hostname 127.0.0.1" in pkg["scripts"]["dev"]
    assert "--hostname 127.0.0.1" in pkg["scripts"]["start"]


def test_windows_ensure_web_api_token_script_exists():
    path = ROOT / "scripts" / "windows_ensure_web_api_token.ps1"
    text = path.read_text(encoding="utf-8")
    assert "AHOS_WEB_API_TOKEN" in text
    assert "NEXT_PUBLIC_AHOS_WEB_API_TOKEN" in text
    assert "db:migrate" in text.lower() or "Will NOT migrate" in text


def test_env_example_documents_web_api_token_keys():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "AHOS_WEB_API_TOKEN=" in text
    assert "NEXT_PUBLIC_AHOS_WEB_API_TOKEN=" in text
    assert "AHOS_WEB_API_ALLOW_OPEN_ACCESS=0" in text


def test_gateway_sends_authorization_when_web_token_set(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "unit-test-web-token")
    captured: dict = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {
                    "text": "ok",
                    "intent": "GREETING",
                    "focus_token": None,
                    "evidence": {},
                }
            ).encode("utf-8")

    def _urlopen(req, timeout=None):
        captured["headers"] = dict(req.headers)
        return _Resp()

    monkeypatch.setattr(svc_mod.urllib.request, "urlopen", _urlopen)
    r = TelegramDomainService().handle_message("سلام")
    assert r["status"] == "OK"
    assert r["source"] == "conversation_gateway"
    assert FOOTER_MANDATED in r["text"]
    auth = captured["headers"].get("Authorization") or captured["headers"].get(
        "authorization"
    )
    assert auth == "Bearer unit-test-web-token"


def test_gateway_omits_authorization_when_web_token_unset(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")
    monkeypatch.delenv("AHOS_WEB_API_TOKEN", raising=False)
    captured: dict = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"text": "ok", "intent": "GREETING"}).encode("utf-8")

    def _urlopen(req, timeout=None):
        captured["headers"] = dict(req.headers)
        return _Resp()

    monkeypatch.setattr(svc_mod.urllib.request, "urlopen", _urlopen)
    TelegramDomainService().handle_message("سلام")
    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert "authorization" not in headers
