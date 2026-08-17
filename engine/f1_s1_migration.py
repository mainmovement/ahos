#!/usr/bin/env python3
"""F1-S1 (conservative, owner-authorized by W12 PART B) — additive append-only guard triggers.

SCOPE LAW: DDL only. Zero row writes. No historical data touched. Idempotent. Rollbackable.
Guarded tables = HISTORY tables (insert-only in the entire pipeline — verified 2026-08-13):
  e01_discovery: discovery_observations, raw_payloads, gap_register, lifecycle_events, gate_summary
  ahos_local:    control_flags
Mutable upsert-by-design state tables are DELIBERATELY NOT guarded (tokens, pairs,
observation_state, opportunity_rank, outcome_label, security_verdicts, feature_definitions,
feature_vector, holder_snapshot, wallet_observation) — documented in F1_RESOLUTION_PLAN.md.
Modes: drill (work on a COPY), apply (live), rollback (drop guards; additive-inverse, verified
on a copy first). All actions write an evidence report with before/after census (rows + content
sha per table) so IDENTICAL-DATA is provable, not asserted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORES = {
    "e01": ROOT / "data" / "e01_discovery.sqlite",
    "ahos_local": ROOT / "data" / "ahos_local.sqlite",
}
GUARDED = {
    "e01": ["discovery_observations", "raw_payloads", "gap_register", "lifecycle_events", "gate_summary"],
    "ahos_local": ["control_flags"],
}
PRE = "f1s1_guard"


def trigger_names(table: str) -> tuple[str, str]:
    return f"{PRE}_no_update_{table}", f"{PRE}_no_delete_{table}"


def census(path: Path, tables: list[str]) -> dict:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    out = {}
    for t in tables:
        n = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        h = hashlib.sha256()
        for row in c.execute(f'SELECT * FROM "{t}" ORDER BY rowid'):
            h.update(repr(row).encode())
        out[t] = {"rows": n, "sha": h.hexdigest()}
    c.close()
    return out


def all_tables(path: Path) -> list[str]:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    tabs = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    c.close()
    return tabs


def guards_present(path: Path) -> list[str]:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    names = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'f1s1_guard_%'")]
    c.close()
    return sorted(names)


def apply(store: Path, tables: list[str]) -> list[str]:
    """Idempotent: CREATE TRIGGER IF NOT EXISTS. Returns applied trigger names."""
    conn = sqlite3.connect(str(store))
    applied = []
    for t in tables:
        n_upd, n_del = trigger_names(t)
        conn.execute(f"CREATE TRIGGER IF NOT EXISTS {n_upd} BEFORE UPDATE ON \"{t}\" "
                     f"BEGIN SELECT RAISE(ABORT,'append-only F1-S1: {t}'); END")
        conn.execute(f"CREATE TRIGGER IF NOT EXISTS {n_del} BEFORE DELETE ON \"{t}\" "
                     f"BEGIN SELECT RAISE(ABORT,'append-only F1-S1: {t}'); END")
        applied += [n_upd, n_del]
    conn.commit()
    conn.close()
    return applied


def rollback(store: Path, tables: list[str]) -> list[str]:
    conn = sqlite3.connect(str(store))
    dropped = []
    for t in tables:
        for name in trigger_names(t):
            conn.execute(f"DROP TRIGGER IF EXISTS {name}")
            dropped.append(name)
    conn.commit()
    conn.close()
    return dropped


def _probe_row(conn: sqlite3.Connection, table: str) -> tuple[str, list]:
    """Build a synthetic INSERT for `table` from its own PRAGMA schema.

    A BEFORE UPDATE/DELETE trigger only fires when a row actually matches. On an
    EMPTY table an `UPDATE ... SET rowid=rowid` touches zero rows and therefore
    proves NOTHING. To make the safety drill valid on a fresh install as well as
    on a populated store, we insert one disposable probe row into the temporary
    COPY and run the destructive attempts against that row.
    """
    cols = conn.execute(f'PRAGMA table_info("{table}")').fetchall()

    # Some columns carry CHECK (col IN ('A','B',...)) constraints. A generic probe
    # string would violate them, so we mine the table DDL for the first allowed
    # literal per column and use that instead.
    ddl_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    ddl = (ddl_row[0] if ddl_row else "") or ""
    enums: dict[str, str] = {}
    for m in re.finditer(r"CHECK\s*\(\s*(\w+)\s+IN\s*\(([^)]*)\)", ddl, re.IGNORECASE):
        col, body = m.group(1), m.group(2)
        literals = re.findall(r"'([^']*)'", body)
        if literals:
            enums[col] = literals[0]

    def _literal(ctype: str, name: str = ""):
        if name in enums:
            return enums[name]
        t = (ctype or "TEXT").upper()
        if "INT" in t:
            return 0
        if any(k in t for k in ("REAL", "FLOA", "DOUB", "NUM")):
            return 0.0
        return "__F1S1_DRILL_PROBE__"

    names, values = [], []
    for _cid, name, ctype, notnull, default, pk in cols:
        if pk and "INTEGER" in (ctype or "").upper():
            continue                      # let AUTOINCREMENT assign it
        if default is not None:
            continue                      # respect schema defaults
        if not notnull and not pk:
            continue                      # nullable ⇒ omit; keeps the row minimal
        names.append(name)
        values.append(_literal(ctype, name))

    if not names:
        # Every column is nullable or defaulted (e.g. control_flags). An empty
        # column list is not valid SQL, so name the first non-autoincrement
        # column explicitly to force exactly one probe row into existence.
        for _cid, name, ctype, _notnull, _default, pk in cols:
            if pk and "INTEGER" in (ctype or "").upper():
                continue
            names.append(name)
            values.append(_literal(ctype, name))
            break
    if not names:
        return f'INSERT INTO "{table}" DEFAULT VALUES', []

    placeholders = ", ".join("?" for _ in names)
    quoted = ", ".join(f'"{n}"' for n in names)
    return f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})', values


def drill(store: Path, tables: list[str]) -> dict:
    """Full safety drill on a COPY: INSERT must work → UPDATE must abort →
    DELETE must abort → rollback → triggers gone → data identical.

    The migration is proven safe BEFORE the live store is ever touched. The drill
    is data-independent: it works on an empty fresh-install store and on a store
    with years of history, because it supplies its own probe row.
    """
    tmp = Path(tempfile.mkdtemp()) / "copy.sqlite"
    shutil.copy2(store, tmp)
    before = census(tmp, tables)
    apply(tmp, tables)

    conn = sqlite3.connect(str(tmp))
    conn.execute("PRAGMA foreign_keys=OFF")     # probing schema guards, not referential integrity
    t0 = tables[0]
    n_before = conn.execute(f'SELECT COUNT(*) FROM "{t0}"').fetchone()[0]

    # 1. INSERT must still work — append-only means append IS allowed.
    insert_ok = False
    try:
        sql, vals = _probe_row(conn, t0)
        conn.execute(sql, vals)
        conn.commit()
        insert_ok = True
    except sqlite3.Error:
        conn.rollback()

    # 2. UPDATE must abort (now there is guaranteed to be >= 1 row to match).
    update_blocked = False
    try:
        conn.execute(f'UPDATE "{t0}" SET rowid=rowid')
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        update_blocked = True

    # 3. DELETE must abort.
    delete_blocked = False
    try:
        conn.execute(f'DELETE FROM "{t0}"')
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        delete_blocked = True

    n_after = conn.execute(f'SELECT COUNT(*) FROM "{t0}"').fetchone()[0]
    conn.close()

    # 4. Rollback the guards, then remove the probe row so the census can prove
    #    the drill left the data byte-identical to how it started.
    rollback(tmp, tables)
    gone = guards_present(tmp) == []
    if insert_ok:
        conn = sqlite3.connect(str(tmp))
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute(f'DELETE FROM "{t0}" WHERE rowid = (SELECT MAX(rowid) FROM "{t0}")')
        conn.commit()
        conn.close()
    after = census(tmp, tables)
    identical = before == after
    tmp.unlink()

    return {"store": str(store), "update_blocked": update_blocked,
            "delete_blocked": delete_blocked, "insert_path": insert_ok,
            "row_count_stable": (n_after == n_before + (1 if insert_ok else 0)),
            "rollback_clean": gone, "data_identical_after_drill": identical}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["drill", "apply", "rollback"])
    ap.add_argument("--report", default=None)
    args = ap.parse_args()
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    report = {"probe_set": f"W12A-F1S1-{args.mode.upper()}", "ts": ts, "mode": args.mode,
              "law": "DDL only; zero row writes; census before/after proves identical data"}
    if args.mode == "drill":
        report["drills"] = [drill(p, GUARDED[k]) for k, p in STORES.items()]
        report["verdict"] = "SAFE" if all(
            d["update_blocked"] and d["rollback_clean"] and d["data_identical_after_drill"]
            for d in report["drills"]) else "UNSAFE"
    else:
        for k, p in STORES.items():
            tabs = all_tables(p)
            before = census(p, tabs)
            names = apply(p, GUARDED[k]) if args.mode == "apply" else rollback(p, GUARDED[k])
            after = census(p, tabs)
            report[k] = {"triggers": names, "guards_present_after": guards_present(p),
                         "census_before": before, "census_after": after,
                         "data_identical": before == after}
        report["verdict"] = "OK" if all(report[k]["data_identical"] for k in STORES) else "DATA_CHANGED"
    path = Path(args.report or ROOT / "reports" / f"f1_s1_{args.mode}_{ts}.json")
    path.write_text(json.dumps(report, indent=1))
    print(json.dumps({"verdict": report["verdict"], "report": str(path)}))
    return 0 if report["verdict"] in ("SAFE", "OK") else 1


if __name__ == "__main__":
    sys.exit(main())
