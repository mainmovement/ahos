#!/usr/bin/env python3
"""F12-O2a — COVERAGE-AWARE OBSERVATION SCHEDULER (owner directive 2026-08-13).
Tests written BEFORE the scheduler module exists (owner build order: tests first).

Owner-mandated battery (12) + clarifying edges. Network-free: the scheduler is pure /
read-only against a fixture store (real schema); poller runs use injected fake fetches.

Pinned laws: expired windows are NEVER attempted (only honestly classified MISSED /
UNRECOVERABLE) · open legal windows served by tier (near-expiry → tracked positions → other
coverable) · selection is no longer ORDER BY first_seen + LIMIT · true timestamps only ·
duplicate-safe · RATE_LIMITED aborts cleanly · restart-safe · rotation fairness ·
PRE_FIX/POST_FIX byte-isolation · every Lane-A frozen file sha-pinned · scheduler
classification ≡ lifecycle.due_snapshots semantics (exact property, seeds fixed).
"""
from __future__ import annotations

import hashlib
import random
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from discovery import observations as obs           # noqa: E402
from discovery import lifecycle                     # noqa: E402
from discovery import observe_active as oa          # noqa: E402
from discovery import observation_scheduler as sch  # noqa: E402  (created by F12-O2a)

T0 = 1_786_500_000.0


# ---------------- fixtures ----------------
def _mk(conn, chain, addr, t0, price=1.0):
    tid = obs.upsert_token(conn, chain, addr, first_seen_ts=t0, provider="fx", symbol=addr[-4:])
    raw0 = obs.store_raw(conn, "fx", f"/fx/{addr}", t0, 200, {"fx": addr})
    pid = obs.upsert_pair(conn, chain, "raydium", f"pair_{addr}", tid, t0, "fx", raw0)
    lifecycle.register_discovery(conn, tid, t0)
    obs.record_observation(conn, tid, "fx", t0, raw0, pair=pid, metrics={"price_usd": price})
    lifecycle.on_observation(conn, tid, t0)
    return tid


def _store(tmp_path, spec):
    conn = obs.open_store(tmp_path / "fx.sqlite")
    ids = {addr: _mk(conn, chain, addr, t0) for chain, addr, t0 in spec}
    conn.commit()
    return conn, ids


def _env_ok(addr, price=2.0):
    return {"availability": "OK", "provider_id": "dexscreener",
            "endpoint": f"/tokens/v1/solana/{addr}", "http_status": 200,
            "payload": [{"chainId": "solana", "pairAddress": f"pair_{addr}",
                         "dexId": "raydium", "priceUsd": str(price),
                         "baseToken": {"address": addr, "symbol": "X", "name": "X"},
                         "quoteToken": {"symbol": "SOL"}, "liquidity": {"usd": 50000},
                         "fdv": 1_000_000, "marketCap": 900_000, "volume": {"h24": 1000},
                         "txns": {}, "priceChange": {}}]}


def _fetcher(envelopes, calls=None):
    def f(chain, address, now):
        if calls is not None:
            calls.append(address)
        return envelopes[(chain, address)]
    return f


# ----- 1 · queue starvation: uncoverable backlog can never starve legal windows -----
def test_queue_starvation_prevention(tmp_path):
    now = T0 + 6 * 3600
    spec = [("solana", f"OLD{i}", T0) for i in range(12)]      # s+15m/s+1h/s+4h all MISSED by now
    spec += [("solana", "FRESH1", T0 + 7000), ("solana", "FRESH2", T0 + 7000)]  # s+4h OPEN now
    conn, ids = _store(tmp_path, spec)
    plan = sch.build_plan(conn, now)
    assert {c["token_id"] for c in plan["candidates"]} == {ids["FRESH1"], ids["FRESH2"]}
    assert plan["counts"]["by_state"]["MISSED"] >= 12 * 3      # backlog honestly classified
    rep = oa.run_observe_active(conn, now=now, min_interval=0, fetch=_fetcher({
        ("solana", "FRESH1"): _env_ok("FRESH1"), ("solana", "FRESH2"): _env_ok("FRESH2")}))
    assert rep["attempted"] == 2 and rep["recorded"] == 2
    n_old = conn.execute("SELECT COUNT(*) FROM discovery_observations WHERE token_id=?",
                         (ids["OLD0"],)).fetchone()[0]
    assert n_old == 1                                          # never re-fetched past windows


