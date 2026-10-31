"""Safe Telegram commands for one allowlisted chat. Paper only.

The chat id comes from the first value of TELEGRAM_ALLOWED_CHAT_IDS already
loaded in the process. This module never opens an env file and never records
the id or a confirmation code. A pause is a HALT on the mission ledger the
running paper cycle already reads. It does not flatten open paper positions.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore

PAUSE_SOURCE = "telegram_paper_pause"
LEDGER_REL = Path("data") / "mission_ledger" / "mission_ledger.jsonl"
STATE_REL = Path("reports") / "grok" / "PAPER" / "telegram_operator_state.json"
AUDIT_REL = Path("reports") / "grok" / "PAPER" / "telegram_operator_audit.jsonl"
PUBLIC_REL = Path("reports") / "grok" / "PAPER" / "telegram_operator_public.json"
POSITIONS_REL = Path("reports") / "grok" / "PAPER" / "paper_positions.json"
TRADES_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"
CODE_TTL_S = 120
LOCK_S = 3600
MAX_BAD = 3
RATE_MAX = 10
RATE_WINDOW_S = 60
DASHBOARD_FA = "این کار فقط از داشبورد محلی انجام می‌شود."
_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_COMMANDS = ("گزارش الان", "وضعیت", "توقف موقت", "ادامه", "بستن همه")
_NEEDS_CODE = frozenset({"توقف موقت", "ادامه", "بستن همه"})
_LATIN_BLOCK = re.compile(r"\b(live|promote|shell|hold|exec)\b", re.I)
_PERSIAN_BLOCK = (
    "پول واقعی",
    "معامله واقعی",
    "کلید زنده",
    "زنده کن",
    "ارتقا",
    "ترفیع",
    "پرچم",
    "وزن",
    "دروازه",
    "گیت",
    "شل",
    "ترمینال",
    "اجرا کن",
)


def mehrdad_chat_id(raw: str | None = None) -> str | None:
    """First numeric id in the allowlist. Later ids are not owners."""
    if raw is None:
        raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS")
    for part in (raw or "").split(","):
        item = part.strip()
        if item.isdigit():
            return item
    return None


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


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _write(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _state(root: Path) -> dict[str, Any]:
    doc = _read(root / STATE_REL)
    doc.setdefault("bad_codes", 0)
    doc.setdefault("attempts", [])
    return doc


def _save_state(root: Path, doc: dict[str, Any]) -> None:
    clean = {k: v for k, v in doc.items() if k != "code"}
    _write(root / STATE_REL, clean)


def _audit(root: Path, row: dict[str, Any]) -> None:
    text = json.dumps(row, ensure_ascii=False)
    from architecture.security.negahban import scan

    if scan(text).level == "HALT":
        return
    path = root / AUDIT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")


def _public(root: Path, *, paused: bool, locked: bool, command: str, alert: bool) -> None:
    _write(root / PUBLIC_REL, {
        "schema": "ahos.telegram_operator_public.v1",
        "paper_only": True,
        "live_switch": False,
        "paused_new_entries": paused,
        "locked": locked,
        "last_command": command,
        "negahban_alert": alert,
        "judge": "NO_PROMOTION",
        "dashboard_only": [
            "live_switch",
            "tier_promotion",
            "hold_flags",
            "weights",
            "gates",
            "shell",
        ],
    })


def _publish(root: Path, *, command: str, paused: bool, alert: bool) -> None:
    store = WorldStateStore(root)
    prev = store.read()
    sections = prev.get("sections") or {}
    traces = dict(sections.get("traces") or {})
    traces["telegram_operator"] = {
        "command": command,
        "paused_new_entries": paused,
        "negahban_alert": alert,
        "judge": "NO_PROMOTION",
        "paper_only": True,
        "live_switch": False,
    }
    kill = dict(sections.get("kill_switch") or {})
    kill["telegram_paper_pause"] = {
        "paused": paused,
        "source": PAUSE_SOURCE,
        "paper_only": True,
    }
    store.commit({"traces": traces, "kill_switch": kill}, {"traces": "AG-33", "kill_switch": "AG-08"})
    claim = (
        "Three wrong Telegram confirmation codes locked operator commands for one hour."
        if alert
        else "A paper-only Telegram command was logged. It does not promote or arm live trading."
    )
    MessageBus(root).deliver(AgentMessage(
        sender="AG-33",
        receiver="AG-08" if not alert else "AG-09",
        evidence=("reports/grok/PAPER/telegram_operator_audit.jsonl",),
        claim=claim,
        confidence=0.4 if alert else 0.6,
        required_action=RequiredAction.ADVISE if alert else RequiredAction.OBSERVE,
    ))


def _ledger(root: Path):
    from architecture.mission.ledger import MissionLedger

    path = root / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    return MissionLedger(path)


def our_pause_hash(root: Path) -> str | None:
    try:
        halted, entry = _ledger(root).halted()
    except Exception:
        return None
    if not halted or not isinstance(entry, dict):
        return None
    payload = entry.get("payload") or {}
    if payload.get("source") != PAUSE_SOURCE:
        return None
    digest = entry.get("entry_hash")
    return digest if isinstance(digest, str) else None


def pause_new_entries(root: Path) -> tuple[bool, str]:
    """HALT new paper risk. Open positions stay open. A foreign halt is left alone."""
    try:
        ledger = _ledger(root)
        halted, entry = ledger.halted()
    except Exception:
        return False, "توقف ثبت نشد و ورودهای کاغذی عوض نشدند."
    if halted:
        payload = (entry or {}).get("payload") or {}
        if payload.get("source") == PAUSE_SOURCE:
            return True, "ورود تازهٔ کاغذی از قبل متوقف است. موقعیت‌های باز بسته نشدند."
        return False, "یک توقف دیگر روی دفتر است و این فرمان آن را برنداشت."
    try:
        ledger.halt(
            PAUSE_SOURCE,
            "operator paused new paper entries",
            detail="open positions stay open",
            agent="AG:33",
        )
    except Exception:
        return False, "توقف ثبت نشد و ورودهای کاغذی عوض نشدند."
    return True, "ورود تازهٔ کاغذی متوقف شد. موقعیت‌های باز بسته نشدند. کلید پول واقعی همچنان خاموش است."


def resume_entries(root: Path) -> tuple[bool, str]:
    """Release only the Telegram paper pause. Any other halt stays."""
    try:
        ledger = _ledger(root)
        halted, entry = ledger.halted()
    except Exception:
        return False, "ادامه ثبت نشد و وضعیت دفتر عوض نشد."
    if not halted:
        return True, "ورود تازهٔ کاغذی مجاز است. کلید پول واقعی همچنان خاموش است."
    payload = (entry or {}).get("payload") or {}
    if payload.get("source") != PAUSE_SOURCE:
        return False, "توقف روی دفتر از این گفتگو نیست و برداشته نشد."
    digest = entry.get("entry_hash")
    if not isinstance(digest, str):
        return False, "ادامه ثبت نشد و وضعیت دفتر عوض نشد."
    try:
        ledger.clear_halt(digest, note="operator resumed paper entries", agent="AG:33")
    except Exception:
        return False, "ادامه ثبت نشد و توقف کاغذی سر جایش ماند."
    return True, "ورود تازهٔ کاغذی دوباره مجاز است. کلید پول واقعی همچنان خاموش است."


def apply_armed_close(root: Path, *, inside_cycle: bool = False) -> dict[str, Any]:
    """Flatten the paper book only when this process owns the next read.

    A Telegram request while the paper cycle is already running leaves the
    flag armed. That process still has the book in memory, so this call does
    not edit it.
    """
    root = Path(root)
    doc = _state(root)
    if doc.get("close_armed") is not True:
        return {"closed": 0, "armed": False, "deferred": False}
    if not inside_cycle:
        from architecture.ai.telegram_llm_fallback import _trader_process_alive

        if _trader_process_alive():
            return {"closed": 0, "armed": True, "deferred": True}
    path = root / POSITIONS_REL
    book = _read(path)
    positions = book.get("positions") if isinstance(book.get("positions"), dict) else {}
    closed = 0
    kept: dict[str, Any] = {}
    trades = root / TRADES_REL
    trades.parent.mkdir(parents=True, exist_ok=True)
    now = _utc()
    for symbol, pos in positions.items():
        if not isinstance(pos, dict):
            kept[symbol] = pos
            continue
        try:
            qty = float(pos["qty"])
            entry = float(pos["entry_price"])
            mark = float(pos.get("mark_price") or entry)
            side = str(pos.get("side") or "")
        except (KeyError, TypeError, ValueError):
            kept[symbol] = pos
            continue
        direction = 1.0 if side == "LONG" else -1.0 if side == "SHORT" else None
        if direction is None or qty <= 0 or entry <= 0:
            kept[symbol] = pos
            continue
        row = {
            "event": "CLOSE",
            "symbol": symbol,
            "desk": pos.get("desk"),
            "side": side,
            "reason": "OPERATOR_TELEGRAM_CLOSE",
            "paper_only": True,
            "entry_price": entry,
            "fill_price": mark,
            "qty": qty,
            "opened_at": pos.get("opened_at"),
            "closed_at": now,
            "realized_pnl_usd": round((mark - entry) * qty * direction, 4),
        }
        with trades.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        closed += 1
    book["positions"] = kept
    _write(path, book)
    doc["close_armed"] = bool(kept)
    _save_state(root, doc)
    return {"closed": closed, "armed": bool(kept), "deferred": False}


def _classify(text: str) -> tuple[str | None, str | None]:
    folded = (text or "").strip().translate(_EN)
    for command in _COMMANDS:
        if folded == command:
            return command, None
        prefix = command + " "
        if folded.startswith(prefix):
            rest = folded[len(prefix):].strip()
            if re.fullmatch(r"\d{6}", rest):
                return command, rest
            return "blocked", None
    if re.fullmatch(r"\d{6}", folded):
        return "confirm", folded
    lowered = folded.lower()
    if _LATIN_BLOCK.search(lowered) or any(phrase in folded for phrase in _PERSIAN_BLOCK):
        return "blocked", None
    return None, None


def _issue(doc: dict[str, Any], command: str, now: datetime) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(8)
    doc["pending_command"] = command
    doc["code_salt"] = salt
    doc["code_sha256"] = hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()
    doc["code_expires"] = _utc(now + timedelta(seconds=CODE_TTL_S))
    return code


def _code_ok(doc: dict[str, Any], code: str, now: datetime) -> bool:
    salt = doc.get("code_salt")
    digest = doc.get("code_sha256")
    expires = _parse(doc.get("code_expires") if isinstance(doc.get("code_expires"), str) else None)
    if not isinstance(salt, str) or not isinstance(digest, str) or expires is None:
        return False
    if now > expires:
        return False
    check = hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(check, digest)


def _locked(doc: dict[str, Any], now: datetime) -> bool:
    until = _parse(doc.get("lock_until") if isinstance(doc.get("lock_until"), str) else None)
    return until is not None and now < until


def _rate_limited(doc: dict[str, Any], now: datetime) -> bool:
    window = []
    for stamp in doc.get("attempts") or []:
        moment = _parse(stamp if isinstance(stamp, str) else None)
        if moment is not None and (now - moment).total_seconds() <= RATE_WINDOW_S:
            window.append(_utc(moment))
    doc["attempts"] = window
    return len(window) >= RATE_MAX


def _note_attempt(doc: dict[str, Any], now: datetime) -> None:
    attempts = list(doc.get("attempts") or [])
    attempts.append(_utc(now))
    doc["attempts"] = attempts[-RATE_MAX:]


def _status_text(root: Path, now: datetime) -> str:
    from architecture.ai.telegram_llm_fallback import world_state_reply

    text = world_state_reply(root, now=now)
    if our_pause_hash(root):
        text += "\nورود تازهٔ کاغذی با فرمان متوقف است."
    return text


def dispatch(
    root: Path,
    chat_id: int | str,
    text: str,
    *,
    allow_raw: str | None = None,
    now: datetime | None = None,
    publish: bool = True,
) -> dict[str, Any] | None:
    """Handle one safe command. None means the text is ordinary chat."""
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    command, code = _classify(text)
    if command is None:
        return None
    owner = mehrdad_chat_id(allow_raw)
    if owner is None or str(chat_id) != owner:
        _audit(root, {"ts": _utc(moment), "event": "ignored", "reason": "not_allowlisted"})
        return {"text": "", "status": "IGNORED", "command": command, "handled": True}
    doc = _state(root)
    if _locked(doc, moment):
        _audit(root, {"ts": _utc(moment), "event": "locked", "command": command})
        return {
            "text": "به‌خاطر سه کد نادرست، فرمان‌ها تا یک ساعت قفل است.",
            "status": "LOCKED",
            "command": command,
            "handled": True,
        }
    if command == "confirm":
        command = str(doc.get("pending_command") or "")
        if command not in _NEEDS_CODE:
            return None
    if _rate_limited(doc, moment):
        _save_state(root, doc)
        _audit(root, {"ts": _utc(moment), "event": "rate_limited", "command": command})
        return {
            "text": "فرمان‌ها در این دقیقه زیاد شده‌اند. کمی بعد دوباره بفرست.",
            "status": "RATE_LIMITED",
            "command": command,
            "handled": True,
        }
    _note_attempt(doc, moment)
    if command == "blocked":
        _save_state(root, doc)
        _audit(root, {"ts": _utc(moment), "event": "blocked", "command": "blocked"})
        _public(root, paused=our_pause_hash(root) is not None, locked=False, command="blocked", alert=False)
        return {"text": DASHBOARD_FA, "status": "BLOCKED", "command": "blocked", "handled": True}
    if command in ("گزارش الان", "وضعیت"):
        if command == "گزارش الان":
            from architecture.mission.mehrdad_digest import compose_mehrdad_digest

            reply = compose_mehrdad_digest(root, now=moment)
        else:
            reply = _status_text(root, moment)
        _save_state(root, doc)
        _audit(root, {"ts": _utc(moment), "event": "read", "command": command})
        if publish:
            try:
                _publish(root, command=command, paused=our_pause_hash(root) is not None, alert=False)
            except Exception:
                pass
        _public(root, paused=our_pause_hash(root) is not None, locked=False, command=command, alert=False)
        return {"text": reply, "status": "OK", "command": command, "handled": True}
    if command in _NEEDS_CODE and code is None:
        issued = _issue(doc, command, moment)
        _save_state(root, doc)
        _audit(root, {"ts": _utc(moment), "event": "code_sent", "command": command})
        shown = issued.translate(_FA)
        return {
            "text": f"این کد را تا دو دقیقه برگردان: {shown}",
            "status": "CODE",
            "command": command,
            "handled": True,
        }
    if not _code_ok(doc, code or "", moment):
        doc["bad_codes"] = int(doc.get("bad_codes") or 0) + 1
        alert = False
        reply = "کد نادرست است یا مهلت دو دقیقه‌اش گذشته."
        if doc["bad_codes"] >= MAX_BAD:
            from datetime import timedelta

            doc["lock_until"] = _utc(moment + timedelta(seconds=LOCK_S))
            doc["bad_codes"] = 0
            doc["pending_command"] = None
            alert = True
            reply = "به‌خاطر سه کد نادرست، فرمان‌ها تا یک ساعت قفل است."
        _save_state(root, doc)
        _audit(root, {"ts": _utc(moment), "event": "bad_code", "command": command, "negahban_alert": alert})
        _public(root, paused=our_pause_hash(root) is not None, locked=alert, command=command, alert=alert)
        if publish:
            try:
                _publish(root, command=command, paused=our_pause_hash(root) is not None, alert=alert)
            except Exception:
                pass
        return {"text": reply, "status": "LOCKED" if alert else "BAD_CODE", "command": command, "handled": True}
    doc["bad_codes"] = 0
    doc["pending_command"] = None
    doc["code_sha256"] = None
    if command == "توقف موقت":
        ok, reply = pause_new_entries(root)
    elif command == "ادامه":
        ok, reply = resume_entries(root)
    else:
        doc["close_armed"] = True
        _save_state(root, doc)
        result = apply_armed_close(root)
        doc = _state(root)
        if result.get("deferred"):
            ok, reply = True, "درخواست بستن کاغذی ثبت شد. فرآیند در حال اجرا دفتر را در حافظه دارد، پس این فراخوان موقعیت‌ها را نبست."
        elif result.get("closed"):
            ok, reply = True, "موقعیت‌های کاغذی بسته‌شدنی بسته شدند. کلید پول واقعی همچنان خاموش است."
        else:
            ok, reply = False, "موقعیت کاغذیِ قابل بستن در پرونده نبود."
    _save_state(root, doc)
    _audit(root, {"ts": _utc(moment), "event": "executed" if ok else "refused", "command": command})
    paused = our_pause_hash(root) is not None
    _public(root, paused=paused, locked=False, command=command, alert=False)
    if publish:
        try:
            _publish(root, command=command, paused=paused, alert=False)
        except Exception:
            pass
    return {"text": reply, "status": "OK" if ok else "REFUSED", "command": command, "handled": True}
