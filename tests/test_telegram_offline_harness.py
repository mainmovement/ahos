#!/usr/bin/env python3
"""GM-02 - offline Telegram edge harness (no credentials, no internet).

Drives the REAL runner -> domain service -> HTTP path against a stub
Conversation Gateway bound to 127.0.0.1, using the existing
``MockTelegramAdapter`` as the fake Telegram transport.

Proves (offline): envelope contract, sender identity propagation, allowlist
fail-closed behaviour, duplicate / malformed update rejection, audit records
without raw text, and offline fallback.

NOT proven here: anything about api.telegram.org. Live E2E (G11) stays
LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED. These are self-tests, not
independent verification.
"""
from __future__ import annotations

import ast
import json
import socket
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import telegram_ai.service as svc_mod  # noqa: E402
from telegram_ai.adapter import MockTelegramAdapter, TelegramSecurityGate, TelegramUpdate  # noqa: E402
from telegram_ai.bot import TelegramBotRunner  # noqa: E402
from telegram_ai.envelope import (  # noqa: E402
    AUDIT_SCHEMA,
    ENVELOPE_SCHEMA,
    ReplayGuard,
    TelegramAuditLog,
    build_update_envelope,
    hash_identifier,
    redact_envelope,
)
from telegram_ai.response_contract import FOOTER_MANDATED  # noqa: E402
from telegram_ai.service import TelegramDomainService  # noqa: E402

FAKE_WEB_TOKEN = "gm02-fake-web-token-not-a-secret"  # synthetic, test only
SECRET_TEXT = "my private note 0xDEADBEEF"


# --------------------------------------------------------------------- stub --

class _StubGateway:
    """Minimal Conversation Gateway stand-in on 127.0.0.1 (ephemeral port)."""

    def __init__(self, status: int = 200, body: bytes | None = None):
        self.requests: list[dict] = []
        self.status = status
        self.body = body if body is not None else json.dumps(
            {"reply": "پاسخ آزمایشی دروازه", "intent": "general"}).encode("utf-8")
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n)
                outer.requests.append({
                    "path": self.path,
                    "auth": self.headers.get("Authorization"),
                    "json": json.loads(raw.decode("utf-8")),
                })
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(outer.body)

            def log_message(self, *a):  # silence
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/chat"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        self.server.server_close()


def _closed_port_url() -> str:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return f"http://127.0.0.1:{port}/api/chat"


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch):
    # Never route the loopback stub through an operator proxy.
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(k, raising=False)
    direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    monkeypatch.setattr(svc_mod.urllib.request, "urlopen", direct.open)
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", FAKE_WEB_TOKEN)
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "")


def _runner(tmp_path, *, allowed=(100,), admins=(), audit=None, guard=None, rps=1000.0):
    adapter = MockTelegramAdapter()
    service = TelegramDomainService(ledger_db_path=str(tmp_path / "ledger.sqlite"))
    gate = TelegramSecurityGate(allowed_chat_ids=list(allowed), admin_user_ids=list(admins),
                                rate_limit_user_rps=rps, allow_open_access=False)
    runner = TelegramBotRunner(adapter, service=service, gate=gate,
                               replay_guard=guard, audit_log=audit or TelegramAuditLog())
    return adapter, runner


# ----------------------------------------------------------- envelope contract --

def test_envelope_contract_fields_and_no_raw_text():
    up = TelegramUpdate(7, chat_id=100, user_id=4242, username="u", text=SECRET_TEXT, is_command=False)
    env = build_update_envelope(up)
    assert env["schema"] == ENVELOPE_SCHEMA
    assert env["channel"] == "telegram"
    assert env["update_id"] == 7 and env["update_id_valid"] is True
    assert env["chat_id"] == "100" and env["sender_user_id"] == "4242"
    assert env["chat_ref"].startswith("sha256:") and env["sender_ref"].startswith("sha256:")
    assert env["text_len"] == len(SECRET_TEXT)
    assert len(env["text_sha256"]) == 64
    assert SECRET_TEXT not in json.dumps(env, ensure_ascii=False)
    red = redact_envelope(env)
    assert "chat_id" not in red and "sender_user_id" not in red


def test_hash_identifier_is_stable_and_marks_missing_sender():
    assert hash_identifier(4242) == hash_identifier("4242")
    assert hash_identifier(4242) != hash_identifier(4243)
    assert hash_identifier("") == "UNKNOWN"
    assert hash_identifier(None) == "UNKNOWN"
    assert "4242" not in hash_identifier(4242)


# --------------------------------------------------------- sender identity --

