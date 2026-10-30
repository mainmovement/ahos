"""Telegram answers a free-form question from the paper file when models fail."""
from datetime import datetime, timezone
from pathlib import Path

from architecture.ai.telegram_llm_fallback import ETA, answer_question, error_class, is_bare_menu


def _quota(model: str) -> dict:
    return {
        "ok": False,
        "status": "QUOTA_EXHAUSTED",
        "reason_code": "HTTP_429_QUOTA",
        "parts": [],
        "attempts": [{
            "model": model,
            "status": "QUOTA_EXHAUSTED",
            "reason_code": "HTTP_429_QUOTA",
            "http_status": 429,
            "error_kind": "HTTPError",
        }],
    }


def test_failed_chain_answers_from_the_paper_file_and_alerts(tmp_path: Path) -> None:
    calls: list[str] = []
    pauses: list[float] = []

    def chat(request):
        model = request["models"][0]
        calls.append(model)
        return _quota(model)

    now = datetime(2026, 10, 30, 17, 30, tzinfo=timezone.utc)
    doc = answer_question(
        tmp_path,
        "چقدر مونده سودده بشه؟",
        chat=chat,
        local_ask=lambda _q: None,
        sleep=pauses.append,
        now=now,
    )
    assert calls == ["gemini-flash-latest", "gemini-flash-lite-latest"]
    assert pauses
    assert is_bare_menu(doc["text"]) is False
    assert "دقیق متوجه نشدم" not in doc["text"]
    assert ETA in doc["text"]
    assert "سرمایهٔ کاغذی" in doc["text"]
    assert doc["error_class"] == "quota_429"
    assert doc["source"] == "world_state"
    assert doc["negahban_alert"] is True
    health = (tmp_path / "reports" / "grok" / "PAPER" / "telegram_llm_health.json").read_text(encoding="utf-8")
    assert "quota_429" in health
    assert "AIza" not in health
    assert "api_key" not in health
    bus = (tmp_path / "reports" / "grok" / "PAPER" / "agent_bus.jsonl").read_text(encoding="utf-8")
    assert "AG-09" in bus and "ADVISE" in bus


def test_a_good_answer_is_cached(tmp_path: Path) -> None:
    calls = {"n": 0}

    def chat(request):
        calls["n"] += 1
        return {
            "ok": True,
            "status": "READY",
            "reason_code": "OK",
            "parts": [{"text": "سود کاغذی هنوز پایدار نشده است. شرط صادقانه: 30 fresh closes + DSR>0.95 + PBO<0.5"}],
            "attempts": [{"model": request["models"][0], "status": "READY", "reason_code": "OK", "http_status": 200, "error_kind": ""}],
        }

    now = datetime(2026, 10, 30, 17, 0, tzinfo=timezone.utc)
    first = answer_question(tmp_path, "چقدر مونده سودده بشه؟", chat=chat, local_ask=lambda _q: None, sleep=lambda _s: None, now=now)
    second = answer_question(tmp_path, "چقدر مونده سودده بشه؟", chat=chat, local_ask=lambda _q: None, sleep=lambda _s: None, now=now)
    assert calls["n"] == 1
    assert first["source"] == "gemini-flash-latest"
    assert second["source"] == "cache"
    assert second["text"] == first["text"]


def test_a_server_error_is_network_and_a_timeout_exception_is_timeout() -> None:
    assert error_class("UNAVAILABLE", "HTTP_503_SERVER_OR_TIMEOUT", 503, "HTTPError") == "network"
    assert error_class("UNAVAILABLE", "NETWORK", None, "TimeoutError") == "timeout"
    assert error_class("QUOTA_EXHAUSTED", "HTTP_429_QUOTA", 429, "HTTPError") == "quota_429"


def test_a_new_outage_after_a_recovery_does_not_use_the_old_clock(tmp_path: Path) -> None:
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "telegram_llm_health.json").write_text(
        '{"schema":"ahos.telegram_llm_health.v1","down_since_utc":null,"answered_from":"gemini-flash-lite-latest"}',
        encoding="utf-8",
    )

    def chat(request):
        return _quota(request["models"][0])

    now = datetime(2026, 10, 30, 17, 30, tzinfo=timezone.utc)
    doc = answer_question(tmp_path, "چقدر مونده سودده بشه؟", chat=chat, local_ask=lambda _q: None, sleep=lambda _s: None, now=now)
    assert doc["negahban_alert"] is False
    health = (paper / "telegram_llm_health.json").read_text(encoding="utf-8")
    assert "2026-10-30T17:30:00Z" in health
    assert "2026-10-30T16:03:00Z" not in health.split("down_since_utc")[1][:40]


def test_timeout_retries_once_then_uses_local(tmp_path: Path) -> None:
    calls = {"n": 0}

    def chat(request):
        calls["n"] += 1
        return {
            "ok": False,
            "status": "UNAVAILABLE",
            "reason_code": "NETWORK",
            "parts": [],
            "attempts": [{
                "model": request["models"][0],
                "status": "UNAVAILABLE",
                "reason_code": "NETWORK",
                "http_status": None,
                "error_kind": "URLError:TimeoutError",
            }],
        }

    doc = answer_question(
        tmp_path,
        "سوال",
        chat=chat,
        local_ask=lambda _q: "از مدل محلی: هنوز سود پایدار نیست.",
        sleep=lambda _s: None,
        now=datetime(2026, 10, 30, 16, 10, tzinfo=timezone.utc),
        publish=False,
    )
    assert calls["n"] >= 2
    assert doc["source"] == "local"
    assert "مدل محلی" in doc["text"]
    assert doc["negahban_alert"] is False