# ----- 2 · repeated-head overlap: coverage removes candidates ⇒ empty intersections -----
def test_no_repeated_head_overlap(tmp_path):
    spec = [("solana", f"W{i}", T0) for i in range(6)]         # all s+1h windows open together
    conn, ids = _store(tmp_path, spec)
    envs = {("solana", f"W{i}"): _env_ok(f"W{i}") for i in range(6)}
    seen = []
    for k, t in enumerate([T0 + 3600, T0 + 3660, T0 + 3720]):
        calls = []
        rep = oa.run_observe_active(conn, now=t, fetch=_fetcher(envs, calls),
                                    max_tokens=2, min_interval=0)
        seen.append(set(calls))
        assert rep["recorded"] == [2, 2, 2][k]
    assert seen[0].isdisjoint(seen[1]) and seen[1].isdisjoint(seen[2])
    assert len(set().union(*seen)) == 6                        # full rotation, nobody twice
    rep2 = oa.run_observe_active(conn, now=T0 + 4500, fetch=_fetcher(envs), min_interval=0)
    assert rep2["attempted"] == 0                              # window closed: nothing attempted


# ----- 3 · coverable-window prioritization: tier1 near-expiry > tier2 tracked > tier3 -----
def test_coverable_window_prioritization(tmp_path):
    now = T0 + 3900
    conn, ids = _store(tmp_path, [
        ("solana", "NEAR", T0),                                # s+1h closes in 300s  → tier1
        ("solana", "TRACKED", T0 - 10300),                     # s+4h closes in 2000s → tier2
        ("solana", "PLAIN", T0 - 9100),                        # s+4h closes in 3200s → tier3
        ("solana", "PASTONLY", T0 - 6 * 3600),                 # all windows closed/future
        ("solana", "FUTURE", T0 + 20 * 3600),                  # only future windows
    ])
    plan = sch.build_plan(conn, now, tracked={ids["TRACKED"]}, min_interval=0)
    order = [c["token_id"] for c in plan["candidates"]]
    assert order == [ids["NEAR"], ids["TRACKED"], ids["PLAIN"]]
    tiers = {c["token_id"]: c["tier"] for c in plan["candidates"]}
    assert tiers == {ids["NEAR"]: 1, ids["TRACKED"]: 2, ids["PLAIN"]: 3}
    assert ids["PASTONLY"] not in order and ids["FUTURE"] not in order
    # sanity on the arithmetic the tiering relies on
    by_tid = {c["token_id"]: c for c in plan["candidates"]}
    assert abs((by_tid[ids["NEAR"]]["close_ts"] - now) - 300) < 1e-6
    assert abs((by_tid[ids["TRACKED"]]["close_ts"] - now) - 2000) < 1e-6
    assert abs((by_tid[ids["PLAIN"]]["close_ts"] - now) - 3200) < 1e-6


# ----- 4 · expired-window exclusion: never attempted even with an otherwise empty queue -----
def test_expired_window_exclusion(tmp_path):
    conn, ids = _store(tmp_path, [("solana", "OLD", T0)])
    now = T0 + 8 * 3600                                        # s+15m..s+4h windows all closed
    states = {d["label"]: d["state"] for d in sch.slot_states_for_token(conn, ids["OLD"], now)}
    assert states["s+15m"] == sch.MISSED and states["s+1h"] == sch.MISSED
    assert states["s+4h"] == sch.MISSED
    assert sch.build_plan(conn, now)["candidates"] == []
    rep = oa.run_observe_active(conn, now=now, fetch=_fetcher({}), min_interval=0)
    assert rep["attempted"] == 0 and rep["recorded"] == 0
    assert conn.execute("SELECT COUNT(*) FROM gap_register").fetchone()[0] == 0  # no fake gaps either


