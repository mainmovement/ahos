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


def test_windows_ops_toward_pre_soak_script_exists():
    path = ROOT / "scripts" / "windows_ops_toward_pre_soak.ps1"
    text = path.read_text(encoding="utf-8")
    assert "web_api_auth.ts" in text
    assert "windows_ensure_web_api_token.ps1" in text
    assert "operator_validation_gate.py" in text
    assert "OPERATOR_READY" in text


def test_windows_run_operator_gate_script_exists():
    path = ROOT / "scripts" / "windows_run_operator_gate.ps1"
    text = path.read_text(encoding="utf-8")
    assert "--platform" in text and "windows" in text
    assert "operator_validation_gate.py" in text
    assert "probe-providers" in text
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in text
    assert "LATEST_WINDOWS_GATE.txt" in text
    assert "Set-Clipboard" in text
    assert "notepad.exe" in text
    assert "Env:AHOS_WEB_API_TOKEN" in text or 'Set-Item -Path ("Env:"' in text
    assert "gh pr comment" in text
    assert "AHOS_GATE_PR" in text
    assert "windows_telegram_send_gate_paste.ps1" in text


def test_windows_telegram_send_gate_paste_script_exists():
    path = ROOT / "scripts" / "windows_telegram_send_gate_paste.ps1"
    text = path.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "TELEGRAM_ALLOWED_CHAT_IDS" in text
    assert "sendDocument" in text
    assert "OPERATOR_READY" in text or "NOT OPERATOR_READY" in text or "NOT READY" in text
    assert "db:migrate" in text.lower() or "Does not migrate" in text


def test_windows_g11_telegram_e2e_helper_exists():
    path = ROOT / "scripts" / "windows_g11_telegram_e2e_helper.ps1"
    text = path.read_text(encoding="utf-8")
    assert "telegram_e2e_" in text
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "TelegramE2eArtifact" in text or "telegram-e2e-artifact" in text
    assert "OPERATOR_READY" in text
    assert "db:migrate" in text.lower()


def test_windows_preflight_ops_script_exists():
    path = ROOT / "scripts" / "windows_preflight_ops.ps1"
    text = path.read_text(encoding="utf-8")
    assert "AHOS_WEB_API_TOKEN" in text
    assert "DATABASE_URL" in text
    assert "web_api_auth.ts" in text
    assert "db:migrate" in text.lower() or "do NOT db:migrate" in text
    assert "sqlite_evidence" in text or "e01_discovery" in text
    assert "pg_isready" in text


def test_windows_ops_bat_auto_starts_next_and_runs_gate():
    text = (ROOT / "AHOS_WINDOWS_OPS.bat").read_text(encoding="utf-8", errors="replace")
    assert "windows_post_merge_reconcile.ps1" in text
    assert "KeepCurrentBranch" in text
    assert "windows_preflight_ops.ps1" in text
    assert "windows_restart_next_dev.ps1" in text or "npm run dev" in text
    assert "127.0.0.1:3000" in text
    assert "/api/chat" in text
    assert "windows_seed_local_evidence.ps1" in text
    assert "windows_wait_for_web_api.ps1" in text or "/api/chat" in text
    assert "windows_ensure_postgres_win.ps1" in text
    assert "windows_run_operator_gate.ps1" in text
    assert "windows_ops_last_run.log" in text or "LOG=" in text
    assert "db:migrate" in text.lower()
    assert "OPERATOR_READY" in text


def test_windows_wait_for_web_api_script_exists():
    path = ROOT / "scripts" / "windows_wait_for_web_api.ps1"
    text = path.read_text(encoding="utf-8")
    assert "/api/chat" in text
    assert "AHOS_WEB_API_TOKEN" in text
    assert "Invoke-WebRequest" in text


def test_windows_ensure_postgres_win_script_exists():
    path = ROOT / "scripts" / "windows_ensure_postgres_win.ps1"
    text = path.read_text(encoding="utf-8")
    assert "ahos_postgres_win" in text
    assert "docker compose" in text
    assert "pg_isready" in text
    assert "db:migrate" in text.lower() or "Never db:migrate" in text


def test_windows_seed_local_evidence_script_exists():
    path = ROOT / "scripts" / "windows_seed_local_evidence.ps1"
    text = path.read_text(encoding="utf-8")
    assert "lifecycle_status" in text
    assert "single-cycle" in text
    assert "OPERATOR_READY" in text
    assert "db:migrate" in text.lower() or "Never migrates" in text


def test_windows_run_this_first_points_at_ops_bat():
    text = (ROOT / "WINDOWS_RUN_THIS_FIRST.txt").read_text(encoding="utf-8")
    assert "AHOS_WINDOWS_OPS.bat" in text
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in text
    assert "db:migrate" in text.lower()
    start_ps1 = (ROOT / "start_ahos.ps1").read_text(encoding="utf-8")
    assert "AHOS_WINDOWS_OPS.bat" in start_ps1
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in start_ps1


def test_windows_restart_next_dev_script_exists():
    path = ROOT / "scripts" / "windows_restart_next_dev.ps1"
    text = path.read_text(encoding="utf-8")
    assert "Stop-Process" in text
    assert "npm run dev" in text
    assert "3000" in text


def test_post_merge_reconcile_supports_keep_current_branch():
    text = (ROOT / "scripts" / "windows_post_merge_reconcile.ps1").read_text(encoding="utf-8")
    assert "KeepCurrentBranch" in text
    assert "windows_ensure_web_api_token.ps1" in text
    assert "web_api_auth.ts" in text
    assert "operator_validation_gate.py" in text or "windows_run_operator_gate.ps1" in text


def test_install_windows_gate_cli_matches_runner():
    text = (ROOT / "install_windows.ps1").read_text(encoding="utf-8", errors="replace")
    assert "--repo-root" not in text
    assert "--require-owner-action" not in text
    assert "windows_run_operator_gate.ps1" in text
    assert "windows_ensure_web_api_token.ps1" in text


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
