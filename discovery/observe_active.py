#!/usr/bin/env python3
"""F12-O2/O2a — supplemental observation poller (owner-approved, strict evidence bounds).

v1 (2026-08-13 04:30Z): fetch-side consumer of the existing snapshot machinery; selection
ORDER BY first_seen_ts LIMIT cap over due-uncovered tokens. MEASURED DEFECT (R-41): due slots
whose tolerance windows have closed never leave the selection set ⇒ the oldest cohort was
re-attempted forever (identical 40-token head across runs) while legal windows starved.

v2 (2026-08-13, F12-O2a owner directive): selection delegated to the COVERAGE-AWARE
OBSERVATION SCHEDULER (discovery/observation_scheduler.py). Only WINDOW_OPEN slots are
attempted — ranked ① near-expiry open windows ② tracked positions with a legal open window
(tracked set injected; loader reads the paper store READ-ONLY) ③ other coverable tokens.
Expired windows are NEVER attempted (they stay honestly MISSED/UNRECOVERABLE in reports and
are registered as gaps by the existing materialize-sweep path only). RATE_LIMITED
(PAL rate_starved) aborts the run cleanly instead of storming.

UNCHANGED BOUNDARIES (owner directive, both versions): no historical backfill · no fabricated
availability · no retrieved_ts manipulation · no threshold/card/rule changes · PRE_FIX data
byte-frozen · failures recorded EXPLICITLY as error_state rows (never silent, never
substituted) · gap_register never touched by this tool. Segmentation stays dual: new rows are
identifiable by retrieved_ts ≥ run ts AND the explicit obs_id lists in run reports.

DESIGN LAWS: idempotent (INSERT OR IGNORE obs_id) · provenance-preserving (raw payload stored,
sha-joined) · rate-limited (PAL token bucket + max_tokens cap + clean rate-starve abort) ·
failure-tolerant (per-token commit; one provider failure never aborts the run) · observable
(run report incl. slot census) · auditable (obs_ids list) · restart-safe (state derived from
tables only) · duplicate-safe (cooldown + obs_id dedup) · provider-aware · stale-aware.
Rollback path: docs/archive/observe_active_v1_src_20260813.txt (sha in R-43).
"""
from __future__ import annotations
import argparse, json, sqlite3, sys, time
from pathlib import Path

from . import observations as obs
from . import lifecycle
from . import identity
from . import collect as _collect          # reuse: normalize_dex_pairs (no duplication)
from . import observation_scheduler as sch

POLLER_VERSION = "observe_active:v2"
DEFAULT_STORE = Path(__file__).resolve().parent.parent / "data" / "e01_discovery.sqlite"
DEFAULT_TRACKED_STORE = Path(__file__).resolve().parent.parent / "data" / "paper_trading.sqlite"
MIN_INTERVAL_DEFAULT = 240.0              # s+15m slot tolerance is ±300s; 240s keeps slots servable


def load_open_tracked_tokens(store_path: str | None) -> tuple[frozenset, str | None]:
    """Open paper positions' token ids, READ-ONLY. Generic tracked-set source: any future
    position-tracking consumer can be wired the same way. Absence degrades to no tier-2 boost."""
    if not store_path:
        return frozenset(), None
    p = Path(store_path)
    if not p.exists():
        return frozenset(), f"tracked_store_missing:{p.name}"
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        rows = conn.execute(
            """SELECT DISTINCT t.token_id FROM paper_trade_v2 t
               LEFT JOIN paper_exit_v2 x  ON x.trade_id  = t.trade_id
               LEFT JOIN paper_exit_v3 x3 ON x3.trade_id = t.trade_id
               WHERE x.trade_id IS NULL AND x3.trade_id IS NULL""").fetchall()
        conn.close()
        return frozenset(r[0] for r in rows), None
    except Exception as e:  # noqa: BLE001 — degrade, disclose, never crash the poller
        return frozenset(), f"tracked_store_unreadable:{type(e).__name__}"


def _our_pairs(conn, token_id: str) -> dict:
    return {r["pair_address"]: r["pair_id"] for r in
            conn.execute("SELECT pair_id, pair_address FROM pairs WHERE token_id=?", (token_id,))}


