#!/usr/bin/env python3
"""AHOS Database Bootstrap — creates all 4 SQLite stores with canonical schemas.

WHY THIS EXISTS
---------------
`.gitignore` excludes `*.sqlite` (correct: databases are runtime state, not source).
But `StartupValidator` fail-closes when `data/paper_trading.sqlite` is missing, so a
fresh clone could never boot. This script is the missing link between `git clone`
and `python -m architecture.runtime`.

LAWS
----
  - IDEMPOTENT: every statement is CREATE ... IF NOT EXISTS. Re-running is a no-op.
  - NON-DESTRUCTIVE: never drops, never deletes, never overwrites an existing row.
    Existing databases are opened and topped-up with missing tables only.
  - ZERO FABRICATION: creates EMPTY schemas. No fake tokens, no fake trades, no
    fake prices. An empty store is honest; a seeded store is a lie.
  - APPEND-ONLY GUARDS: applies the F1-S1 trigger set to history tables so the
    append-only invariant holds from the very first boot.

USAGE
-----
    python scripts/init_databases.py              # create/repair all stores
    python scripts/init_databases.py --verify     # report only, change nothing
    python scripts/init_databases.py --with-guards   # also apply F1-S1 triggers
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import (  # noqa: E402
    get_data_dir,
    get_discovery_db_path,
    get_paper_trading_db_path,
    get_local_db_path,
    get_knowledge_db_path,
)

# --------------------------------------------------------------------------
# Schema sources. Each store composes SQL from the module that OWNS it, so the
# bootstrap can never drift from the runtime's own CREATE TABLE statements.
# --------------------------------------------------------------------------

DISCOVERY_SCHEMA_FILE = ROOT / "discovery" / "schema_sqlite.sql"

# The paper lab evolved across three generations; each generation owns its own
# SQL file and all three are live (v1 lab tables, v2 bankroll/portfolio, v3
# realizable-value + learning loop). Loading all three yields the canonical
# 34-trigger append-only surface the regression tests pin.
PAPER_SCHEMA_FILES = [
    ROOT / "paper_trading" / "schema.sql",
    ROOT / "paper_trading" / "schema_v2.sql",
    ROOT / "paper_trading" / "schema_v3.sql",
]

# Tables the runtime creates lazily but the validator/tests expect up-front.
LOCAL_EXTRA_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS control_flags (
  ts     TEXT DEFAULT (datetime('now')),
  action TEXT,
  detail TEXT
);
"""

# NOTE: `production_observations` is owned by architecture/collector/engine.py.
# We do NOT redeclare it here — CollectorEngine.__init__ creates it with its own
# canonical column set. Duplicating the DDL would guarantee schema drift.


def _log(msg: str) -> None:
    print(f"  {msg}")


def _apply_sql(conn: sqlite3.Connection, sql: str) -> None:
    conn.executescript(sql)
    conn.commit()


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _module_schemas() -> dict[str, list[str]]:
    """Collect SCHEMA_* constants from the modules that own each store."""
    from architecture.scheduling.engine import SCHEMA_SCHEDULER
    from architecture.runtime.metrics import SCHEMA_METRICS
    from architecture.positions.manager import SCHEMA_POSITIONS
    from architecture.knowledge.store import SCHEMA_KNOWLEDGE
    from architecture.learning.score_ledger import SCHEMA_SCORE_LEDGER

    lifecycle_schema = """
    CREATE TABLE IF NOT EXISTS runtime_lifecycle_events (
      event_id    TEXT PRIMARY KEY,
      run_id      TEXT NOT NULL,
      ts          REAL NOT NULL,
      from_state  TEXT,
      to_state    TEXT NOT NULL,
      detail      TEXT,
      meta_json   TEXT
    );
    """

    return {
        "local": [SCHEMA_SCHEDULER, SCHEMA_METRICS, lifecycle_schema,
                  LOCAL_EXTRA_SCHEMA, SCHEMA_SCORE_LEDGER],
        "paper": [SCHEMA_POSITIONS],
        "knowledge": [SCHEMA_KNOWLEDGE],
    }


def init_discovery(verify: bool) -> dict:
    path = Path(get_discovery_db_path())
    before = path.exists()
    if verify and not before:
        return {"store": "e01_discovery", "exists": False, "tables": 0, "created": False}

    conn = sqlite3.connect(str(path))
    if not verify:
        _apply_sql(conn, DISCOVERY_SCHEMA_FILE.read_text(encoding="utf-8"))
    tables = sorted(_table_names(conn))
    conn.close()

    if not verify:
        # Delegate production_observations to its owning module (no DDL duplication).
        from architecture.collector.engine import CollectorEngine

        CollectorEngine(db_path=str(path))
        conn = sqlite3.connect(str(path))
        tables = sorted(_table_names(conn))
        conn.close()

    return {
        "store": "e01_discovery",
        "path": str(path),
        "exists": True,
        "created": not before,
        "tables": len(tables),
        "table_names": tables,
    }


