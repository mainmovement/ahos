#!/usr/bin/env python3
"""Write the official soak t0 snapshot -> reports/soak/system_state_t0.json

t0 is the single most consequential artifact in the whole program: it is the
timestamp the 168-hour clock is measured from, and every later snapshot is
judged against it. So this tool refuses to produce a *valid* t0 unless the
conditions that make it meaningful actually hold:

  * the laptop baseline exists and says official_168h_eligible=true
  * the host is Windows (the declared target; Arena/sandbox hours never count)
  * the daemon is alive -- watchdog reports OK, not NO_HEARTBEATS
  * predictions are being stamped `local` (the calibration-eligible namespace)

If any of those fail it still WRITES the snapshot -- a refusal that leaves no
record is not evidence -- but marks `t0_valid: false` and lists the reasons,
and exits non-zero. A t0 written on a host that cannot host the soak must never
be mistakable for the real thing.

Read-only with respect to operational state.

Usage:
    python scripts/soak_t0_snapshot.py
    python scripts/soak_t0_snapshot.py --no-probe

Exit codes:
    0 = a VALID official t0 was written (the clock starts here)
    3 = snapshot written but NOT valid as t0 (reasons listed inside)
    2 = the snapshot could not be produced
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import connect_sqlite_ro, get_local_db_path  # noqa: E402
from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402

SCHEMA = "ahos.soak_t0.v1"
DEFAULT_OUT = ROOT / "reports" / "soak" / "system_state_t0.json"
BASELINE = ROOT / "reports" / "local_laptop_baseline.json"


def _baseline_status() -> dict:
    if not BASELINE.is_file():
        return {"present": False, "official_168h_eligible": False,
                "detail": "reports/local_laptop_baseline.json not found — "
                          "run scripts/record_local_laptop_baseline.py first"}
    try:
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"present": True, "official_168h_eligible": False,
                "detail": f"unreadable baseline: {type(e).__name__}: {e}"[:200]}
    return {
        "present": True,
        "official_168h_eligible": bool(data.get("official_168h_eligible")),
        "failed_checks": [k for k, v in (data.get("checks") or {}).items() if not v],
        "baseline_utc": data.get("timestamp_utc"),
        "baseline_commit": (data.get("git") or {}).get("commit_sha"),
    }


def _watchdog_status() -> dict:
    try:
        from architecture.scheduling import watchdog
        return watchdog.watchdog_report(get_local_db_path(), max_age_sec=300.0)
    except Exception as e:
        return {"status": "UNAVAILABLE", "detail": f"{type(e).__name__}: {e}"[:200]}


def _heartbeat_status() -> dict:
    """Raw heartbeat rows — the evidence behind the watchdog verdict."""
    import sqlite3
    try:
        conn = connect_sqlite_ro(get_local_db_path())
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            "SELECT component, last_heartbeat_ts, last_heartbeat_utc, "
            "downtime_detected_sec FROM scheduler_heartbeats").fetchall()]
        runs = conn.execute("SELECT COUNT(*) FROM scheduler_runs").fetchone()[0]
        conn.close()
        now = time.time()
        for r in rows:
            r["age_sec"] = round(now - float(r["last_heartbeat_ts"]), 1)
        return {"components": rows, "component_count": len(rows),
                "scheduler_runs_total": int(runs)}
    except Exception as e:
        return {"components": [], "component_count": 0,
                "error": f"{type(e).__name__}: {e}"[:200]}


def _prediction_status() -> dict:
    try:
        from architecture.learning.score_ledger import ScoreLedger, resolve_source
        ledger = ScoreLedger()
        census = ledger.source_census()
        return {
            "total_rows": ledger.count(),
            "source_census": census,
            "local_rows": ledger.count(source="local"),
            "resolved_source_for_this_process": resolve_source(),
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"[:200], "local_rows": 0}


def _provider_status(chain: str, do_probe: bool) -> dict:
    if not do_probe:
        return {"probed": False, "any_success": False,
                "note": "probe skipped (--no-probe); reachability UNKNOWN, not assumed"}
    try:
        from architecture.providers.probe import probe_providers
        payload = probe_providers(chain=chain).as_dict()
        payload["probed"] = True
        return payload
    except Exception as e:
        return {"probed": True, "any_success": False,
                "error": f"{type(e).__name__}: {e}"[:200]}


def build_snapshot(chain: str = "solana", do_probe: bool = True) -> dict:
    baseline = _baseline_status()
    watchdog = _watchdog_status()
    heartbeats = _heartbeat_status()
    predictions = _prediction_status()
    providers = _provider_status(chain, do_probe)
    is_windows = platform.system() == "Windows"

    invalid: list[str] = []
    if not is_windows:
        invalid.append(
            f"host is {platform.system()}, not Windows — the official soak target "
            "is the operator's laptop; sandbox hours never count")
    if not baseline.get("official_168h_eligible"):
        invalid.append(
            "laptop baseline is not eligible "
            f"(failed: {baseline.get('failed_checks') or baseline.get('detail')})")
    if watchdog.get("status") != "OK":
        invalid.append(
            f"watchdog status is {watchdog.get('status')} — the daemon must be "
            "running and heart-beating before t0 is meaningful")
    if predictions.get("resolved_source_for_this_process") != "local":
        invalid.append(
            "evidence namespace is "
            f"'{predictions.get('resolved_source_for_this_process')}' — set "
            "AHOS_EVIDENCE_SOURCE=local so predictions are calibration-eligible")

    return {
        "schema": SCHEMA,
        "timestamp_utc": utc_now(),
        "timestamp_epoch": time.time(),
        "git": git_meta(),
        "environment": environment_fingerprint(),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "is_windows": is_windows,
        },
        "baseline": baseline,
        "watchdog": watchdog,
        "heartbeats": heartbeats,
        "predictions": predictions,
        "providers": providers,
        "evidence_source": predictions.get("resolved_source_for_this_process"),
        "t0_valid": not invalid,
        "t0_invalid_reasons": invalid,
        "soak_status": "LOCAL_SOAK_RUNNING" if not invalid else "NOT_STARTED",
        "note": (
            "t0_valid=true means the 168-hour clock legitimately starts at "
            "timestamp_utc. t0_valid=false means this file is a diagnostic "
            "record only and must never be cited as the start of the window."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS official soak t0 snapshot")
    ap.add_argument("--chain", default="solana")
    ap.add_argument("--no-probe", action="store_true")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)

    try:
        snap = build_snapshot(chain=args.chain, do_probe=not args.no_probe)
    except Exception as e:
        print(f"ERROR: could not build t0 snapshot: {type(e).__name__}: {e}")
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"t0_valid        : {snap['t0_valid']}")
    print(f"soak_status     : {snap['soak_status']}")
    print(f"timestamp_utc   : {snap['timestamp_utc']}")
    print(f"git sha         : {snap['git']['commit_sha'][:12]}")
    print(f"os              : {snap['os']['system']} ({snap['os']['machine']})")
    print(f"watchdog        : {snap['watchdog'].get('status')}")
    print(f"heartbeats      : {snap['heartbeats'].get('component_count')} component(s)")
    print(f"evidence source : {snap['evidence_source']}")
    prov = snap["providers"]
    print(f"providers       : {prov.get('status_counts', 'NOT PROBED')} "
          f"any_success={prov.get('any_success')}")
    for reason in snap["t0_invalid_reasons"]:
        print(f"  NOT A VALID t0: {reason}")
    print(f"artifact        : {out}")
    return 0 if snap["t0_valid"] else 3


if __name__ == "__main__":
    sys.exit(main())
