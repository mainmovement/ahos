#!/usr/bin/env python3
"""Coverage guardrail (F12 lesson, Lane B): OBSERVATION COVERAGE is a first-class invariant.

A healthy experiment pipeline is reported ONLY via the full bundle:
  COLLECTION HEALTH + OBSERVATION FRESHNESS + HORIZON COVERAGE + GAP DETECTION + RECOVERY STATUS
— never via (tokens count, resolved count) alone. Fixture-pinned; live runs are read-only.

Deterministic classifier (frozen here, versioned):
  STARVING : active tokens are being discovered but share_with_obs_last_24h < 0.30
             (or zero successful observations in window while gaps accumulate > 0)
  DEGRADED : 0.30 <= share < 0.80  OR  missed-slots accumulated in last 24h > 0
  HEALTHY  : share >= 0.80 AND no new missed slots in last 24h
UNKNOWN when the store lacks the tables (never fabricated).
"""
from __future__ import annotations
import json, sqlite3, time
from pathlib import Path
from config.paths import connect_sqlite_ro

ROOT = Path(__file__).resolve().parent.parent


def coverage_report(store_path, *, now: float | None = None, reports_dir: Path | None = None) -> dict:
    now = time.time() if now is None else now
    db = Path(store_path)
    rep = {"tool": "coverage_audit", "version": "v1", "ts": now, "store": str(db),
           "verdict": "UNKNOWN", "blocks": {}}
    if not db.exists():
        return rep
    conn = connect_sqlite_ro(db)
    conn.row_factory = sqlite3.Row
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    need = {"observation_state", "discovery_observations", "gap_register"}
    if not need <= names:
        conn.close()
        return rep
    day_ago = now - 86400.0

    active = conn.execute("SELECT COUNT(*) c FROM observation_state WHERE state != 'RESOLVED'").fetchone()["c"]
    with24 = conn.execute(
        """SELECT COUNT(DISTINCT token_id) c FROM discovery_observations WHERE retrieved_ts >= ?""",
        (day_ago,)).fetchone()["c"]
    obs_ok_24h = conn.execute(
        "SELECT COUNT(*) c FROM discovery_observations WHERE retrieved_ts >= ? AND error_state IS NULL",
        (day_ago,)).fetchone()["c"]
    rep["blocks"]["collection_health"] = {
        "active_tokens": active, "tokens_with_obs_last_24h": with24,
        "observations_last_24h": conn.execute(
            "SELECT COUNT(*) c FROM discovery_observations WHERE retrieved_ts >= ?",
            (day_ago,)).fetchone()["c"],
        "successful_observations_last_24h": obs_ok_24h}

    latest = conn.execute(
        """SELECT MAX(retrieved_ts) m FROM discovery_observations
           WHERE error_state IS NULL GROUP BY token_id""").fetchall()
    ages_h = sorted((now - r["m"]) / 3600.0 for r in latest if r["m"] is not None)
    med = ages_h[len(ages_h) // 2] if ages_h else None
    fresh = sum(1 for a in ages_h if a <= 24.0)
    rep["blocks"]["observation_freshness"] = {
        "tokens_tracked": len(ages_h), "median_latest_obs_age_h": med,
        "share_latest_obs_within_24h": (fresh / len(ages_h)) if ages_h else None}

    resolved = conn.execute("SELECT COUNT(*) c FROM observation_state WHERE state='RESOLVED'").fetchone()["c"]
    covered72 = conn.execute(
        """SELECT COUNT(*) c FROM observation_state s WHERE s.state='RESOLVED' AND EXISTS (
             SELECT 1 FROM discovery_observations o WHERE o.token_id=s.token_id AND o.error_state IS NULL
               AND o.retrieved_ts BETWEEN s.first_seen_ts + 72*3600 - 1800 AND s.first_seen_ts + 72*3600 + 1800)"""
    ).fetchone()["c"]
    rep["blocks"]["horizon_coverage"] = {
        "resolved_total": resolved, "resolved_with_72h_window_point": covered72,
        "share": (covered72 / resolved) if resolved else None}

    gaps_total = conn.execute("SELECT COUNT(*) c FROM gap_register").fetchone()["c"]
    gaps_24h = conn.execute("SELECT COUNT(*) c FROM gap_register WHERE noted_ts >= ?",
                            (day_ago,)).fetchone()["c"]
    rep["blocks"]["gap_detection"] = {"missed_total": gaps_total, "missed_last_24h": gaps_24h}

    recovery = {"poller_reports": 0, "last_run_ts": None, "last_recorded": None, "last_failures": None}
    rdir = Path(reports_dir) if reports_dir else ROOT / "reports"
    files = [f for f in rdir.glob("observe_active_*.json") if "isolation" not in f.name]
    if files:
        try:
            last = max((json.loads(f.read_text(encoding='utf-8')) for f in files), key=lambda d: d.get("ts") or 0)
            recovery = {"poller_reports": len(files), "last_run_ts": last.get("ts"),
                        "last_recorded": last.get("recorded"),
                        "last_failures": len(last.get("failures") or []),
                        "poller_version": last.get("version")}
        except Exception as e:  # noqa: BLE001
            recovery = {"poller_reports": len(files), "parse_error": str(e)[:80]}
    rep["blocks"]["recovery_status"] = recovery

    share = (conn.execute(
        """SELECT COUNT(DISTINCT o.token_id) * 1.0 / NULLIF((
             SELECT COUNT(*) FROM observation_state WHERE state != 'RESOLVED'), 0) s
           FROM discovery_observations o WHERE o.retrieved_ts >= ? AND o.error_state IS NULL""",
        (day_ago,)).fetchone()["s"])
    conn.close()
    share = share if share is not None else (1.0 if active == 0 else 0.0)
    rep["blocks"]["collection_health"]["share_active_with_fresh_obs_24h"] = share
    if share < 0.30 and (obs_ok_24h == 0 and gaps_total > 0):
        rep["verdict"] = "STARVING"
    elif share < 0.80 or gaps_24h > 0:
        rep["verdict"] = "DEGRADED"
    else:
        rep["verdict"] = "HEALTHY"
    rep["classifier"] = ("STARVING iff share<0.30&no-success&gap>0; DEGRADED iff share<0.80 or "
                         "missed_24h>0; else HEALTHY (frozen, v1)")
    return rep


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(ROOT / "data" / "e01_discovery.sqlite"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    rep = coverage_report(args.store)
    out = Path(args.out) if args.out else ROOT / "reports" / f"coverage_audit_{time.strftime('%Y%m%d_%H%M%S', time.gmtime(rep['ts']))}.json"
    out.write_text(json.dumps(rep, indent=1))
    print(json.dumps({"verdict": rep["verdict"], **{k: (v if not isinstance(v, dict) else "<block>") for k, v in rep["blocks"].items()}}, indent=1))
    print("report ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