# ----- 5 · duplicate observation -----
def test_duplicate_observation_safety(tmp_path):
    conn, ids = _store(tmp_path, [("solana", "DUP", T0)])
    envs = {("solana", "DUP"): _env_ok("DUP")}
    now = T0 + 3600
    r1 = oa.run_observe_active(conn, now=now, fetch=_fetcher(envs), min_interval=0)
    r2 = oa.run_observe_active(conn, now=now, fetch=_fetcher(envs), min_interval=0)
    assert r1["recorded"] == 1 and r2["recorded"] == 0 and r2["attempted"] == 0
    assert conn.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0] == 2


# ----- 6 · rate-limit behavior: explicit RATE_LIMITED row, then clean abort (no storm) -----
def test_rate_limit_behavior_aborts_cleanly(tmp_path):
    spec = [("solana", f"R{i}", T0) for i in range(5)]
    conn, ids = _store(tmp_path, spec)
    calls = []

    def f(chain, address, now):
        calls.append(address)
        if len(calls) >= 3:   # PAL local budget starves at the 3rd attempt (rate_starved shape)
            return {"availability": "DOWN", "provider_id": "dexscreener",
                    "endpoint": f"/tokens/v1/solana/{address}", "http_status": None,
                    "payload": None,
                    "error_state": {"kind": "rate_starved", "message": "local budget exhausted"}}
        return _env_ok(address)
    rep = oa.run_observe_active(conn, now=T0 + 3600, fetch=f, min_interval=0)
    assert len(calls) == 3                                     # hard stop, zero retry storm
    assert rep["recorded"] == 2
    assert rep["aborted"] == "rate_budget_exhausted"
    assert [x["kind"] for x in rep["failures"]] == ["rate_limited"]
    assert rep["not_attempted"] == 2                           # remaining candidates disclosed
    row = conn.execute("SELECT error_state, price_usd FROM discovery_observations "
                       "WHERE error_state LIKE '%rate_limited%'").fetchone()
    assert row is not None and row["price_usd"] is None        # explicit, never fabricated


# ----- 7 · provider failure -----
def test_provider_failure_explicit_and_continues(tmp_path):
    conn, ids = _store(tmp_path, [("solana", "BAD", T0), ("solana", "GOOD", T0)])
    envs = {("solana", "BAD"): {"availability": "DOWN", "provider_id": "dexscreener",
                                "endpoint": "/tokens/v1/solana/BAD", "http_status": 521,
                                "payload": None,
                                "error_state": {"kind": "http_error", "code": 521}},
            ("solana", "GOOD"): _env_ok("GOOD")}
    rep = oa.run_observe_active(conn, now=T0 + 3600, fetch=_fetcher(envs), min_interval=0)
    assert rep["recorded"] == 1 and rep["attempted"] == 2      # failure never aborts the run
    bad = [x for x in rep["failures"] if x["token_id"] == ids["BAD"]]
    assert bad and bad[0]["kind"] == "provider_unavailable"
    row = conn.execute("SELECT price_usd, error_state FROM discovery_observations "
                       "WHERE token_id=? ORDER BY retrieved_ts DESC LIMIT 1",
                       (ids["BAD"],)).fetchone()
    assert row["price_usd"] is None and "521" in row["error_state"]


# ----- 8 · restart / resume -----
def test_restart_resume_duplicate_safe(tmp_path):
    spec = [("solana", f"C{i}", T0) for i in range(4)]
    conn, ids = _store(tmp_path, spec)
    calls = {"n": 0}

    def crashing(chain, address, now):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("SIMULATED MID-RUN CRASH")
        return _env_ok(address)
    with pytest.raises(RuntimeError):
        oa.run_observe_active(conn, now=T0 + 3600, fetch=crashing, min_interval=0)
    before = conn.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
    envs = {("solana", f"C{i}"): _env_ok(f"C{i}") for i in range(4)}
    rep = oa.run_observe_active(conn, now=T0 + 3660, fetch=_fetcher(envs), min_interval=0)
    after = conn.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
    assert after - before == 2 and rep["recorded"] == 2        # only the unserved pair


