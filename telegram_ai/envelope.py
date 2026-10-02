#!/usr/bin/env python3
"""AHOS Telegram edge hardening primitives (GM-02, offline / no-credential).

Telegram is an interaction EDGE (AGENTS.md). Nothing here scores, decides,
or grants capability. These helpers only make the edge accountable:

  * ``ENVELOPE_SCHEMA`` / ``build_update_envelope`` - a versioned, explicit
    description of one inbound update (who, where, which update, how long).
  * ``ReplayGuard`` - rejects a Telegram ``update_id`` that was already
    processed, or that is malformed, so a replayed / duplicated delivery is
    never dispatched twice.
  * ``TelegramAuditLog`` - append-only audit records. Records carry hashed
    chat/user identifiers, the message length and a SHA-256 of the text -
    never the raw text, never a token.

All three are pure / in-memory by default. A file sink is opt-in (explicit
path), so importing or constructing them never writes evidence.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

ENVELOPE_SCHEMA = "ahos.telegram.update_envelope.v1"
AUDIT_SCHEMA = "ahos.telegram.audit.v1"

# Statuses the runner may emit. Kept closed so audit consumers can validate.
AUDIT_STATUSES = frozenset({
    "PROCESSED",
    "UNAUTHORIZED",
    "RATE_LIMITED",
    "DUPLICATE_REJECTED",
    "INVALID_UPDATE_REJECTED",
})


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_identifier(value: Any) -> str:
    """Stable, non-reversible reference for a chat/user id (audit only).

    Empty / missing ids hash to the literal ``"UNKNOWN"`` so an absent sender
    is visible instead of silently looking like a real principal.
    """
    raw = "" if value is None else str(value).strip()
    if not raw:
        return "UNKNOWN"
    return "sha256:" + _sha256_hex("ahos.telegram.id:" + raw)[:16]


def _valid_update_id(update_id: Any) -> bool:
    # bool is an int subclass; True/False are not Telegram update ids.
    return isinstance(update_id, int) and not isinstance(update_id, bool) and update_id > 0


def build_update_envelope(update: Any) -> dict[str, Any]:
    """Describe one inbound update without leaking its content.

    ``sender_user_id`` / ``chat_id`` are the raw Telegram ids as strings (the
    gateway needs a principal to attribute the request to); ``*_ref`` fields
    are the hashed forms used for audit.
    """
    text = getattr(update, "text", "") or ""
    user_id = getattr(update, "user_id", "")
    chat_id = getattr(update, "chat_id", "")
    return {
        "schema": ENVELOPE_SCHEMA,
        "channel": "telegram",
        "update_id": getattr(update, "update_id", None),
        "update_id_valid": _valid_update_id(getattr(update, "update_id", None)),
        "chat_id": "" if chat_id is None else str(chat_id),
        "sender_user_id": "" if user_id is None else str(user_id),
        "chat_ref": hash_identifier(chat_id),
        "sender_ref": hash_identifier(user_id),
        "is_command": bool(getattr(update, "is_command", False)),
        "text_len": len(text),
        "text_sha256": _sha256_hex(text),
        "received_ts": float(getattr(update, "timestamp", 0.0) or 0.0),
    }


_RAW_ID_FIELDS = ("chat_id", "sender_user_id")


def redact_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Envelope safe to return/print: raw Telegram ids removed, hashes kept."""
    return {k: v for k, v in envelope.items() if k not in _RAW_ID_FIELDS}


class ReplayGuard:
    """Reject duplicate or malformed Telegram ``update_id`` values.

    Bounded memory: remembers the last ``capacity`` accepted ids. Ids are
    accepted at most once; ids that are not positive integers are rejected.
    """

    def __init__(self, capacity: int = 4096):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = int(capacity)
        self._seen: "OrderedDict[int, None]" = OrderedDict()
        self._lock = threading.Lock()

    def check(self, update_id: Any) -> str:
        """Return ``"ACCEPT"``, ``"DUPLICATE"`` or ``"INVALID"`` and record accepts."""
        if not _valid_update_id(update_id):
            return "INVALID"
        with self._lock:
            if update_id in self._seen:
                return "DUPLICATE"
            self._seen[update_id] = None
            while len(self._seen) > self.capacity:
                self._seen.popitem(last=False)
            return "ACCEPT"

    def __len__(self) -> int:
        return len(self._seen)


class TelegramAuditLog:
    """Append-only audit trail for the Telegram edge.

    In-memory (bounded) by default. Pass ``path`` to additionally append JSON
    lines to a file; the file is opened in append mode only and never
    truncated or rewritten.
    """

    def __init__(self, path: str | Path | None = None, max_memory: int = 1000):
        self.path = Path(path) if path else None
        self.max_memory = int(max_memory)
        self.records: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(self, envelope: dict[str, Any], status: str, *, intent: str | None = None,
               source: str | None = None) -> dict[str, Any]:
        if status not in AUDIT_STATUSES:
            raise ValueError(f"unknown audit status: {status}")
        rec = {
            "schema": AUDIT_SCHEMA,
            "ts": time.time(),
            "status": status,
            "update_id": envelope.get("update_id"),
            "chat_ref": envelope.get("chat_ref", "UNKNOWN"),
            "sender_ref": envelope.get("sender_ref", "UNKNOWN"),
            "is_command": envelope.get("is_command", False),
            "text_len": envelope.get("text_len", 0),
            "text_sha256": envelope.get("text_sha256"),
            "intent": intent,
            "source": source,
        }
        with self._lock:
            self.records.append(rec)
            if len(self.records) > self.max_memory:
                del self.records[: len(self.records) - self.max_memory]
            if self.path is not None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        return rec
