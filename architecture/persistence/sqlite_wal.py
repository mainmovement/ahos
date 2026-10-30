"""Turn on WAL at a quiet connection. PAPER_ONLY. Does not delete a database."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def connect_writer(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def apply_wal(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return {"path": str(target), "applied": False, "reason": "ABSENT"}
    try:
        conn = connect_writer(target)
    except sqlite3.OperationalError as exc:
        return {"path": str(target), "applied": False, "reason": f"LOCKED:{exc.__class__.__name__}"}
    try:
        mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0])
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    finally:
        conn.close()
    return {
        "path": str(target),
        "applied": mode.lower() == "wal" and integrity == "ok",
        "journal_mode": mode,
        "integrity": integrity,
        "reason": "WAL" if mode.lower() == "wal" and integrity == "ok" else "CHECK_FAILED",
    }