def init_paper(verify: bool) -> dict:
    path = Path(get_paper_trading_db_path())
    before = path.exists()
    if verify and not before:
        return {"store": "paper_trading", "exists": False, "tables": 0, "created": False}

    conn = sqlite3.connect(str(path))
    if not verify:
        # Lab generations v1 -> v2 -> v3, in order (v3 references v2 tables).
        for schema_file in PAPER_SCHEMA_FILES:
            _apply_sql(conn, schema_file.read_text(encoding="utf-8"))
        # architecture/positions owns the Section XI event-sourced tables.
        for sql in _module_schemas()["paper"]:
            _apply_sql(conn, sql)
    tables = sorted(_table_names(conn))
    conn.close()
    return {
        "store": "paper_trading",
        "path": str(path),
        "exists": True,
        "created": not before,
        "tables": len(tables),
        "table_names": tables,
    }


def init_local(verify: bool) -> dict:
    path = Path(get_local_db_path())
    before = path.exists()
    if verify and not before:
        return {"store": "ahos_local", "exists": False, "tables": 0, "created": False}

    conn = sqlite3.connect(str(path))
    if not verify:
        for sql in _module_schemas()["local"]:
            _apply_sql(conn, sql)
    tables = sorted(_table_names(conn))
    conn.close()
    return {
        "store": "ahos_local",
        "path": str(path),
        "exists": True,
        "created": not before,
        "tables": len(tables),
        "table_names": tables,
    }


def init_knowledge(verify: bool) -> dict:
    path = Path(get_knowledge_db_path())
    before = path.exists()
    if verify and not before:
        return {"store": "ahos_knowledge", "exists": False, "tables": 0, "created": False}

    conn = sqlite3.connect(str(path))
    if not verify:
        for sql in _module_schemas()["knowledge"]:
            _apply_sql(conn, sql)
    tables = sorted(_table_names(conn))
    conn.close()
    return {
        "store": "ahos_knowledge",
        "path": str(path),
        "exists": True,
        "created": not before,
        "tables": len(tables),
        "table_names": tables,
    }


def apply_append_only_guards() -> dict:
    """Apply F1-S1 append-only triggers to history tables (idempotent)."""
    from engine import f1_s1_migration as mig

    applied: dict[str, list[str]] = {}
    for key, store in mig.STORES.items():
        if not Path(store).exists():
            continue
        tables = mig.GUARDED[key]
        existing = set(mig.all_tables(Path(store)))
        present = [t for t in tables if t in existing]
        if present:
            applied[key] = mig.apply(Path(store), present)
    return applied


def integrity_check() -> dict:
    out = {}
    for name, p in {
        "e01_discovery": get_discovery_db_path(),
        "paper_trading": get_paper_trading_db_path(),
        "ahos_local": get_local_db_path(),
        "ahos_knowledge": get_knowledge_db_path(),
    }.items():
        if not Path(p).exists():
            out[name] = "MISSING"
            continue
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        row = conn.execute("PRAGMA integrity_check;").fetchone()
        conn.close()
        out[name] = row[0] if row else "unknown"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS database bootstrap (idempotent, non-destructive)")
    ap.add_argument("--verify", action="store_true", help="report only; create nothing")
    ap.add_argument("--with-guards", action="store_true", help="apply F1-S1 append-only triggers")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    get_data_dir()  # ensures data/ exists

    print("=" * 62)
    print("  AHOS Database Bootstrap" + ("  [VERIFY ONLY]" if args.verify else ""))
    print("=" * 62)

    results = [
        init_discovery(args.verify),
        init_paper(args.verify),
        init_local(args.verify),
        init_knowledge(args.verify),
    ]

    for r in results:
        mark = "NEW " if r.get("created") else "OK  "
        if not r.get("exists"):
            mark = "MISS"
        _log(f"[{mark}] {r['store']:<16} tables={r.get('tables', 0)}")

    guards = {}
    if args.with_guards and not args.verify:
        guards = apply_append_only_guards()
        total = sum(len(v) for v in guards.values())
        _log(f"[OK  ] append-only guards applied: {total} triggers")

    checks = integrity_check()
    print("-" * 62)
    for name, status in checks.items():
        _log(f"integrity_check({name}) = {status}")

    all_ok = all(v == "ok" for v in checks.values())
    print("=" * 62)
    print(f"  RESULT: {'ALL STORES HEALTHY' if all_ok else 'ATTENTION REQUIRED'}")
    print("=" * 62)

    if args.json:
        print(json.dumps({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stores": results,
            "guards": guards,
            "integrity": checks,
            "all_ok": all_ok,
        }, indent=2))

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
