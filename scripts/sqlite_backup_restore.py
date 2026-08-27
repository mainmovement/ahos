#!/usr/bin/env python3
"""AHOS SQLite backup / restore drill (M-GAP-010).

Minimal, stdlib-only. Uses the SQLite Online Backup API so WAL/journal state
is copied as a consistent snapshot. Never mutates the source database.

Laws:
  - Fail closed: missing source, failed integrity_check, or row-count mismatch
    is a FAIL (never a silent success).
  - Zero fabrication: empty tables stay empty; counts come from the file.
  - Evidence: every drill writes a JSON record (hashes, counts, integrity).

Usage:
    python scripts/sqlite_backup_restore.py drill \\
        --workdir reports/_scratch/backup_restore_drill \\
        --report reports/backup_restore_drill.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import connect_sqlite_ro  # noqa: E402

SCHEMA_VERSION = "ahos.backup_restore.v1"

SYNTHETIC_SCHEMA = """
CREATE TABLE IF NOT EXISTS drill_meta (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drill_events (
    id INTEGER PRIMARY KEY,
    payload TEXT NOT NULL
);
"""

SYNTHETIC_ROWS = {
    "drill_meta": [("schema", SCHEMA_VERSION), ("fixture", "synthetic")],
    "drill_events": [(1, "alpha"), (2, "beta"), (3, "gamma")],
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git_meta(cwd: Path | None = None) -> dict:
    repo = cwd or ROOT
    def _run(args: list[str]) -> str:
        try:
            proc = subprocess.run(
                args, cwd=str(repo), capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return proc.stdout.strip() if proc.returncode == 0 else ""

    porcelain = _run(["git", "status", "--porcelain"])
    return {
        "commit_sha": _run(["git", "rev-parse", "HEAD"]) or "UNKNOWN",
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "UNKNOWN",
        "working_tree_clean": porcelain == "",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integrity_check(path: Path) -> str:
    if not path.is_file():
        return "NO_DATA"
    try:
        conn = connect_sqlite_ro(path)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return "NO_DATA"
    return row[0] if row else "NO_DATA"


def table_row_counts(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {}
    conn = connect_sqlite_ro(path)
    try:
        names = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
        ]
        return {
            name: int(conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
            for name in names
        }
    finally:
        conn.close()


def copy_sqlite(src: Path, dest: Path) -> None:
    """Consistent snapshot via the Online Backup API. Source is opened read-only."""
    if not src.is_file():
        raise FileNotFoundError(f"source sqlite missing: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    src_conn = connect_sqlite_ro(src)
    try:
        dest_conn = sqlite3.connect(str(dest))
        try:
            src_conn.backup(dest_conn)
            dest_conn.commit()
        finally:
            dest_conn.close()
    finally:
        src_conn.close()


def build_synthetic_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SYNTHETIC_SCHEMA)
        conn.executemany(
            "INSERT INTO drill_meta(k, v) VALUES (?, ?)", SYNTHETIC_ROWS["drill_meta"],
        )
        conn.executemany(
            "INSERT INTO drill_events(id, payload) VALUES (?, ?)",
            SYNTHETIC_ROWS["drill_events"],
        )
        conn.commit()
    finally:
        conn.close()


def inspect(path: Path, role: str) -> dict:
    exists = path.is_file()
    return {
        "role": role,
        "path": str(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists else None,
        "integrity_check": integrity_check(path) if exists else "NO_DATA",
        "row_counts": table_row_counts(path) if exists else {},
        "row_total": sum(table_row_counts(path).values()) if exists else 0,
    }


def verify_restore(source_info: dict, restored_info: dict) -> list[str]:
    failures: list[str] = []
    if source_info.get("integrity_check") != "ok":
        failures.append(f"source integrity_check={source_info.get('integrity_check')}")
    if restored_info.get("integrity_check") != "ok":
        failures.append(f"restored integrity_check={restored_info.get('integrity_check')}")
    if source_info.get("row_counts") != restored_info.get("row_counts"):
        failures.append(
            f"row_count mismatch source={source_info.get('row_counts')} "
            f"restored={restored_info.get('row_counts')}"
        )
    return failures


def drill_one(source: Path, backup: Path, restored: Path) -> dict:
    source_info = inspect(source, "source")
    if not source.is_file():
        return {
            "source": source_info,
            "backup": inspect(backup, "backup"),
            "restored": inspect(restored, "restored"),
            "failures": [f"source missing: {source}"],
            "verdict": "FAIL",
        }

    copy_sqlite(source, backup)
    backup_info = inspect(backup, "backup")
    copy_sqlite(backup, restored)
    restored_info = inspect(restored, "restored")
    failures = verify_restore(source_info, restored_info)
    if backup_info.get("integrity_check") != "ok":
        failures.append(f"backup integrity_check={backup_info.get('integrity_check')}")
    if not backup_info.get("sha256"):
        failures.append("backup hash missing")
    return {
        "source": source_info,
        "backup": backup_info,
        "restored": restored_info,
        "failures": failures,
        "verdict": "FAIL" if failures else "PASS",
    }


def seed_ahos_probe_rows(data_dir: Path) -> dict[str, int]:
    """Insert a few honest probe rows into real AHOS stores (if present)."""
    inserted: dict[str, int] = {}
    local = data_dir / "ahos_local.sqlite"
    if local.is_file():
        conn = sqlite3.connect(str(local))
        try:
            conn.execute(
                "INSERT INTO control_flags(action, detail) VALUES (?, ?)",
                ("backup_restore_drill", SCHEMA_VERSION),
            )
            conn.commit()
            inserted["ahos_local.control_flags"] = 1
        except sqlite3.Error:
            conn.rollback()
        finally:
            conn.close()
    return inserted


def run_drill(workdir: Path, include_ahos_stores: bool = True) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    stores: list[dict] = []

    synthetic = workdir / "source" / "synthetic_drill.sqlite"
    build_synthetic_source(synthetic)
    stores.append(
        drill_one(
            synthetic,
            workdir / "backup" / "synthetic_drill.sqlite",
            workdir / "restored" / "synthetic_drill.sqlite",
        )
    )

    ahos_seed: dict[str, int] = {}
    if include_ahos_stores:
        import os
        from scripts import init_databases as initdb

        data_dir = workdir / "ahos_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        os.environ["AHOS_DATA_DIR"] = str(data_dir)
        initdb.init_discovery(verify=False)
        initdb.init_paper(verify=False)
        initdb.init_local(verify=False)
        initdb.init_knowledge(verify=False)
        ahos_seed = seed_ahos_probe_rows(data_dir)
        for name in (
            "e01_discovery.sqlite",
            "paper_trading.sqlite",
            "ahos_local.sqlite",
            "ahos_knowledge.sqlite",
        ):
            src = data_dir / name
            if src.is_file():
                stores.append(
                    drill_one(
                        src,
                        workdir / "backup" / name,
                        workdir / "restored" / name,
                    )
                )

    failed = [s for s in stores if s["verdict"] != "PASS"]
    report = {
        "schema": SCHEMA_VERSION,
        "timestamp_utc": utc_now(),
        "git": git_meta(),
        "command": "python scripts/sqlite_backup_restore.py drill",
        "workdir": str(workdir),
        "include_ahos_stores": include_ahos_stores,
        "ahos_probe_rows_inserted": ahos_seed,
        "store_count": len(stores),
        "passed": sum(1 for s in stores if s["verdict"] == "PASS"),
        "failed": len(failed),
        "stores": stores,
        "verdict": "FAIL" if failed else "PASS",
        "unproven": [
            "7 consecutive nightly backups on a persistent host (original Month-1 acceptance remainder)",
            "restore onto a fresh host / different machine",
            "cron/systemd timer actually firing in production",
        ],
    }
    return report


NIGHTLY_TARGET_NIGHTS = 7
NIGHTLY_SERIES_SCHEMA = "ahos.nightly_backup_series.v1"


def _real_stores() -> dict[str, Path]:
    from config.paths import (
        get_discovery_db_path, get_knowledge_db_path,
        get_local_db_path, get_paper_trading_db_path,
    )
    return {
        "e01_discovery": Path(get_discovery_db_path()),
        "paper_trading": Path(get_paper_trading_db_path()),
        "ahos_local": Path(get_local_db_path()),
        "ahos_knowledge": Path(get_knowledge_db_path()),
    }


def run_nightly(backup_root: Path, series_path: Path,
                now: float | None = None) -> dict:
    """Take ONE night's verified backup and append it to the series ledger.

    M-GAP-010's residual is "7 consecutive nightly backups on the operator's
    host". That cannot be produced by a tool in one run, and this function does
    not pretend otherwise: it performs exactly one night, records it, and
    reports how many DISTINCT calendar days the series actually contains.

    `series_complete` only turns true when 7 distinct UTC dates are present --
    running this seven times in one afternoon will not satisfy it.
    """
    ts = time.time() if now is None else now
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(ts))
    date_utc = time.strftime("%Y-%m-%d", time.gmtime(ts))

    series: dict = {}
    if series_path.is_file():
        try:
            series = json.loads(series_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            series = {}
    nights: list[dict] = list(series.get("nights", []))

    night_dir = backup_root / stamp
    entries: list[dict] = []
    for name, src in _real_stores().items():
        if not src.is_file():
            entries.append({"store": name, "source": str(src),
                            "verdict": "MISSING_SOURCE", "integrity_check": "NO_DATA"})
            continue
        dest = night_dir / f"{name}.sqlite"
        try:
            copy_sqlite(src, dest)
            src_info = inspect(src, "source")
            bak_info = inspect(dest, "backup")
            failures = verify_restore(src_info, bak_info)
            entries.append({
                "store": name,
                "source": str(src),
                "backup": str(dest),
                "source_sha256": src_info["sha256"],
                "backup_sha256": bak_info["sha256"],
                "row_counts": bak_info["row_counts"],
                "integrity_check": bak_info["integrity_check"],
                "verdict": "FAIL" if failures else "PASS",
                "failures": failures,
            })
        except Exception as exc:
            entries.append({"store": name, "source": str(src),
                            "verdict": "FAIL",
                            "failures": [f"{type(exc).__name__}: {exc}"[:200]]})

    failed = [e for e in entries if e["verdict"] != "PASS"]
    nights.append({
        "night_utc": stamp,
        "date_utc": date_utc,
        "backup_dir": str(night_dir),
        "stores": entries,
        "verdict": "FAIL" if failed else "PASS",
    })

    distinct_dates = sorted({n["date_utc"] for n in nights})
    passing_dates = sorted({n["date_utc"] for n in nights if n["verdict"] == "PASS"})

    report = {
        "schema": NIGHTLY_SERIES_SCHEMA,
        "updated_utc": utc_now(),
        "git": git_meta(),
        "backup_root": str(backup_root),
        "target_nights": NIGHTLY_TARGET_NIGHTS,
        "runs_recorded": len(nights),
        "distinct_dates": distinct_dates,
        "distinct_passing_dates": passing_dates,
        "nights_completed": len(passing_dates),
        # The honest gate: distinct calendar days, not invocations.
        "series_complete": len(passing_dates) >= NIGHTLY_TARGET_NIGHTS,
        "latest_verdict": nights[-1]["verdict"],
        "nights": nights,
        "unproven_until_operator_runs_them": [
            f"{NIGHTLY_TARGET_NIGHTS} consecutive nightly backups on the laptop "
            f"({len(passing_dates)}/{NIGHTLY_TARGET_NIGHTS} distinct days so far)",
            "restore onto a FRESH host (different machine) — USER-ACTION-REQUIRED",
        ],
    }
    write_report(report, series_path)
    return report


def write_report(report: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS SQLite backup/restore drill")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_backup = sub.add_parser("backup", help="snapshot source -> dest")
    p_backup.add_argument("--source", required=True)
    p_backup.add_argument("--dest", required=True)

    p_restore = sub.add_parser("restore", help="restore backup -> dest")
    p_restore.add_argument("--backup", required=True)
    p_restore.add_argument("--dest", required=True)

    p_drill = sub.add_parser("drill", help="full backup+restore verification")
    p_drill.add_argument("--workdir", default=str(ROOT / "reports" / "_scratch" / "backup_restore_drill"))
    p_drill.add_argument("--report", default=str(ROOT / "reports" / "backup_restore_drill.json"))
    p_drill.add_argument("--synthetic-only", action="store_true")

    p_nightly = sub.add_parser(
        "nightly", help="take ONE night's verified backup of the real stores "
                        "and append it to the 7-night series ledger")
    p_nightly.add_argument("--backup-root", default=str(ROOT / "data" / "backups"))
    p_nightly.add_argument("--series", default=str(ROOT / "reports" / "nightly_backup_series.json"))

    args = ap.parse_args(argv)

    if args.cmd == "nightly":
        rep = run_nightly(Path(args.backup_root), Path(args.series))
        print(f"night verdict     : {rep['latest_verdict']}")
        print(f"distinct days     : {rep['nights_completed']}/{rep['target_nights']}")
        print(f"series_complete   : {rep['series_complete']}")
        print(f"series ledger     : {args.series}")
        for note in rep["unproven_until_operator_runs_them"]:
            print(f"  UNPROVEN: {note}")
        return 0 if rep["latest_verdict"] == "PASS" else 1

    if args.cmd == "backup":
        copy_sqlite(Path(args.source), Path(args.dest))
        info = inspect(Path(args.dest), "backup")
        print(json.dumps(info, indent=2))
        return 0 if info["integrity_check"] == "ok" else 1

    if args.cmd == "restore":
        copy_sqlite(Path(args.backup), Path(args.dest))
        info = inspect(Path(args.dest), "restored")
        print(json.dumps(info, indent=2))
        return 0 if info["integrity_check"] == "ok" else 1

    report = run_drill(Path(args.workdir), include_ahos_stores=not args.synthetic_only)
    write_report(report, Path(args.report))
    print(json.dumps({
        "verdict": report["verdict"],
        "passed": report["passed"],
        "failed": report["failed"],
        "report": args.report,
        "timestamp_utc": report["timestamp_utc"],
        "commit_sha": report["git"]["commit_sha"],
    }, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
