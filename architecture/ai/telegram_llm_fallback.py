"""Telegram free-form fallback. Paper status only. No key is stored or printed.

The chain is Gemini flash, then flash-lite, then a local small model when one
is already running. A timeout or a dropped connection is retried once after a
pause. Quota and a bad model name move to the next model. When every model
fails, the reply is a fixed Persian reading of the shared world-state.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore

HEALTH_REL = Path("reports") / "grok" / "PAPER" / "telegram_llm_health.json"
CACHE_REL = Path("reports") / "grok" / "PAPER" / "telegram_llm_cache.json"
REPORTED_TEHRAN = "2026-10-30T19:33:00+03:30"
REPORTED_UTC = "2026-10-30T16:03:00Z"
CHAIN = ("gemini-flash-latest", "gemini-flash-lite-latest")
CACHE_S = 600
BACKOFF_S = (0.6, 1.8)
ETA = "30 fresh closes + DSR>0.95 + PBO<0.5"
_SMALL = re.compile(r"(tiny|mini|small|0\.5b|1b|1\.5b|3b)", re.I)
_SECRET = re.compile(r"(AIza[0-9A-Za-z_\-]{8,}|Bearer\s+\S+|api[_-]?key\s*[:=]\s*\S+)", re.I)
_MENU = ("دقیق متوجه نشدم", "یکی از این‌ها را امتحان کن")
_DESK_FA = {
    "ASIA_EQUITIES": "سهام آسیا",
    "US_EQUITIES": "سهام آمریکا",
    "EU_EQUITIES": "سهام اروپا",
    "CRYPTO": "رمزارز",
    "CRYPTO_FUTURES": "فیوچرز رمزارز",
    "OIL": "نفت",
    "GOLD": "طلا",
    "FOREX": "ارز",
    "LISTED_FUTURES": "فیوچرز فهرست‌شده",
}
_DIGITS = str.maketrans("0123456789.-", "۰۱۲۳۴۵۶۷۸۹٫−")


def is_bare_menu(text: str) -> bool:
    return any(piece in (text or "") for piece in _MENU)


def _needs_paper_status(question: str) -> bool:
    """A profit or readiness question is answered from the paper file, not invented."""
    text = question or ""
    return any(word in text for word in ("سود", "مونده", "آمادگی"))


def error_class(status: str, reason: str, http_status: int | None, kind: str) -> str:
    """One of quota_429, network, model_name, timeout, auth, other. No body text."""
    reason_l = (reason or "").lower()
    kind_l = (kind or "").lower()
    if http_status == 429 or status == "QUOTA_EXHAUSTED" or "429" in reason_l or "quota" in reason_l:
        return "quota_429"
    if status == "MODEL_UNAVAILABLE" or "model_not_found" in reason_l or reason_l.startswith("model"):
        return "model_name"
    if "timeouterror" in kind_l:
        return "timeout"
    if status == "AUTH_FAILED" or reason_l.startswith("auth"):
        return "auth"
    if (
        status in {"UNAVAILABLE", "DEGRADED"}
        or (isinstance(http_status, int) and http_status >= 500)
        or "urlerror" in kind_l
        or "network" in reason_l
    ):
        return "network"
    return "other"


def _utc(moment: datetime | None = None) -> str:
    now = moment or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(stamp: str | None) -> datetime | None:
    if not isinstance(stamp, str) or not stamp:
        return None
    try:
        return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _scrub(text: str) -> str:
    return _SECRET.sub("[redacted]", text or "")


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _fa(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".translate(_DIGITS)


def world_state_reply(root: Path, *, now: datetime | None = None) -> str:
    """Equity, readiness, soak, paused desks, blockers, and the registered ETA rule."""
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    from architecture.mission.mehrdad_status import build_mehrdad_status

    status = build_mehrdad_status(root)
    equity = status.get("equity_usd")
    if isinstance(equity, (int, float)) and not isinstance(equity, bool):
        equity_line = f"سرمایهٔ کاغذی الان {_fa(float(equity), 2)} دلار است."
    else:
        equity_line = "سرمایهٔ کاغذی الان در پرونده نیست."
    pct = status.get("readiness_pct")
    if isinstance(pct, (int, float)) and not isinstance(pct, bool):
        ready_line = f"آمادگی پول واقعی {_fa(float(pct), 0)} درصد است."
    else:
        ready_line = "آمادگی پول واقعی در پرونده نیست."
    soak = _read(root / "reports" / "grok" / "M13_SOAK" / "soak_status.json")
    started = _parse(soak.get("window_started_utc") if isinstance(soak.get("window_started_utc"), str) else None)
    if started is None:
        soak_line = "ساعت آزمون پیوسته در پرونده نیست."
    else:
        hours = round((moment - started).total_seconds() / 3600.0, 1)
        soak_line = f"آزمون پیوسته حدود {_fa(hours, 1)} ساعت از ۷۲ ساعت را آمده است."
    pause = _read(root / "reports" / "grok" / "PAPER" / "desk_pause.json")
    names = [
        _DESK_FA.get(str(name), "یک میز")
        for name in (pause.get("paused_desks") or [])
        if isinstance(name, str)
    ]
    desk_line = "میز متوقف در پرونده نیست." if not names else "میزهای متوقف: " + "، ".join(names) + "."
    blockers = [str(item) for item in (status.get("missing_fa") or []) if str(item).strip()]
    block_line = "مانده‌ها: " + " ".join(blockers[:3]) if blockers else "مانده‌ای در پرونده ثبت نشده است."
    return "\n".join([
        "سود کاغذی هنوز پایدار نشده است.",
        equity_line,
        ready_line,
        soak_line,
        desk_line,
        block_line,
        f"شرط صادقانه: {ETA}",
        "این جواب از پروندهٔ مشترک خوانده شده و معامله‌ای باز نمی‌کند.",
    ])


def _default_chat(request: dict[str, Any]) -> dict[str, Any]:
    from architecture.ai.gemini_chat import chat_step

    return chat_step(request)


def _pick_small(models: list[dict[str, Any]]) -> str | None:
    names = [str(row.get("name") or "") for row in models if isinstance(row, dict)]
    for name in names:
        if name and _SMALL.search(name):
            return name
    return None


def _default_local(question: str) -> str | None:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            doc = json.loads(resp.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
    name = _pick_small(doc.get("models") if isinstance(doc, dict) else [])
    if not name:
        return None
    body = json.dumps({
        "model": name,
        "prompt": question[:500],
        "stream": False,
        "options": {"num_predict": 180},
    }).encode("utf-8")
    try:
        call = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(call, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
    text = _scrub(str((payload or {}).get("response") or "")).strip()
    return text or None


def _cache_get(root: Path, key: str, now: datetime) -> str | None:
    doc = _read(root / CACHE_REL)
    row = doc.get(key) if isinstance(doc.get(key), dict) else None
    if not row:
        return None
    stamp = _parse(row.get("at") if isinstance(row.get("at"), str) else None)
    if stamp is None or (now - stamp).total_seconds() > CACHE_S:
        return None
    text = row.get("text")
    return text if isinstance(text, str) and text.strip() else None


def _cache_put(root: Path, key: str, text: str, now: datetime) -> None:
    path = root / CACHE_REL
    doc = _read(path)
    doc[key] = {"at": _utc(now), "text": _scrub(text)[:2000]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _write_health(root: Path, doc: dict[str, Any]) -> None:
    path = root / HEALTH_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _publish(root: Path, health: dict[str, Any]) -> None:
    store = WorldStateStore(root)
    prev = store.read()
    traces = dict((prev.get("sections") or {}).get("traces") or {})
    traces["telegram_llm"] = {
        "error_class": health.get("error_class"),
        "answered_from": health.get("answered_from"),
        "down_since_utc": health.get("down_since_utc"),
        "negahban_alert": health.get("negahban_alert") is True,
        "paper_only": True,
    }
    store.commit({"traces": traces}, {"TELEGRAM_LLM": "fallback"})
    if health.get("negahban_alert") is True:
        MessageBus(root).deliver(AgentMessage(
            sender="AG-33",
            receiver="AG-09",
            evidence=("reports/grok/PAPER/telegram_llm_health.json",),
            claim="Telegram LLM has been down for more than one hour. The reply is paper status only.",
            confidence=0.4,
            required_action=RequiredAction.ADVISE,
        ))
    else:
        MessageBus(root).deliver(AgentMessage(
            sender="AG-33",
            receiver="AG-09",
            evidence=("reports/grok/PAPER/telegram_llm_health.json",),
            claim="Telegram free-form reply used the model chain or the paper file. No trade was opened.",
            confidence=0.3,
            required_action=RequiredAction.OBSERVE,
        ))


def answer_question(
    root: Path,
    question: str,
    *,
    chat: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    local_ask: Callable[[str], str | None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: datetime | None = None,
    publish: bool = True,
) -> dict[str, Any]:
    """Retry, then the next model, then the paper file. Never returns the bare menu."""
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    key = hashlib.sha256(question.strip().encode("utf-8")).hexdigest()
    cached = _cache_get(root, key, moment)
    if cached and not is_bare_menu(cached) and not (_needs_paper_status(question) and ETA not in cached):
        return {"text": cached, "source": "cache", "error_class": None, "attempts": [], "negahban_alert": False}

    caller = chat or _default_chat
    attempts: list[dict[str, Any]] = []
    text: str | None = None
    source = "world_state"
    stop_gemini = False
    model_ok = False
    for index, model in enumerate(CHAIN):
        if stop_gemini:
            break
        for attempt_no in (1, 2):
            raw = caller({
                "system": "فقط فارسی. معامله باز نکن. عدد تازه نساز.",
                "contents": [{"role": "user", "parts": [{"text": question[:500]}]}],
                "models": [model],
                "timeout_ms": 4000,
            })
            if not isinstance(raw, dict):
                raw = {}
            row = (raw.get("attempts") or [{}])[-1] if isinstance(raw.get("attempts"), list) else {}
            if not isinstance(row, dict):
                row = {}
            status = str((raw or {}).get("status") or row.get("status") or "")
            reason = str((raw or {}).get("reason_code") or row.get("reason_code") or "")
            http = row.get("http_status")
            http_i = int(http) if isinstance(http, int) else None
            kind = str(row.get("error_kind") or "")
            klass = error_class(status, reason, http_i, kind)
            attempts.append({
                "model": model,
                "error_class": klass if not raw.get("ok") else None,
                "http_status": http_i,
                "reason_code": reason[:80],
                "error_kind": kind[:80],
            })
            if raw.get("ok"):
                parts = raw.get("parts") or []
                joined = _scrub("".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))).strip()
                if joined and not is_bare_menu(joined):
                    model_ok = True
                    if _needs_paper_status(question) and ETA not in joined:
                        attempts[-1]["error_class"] = "ungrounded"
                    else:
                        text = joined
                        source = model
                        break
            if klass == "auth":
                stop_gemini = True
                break
            if klass in {"timeout", "network"} and attempt_no == 1:
                sleep(BACKOFF_S[min(index, len(BACKOFF_S) - 1)])
                continue
            if attempt_no == 1 and klass in {"quota_429", "model_name", "other"}:
                sleep(BACKOFF_S[0])
            break
        if text:
            break
        if not stop_gemini and index + 1 < len(CHAIN):
            sleep(BACKOFF_S[min(index, len(BACKOFF_S) - 1)])

    if text is None:
        local = (local_ask or _default_local)(question)
        if local and not is_bare_menu(local):
            cleaned = _scrub(local)
            if _needs_paper_status(question) and ETA not in cleaned:
                attempts.append({"model": "local", "error_class": "ungrounded", "http_status": None, "reason_code": "UNGROUNDED", "error_kind": ""})
            else:
                text = cleaned
                source = "local"
                attempts.append({"model": "local", "error_class": None, "http_status": None, "reason_code": "", "error_kind": ""})
        elif local is None:
            attempts.append({"model": "local", "error_class": "network", "http_status": None, "reason_code": "LOCAL_ABSENT", "error_kind": ""})

    if text is None:
        text = world_state_reply(root, now=moment)
        source = "world_state"

    classes = [row["error_class"] for row in attempts if row.get("error_class") and row["error_class"] != "ungrounded"]
    primary = classes[0] if classes else None
    prev = _read(root / HEALTH_REL)
    reported = _parse(REPORTED_UTC)
    if source == "world_state" and not model_ok:
        prior = prev.get("down_since_utc") if isinstance(prev.get("down_since_utc"), str) else None
        seen_before = prev.get("schema") == "ahos.telegram_llm_health.v1"
        if prior:
            down_since = prior
        elif seen_before:
            down_since = _utc(moment)
        elif reported is not None and 0 <= (moment - reported).total_seconds() <= 6 * 3600:
            down_since = REPORTED_UTC
        else:
            down_since = _utc(moment)
    else:
        down_since = None
    down_at = _parse(down_since)
    alert = bool(down_at and (moment - down_at).total_seconds() > 3600 and prev.get("alerted_for") != down_since)
    health = {
        "schema": "ahos.telegram_llm_health.v1",
        "paper_only": True,
        "incident_tehran": REPORTED_TEHRAN,
        "incident_utc": REPORTED_UTC,
        "historical_log": "ABSENT",
        "error_class": primary,
        "classified_by": "live_probe",
        "attempts": attempts,
        "answered_from": source,
        "down_since_utc": down_since,
        "negahban_alert": alert,
        "alerted_for": down_since if alert else prev.get("alerted_for"),
        "generated_at": _utc(moment),
    }
    _write_health(root, health)
    if source in {CHAIN[0], CHAIN[1], "local"}:
        _cache_put(root, key, text, moment)
    if publish:
        _publish(root, health)
    return {
        "text": text,
        "source": source,
        "error_class": primary,
        "attempts": attempts,
        "negahban_alert": alert,
    }