def _record_failure(conn, tid, pid, provider, endpoint, now, http_status, payload,
                    error_state, dry_run):
    if dry_run:
        return None
    sha = obs.store_raw(conn, provider, endpoint, now, http_status,
                        payload if payload is not None else {"error_state": error_state})
    oid = obs.record_observation(conn, tid, provider, now, sha, pair=pid,
                                 source_ts=None, metrics=None, error_state=error_state)
    inserted = conn.execute("SELECT changes()").fetchone()[0]   # INSERT OR IGNORE dedup-aware
    conn.commit()
    return oid if inserted else None


def run_observe_active(conn, *, now: float | None = None, fetch, dry_run: bool = False,
                       max_tokens: int = 40, min_interval: float = MIN_INTERVAL_DEFAULT,
                       near_expiry_s: float = sch.NEAR_EXPIRY_DEFAULT,
                       tracked=frozenset(), tracked_note: str | None = None,
                       sleep_s: float = 0.0) -> dict:
    """One poller pass. `fetch(chain, address, now) -> PAL-style envelope` (injected for tests)."""
    now = time.time() if now is None else now
    plan = sch.build_plan(conn, now, tracked=tracked, min_interval=min_interval,
                          near_expiry_s=near_expiry_s)
    selected = plan["candidates"][:max_tokens]
    rep = {"tool": "observe_active", "version": POLLER_VERSION,
           "scheduler_version": sch.SCHEDULER_VERSION, "ts": now, "dry_run": dry_run,
           "max_tokens": max_tokens, "min_interval": min_interval,
           "near_expiry_s": near_expiry_s,
           "tracked_size": len(plan["tracked_size"] and tracked or tracked),
           "tracked_note": tracked_note,
           "eligible_total": len(plan["candidates"]),
           "not_selected_by_cap": len(plan["candidates"]) - len(selected),
           "by_state": plan["counts"]["by_state"],
           "skipped_cooldown": plan["counts"]["skipped_cooldown"],
           "selected": [{"token_id": c["token_id"], "tier": c["tier"],
                         "open_slots": c["open_slots"], "close_ts": c["close_ts"]}
                        for c in selected],
           "aborted": None, "not_attempted": 0,
           "attempted": 0, "recorded": 0, "would_record": 0,
           "failures": [], "obs_ids": []}
    for i, cand in enumerate(selected):
        tid, chain, address = cand["token_id"], cand["chain_id"], cand["address"]
        if i and sleep_s:
            time.sleep(sleep_s)
        rep["attempted"] += 1
        pid_candidates = _our_pairs(conn, tid)
        canonical_pid = next(iter(pid_candidates.values()), None)
        env = fetch(chain, address, now)
        provider = env.get("provider_id") or "unknown"
        endpoint = env.get("endpoint") or ""
        if env.get("availability") != "OK":
            kind = (env.get("error_state") or {}).get("kind")
            if kind == "rate_starved":                            # RATE_LIMITED — stop cleanly
                es = {"kind": "rate_limited", "detail": env.get("error_state"),
                      "endpoint": endpoint}
                oid = _record_failure(conn, tid, canonical_pid, provider, endpoint, now,
                                      env.get("http_status"), env.get("payload"), es, dry_run)
                rep["failures"].append({"token_id": tid, "kind": "rate_limited",
                                        "obs_id": oid, "provider": provider,
                                        "tier": cand["tier"], "slots": cand["open_slots"]})
                rep["aborted"] = "rate_budget_exhausted"
                rep["not_attempted"] = len(selected) - rep["attempted"]
                break
            es = {"kind": "provider_unavailable", "detail": env.get("error_state"),  # PROVIDER_FAILED
                  "endpoint": endpoint}
            oid = _record_failure(conn, tid, canonical_pid, provider, endpoint, now,
                                  env.get("http_status"), env.get("payload"), es, dry_run)
            rep["failures"].append({"token_id": tid, "kind": es["kind"],
                                    "obs_id": oid, "provider": provider,
                                    "tier": cand["tier"], "slots": cand["open_slots"]})
            continue
        if provider != "dexscreener":
            es = {"kind": "unsupported_provider_payload", "provider": provider}
            oid = _record_failure(conn, tid, canonical_pid, provider, endpoint, now,
                                  env.get("http_status"), env.get("payload"), es, dry_run)
            rep["failures"].append({"token_id": tid, "kind": es["kind"], "obs_id": oid,
                                    "provider": provider, "tier": cand["tier"],
                                    "slots": cand["open_slots"]})
            continue
        recs = _collect.normalize_dex_pairs(env.get("payload"), chain) or []
        # wrong-token hard guard: metrics must describe the QUERIED token only.
        recs = [r for r in recs if (r.get("address") or "").lower() == (address or "").lower()]
        matched = [r for r in recs if r.get("pair_address") in pid_candidates]
        rec = matched[0] if matched else max(
            recs, key=lambda r: (r["metrics"].get("liquidity_usd") or 0), default=None)
        if rec is None or not (rec["metrics"].get("price_usd")):
            es = {"kind": "no_valid_price", "endpoint": endpoint}
            oid = _record_failure(conn, tid, canonical_pid, provider, endpoint, now,
                                  env.get("http_status"), env.get("payload"), es, dry_run)
            rep["failures"].append({"token_id": tid, "kind": "no_valid_price", "obs_id": oid,
                                    "provider": provider, "tier": cand["tier"],
                                    "slots": cand["open_slots"]})
            continue
        pid = pid_candidates.get(rec.get("pair_address")) if matched else None
        if dry_run:
            rep["would_record"] += 1       # dry-run never counts as recorded (nothing is written)
            continue
        sha = obs.store_raw(conn, provider, endpoint, now, env.get("http_status"), env["payload"])
        metrics = dict(rec["metrics"])
        if rec.get("pool_created_ts"):
            metrics["pair_age_minutes"] = max(0, int((now - rec["pool_created_ts"]) / 60))
        oid = obs.record_observation(conn, tid, provider, now, sha, pair=pid,
                                     source_ts=None, metrics=metrics)
        inserted = conn.execute("SELECT changes()").fetchone()[0]
        if inserted:
            lifecycle.on_observation(conn, tid, now)
        conn.commit()
        if inserted:
            rep["recorded"] += 1
            rep["obs_ids"].append(oid)
        else:
            rep["deduped"] = rep.get("deduped", 0) + 1          # re-served same instant: swallowed
    return rep