# ----- 9 · fairness / rotation -----
def test_fairness_full_rotation_no_starvation(tmp_path):
    n = 9
    spec = [("solana", f"F{i}", T0) for i in range(n)]
    conn, ids = _store(tmp_path, spec)
    envs = {("solana", f"F{i}"): _env_ok(f"F{i}") for i in range(n)}
    for step in range(6):                                      # same s+1h window, advancing now
        now = T0 + 3600 + step * 60
        oa.run_observe_active(conn, now=now, fetch=_fetcher(envs), max_tokens=2, min_interval=0)
    covered = {r[0] for r in conn.execute(
        "SELECT DISTINCT token_id FROM discovery_observations WHERE provider='dexscreener'")}
    assert covered == set(ids.values())                        # EVERY token served (no starvation)


# ----- 10 · provenance / timestamps -----
def test_provenance_true_timestamps_only(tmp_path):
    conn, ids = _store(tmp_path, [("solana", "P", T0)])
    runs = [T0 + 3600, T0 + 4 * 3600, T0 + 12 * 3600]          # s+1h, s+4h, s+12h windows
    envs = {("solana", "P"): _env_ok("P", price=3.0)}
    for t in runs:
        oa.run_observe_active(conn, now=t, fetch=_fetcher(envs), min_interval=0)
    rows = conn.execute("SELECT retrieved_ts, raw_ref, source_ts FROM discovery_observations "
                        "WHERE provider='dexscreener' ORDER BY retrieved_ts").fetchall()
    assert [r["retrieved_ts"] for r in rows] == runs           # retrieved_ts == run-now, always
    assert all(r["source_ts"] is None for r in rows)           # never invented
    assert all(conn.execute("SELECT COUNT(*) FROM raw_payloads WHERE payload_sha256=?",
                            (r["raw_ref"],)).fetchone()[0] == 1 for r in rows)


# ----- 11 · PRE_FIX / POST_FIX isolation -----
def test_pre_post_fix_isolation(tmp_path):
    conn, ids = _store(tmp_path, [("solana", "S", T0)])
    ACT = T0 + 1800.0                                          # surrogate activation timestamp
    pre = conn.execute("SELECT * FROM discovery_observations ORDER BY rowid").fetchall()
    assert all(r["retrieved_ts"] < ACT for r in pre)           # fixture history is all-PRE
    now = T0 + 4 * 3600                                        # future legal window
    rep = oa.run_observe_active(conn, now=now, fetch=_fetcher({("solana", "S"): _env_ok("S")}),
                                min_interval=0)
    assert rep["recorded"] == 1
    post = conn.execute("SELECT * FROM discovery_observations ORDER BY rowid").fetchall()
    assert post[: len(pre)] == pre                             # PRE rows byte-identical
    new = post[len(pre):]
    assert all(r["retrieved_ts"] >= ACT for r in new)
    assert [r["obs_id"] for r in new] == rep["obs_ids"]        # dual segmentation evidence


# ----- 12 · Lane-A integrity + classification ≡ frozen lifecycle + genericity -----
def _frozen_pins() -> dict[str, str]:
    pins = {}
    man = ROOT.parent / "ahos_snap_w15_after.txt"
    for line in man.read_text().splitlines():
        h, p = line.split(None, 1)
        if (p.startswith("./discovery/") or p.startswith("./paper_trading/")) \
                and p.endswith(".py") and "observe_active" not in p and "feature_store" not in p:
            pins[p] = h                                        # owner-amended artifacts excluded from w15 baseline
        if p in ("./discovery/schema_sqlite.sql", "./discovery/providers.yaml"):
            pins[p] = h
    # Explicitly pin owner-amended feature_store.py (A-1 amendment, Wave 19)
    pins["./discovery/feature_store.py"] = "d3086e729f5cf1018cfd8d102d5f65153d6878148fce5cfe9bc10901b98c1e1c"
    return pins


