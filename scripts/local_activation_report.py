#!/usr/bin/env python3
"""AHOS local activation evidence package (Phase 12).

Produces `reports/local_activation_report.json`: one machine-readable record of
whether THIS host is correctly installed and honestly instrumented to begin
collecting real evidence.

It answers, from measurement rather than assertion:
  * which commit and which interpreter/OS produced this record
  * are the four SQLite stores present, healthy, and carrying the ledger guards
  * does this host actually reach any market-data provider (classified, honest)
  * is the runtime importable and the Lane-A freeze intact
  * which evidence namespace predictions will be stamped with

Read-only with respect to operational state: it opens stores `mode=ro`, runs no
scoring, and writes no prediction. The provider probe performs live network
calls and records failures as evidence -- never bypassing TLS to force a pass.

Usage:
    python scripts/local_activation_report.py
    python scripts/local_activation_report.py --no-probe      # skip network
    python scripts/local_activation_report.py --stdout

Exit codes:
    0 = report written and the host is activation-ready
    3 = report written, but the host is NOT ready (reasons listed in the file)
    2 = the report itself could not be produced
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import (  # noqa: E402
    connect_sqlite_ro,
    get_discovery_db_path,
    get_knowledge_db_path,
    get_local_db_path,
    get_paper_trading_db_path,
)
from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402

SCHEMA = "ahos.local_activation.v1"

REQUIRED_STORES = {
    "e01_discovery": get_discovery_db_path,
    "paper_trading": get_paper_trading_db_path,
    "ahos_local": get_local_db_path,
    "ahos_knowledge": get_knowledge_db_path,
}

LEDGER_GUARDS = {
    "ahos_guard_no_update_opportunity_score_ledger",
    "ahos_guard_no_delete_opportunity_score_ledger",
}


def _store_status(name: str, path_fn) -> dict:
    path = Path(path_fn())
    if not path.is_file():
        return {"store": name, "path": str(path), "exists": False,
                "integrity_check": "NO_DATA", "tables": 0, "ok": False}
    try:
        conn = connect_sqlite_ro(path)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'")]
        conn.close()
        return {
            "store": name, "path": str(path), "exists": True,
            "integrity_check": integrity, "tables": len(tables),
            "bytes": path.stat().st_size,
            "ok": integrity == "ok",
        }
    except sqlite3.Error as e:
        return {"store": name, "path": str(path), "exists": True,
                "integrity_check": f"ERROR: {e}", "tables": 0, "ok": False}


def _prediction_ledger_status() -> dict:
    """Ledger presence, append-only guards, and the evidence-namespace census."""
    try:
        from architecture.learning.score_ledger import (
            CALIBRATION_ELIGIBLE_SOURCES, ScoreLedger, resolve_source,
        )
        ledger = ScoreLedger()
        conn = connect_sqlite_ro(ledger.db_path)
        guards = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' "
            "AND name LIKE '%score_ledger%'")}
        conn.close()
        census = ledger.source_census()
        eligible = sorted(CALIBRATION_ELIGIBLE_SOURCES)
        return {
            "table_present": True,
            "append_only_guards": sorted(guards),
            "guards_ok": LEDGER_GUARDS.issubset(guards),
            "total_rows": ledger.count(),
            "source_census": census,
            "calibration_eligible_sources": eligible,
            "calibration_eligible_rows": sum(
                n for s, n in census.items() if s in CALIBRATION_ELIGIBLE_SOURCES),
            "resolved_source_for_this_process": resolve_source(),
        }
    except Exception as e:
        return {"table_present": False, "guards_ok": False,
                "error": f"{type(e).__name__}: {e}"[:200]}


def _outcome_label_status() -> dict:
    """Are outcome labels being produced? (the other half of a calibration pair)"""
    try:
        conn = connect_sqlite_ro(get_discovery_db_path())
        labels = conn.execute("SELECT COUNT(*) FROM outcome_label").fetchone()[0]
        resolved = conn.execute(
            "SELECT COUNT(*) FROM observation_state WHERE state='RESOLVED'").fetchone()[0]
        observing = conn.execute(
            "SELECT COUNT(*) FROM observation_state").fetchone()[0]
        obs_rows = conn.execute(
            "SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
        conn.close()
        return {"outcome_labels": labels, "tokens_resolved": resolved,
                "tokens_tracked": observing, "discovery_observations": obs_rows}
    except sqlite3.Error as e:
        return {"error": f"{type(e).__name__}: {e}"[:200]}


def _lane_a_status() -> dict:
    try:
        from scripts import freeze_lane_a
        drift, missing, untracked = freeze_lane_a.verify(root=ROOT)
        return {
            "ok": not drift and not missing and not untracked,
            "drift": sorted(drift),
            "missing": sorted(missing),
            "untracked": sorted(untracked),
        }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}


def _runtime_status() -> dict:
    """Can the runtime and its safety laws load on this host?"""
    status: dict = {}
    try:
        import architecture.runtime.__main__  # noqa: F401
        status["runtime_importable"] = True
    except Exception as e:
        status["runtime_importable"] = False
        status["runtime_import_error"] = f"{type(e).__name__}: {e}"[:200]

    try:
        from architecture.security import assert_safe_environment
        assert_safe_environment()
        status["paper_only_invariant"] = "ENFORCED"
    except Exception as e:
        status["paper_only_invariant"] = f"VETO: {e}"[:200]

    try:
        from architecture.scheduling import watchdog
        status["watchdog"] = watchdog.watchdog_report(
            get_local_db_path(), max_age_sec=300.0)
    except Exception as e:
        status["watchdog"] = {"status": "UNAVAILABLE",
                              "detail": f"{type(e).__name__}: {e}"[:200]}
    return status


def _provider_status(chain: str, do_probe: bool) -> dict:
    if not do_probe:
        return {"probed": False,
                "note": "network probe skipped (--no-probe); "
                        "live reachability therefore UNKNOWN, not assumed"}
    try:
        from architecture.providers.probe import probe_providers
        report = probe_providers(chain=chain)
        payload = report.as_dict()
        payload["probed"] = True
        return payload
    except Exception as e:
        return {"probed": True, "error": f"{type(e).__name__}: {e}"[:200],
                "any_success": False, "m_gap_007_live_success_proven": False}


def build_report(chain: str = "solana", do_probe: bool = True) -> dict:
    stores = [_store_status(n, fn) for n, fn in REQUIRED_STORES.items()]
    ledger = _prediction_ledger_status()
    lane_a = _lane_a_status()
    runtime = _runtime_status()
    providers = _provider_status(chain, do_probe)
    outcomes = _outcome_label_status()

    blockers: list[str] = []
    for s in stores:
        if not s["ok"]:
            blockers.append(f"store {s['store']}: integrity={s['integrity_check']}")
    if not ledger.get("guards_ok"):
        blockers.append("prediction ledger append-only guards missing")
    if not lane_a.get("ok"):
        blockers.append("Lane-A freeze drift or missing files")
    if not runtime.get("runtime_importable"):
        blockers.append("runtime entrypoint does not import")
    if runtime.get("paper_only_invariant") != "ENFORCED":
        blockers.append("paper-only invariant not enforced")

    # Not a blocker for INSTALLATION, but it IS a blocker for real data.
    data_blockers: list[str] = []
    if do_probe and not providers.get("any_success"):
        data_blockers.append(
            "no provider returned SUCCESS on this host — real predictions "
            "cannot accumulate until market-data egress works (M-GAP-007)")
    if ledger.get("resolved_source_for_this_process") not in ("local",):
        data_blockers.append(
            "evidence source for this process is "
            f"'{ledger.get('resolved_source_for_this_process')}' — predictions "
            "will NOT be calibration-eligible; set AHOS_EVIDENCE_SOURCE=local "
            "in the daemon shell")

    installation_ready = not blockers
    if installation_ready and not data_blockers:
        classification = "READY_FOR_REAL_LOCAL_DATA"
    elif installation_ready:
        classification = "INSTALLED_AWAITING_REAL_DATA_PRECONDITIONS"
    else:
        classification = "NOT_READY"

    return {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "command": "python scripts/local_activation_report.py",
        "git": git_meta(),
        "environment": environment_fingerprint(),
        "databases": stores,
        "prediction_ledger": ledger,
        "outcome_labeling": outcomes,
        "lane_a": lane_a,
        "runtime": runtime,
        "providers": providers,
        "evidence_source": ledger.get("resolved_source_for_this_process"),
        "installation_ready": installation_ready,
        "installation_blockers": blockers,
        "real_data_blockers": data_blockers,
        "classification": classification,
        "not_claimed": [
            "168-hour local soak (never run on this host)",
            "live provider success (see providers.status_counts)",
            "scoring calibration (requires accumulated real pairs)",
            "7 consecutive nightly backups",
            "production readiness of any kind",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS local activation evidence package")
    ap.add_argument("--chain", default="solana")
    ap.add_argument("--no-probe", action="store_true",
                    help="skip the live provider probe (reachability stays UNKNOWN)")
    ap.add_argument("--out", default=str(ROOT / "reports" / "local_activation_report.json"))
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args(argv)

    try:
        report = build_report(chain=args.chain, do_probe=not args.no_probe)
    except Exception as e:
        print(f"ERROR: could not build activation report: {type(e).__name__}: {e}")
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"classification     : {report['classification']}")
    print(f"git sha            : {report['git']['commit_sha'][:12]} "
          f"(clean={report['git']['working_tree_clean']})")
    print(f"evidence source    : {report['evidence_source']}")
    print(f"databases          : "
          f"{sum(1 for s in report['databases'] if s['ok'])}/{len(report['databases'])} healthy")
    print(f"ledger guards      : {report['prediction_ledger'].get('guards_ok')}  "
          f"rows={report['prediction_ledger'].get('total_rows')} "
          f"census={report['prediction_ledger'].get('source_census')}")
    print(f"outcome labels     : {report['outcome_labeling'].get('outcome_labels')}")
    print(f"lane-A             : {'OK' if report['lane_a'].get('ok') else 'DRIFT'}")
    prov = report["providers"]
    if prov.get("probed"):
        print(f"providers          : {prov.get('status_counts')} "
              f"any_success={prov.get('any_success')}")
    else:
        print("providers          : NOT PROBED (reachability UNKNOWN)")
    for b in report["installation_blockers"]:
        print(f"  INSTALL BLOCKER  : {b}")
    for b in report["real_data_blockers"]:
        print(f"  REAL-DATA BLOCKER: {b}")
    print(f"artifact           : {out}")

    if args.stdout:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0 if report["classification"] == "READY_FOR_REAL_LOCAL_DATA" else 3


if __name__ == "__main__":
    sys.exit(main())
