#!/usr/bin/env python3
"""AHOS Month 1 — Controlled Failure Matrix (Phase 2 of the Operational Gate).

Deliberately injects failures into REAL components (no mocks of the system
under test — only fault injection at the edges: transport, time, process,
sqlite) and verifies every failure is either FAIL-CLOSED or EXPLICITLY
OBSERVABLE. Never fabricates a success.

Categories: SCHEDULER · PROVIDERS · PERSISTENCE · SAFETY.

Usage:
    python scripts/month1_failure_matrix.py            # run all, write JSON evidence
    python scripts/month1_failure_matrix.py --json -   # print JSON to stdout only

Output: reports/month1_failure_matrix.json (+ per-scenario evidence fields).
Exit 0 iff every scenario verdict is PASS.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.scheduling import engine as sched_engine
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask
from architecture.scheduling import watchdog
from architecture.providers.adapters import DexScreenerAdapter
from architecture.providers.coingecko import CoinGeckoAdapter
from architecture.providers.chain_explorer import ChainExplorerAdapter
from architecture.providers.collect import ProviderCollector
from architecture.providers.contracts import NormalizedTokenCandidate
from architecture.scoring.engine import OpportunityScorer
from architecture.runtime.observation_loop import RuntimeSafetyGate

RESULTS: list[dict] = []


def force_kill(proc: subprocess.Popen, *, wait_timeout: float = 15.0) -> None:
    """Abruptly stop a child process for crash-injection scenarios.

    ``signal.SIGKILL`` is POSIX-only and raises ``AttributeError`` on Windows.
    ``Popen.kill()`` is the portable equivalent: SIGKILL on POSIX, and
    ``TerminateProcess`` on Windows. ``terminate()`` is tried first so a
    cooperative child can exit; ``kill()`` escalates if it stays alive so the
    lease/DB crash path still runs against a truly dead process.
    """
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
    except OSError:
        pass
    try:
        proc.wait(timeout=min(2.0, wait_timeout))
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        proc.kill()
    except OSError:
        pass
    proc.wait(timeout=wait_timeout)


def record(category: str, name: str, fault: str, expected: str,
           passed: bool, evidence: str) -> None:
    RESULTS.append({
        "category": category, "scenario": name, "injected_fault": fault,
        "expected_behavior": expected, "verdict": "PASS" if passed else "FAIL",
        "evidence": evidence,
    })
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {category}/{name}: {evidence[:140]}")


def fresh_scheduler(workdir: Path, lease_duration: float = 300.0) -> ProductionScheduler:
    return ProductionScheduler(
        db_path=str(workdir / "local.sqlite"),
        discovery_db_path=str(workdir / "discovery.sqlite"),
        lease_duration_sec=lease_duration,
    )


def make_discovery_schema(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS observation_state (
            token_id TEXT PRIMARY KEY, state TEXT NOT NULL, first_seen_ts REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS discovery_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, token_id TEXT NOT NULL, retrieved_ts REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS gap_register (
            id INTEGER PRIMARY KEY AUTOINCREMENT, token_id TEXT NOT NULL,
            kind TEXT NOT NULL, expected_ts REAL, noted_ts REAL, detail TEXT);
    """)
    conn.commit()
    conn.close()


# =============================== fault transports ==============================

class ExplodingTransport:
    def __call__(self, req, timeout=10):
        raise ConnectionError("network unreachable (injected)")


class TimeoutTransport:
    def __call__(self, req, timeout=10):
        raise TimeoutError("simulated provider timeout (injected)")


class RawResponse:
    def __init__(self, raw: bytes, status: int = 200):
        self._raw, self.status = raw, status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._raw


class MalformedTransport:
    """200 status, garbage bytes."""

    def __call__(self, req, timeout=10):
        return RawResponse(b"not-json{{{")


class PartialTransport:
    """Valid JSON, most fields missing."""

    def __call__(self, req, timeout=10):
        url = req.full_url
        if "dexscreener" in url:
            return RawResponse(json.dumps({"pairs": [{"baseToken": {"symbol": "X"}}]}).encode())
        return RawResponse(json.dumps({"market_data": {}}).encode())


# ================================ SCHEDULER ====================================

class _FakeTime:
    def __init__(self, wall_offset: float):
        self._off = wall_offset

    def time(self):
        return time.time() + self._off

    def monotonic(self):
        return time.monotonic()


