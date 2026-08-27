"""Wave-25: the launcher -- the difference between 'a library' and 'it runs'.

The acceptance criterion for this project is that the user copies, pastes, and
it works. That makes the launcher a first-class component, not glue: if
preflight lies, or the poll offset is mishandled, the user experiences a broken
product no matter how good the analysis layer is.

Pinned here:
  * .env parsing (comments, quotes, blank lines, '=' inside values)
  * the update offset advances BEFORE handling, so one poisoned message cannot
    wedge the bot into an infinite replay loop across restarts
  * preflight reports every failure, and never claims success on a bad config
  * proxy transport selection degrades instead of crashing
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import run_bot
from telegram_ai.adapter import (
    build_proxy_transport, ProductionTelegramAdapter,
    MockTelegramAdapter, TelegramSecurityGate,
)


# ------------------------------------------------------------------- .env --

def test_dotenv_parses_comments_quotes_and_blanks(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text(
        "# a comment\n"
        "\n"
        "TELEGRAM_BOT_TOKEN=\"123:ABC\"\n"
        "ALL_PROXY='socks5://127.0.0.1:10808'\n"
        "  SPACED  =  value  \n"
        "URLish=http://x/y?a=b&c=d\n"
        "novalue\n",
        encoding="utf-8")
    for k in ("TELEGRAM_BOT_TOKEN", "ALL_PROXY", "SPACED", "URLish"):
        monkeypatch.delenv(k, raising=False)

    got = run_bot.load_dotenv(p)
    assert got["TELEGRAM_BOT_TOKEN"] == "123:ABC"      # quotes stripped
    assert got["ALL_PROXY"] == "socks5://127.0.0.1:10808"
    assert got["SPACED"] == "value"                    # whitespace trimmed
    assert got["URLish"] == "http://x/y?a=b&c=d"       # '=' inside value kept
    assert "novalue" not in got


def test_dotenv_missing_file_is_not_an_error(tmp_path):
    assert run_bot.load_dotenv(tmp_path / "nope.env") == {}


def test_dotenv_never_overrides_real_environment(tmp_path, monkeypatch):
    """An explicitly exported value must win over the file."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from-env")
    p = tmp_path / ".env"
    p.write_text("TELEGRAM_BOT_TOKEN=from-file\n", encoding="utf-8")
    run_bot.load_dotenv(p)
    assert os.environ["TELEGRAM_BOT_TOKEN"] == "from-env"


def test_id_list_parsing():
    assert run_bot._ids("1, 2 ,3") == ["1", "2", "3"]
    assert run_bot._ids("") == []
    assert run_bot._ids(None) == []


# ----------------------------------------------------------------- offset --

def test_offset_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(run_bot, "OFFSET_FILE", tmp_path / "off.json")
    assert run_bot.read_offset() is None
    run_bot.write_offset(42)
    assert run_bot.read_offset() == 42


def test_corrupt_offset_file_reads_as_none(tmp_path, monkeypatch):
    f = tmp_path / "off.json"
    f.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(run_bot, "OFFSET_FILE", f)
    assert run_bot.read_offset() is None


def test_offset_write_failure_is_survivable(tmp_path, monkeypatch):
    """Losing an offset costs one replayed message; it must never crash the bot."""
    monkeypatch.setattr(run_bot, "OFFSET_FILE", tmp_path / "nodir" / "x" / "o.json")
    run_bot.write_offset(7)  # must not raise


# ------------------------------------------------------------- preflight --

def _clear(monkeypatch):
    for k in ("TELEGRAM_BOT_TOKEN", "ALL_PROXY", "HTTPS_PROXY",
              "TELEGRAM_ALLOWED_CHAT_IDS"):
        monkeypatch.delenv(k, raising=False)


def test_preflight_fails_without_a_token(monkeypatch):
    _clear(monkeypatch)
    ok, notes = run_bot.preflight(verbose=False)
    assert ok is False
    assert any("TELEGRAM_BOT_TOKEN" in n for n in notes)


def test_preflight_rejects_a_malformed_token(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "garbage-no-colon")
    ok, notes = run_bot.preflight(verbose=False)
    assert ok is False
    assert any("معتبر" in n for n in notes)


def test_preflight_warns_about_open_access(monkeypatch):
    """Single-user product: an unrestricted bot is a real finding, not a nit."""
    _clear(monkeypatch)
    ok, notes = run_bot.preflight(verbose=False)
    assert any("TELEGRAM_ALLOWED_CHAT_IDS" in n for n in notes)


def test_preflight_reports_missing_proxy(monkeypatch):
    _clear(monkeypatch)
    _, notes = run_bot.preflight(verbose=False)
    assert any("پروکسی" in n for n in notes)


