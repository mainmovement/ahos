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


def drill(store: Path, tables: list[str]) -> dict:
    """Full safety drill on a COPY: apply → UPDATE must fail → INSERT must work → rollback →
    triggers gone → data identical. Migration is proven safe BEFORE touching the live store."""
    tmp = Path(tempfile.mkdtemp()) / "copy.sqlite"
    shutil.copy2(store, tmp)
    before = census(tmp, tables)
    apply(tmp, tables)
    conn = sqlite3.connect(str(tmp))
    t0 = tables[0]
    update_blocked = False
    try:
        conn.execute(f'UPDATE "{t0}" SET rowid=rowid')
        conn.commit()
    except sqlite3.IntegrityError:
        update_blocked = True
    n_before = conn.execute(f'SELECT COUNT(*) FROM "{t0}"').fetchone()[0]
    insert_ok = True
    try:
        if t0 == "control_flags":
            conn.execute(f'INSERT INTO "{t0}"(action, detail) VALUES (?, ?)', ("DRILL", "f1s1 drill"))
            conn.execute(f'DELETE FROM "{t0}" WHERE action="DRILL"')  # DELETE on guarded = blocked; so we do not expect commit
            conn.commit()
            insert_ok = False  # should not reach (DELETE must abort)
        else:
            conn.execute(f'INSERT INTO "{t0}" SELECT * FROM "{t0}" LIMIT 0')  # zero-row insert
            conn.commit()
    except sqlite3.IntegrityError:
        # for control_flags the DELETE must abort — that IS the proof; re-open clean
        insert_ok = "delete-blocked-as-required"
        conn.close()
        conn = sqlite3.connect(str(tmp))
    n_after = conn.execute(f'SELECT COUNT(*) FROM "{t0}"').fetchone()[0]
    conn.close()
    rollback(tmp, tables)
    after = census(tmp, tables)
    gone = guards_present(tmp) == []
    identical = before == after
    tmp.unlink()
    return {"store": str(store), "update_blocked": update_blocked, "insert_path": insert_ok,
            "row_count_stable": n_before == n_after, "rollback_clean": gone,
            "data_identical_after_drill": identical}


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
