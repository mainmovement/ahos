#!/usr/bin/env python3
"""Read-only AHOS system-state snapshot (Phase 8 observability).

Does not start the daemon. Does not invent success. Missing stores/heartbeats
are NO_DATA / NO_HEARTBEATS. Optional live provider probe records the real
envelope (OK / ERROR / TIMEOUT / DOWN) and never fabricates tokens.

Usage:
    python scripts/system_state_snapshot.py
    python scripts/system_state_snapshot.py --probe-providers
    python scripts/system_state_snapshot.py --out reports/system_state_snapshot.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evidence_common import (  # noqa: E402
    environment_fingerprint, git_meta, observation_event, utc_now,
)
from scripts import soak_snapshot as snap  # noqa: E402
from scripts.freeze_lane_a import verify as lane_a_verify  # noqa: E402
from scripts.sqlite_backup_restore import integrity_check, table_row_counts  # noqa: E402
from config.paths import (  # noqa: E402
    get_discovery_db_path, get_knowledge_db_path, get_local_db_path,
    get_paper_trading_db_path,
)

SCHEMA = "ahos.system_state.v1"
STORES = {
    "ahos_local": get_local_db_path,
    "e01_discovery": get_discovery_db_path,
    "paper_trading": get_paper_trading_db_path,
    "ahos_knowledge": get_knowledge_db_path,
}


def _store_status(path_fn) -> dict:
    path = Path(path_fn())
    if not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "integrity_check": "NO_DATA",
            "row_total": "NO_DATA",
        }
    counts = table_row_counts(path)
    return {
        "path": str(path),
        "exists": True,
        "integrity_check": integrity_check(path),
        "row_counts": counts,
        "row_total": sum(counts.values()),
    }


def _probe_providers() -> list[dict]:
    """Live reachability for EVERY registered provider, via the canonical
    probe (architecture/providers/probe.py — M-GAP-016 status vocabulary).
    Failures are evidence, never blockers. One probe implementation; the
    snapshot no longer duplicates a 2-provider subset with raw exception
    class names as statuses."""
    from architecture.providers.probe import probe_providers

    report = probe_providers(chain="solana")
    return [
        {
            "provider_id": r.provider_id,
            "probed_at_utc": r.probed_at_utc,
            "status": r.status,
            "token_count": r.token_count,
            "error": r.detail,
            "latency_ms": r.latency_ms,
        }
        for r in report.results
    ]


def build_snapshot(probe_providers: bool = False, window_hours: float = 24.0) -> dict:
    git = git_meta()
    soak = snap.snapshot(window_hours=window_hours)
    stores = {name: _store_status(fn) for name, fn in STORES.items()}
    drift, missing, untracked = lane_a_verify()
    last_backup = ROOT / "reports" / "backup_restore_drill.json"
    backup_meta = {
        "committed_drill_exists": last_backup.is_file(),
        "path": str(last_backup) if last_backup.is_file() else None,
        "verdict": None,
    }
    if last_backup.is_file():
        try:
            backup_meta["verdict"] = json.loads(last_backup.read_text(encoding="utf-8")).get("verdict")
        except json.JSONDecodeError:
            backup_meta["verdict"] = "UNREADABLE"

    events: list[dict] = []
    wd = soak["watchdog"]
    events.append(observation_event(
        event_type="WATCHDOG_STATUS",
        severity={"OK": "INFO", "STALE": "WARN", "NO_HEARTBEATS": "WARN"}.get(wd["status"], "ERROR"),
        evidence_path="reports/system_state_snapshot.json#watchdog",
        detail=f"status={wd['status']} detail={wd.get('detail')}",
        commit_sha=git["commit_sha"],
    ))
    events.append(observation_event(
        event_type="SCHEDULER_WINDOW",
        severity="INFO",
        evidence_path="reports/system_state_snapshot.json#scheduler",
        detail=f"runs_in_window={soak['scheduler']['runs_in_window']} "
               f"status_counts={soak['scheduler']['status_counts']}",
        commit_sha=git["commit_sha"],
    ))
    for name, st in stores.items():
        sev = "INFO" if st["integrity_check"] == "ok" else (
            "WARN" if st["integrity_check"] == "NO_DATA" else "ERROR"
        )
        events.append(observation_event(
            event_type="PERSISTENCE_INTEGRITY",
            severity=sev,
            evidence_path=f"reports/system_state_snapshot.json#stores.{name}",
            detail=f"{name} integrity={st['integrity_check']} exists={st['exists']}",
            commit_sha=git["commit_sha"],
        ))

    provider_probe = _probe_providers() if probe_providers else []
    for p in provider_probe:
        ok = p["status"] == "OK" and p["token_count"] > 0
        events.append(observation_event(
            event_type="PROVIDER_PROBE",
            severity="INFO" if ok else "WARN",
            evidence_path="reports/system_state_snapshot.json#provider_probe",
            detail=f"{p['provider_id']} status={p['status']} tokens={p['token_count']}",
            commit_sha=git["commit_sha"],
        ))

    return {
        "schema": SCHEMA,
        "timestamp_utc": utc_now(),
        "command": "python scripts/system_state_snapshot.py",
        "git": git,
        "environment": environment_fingerprint(),
        "exit_code": 0,
        "result": "RECORDED",
        "lane_a": {
            "drift": drift, "missing": missing, "untracked": untracked,
            "ok": not drift and not missing,
        },
        "watchdog": soak["watchdog"],
        "scheduler": soak["scheduler"],
        "soak_observations": soak["observations"],
        "integrity": soak["integrity"],
        "stores": stores,
        "backup": backup_meta,
        "provider_probe": provider_probe,
        "events": events,
        "honest_limitations": [
            "This snapshot does not start the daemon.",
            "NO_HEARTBEATS / NO_DATA is the honest state of a host that is not under soak.",
            "A live provider probe, if present, is one request — not availability proof.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS read-only system state snapshot")
    ap.add_argument("--out", default=str(ROOT / "reports" / "system_state_snapshot.json"))
    ap.add_argument("--probe-providers", action="store_true")
    ap.add_argument("--window-hours", type=float, default=24.0)
    args = ap.parse_args(argv)

    report = build_snapshot(probe_providers=args.probe_providers, window_hours=args.window_hours)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": report["result"],
        "artifact": str(dest),
        "commit_sha": report["git"]["commit_sha"],
        "watchdog": report["watchdog"]["status"],
        "lane_a_ok": report["lane_a"]["ok"],
        "events": len(report["events"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