def matrix_scheduler(workdir: Path) -> None:
    ran: list[str] = []

    def task(label: str):
        def _t():
            ran.append(label)
        return ScheduleTask(task_id=label, target_offset_sec=0, tolerance_sec=5,
                            action_fn=_t, label=label)

    # 1. normal cycle
    s = fresh_scheduler(workdir)
    r = s.execute_scheduled_cycle("M_NORMAL", [task("t1")])
    lock_left = sqlite3.connect(str(workdir / "local.sqlite")).execute(
        "SELECT COUNT(*) FROM scheduler_locks WHERE lock_name='M_NORMAL'").fetchone()[0]
    ok = r["status"] == "SUCCESS" and ran == ["t1"] and lock_left == 0
    record("SCHEDULER", "normal_cycle", "none (baseline)",
           "SUCCESS + task executed + lease released", ok,
           f"status={r['status']} tasks={r.get('tasks_executed')} locks_left={lock_left}")

    # 2. duplicate cycle (sequential re-run is legal — lease released between)
    r2 = s.execute_scheduled_cycle("M_NORMAL", [task("t2")])
    rows = sqlite3.connect(str(workdir / "local.sqlite")).execute(
        "SELECT COUNT(*) FROM scheduler_runs WHERE schedule_name='M_NORMAL'").fetchone()[0]
    ok = r2["status"] == "SUCCESS" and rows == 2 and ran == ["t1", "t2"]
    record("SCHEDULER", "duplicate_cycle_sequential", "same schedule re-entered",
           "second run SUCCESS, both runs recorded distinctly", ok,
           f"second={r2['status']} run_rows={rows}")

    # 3. overlapping cycle (lease held by 'another' runner)
    s3 = fresh_scheduler(workdir)
    s3.acquire_lease("M_OVERLAP", "other_run", time.time())
    r3 = s3.execute_scheduled_cycle("M_OVERLAP", [task("t3")])
    ok = r3["status"] == "SKIPPED_LOCKED" and "t3" not in ran
    record("SCHEDULER", "overlapping_cycle", "foreign live lease on lock",
           "SKIPPED_LOCKED, task NOT executed", ok, f"status={r3['status']}")

    # 4. stale lease takeover
    s4 = fresh_scheduler(workdir)
    conn = sqlite3.connect(str(workdir / "local.sqlite"))
    conn.execute("INSERT OR REPLACE INTO scheduler_locks VALUES ('M_STALE','ghost',?,?)",
                 (time.time() - 9999, time.time() - 9000))
    conn.commit(); conn.close()
    r4 = s4.execute_scheduled_cycle("M_STALE", [task("t4")])
    ok = r4["status"] == "SUCCESS" and "t4" in ran
    record("SCHEDULER", "stale_lease_takeover", "expired lease left by dead holder",
           "lease reclaimed, cycle SUCCESS", ok, f"status={r4['status']}")

    # 5+23. crashed process holding lease, then recovery after expiry
    # (crasher acquires a 1s lease; parent must be refused while it lives and
    #  take over only after real expiry — real timing, no fudged timestamps)
    s5 = fresh_scheduler(workdir, lease_duration=1.0)
    crasher = subprocess.Popen(
        [sys.executable, "-c",
         "import sys,time;sys.path.insert(0,%r);"
         "from architecture.scheduling.engine import ProductionScheduler;"
         "s=ProductionScheduler(db_path=%r, discovery_db_path=%r, lease_duration_sec=1.0);"
         "print(s.acquire_lease('M_CRASH','crash_run',time.time()),flush=True);time.sleep(60)"
         % (str(ROOT), str(workdir / "local.sqlite"), str(workdir / "discovery.sqlite"))],
        stdout=subprocess.PIPE, text=True)
    acquired = crasher.stdout.readline().strip()
    time.sleep(0.5)
    force_kill(crasher)
    # immediate takeover attempt against a LIVE-duration lease must be refused
    r5a = s5.execute_scheduled_cycle("M_CRASH", [task("t5")])
    # but our scheduler instance uses lease_duration=1s => after expiry it takes over
    time.sleep(1.2)
    r5b = s5.execute_scheduled_cycle("M_CRASH", [task("t5")])
    ok = (r5a["status"] == "SKIPPED_LOCKED" and r5b["status"] == "SUCCESS"
          and "t5" in ran and acquired == "True")
    record("SCHEDULER", "crashed_process_recovery",
           "hard-kill of lease holder mid-run (terminate/kill)",
           "refused while lease live; takeover after expiry; recovery SUCCESS", ok,
           f"immediate={r5a['status']} after_expiry={r5b['status']}")

    # 6. delayed process -> downtime honestly measured
    s6 = fresh_scheduler(workdir)
    t0 = time.time()
    s6.record_heartbeat("M_DELAY", now=t0)
    r6 = s6.execute_scheduled_cycle("M_DELAY", [], now=t0 + 3600.0)
    ok = abs(r6.get("downtime_detected_sec", -1) - 3600.0) < 1.0
    record("SCHEDULER", "delayed_process", "1h heartbeat gap",
           "downtime_detected_sec ~3600 recorded (visible, not hidden)", ok,
           f"downtime={r6.get('downtime_detected_sec')}")

    # 7/8. clock steps
    s7 = fresh_scheduler(workdir)
    saved = sched_engine.time
    try:
        sched_engine.time = _FakeTime(+600.0)
        rf = s7.check_clock_drift()
        sched_engine.time = _FakeTime(-3600.0)
        rb = s7.check_clock_drift()
    finally:
        sched_engine.time = saved
    ok = rf > 595.0 and rb > 3500.0
    record("SCHEDULER", "clock_step_forward_backward", "+600s then -3600s wall step",
           "drift measured; cycle would ABORTED_DRIFT (unit-proven)", ok,
           f"forward={rf:.1f}s backward={rb:.1f}s")

    # 9/10. watchdog
    db9 = str(workdir / "local.sqlite")
    s9 = fresh_scheduler(workdir)
    s9.record_heartbeat("M_WD", now=time.time() - 1000.0)
    rep = watchdog.watchdog_report(db9, max_age_sec=300)
    ok = rep["status"] == "STALE" and rep["stale_components"][0]["component"] == "M_WD"
    record("SCHEDULER", "watchdog_detection", "1000s-silent component",
           "status STALE, component named", ok, f"status={rep['status']}")

    rep10 = watchdog.watchdog_report(str(workdir / "nope.sqlite"), max_age_sec=300)
    ok = rep10["status"] == "NO_HEARTBEATS"
    record("SCHEDULER", "watchdog_fail_closed", "missing heartbeat DB",
           "NO_HEARTBEATS (never reported OK on absent evidence)", ok,
           f"status={rep10['status']}")