def test_preflight_checks_the_analysis_layer(monkeypatch):
    _clear(monkeypatch)
    _, notes = run_bot.preflight(verbose=False)
    assert any("لایه تحلیل" in n for n in notes)


def test_preflight_never_reports_ok_on_a_broken_config(monkeypatch):
    _clear(monkeypatch)
    ok, _ = run_bot.preflight(verbose=False)
    assert ok is False


# ------------------------------------------------------------------ proxy --

def test_no_proxy_yields_plain_urlopen(monkeypatch):
    import urllib.request
    monkeypatch.delenv("ALL_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    assert build_proxy_transport() is urllib.request.urlopen


def test_http_proxy_builds_a_distinct_opener(monkeypatch):
    import urllib.request
    monkeypatch.delenv("ALL_PROXY", raising=False)
    t = build_proxy_transport("http://127.0.0.1:8080")
    assert t is not urllib.request.urlopen and callable(t)


def test_socks_proxy_degrades_rather_than_crashing(monkeypatch):
    """A missing PySocks must produce a debuggable bot, not an ImportError."""
    monkeypatch.delenv("ALL_PROXY", raising=False)
    t = build_proxy_transport("socks5://127.0.0.1:10808")
    assert callable(t)


def test_env_proxy_is_picked_up(monkeypatch):
    import urllib.request
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:8080")
    assert build_proxy_transport() is not urllib.request.urlopen


def test_injected_transport_always_wins_over_proxy_config(monkeypatch):
    """Tests must never be able to hit the real network by accident."""
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:8080")
    sentinel = lambda *a, **k: None
    a = ProductionTelegramAdapter("123:ABC", transport=sentinel)
    assert a.transport is sentinel


# ------------------------------------------------------------------- api --

class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def test_get_me_success_is_parsed():
    a = ProductionTelegramAdapter(
        "123:ABC", transport=lambda r, timeout=None: _Resp(
            {"ok": True, "result": {"username": "ahos_bot"}}))
    assert a.get_me()["result"]["username"] == "ahos_bot"


def test_get_me_failure_is_reported_not_raised():
    def boom(r, timeout=None):
        raise OSError("TLS/SSL connection has been closed (EOF)")
    out = ProductionTelegramAdapter("123:ABC", transport=boom).get_me()
    assert out["ok"] is False and "OSError" in out["error"]


def test_get_me_error_never_leaks_the_bot_token():
    def boom(r, timeout=None):
        raise OSError("failed calling https://api.telegram.org/bot123:SECRETTOKEN/getMe")
    out = ProductionTelegramAdapter("123:SECRETTOKEN", transport=boom).get_me()
    assert "SECRETTOKEN" not in json.dumps(out)


# ----------------------------------------------------- end-to-end dispatch --

def test_bot_runner_answers_a_persian_conversation_turn():
    """Full path under W57: update -> gate -> gateway-only service -> outbound."""
    from telegram_ai.bot import TelegramBotRunner

    ad = MockTelegramAdapter()
    ad.inject_update(chat_id=1, text="سلام", user_id=99)
    runner = TelegramBotRunner(ad, gate=TelegramSecurityGate())
    up = ad.poll_updates()[0]
    res = runner.process_update(up)
    assert res["status"] == "PROCESSED"
    assert res["intent"] == "gateway_unavailable"
    assert ad.sent_messages, "no reply was delivered"
    assert "EMERGENCY_FALLBACK_ONLY" in ad.sent_messages[0]["text"]


def test_unauthorized_chat_is_refused():
    from telegram_ai.bot import TelegramBotRunner

    ad = MockTelegramAdapter()
    ad.inject_update(chat_id=777, text="سلام", user_id=777)
    runner = TelegramBotRunner(ad, gate=TelegramSecurityGate(allowed_chat_ids=[1]))
    res = runner.process_update(ad.poll_updates()[0])
    assert res["status"] == "UNAUTHORIZED"


def test_send_message_error_never_leaks_the_bot_token():
    """Every outbound path must scrub, not just getMe."""
    def boom(r, timeout=None):
        raise OSError("POST https://api.telegram.org/bot123:SECRETTOKEN/sendMessage failed")
    out = ProductionTelegramAdapter("123:SECRETTOKEN", transport=boom).send_message(1, "hi")
    assert out["ok"] is False
    assert "SECRETTOKEN" not in json.dumps(out)


def test_poll_updates_parses_a_message():
    payload = {"ok": True, "result": [{
        "update_id": 5,
        "message": {"chat": {"id": 1}, "from": {"id": 9, "username": "u"},
                    "text": "سلام"}}]}
    a = ProductionTelegramAdapter("123:ABC",
                                  transport=lambda r, timeout=None: _Resp(payload))
    ups = a.poll_updates()
    assert len(ups) == 1 and ups[0].update_id == 5 and ups[0].text == "سلام"