def test_sender_identity_reaches_gateway(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        adapter, runner = _runner(tmp_path)
        adapter.inject_update(chat_id=100, text="سلام", user_id=4242)
        assert runner.process_pending_updates() == 1
    assert len(gw.requests) == 1
    body = gw.requests[0]["json"]
    assert body["user_id"] == "4242"          # was always "" before GM-02
    assert body["channel"] == "telegram"
    assert body["message"] == "سلام"
    assert gw.requests[0]["auth"] == f"Bearer {FAKE_WEB_TOKEN}"
    sent = adapter.sent_messages[-1]["text"]
    assert "پاسخ آزمایشی دروازه" in sent and FOOTER_MANDATED in sent
    # identity is per-call; it must not be written back into stored context
    assert "user_id" not in runner.user_contexts.get("4242", {})


def test_slash_command_mapping_still_applies(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        adapter, runner = _runner(tmp_path)
        adapter.inject_update(chat_id=100, text="/market", user_id=1)
        runner.process_pending_updates()
    assert gw.requests[0]["json"]["message"] == "آخرین وضعیت بازار چیست؟"


# ------------------------------------------------------------ auth boundary --

def test_unauthorized_chat_never_reaches_gateway(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        audit = TelegramAuditLog()
        adapter, runner = _runner(tmp_path, audit=audit)
        adapter.inject_update(chat_id=999, text="شروع", user_id=999)
        runner.process_pending_updates()
    assert gw.requests == []
    assert [r["status"] for r in audit.records] == ["UNAUTHORIZED"]
    assert "مجاز" in adapter.sent_messages[-1]["text"]


def test_locked_no_allowlist_is_fail_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("AHOS_TELEGRAM_ALLOW_OPEN_ACCESS", raising=False)
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        adapter = MockTelegramAdapter()
        runner = TelegramBotRunner(adapter, service=TelegramDomainService(
            ledger_db_path=str(tmp_path / "l.sqlite")), gate=TelegramSecurityGate())
        adapter.inject_update(chat_id=1, text="stop", user_id=1)
        res = runner.process_update(adapter.poll_updates()[0])
    assert res["status"] == "UNAUTHORIZED"
    assert gw.requests == []


def test_admin_user_in_foreign_chat_is_authorized_and_attributed(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        adapter, runner = _runner(tmp_path, allowed=(100,), admins=(77,))
        adapter.inject_update(chat_id=555, text="سلام", user_id=77)
        runner.process_pending_updates()
    assert gw.requests[0]["json"]["user_id"] == "77"


def test_rate_limit_is_audited_and_not_dispatched(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        audit = TelegramAuditLog()
        adapter, runner = _runner(tmp_path, audit=audit, rps=0.1)
        adapter.inject_update(chat_id=100, text="a", user_id=5)
        adapter.inject_update(chat_id=100, text="b", user_id=5)
        runner.process_pending_updates()
    assert len(gw.requests) == 1
    assert [r["status"] for r in audit.records] == ["PROCESSED", "RATE_LIMITED"]


# ---------------------------------------------------------------- replay --

def test_duplicate_update_is_rejected_and_not_dispatched(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        audit = TelegramAuditLog()
        adapter, runner = _runner(tmp_path, audit=audit)
        up = adapter.inject_update(chat_id=100, text="سلام", user_id=9)
        adapter.poll_updates()
        first = runner.process_update(up)
        second = runner.process_update(up)          # replayed delivery
    assert first["status"] == "PROCESSED"
    assert second["status"] == "DUPLICATE_REJECTED"
    assert len(gw.requests) == 1
    assert len(adapter.sent_messages) == 1
    assert [r["status"] for r in audit.records] == ["PROCESSED", "DUPLICATE_REJECTED"]


def test_duplicate_of_unauthorized_update_is_silent(tmp_path):
    adapter, runner = _runner(tmp_path)
    up = adapter.inject_update(chat_id=999, text="x", user_id=999)
    runner.process_update(up)
    res = runner.process_update(up)
    assert res["status"] == "DUPLICATE_REJECTED"
    assert len(adapter.sent_messages) == 1   # only the first denial was sent


@pytest.mark.parametrize("bad_id", [0, -1, None, True, False, "5", 1.0])
def test_malformed_update_ids_are_rejected(tmp_path, monkeypatch, bad_id):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        audit = TelegramAuditLog()
        adapter, runner = _runner(tmp_path, audit=audit)
        up = TelegramUpdate(bad_id, chat_id=100, user_id=1, username=None, text="hi", is_command=False)
        res = runner.process_update(up)
    assert res["status"] == "INVALID_UPDATE_REJECTED"
    assert gw.requests == [] and adapter.sent_messages == []
    assert audit.records[-1]["status"] == "INVALID_UPDATE_REJECTED"


def test_replay_guard_is_bounded():
    g = ReplayGuard(capacity=3)
    assert [g.check(i) for i in (1, 2, 3)] == ["ACCEPT"] * 3
    assert g.check(2) == "DUPLICATE"
    assert g.check(4) == "ACCEPT"           # evicts 1
    assert len(g) == 3
    assert g.check(1) == "ACCEPT"           # bounded memory: oldest forgotten
    with pytest.raises(ValueError):
        ReplayGuard(capacity=0)


def test_mock_adapter_update_ids_are_monotonic_across_polls():
    ad = MockTelegramAdapter()
    a = ad.inject_update(chat_id=1, text="a")
    ad.poll_updates()
    b = ad.inject_update(chat_id=1, text="b")
    assert b.update_id > a.update_id


# ----------------------------------------------------------------- audit --

def test_audit_records_carry_no_raw_text_or_ids(tmp_path, monkeypatch):
    with _StubGateway() as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        audit = TelegramAuditLog()
        adapter, runner = _runner(tmp_path, audit=audit)
        adapter.inject_update(chat_id=100, text=SECRET_TEXT, user_id=4242)
        runner.process_pending_updates()
    rec = audit.records[-1]
    assert rec["schema"] == AUDIT_SCHEMA and rec["status"] == "PROCESSED"
    assert rec["source"] == "conversation_gateway"
    blob = json.dumps(audit.records, ensure_ascii=False)
    assert SECRET_TEXT not in blob
    assert '"4242"' not in blob and FAKE_WEB_TOKEN not in blob
    assert rec["sender_ref"] == hash_identifier(4242)


def test_audit_file_sink_is_append_only(tmp_path):
    path = tmp_path / "audit" / "telegram_audit.jsonl"
    env = build_update_envelope(TelegramUpdate(1, 1, 1, None, "x", False))
    TelegramAuditLog(path).record(env, "PROCESSED")
    TelegramAuditLog(path).record(env, "DUPLICATE_REJECTED")   # new instance, same file
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(l)["status"] for l in lines] == ["PROCESSED", "DUPLICATE_REJECTED"]


def test_audit_rejects_unknown_status():
    env = build_update_envelope(TelegramUpdate(1, 1, 1, None, "x", False))
    with pytest.raises(ValueError):
        TelegramAuditLog().record(env, "APPROVED_TRADE")


def test_default_runner_writes_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    adapter, runner = _runner(tmp_path / "svc")
    adapter.inject_update(chat_id=100, text="سلام", user_id=1)
    runner.process_pending_updates()
    assert runner.audit_log.path is None
    assert list(tmp_path.rglob("*.jsonl")) == []


# --------------------------------------------------------------- offline --

def test_gateway_down_falls_back_without_scoring(tmp_path, monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", _closed_port_url())
    audit = TelegramAuditLog()
    adapter, runner = _runner(tmp_path, audit=audit)
    adapter.inject_update(chat_id=100, text="فرصت ها", user_id=3)
    runner.process_pending_updates()
    sent = adapter.sent_messages[-1]["text"]
    assert "EMERGENCY_FALLBACK_ONLY" in sent and FOOTER_MANDATED in sent
    assert audit.records[-1]["source"] == "EMERGENCY_FALLBACK_ONLY"


@pytest.mark.parametrize("status,body", [
    (500, b'{"error":"boom"}'),
    (200, b"not json at all"),
    (200, b'["a","list","not","a","dict"]'),
])
def test_bad_gateway_responses_fall_back(tmp_path, monkeypatch, status, body):
    with _StubGateway(status=status, body=body) as gw:
        monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", gw.url)
        adapter, runner = _runner(tmp_path)
        adapter.inject_update(chat_id=100, text="سلام", user_id=3)
        runner.process_pending_updates()
    assert "EMERGENCY_FALLBACK_ONLY" in adapter.sent_messages[-1]["text"]


# ---------------------------------------------------------- static safety --

def test_envelope_module_has_no_network_or_authority_imports():
    src = (ROOT_DIR / "telegram_ai" / "envelope.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    forbidden = {"urllib", "socket", "http", "requests", "httpx", "subprocess",
                 "architecture", "discovery", "paper_trading", "sqlite3"}
    assert not (mods & forbidden), mods & forbidden