# ================================ PROVIDERS ====================================

def matrix_providers() -> None:
    # 11. provider unavailable
    resp = DexScreenerAdapter(transport=ExplodingTransport()).fetch_token_metrics("solana", "X1")
    ok = resp.status in ("DOWN", "ERROR") and resp.tokens == []
    record("PROVIDERS", "provider_unavailable", "ConnectionError on transport",
           "fail-closed envelope, zero tokens", ok,
           f"status={resp.status} tokens={len(resp.tokens)}")

    # 12. timeout
    resp = CoinGeckoAdapter(transport=TimeoutTransport()).fetch_token_metrics("ethereum", "0x1")
    ok = resp.status in ("DOWN", "ERROR") and resp.tokens == []
    record("PROVIDERS", "provider_timeout", "TimeoutError on transport",
           "fail-closed envelope, zero tokens", ok, f"status={resp.status}")

    # 13. malformed response
    resp = DexScreenerAdapter(transport=MalformedTransport()).fetch_token_metrics("solana", "X2")
    ok = resp.status in ("DOWN", "ERROR") and resp.tokens == []
    record("PROVIDERS", "malformed_response", "HTTP 200 with garbage bytes",
           "fail-closed envelope, no crash, no partial parse", ok, f"status={resp.status}")

    # 14. partial response -> UNKNOWN preserved
    resp = DexScreenerAdapter(transport=PartialTransport()).fetch_token_metrics("solana", "X3")
    tok = resp.tokens[0] if resp.tokens else None
    ok = (resp.status == "OK" and tok is not None and tok.metrics.liquidity_usd is None
          and "metrics.liquidity_usd" in tok.unknown_fields)
    record("PROVIDERS", "partial_response", "payload missing most fields",
           "parse OK; absent fields stay UNKNOWN (listed)", ok,
           f"status={resp.status} liquidity={tok.metrics.liquidity_usd if tok else 'n/a'}")

    # 15. conflicting provider data (through unified collect)
    class ConflictingTransport:
        def __call__(self, req, timeout=10):
            url = req.full_url
            if "dexscreener" in url:
                return RawResponse(json.dumps({"pairs": [{
                    "baseToken": {"symbol": "C"}, "priceUsd": "0.10",
                    "liquidity": {"usd": 1000.0}}]}).encode())
            if "coingecko" in url:
                return RawResponse(json.dumps({"symbol": "c", "name": "C",
                    "market_data": {"current_price": {"usd": 0.99}}}).encode())
            return RawResponse(json.dumps({"data": {"attributes": {}}}).encode())
    outcome = ProviderCollector(transport=ConflictingTransport()).collect("ethereum", "0xC")
    ok = (outcome.candidate.metrics.price_usd == 0.10
          and any("metrics.price_usd" in c for c in outcome.conflicts)
          and outcome.field_sources["metrics.price_usd"] == "dexscreener")
    record("PROVIDERS", "conflicting_provider_data", "0.10 vs 0.99 across providers",
           "first-provider-wins + conflict explicitly logged", ok,
           f"kept={outcome.candidate.metrics.price_usd} conflicts={len(outcome.conflicts)}")

    # 16. completely unavailable fields
    outcome = ProviderCollector(transport=PartialTransport()).collect("solana", "Zz")
    cand = outcome.candidate
    ok = (cand.metrics.liquidity_usd is None and cand.confidence_level in ("LOW", "MED")
          and len(cand.unknown_fields) > 10)
    record("PROVIDERS", "all_fields_unavailable", "empty payloads everywhere",
           "all-UNKNOWN candidate, LOW/MED confidence, unknowns listed", ok,
           f"unknown_fields={len(cand.unknown_fields)} confidence={cand.confidence_level}")

    # 17. unsupported chain discipline
    r_cg = CoinGeckoAdapter(transport=ExplodingTransport()).fetch_token_metrics("cardano", "a")
    r_ex = ChainExplorerAdapter(transport=ExplodingTransport()).fetch_token_metrics("solana", "b")
    r_disc = CoinGeckoAdapter(transport=ExplodingTransport()).fetch_candidate_tokens("solana")
    ok = (r_cg.status == "ERROR" and r_ex.status == "UNSUPPORTED"
          and r_disc.status == "UNSUPPORTED" and not (r_cg.tokens or r_ex.tokens or r_disc.tokens))
    record("PROVIDERS", "unsupported_chain", "cardano on CoinGecko; solana on explorer; discovery on CG",
           "ERROR/UNSUPPORTED envelopes; never fabricated data", ok,
           f"cg={r_cg.status} explorer={r_ex.status} discovery={r_disc.status}")

    # 18. unknown-field accounting completeness
    cand = NormalizedTokenCandidate(chain="solana", address="A", symbol="S", name="N")
    unknowns = cand.identify_unknowns()
    n_metrics = 16 + 12  # MarketMetrics + SecuritySignals fields
    ok = len(unknowns) >= n_metrics and all(v is None for v in
           list(cand.metrics.__dict__.values()) + list(cand.security.__dict__.values()))
    record("PROVIDERS", "unknown_field_discipline", "fresh candidate, no data",
           f">={n_metrics} UNKNOWN fields explicitly tracked; all values None", ok,
           f"tracked={len(unknowns)}")


