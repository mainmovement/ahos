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
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
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
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
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
    src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
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

    args = ap.parse_args(argv)

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
