#!/usr/bin/env python3
"""The bridge between what the bot announced and what the user replies to.

The problem this solves
-----------------------
The autonomous cycle announces a token. The user reads it on their phone and
types «۵ میلیون تومان خریدم». The bot answers:

    ثبت خرید کاغذی ناموفق بود: اطلاعات توکن یا مبلغ مشخص نیست.

The intent parser resolved BUY_LOG and read the amount correctly. What it
lacked was the token, because `parse(text, context_token=...)` is fed from
`TelegramBotRunner.user_contexts`, and that dict is only ever written when a
*user question* returns a candidate. A token the pipeline pushed on its own
initiative was never recorded anywhere the conversation could see it.

So the single most likely thing a user does after an alert -- reply "bought
it" -- was the one thing that could not work.

Why a file and not a dict
-------------------------
`user_contexts` lives in memory. This runs on one personal laptop that gets
closed, suspended and rebooted; the pipeline may announce at 3am and the user
may answer at 9am after a restart. An in-memory pointer would be empty exactly
when it is needed. The file is small, single-writer and rewritten atomically.

Scope
-----
Deliberately narrow: remember the last few announcements so a follow-up can be
resolved, and let the user say "the second one". This is a conversational
pointer, not a ledger -- `telegram_ai/positions.py` remains the only writer of
actual positions.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from config.paths import get_data_dir

logger = logging.getLogger(__name__)

# Keeping more than a handful invites the user replying to a stale alert from
# yesterday and having it silently resolve to the wrong token.
MAX_REMEMBERED = 5

# An announcement older than this is not a plausible referent for a bare
# "I bought it". Resolving one would be worse than admitting we don't know:
# it would log a position against a token the user never meant.
STALE_AFTER_SEC = 48 * 3600


def _store_path() -> Path:
    return Path(get_data_dir()) / "announced_tokens.json"


def _read(path: Path) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        # A corrupt pointer file must not take the bot down, but staying silent
        # is how the original bug survived: log it and continue empty.
        logger.warning("announced-token store unreadable (%s): %s",
                       type(exc).__name__, exc)
        return []
    return data if isinstance(data, list) else []


def _write(path: Path, records: list[dict[str, Any]]) -> None:
    """Atomic replace: a power cut mid-write must not leave a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError as exc:
        logger.warning("could not persist announced tokens: %s", exc)
        try:
            os.unlink(tmp)
        except OSError:
            pass


def record_announcement(address: str, chain: str, symbol: str = "",
                        name: str = "", score: float | None = None,
                        now: float | None = None,
                        path: Path | str | None = None) -> dict[str, Any]:
    """Remember a token the bot put in front of the user unprompted."""
    ts = time.time() if now is None else now
    store = Path(path) if path else _store_path()

    record = {"address": address, "chain": chain, "symbol": symbol,
              "name": name, "score": score, "announced_ts": ts}

    records = [r for r in _read(store) if r.get("address") != address]
    records.insert(0, record)
    _write(store, records[:MAX_REMEMBERED])
    return record


def last_announced(now: float | None = None,
                   path: Path | str | None = None) -> dict[str, Any] | None:
    """The most recent announcement still fresh enough to be a referent."""
    ts = time.time() if now is None else now
    for record in _read(Path(path) if path else _store_path()):
        if ts - float(record.get("announced_ts", 0)) <= STALE_AFTER_SEC:
            return record
    return None


def recent_announcements(limit: int = MAX_REMEMBERED, now: float | None = None,
                         path: Path | str | None = None) -> list[dict[str, Any]]:
    """Fresh announcements, newest first."""
    ts = time.time() if now is None else now
    fresh = [r for r in _read(Path(path) if path else _store_path())
             if ts - float(r.get("announced_ts", 0)) <= STALE_AFTER_SEC]
    return fresh[:limit]


def context_token(now: float | None = None,
                  path: Path | str | None = None) -> dict[str, str] | None:
    """Shaped for `intent.parse(text, context_token=...)`."""
    record = last_announced(now=now, path=path)
    if not record:
        return None
    return {"address": record["address"], "chain": record["chain"]}