# ================================ PERSISTENCE ==================================

def matrix_persistence(workdir: Path) -> None:
    # 19. restart continuity
    sa = fresh_scheduler(workdir)
    sa.execute_scheduled_cycle("M_RESTART", [])
    del sa
    sb = fresh_scheduler(workdir)
    rb = sb.execute_scheduled_cycle("M_RESTART", [])
    conn = sqlite3.connect(str(workdir / "local.sqlite"))
    rows = conn.execute("SELECT COUNT(*) FROM scheduler_runs WHERE schedule_name='M_RESTART'").fetchone()[0]
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()
    ok = rb["status"] == "SUCCESS" and rows == 2 and integrity == "ok"
    record("PERSISTENCE", "restart_continuity", "process replaced between cycles",
           "state persists, runs accumulate, DB integrity ok", ok,
           f"rows={rows} integrity={integrity}")

    # 20. interrupted write (hard-kill mid-transaction)
    idb = str(workdir / "interrupted.sqlite")
    crasher = subprocess.Popen(
        [sys.executable, "-c",
         "import sqlite3,time;c=sqlite3.connect(%r);"
         "c.execute('CREATE TABLE t(x INTEGER)');c.commit();"
         "c.execute('INSERT INTO t VALUES (42)');print('ready',flush=True);time.sleep(60)" % idb],
        stdout=subprocess.PIPE, text=True)
    crasher.stdout.readline()
    time.sleep(0.3)
    force_kill(crasher)
    conn = sqlite3.connect(idb)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    rows = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    conn.close()
    ok = integrity == "ok" and rows == 0
    record("PERSISTENCE", "interrupted_write",
           "hard-kill with open uncommitted INSERT (terminate/kill)",
           "transaction rolled back; no partial row; DB not corrupted", ok,
           f"rows={rows} integrity={integrity}")

    # 21. repeated observation -> distinct runs
    sc = fresh_scheduler(workdir)
    ra1 = sc.execute_scheduled_cycle("M_REPEAT", [])
    ra2 = sc.execute_scheduled_cycle("M_REPEAT", [])
    ok = ra1["run_id"] != ra2["run_id"] and ra1["status"] == ra2["status"] == "SUCCESS"
    record("PERSISTENCE", "repeated_observation", "same schedule twice",
           "distinct run_ids; both recorded once", ok,
           f"ids {ra1['run_id'][:8]}.. vs {ra2['run_id'][:8]}..")

    # 22. duplicate event rejected by schema
    dup = False
    try:
        conn = sqlite3.connect(str(workdir / "local.sqlite"))
        conn.execute("INSERT INTO scheduler_runs(run_id,schedule_name,started_ts,status,clock_drift_sec)"
                     " VALUES ('DUPID','X',1.0,'RUNNING',0.0)")
        conn.commit()
        conn.execute("INSERT INTO scheduler_runs(run_id,schedule_name,started_ts,status,clock_drift_sec)"
                     " VALUES ('DUPID','X',1.0,'RUNNING',0.0)")
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        dup = True
    record("PERSISTENCE", "duplicate_event_rejected", "identical PK inserted twice",
           "PRIMARY KEY rejects duplicate event", dup, f"integrity_error_raised={dup}")

    # 23b. missed-window registration honesty (gap register, no backfill)
    make_discovery_schema(workdir / "discovery.sqlite")
    conn = sqlite3.connect(str(workdir / "discovery.sqlite"))
    t0 = time.time() - 30 * 3600.0
    conn.execute("INSERT INTO observation_state VALUES ('tokA','OBSERVING',?)", (t0,))
    conn.commit(); conn.close()
    sc23 = fresh_scheduler(workdir)
    missed = sc23.audit_and_register_missed_windows()
    conn = sqlite3.connect(str(workdir / "discovery.sqlite"))
    gaps = conn.execute("SELECT COUNT(*) FROM gap_register WHERE token_id='tokA'").fetchone()[0]
    backfilled = conn.execute("SELECT COUNT(*) FROM discovery_observations WHERE token_id='tokA'").fetchone()[0]
    conn.close()
    ok = gaps > 0 and backfilled == 0
    record("PERSISTENCE", "missed_windows_registered_not_backfilled",
           "token with 30h-old first_seen, zero observations",
           "missed slots registered in gap_register; NO fabricated observations", ok,
           f"gaps={gaps} backfilled_rows={backfilled}")


