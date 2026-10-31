"""Safe Telegram commands: one chat, paper pause, no live switch."""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telegram_ai.adapter import MockTelegramAdapter, TelegramSecurityGate
from telegram_ai.bot import TelegramBotRunner
from telegram_ai.operator_commands import (
    DASHBOARD_FA,
    apply_armed_close,
    dispatch,
    mehrdad_chat_id,
    our_pause_hash,
)
from telegram_ai.service import TelegramDomainService

NOW = datetime(2026, 10, 31, 11, 0, tzinfo=timezone.utc)
_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def _code(text: str) -> str:
    found = re.search(r"\d{6}", text.translate(_EN))
    assert found is not None
    return found.group(0)


def _go(root: Path, text: str, *, chat: str = "777001", allow: str = "777001", now: datetime = NOW, publish: bool = False):
    return dispatch(root, chat, text, allow_raw=allow, now=now, publish=publish)


def test_only_the_first_numeric_id_is_the_owner():
    assert mehrdad_chat_id("777001, 888002") == "777001"
    assert mehrdad_chat_id("") is None
    assert mehrdad_chat_id("not-an-id, 42") == "42"


def test_other_chats_are_ignored_and_not_logged_with_an_id(tmp_path: Path):
    res = _go(tmp_path, "وضعیت", chat="424242")
    assert res is not None and res["status"] == "IGNORED"
    audit = (tmp_path / "reports" / "grok" / "PAPER" / "telegram_operator_audit.jsonl").read_text(encoding="utf-8")
    assert "424242" not in audit
    assert "777001" not in audit


def test_status_needs_no_code_and_blocked_work_stays_on_the_dashboard(tmp_path: Path):
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trader_status.json").write_text(json.dumps({
        "halted": False,
        "updated_at": "2026-10-31T10:55:00Z",
        "mark_to_market_equity_usd": 99.28,
        "open_positions": {"GC": {}},
        "paper_only": True,
    }), encoding="utf-8")
    status = _go(tmp_path, "وضعیت")
    assert status is not None and status["status"] == "OK"
    assert "۹۹٫۲۸" in status["text"]
    assert "کد" not in status["text"]
    blocked = _go(tmp_path, "پول واقعی را روشن کن")
    assert blocked is not None
    assert blocked["text"] == DASHBOARD_FA
    assert our_pause_hash(tmp_path) is None


def test_pause_and_resume_need_a_short_code(tmp_path: Path):
    issued = _go(tmp_path, "توقف موقت")
    assert issued is not None and issued["status"] == "CODE"
    code = _code(issued["text"])
    state = (tmp_path / "reports" / "grok" / "PAPER" / "telegram_operator_state.json").read_text(encoding="utf-8")
    assert code not in state
    assert our_pause_hash(tmp_path) is None
    done = _go(tmp_path, code)
    assert done is not None and "متوقف شد" in done["text"]
    assert our_pause_hash(tmp_path)
    again = _go(tmp_path, "ادامه", now=NOW + timedelta(seconds=5))
    resumed = _go(tmp_path, _code(again["text"]), now=NOW + timedelta(seconds=6))
    assert resumed is not None and "مجاز است" in resumed["text"]
    assert our_pause_hash(tmp_path) is None


def test_three_wrong_codes_lock_for_an_hour_and_alert(tmp_path: Path):
    _go(tmp_path, "توقف موقت")
    for step in range(2):
        bad = _go(tmp_path, "000000", now=NOW + timedelta(seconds=step + 1))
        assert bad is not None and bad["status"] == "BAD_CODE"
    locked = _go(tmp_path, "000000", now=NOW + timedelta(seconds=4), publish=True)
    assert locked is not None and locked["status"] == "LOCKED"
    public = json.loads((tmp_path / "reports" / "grok" / "PAPER" / "telegram_operator_public.json").read_text(encoding="utf-8"))
    assert public["negahban_alert"] is True
    assert public["judge"] == "NO_PROMOTION"
    later = _go(tmp_path, "وضعیت", now=NOW + timedelta(seconds=10))
    assert later is not None and later["status"] == "LOCKED"
    bus = (tmp_path / "reports" / "grok" / "PAPER" / "agent_bus.jsonl").read_text(encoding="utf-8")
    assert "Three wrong Telegram confirmation codes" in bus
    traces = json.loads((tmp_path / "reports" / "grok" / "PAPER" / "world_state.json").read_text(encoding="utf-8"))
    assert traces["sections"]["traces"]["telegram_operator"]["negahban_alert"] is True


def test_close_all_defers_while_the_trader_process_is_alive(tmp_path: Path, monkeypatch):
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_positions.json").write_text(json.dumps({
        "positions": {"GC": {"side": "LONG", "qty": 1, "entry_price": 10, "mark_price": 11, "desk": "LISTED_FUTURES"}}
    }), encoding="utf-8")
    monkeypatch.setattr("architecture.ai.telegram_llm_fallback._trader_process_alive", lambda: True)
    issued = _go(tmp_path, "بستن همه")
    closed = _go(tmp_path, _code(issued["text"]), now=NOW + timedelta(seconds=1))
    assert closed is not None and "نبست" in closed["text"]
    still = json.loads((paper / "paper_positions.json").read_text(encoding="utf-8"))
    assert "GC" in still["positions"]
    monkeypatch.setattr("architecture.ai.telegram_llm_fallback._trader_process_alive", lambda: False)
    result = apply_armed_close(tmp_path, inside_cycle=True)
    assert result["closed"] == 1
    after = json.loads((paper / "paper_positions.json").read_text(encoding="utf-8"))
    assert after["positions"] == {}
    assert "OPERATOR_TELEGRAM_CLOSE" in (paper / "paper_trades.jsonl").read_text(encoding="utf-8")


def test_runner_answers_status_before_the_gateway(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "telegram_ai.bot.dispatch",
        lambda root, chat_id, text, allow_raw=None: {
            "text": "معامله‌های کاغذی فعال است؛ کلید پول واقعی عمداً خاموش است.",
            "status": "OK",
            "command": "وضعیت",
        },
    )
    adapter = MockTelegramAdapter()
    runner = TelegramBotRunner(
        adapter,
        service=TelegramDomainService(ledger_db_path=str(tmp_path / "local.sqlite")),
        gate=TelegramSecurityGate(allowed_chat_ids=[777001], allow_open_access=False),
        allow_raw="777001",
        silent_unauthorized=True,
    )
    adapter.inject_update(chat_id=424242, text="وضعیت", user_id=424242)
    runner.process_pending_updates()
    assert adapter.sent_messages == []
    adapter.inject_update(chat_id=777001, text="وضعیت", user_id=777001)
    runner.process_pending_updates()
    assert "کلید پول واقعی عمداً خاموش است" in adapter.sent_messages[0]["text"]
    assert "موتور تحلیل خاموش" not in adapter.sent_messages[0]["text"]