def test_lane_a_frozen_files_hash_integrity():
    pins = _frozen_pins()
    assert len(pins) >= 18                                     # full Lane-A surface pinned
    drift = [p for p, h in pins.items()
             if hashlib.sha256((ROOT / p[2:]).read_bytes()).hexdigest() != h]
    assert drift == [], f"LANE-A DRIFT DETECTED: {drift}"


def test_classification_matches_frozen_lifecycle_property():
    """EXACT property vs the FROZEN function: due_snapshots ⇔ state ∈ {WINDOW_OPEN, MISSED,
    UNRECOVERABLE}; everything else ⇔ {ALREADY_OBSERVED, COVERABLE}. Fixed seed."""
    rng = random.Random(20260813)
    with tempfile.TemporaryDirectory() as td:
        conn = obs.open_store(Path(td) / "p.sqlite")
        toks = []
        for i in range(30):
            tid = _mk(conn, "solana", f"PROP{i}", T0 + rng.uniform(0, 5 * 24 * 3600))
            for j in range(rng.randrange(0, 5)):
                ts = T0 + rng.uniform(0, 4 * 24 * 3600)
                raw = obs.store_raw(conn, "fx", f"/fx/PROP{i}/{j}", ts, 200, {"t": ts})
                obs.record_observation(conn, tid, "fx", ts, raw, metrics={"price_usd": 1.0})
            toks.append(tid)
        conn.commit()
        for _ in range(200):
            tid = rng.choice(toks)
            now = T0 + rng.uniform(0, 8 * 24 * 3600)
            due = set(lifecycle.due_snapshots(conn, tid, now))
            states = {d["label"]: d["state"] for d in sch.slot_states_for_token(conn, tid, now)}
            assert due == {l for l, s in states.items()
                           if s in (sch.WINDOW_OPEN, sch.MISSED, sch.UNRECOVERABLE)}
            assert {l for l, s in states.items() if s in (sch.ALREADY_OBSERVED, sch.COVERABLE)} \
                == set(states) - due
        conn.close()


def test_scheduler_is_generic_no_hardcoded_targets():
    src = (ROOT / "discovery" / "observation_scheduler.py").read_text()
    assert "paper_trading" not in src                          # no PT coupling in the scheduler
    assert "tracked" in src.lower()                            # tracked-set is INJECTED


# ----- clarifying edge: DEAD token with an OPEN window stays eligible (revival law) -----
def test_dead_token_with_open_window_stays_eligible(tmp_path):
    conn, ids = _store(tmp_path, [("solana", "D", T0)])
    lifecycle.sweep(conn, T0 + 30 * 3600)                      # no obs >24h ⇒ DEAD (existing law)
    assert conn.execute("SELECT state FROM observation_state WHERE token_id=?",
                        (ids["D"],)).fetchone()["state"] == "DEAD"
    now = T0 + 48 * 3600                                       # s+48h window open (±30m tol)
    plan = sch.build_plan(conn, now, min_interval=0)
    assert [c["token_id"] for c in plan["candidates"]] == [ids["D"]]
    states = {d["label"]: d["state"] for d in sch.slot_states_for_token(conn, ids["D"], now)}
    assert states["s+24h"] == sch.UNRECOVERABLE                # closed while DEAD ⇒ unrecoverable
    rep = oa.run_observe_active(conn, now=now, fetch=_fetcher({("solana", "D"): _env_ok("D")}),
                                min_interval=0)
    assert rep["recorded"] == 1
    assert conn.execute("SELECT state FROM observation_state WHERE token_id=?",
                        (ids["D"],)).fetchone()["state"] == "OBSERVING"