def main(argv=None) -> int:
    from . import pal
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--tracked-store", default=str(DEFAULT_TRACKED_STORE),
                    help="paper store for tier-2 tracked-position boost (RO); '' disables")
    ap.add_argument("--max-tokens", type=int, default=40)
    ap.add_argument("--min-interval", type=float, default=MIN_INTERVAL_DEFAULT)
    ap.add_argument("--near-expiry", type=float, default=sch.NEAR_EXPIRY_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)
    p = pal.PAL()

    def fetch(chain, address, now):
        return p.clients["dexscreener_tokens"].fetch("token_pairs", "pair_enrich",
                                                     chain=chain, address=address, now=now)

    tracked, tracked_note = load_open_tracked_tokens(args.tracked_store)
    conn = obs.open_store(args.store)
    rep = run_observe_active(conn, now=time.time(), fetch=fetch, dry_run=args.dry_run,
                             max_tokens=args.max_tokens, min_interval=args.min_interval,
                             near_expiry_s=args.near_expiry, tracked=tracked,
                             tracked_note=tracked_note)
    conn.close()
    out = Path(args.report) if args.report else (
        Path(__file__).resolve().parent.parent / "reports" /
        f"observe_active_{time.strftime('%Y%m%d_%H%M%S', time.gmtime(rep['ts']))}.json")
    out.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    slim = {k: v for k, v in rep.items() if k not in ("obs_ids", "selected")}
    slim["obs_ids"] = f"{len(rep['obs_ids'])} recorded"
    print(json.dumps(slim, indent=1, ensure_ascii=False))
    print("report ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