# ============================ COLLECTOR (GAP-002) ==============================

def matrix_collector(workdir: Path) -> None:
    # 29. collector-level provider failure is durable & visible (GAP-002:
    # discovered live during the soak pilot — outages were silent)
    from architecture.collector.engine import CollectorEngine
    from architecture.providers.registry import ProviderRouter

    cdb = str(workdir / "collector_discovery.sqlite")
    engine = CollectorEngine(db_path=cdb, router=ProviderRouter(transport=ExplodingTransport()))
    records = engine.collect_candidates("solana", limit=5)
    conn = sqlite3.connect(cdb)
    events = conn.execute("SELECT kind, provider_id FROM provider_failure_events").fetchall()
    conn.close()
    errs = [e for e in events if e[0] == "FETCH_ERROR"]
    ok = (records == [] and {e[1] for e in errs} == {"dexscreener", "geckoterminal"})
    record("PROVIDERS", "collector_failure_durable_visible",
           "network-dead providers at collector level",
           "zero candidates AND durable FETCH_ERROR events (visible, survives restart)",
           ok, f"records={len(records)} fetch_errors={len(errs)}")


# ================================== SAFETY =====================================

def matrix_safety(workdir: Path) -> None:
    # 24. no fabrication on total provider failure
    outcome = ProviderCollector(transport=ExplodingTransport()).collect("solana", "SAF")
    ok = (outcome.candidate.metrics.liquidity_usd is None
          and outcome.candidate.confidence_level == "LOW"
          and len(outcome.candidate.unknown_fields) > 0)
    record("SAFETY", "no_fabricated_provider_data", "every provider unreachable",
           "all-UNKNOWN LOW candidate; exception never escapes", ok,
           f"unknowns={len(outcome.candidate.unknown_fields)} conf={outcome.candidate.confidence_level}")

    # 25. no fabricated score
    cand = NormalizedTokenCandidate(chain="solana", address="SAF2", symbol="S", name="N")
    rep = OpportunityScorer().evaluate(cand, now=1755000000.0)
    missing = rep.answer_missing()
    ok = rep.opportunity_score == 0.0 and rep.confidence_level == "LOW" and len(missing) > 0
    record("SAFETY", "no_fabricated_score", "candidate with zero data fields",
           "score 0.0, confidence LOW, missing-evidence list non-empty", ok,
           f"score={rep.opportunity_score} conf={rep.confidence_level} missing={len(missing)}")

    # 26. env safety veto
    os.environ["AHOS_EXECUTE_LIVE_TRADES"] = "1"
    try:
        verdict = RuntimeSafetyGate(root=ROOT).check()
        ok = not verdict.ok and any("env_safety_veto" in r for r in verdict.reasons)
    finally:
        del os.environ["AHOS_EXECUTE_LIVE_TRADES"]
    record("SAFETY", "env_live_trading_veto", "AHOS_EXECUTE_LIVE_TRADES=1",
           "safety gate vetoes (fail-closed before any cycle)", ok,
           f"ok={verdict.ok} reasons={verdict.reasons[:1]}")

    # 27. Lane-A freeze drift veto
    fake_root = workdir / "frozen_ws"
    (fake_root / "config").mkdir(parents=True, exist_ok=True)
    (fake_root / "config" / "lane_a_freeze.sha256").write_text(
        "# fake manifest\n0000  discovery/collect.py\n", encoding="utf-8")
    verdict27 = RuntimeSafetyGate(root=fake_root).check()
    ok = not verdict27.ok and any("lane_a" in r for r in verdict27.reasons)
    record("SAFETY", "lane_a_freeze_drift_veto", "manifest hash mismatch workspace",
           "observation cycle vetoed on unverifiable Lane-A freeze", ok,
           f"ok={verdict27.ok} reasons={verdict27.reasons[:1]}")

    # 28. no real-money execution surface (static)
    import subprocess as sp
    grep = sp.run(
        ["grep", "-rEn", "--include=*.py",
         r"import ccxt|import web3|from web3|\.place_order\(|\.create_order\(",
         str(ROOT / "architecture"), str(ROOT / "telegram_ai"), str(ROOT / "paper_trading")],
        capture_output=True, text=True)
    hits = [ln for ln in grep.stdout.splitlines() if ln.strip()]
    ok = len(hits) == 0
    record("SAFETY", "no_execution_surface",
           "static scan (execution-surface patterns: SDK imports, order calls)",
           "no exchange SDK import, no order-placement call in source "
           "(broad 1st-pass hit was the sanitizer's own 'private_key' deny-list literal)",
           ok, f"hits={len(hits)}{hits[:1]}")


# ==================================== main =====================================

def run_all(workdir: Path | None = None) -> list[dict]:
    own_tmp = workdir is None
    workdir = workdir or Path(tempfile.mkdtemp(prefix="ahos_failure_matrix_"))
    matrix_scheduler(workdir)
    matrix_providers()
    matrix_persistence(workdir)
    matrix_collector(workdir)
    matrix_safety(workdir)
    if own_tmp:
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)
    return RESULTS


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=None,
                    help="write JSON evidence to this path ('-' = stdout)")
    args = ap.parse_args(argv)

    results = run_all()
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    failed = len(results) - passed
    summary = {
        "executed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(results), "passed": passed, "failed": failed,
        "scenarios": results,
    }

    out_path = args.json
    if out_path == "-":
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    else:
        target = Path(out_path) if out_path else ROOT / "reports" / "month1_failure_matrix.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str),
                          encoding="utf-8")
        print(f"\nevidence written: {target}")
    print(f"TOTAL={len(results)} PASS={passed} FAIL={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
