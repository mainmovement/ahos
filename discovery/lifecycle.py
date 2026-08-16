#!/usr/bin/env python3
"""AHOS STEP 5 — 72-hour observation lifecycle state machine (pure, clock-injected).
States: DISCOVERED → OBSERVING → RESOLVED(T+72h). DEAD if no observation for 24h.
SECURITY_FLAGGED is a parallel attribute (never blocks data collection).
Deterministic: all functions take `now`. No wall-clock reads inside.
"""
from __future__ import annotations
import json, sqlite3

H = 3600.0
SNAPSHOT_SCHEDULE = [  # (label, offset_sec, tolerance_sec) — F §2
    ("s+15m", 15*60, 5*60), ("s+1h", 1*H, 10*60), ("s+4h", 4*H, 30*60),
    ("s+12h", 12*H, 30*60), ("s+24h", 24*H, 30*60), ("s+48h", 48*H, 30*60),
    ("s+72h", 72*H, 30*60), ("s+7d", 7*24*H, 2*H),
]
DEAD_AFTER = 24*H
RESOLVE_AT = 72*H


def register_discovery(conn: sqlite3.Connection, token_id: str, now: float) -> None:
    conn.execute(
        """INSERT INTO observation_state(token_id,state,entered_ts,first_seen_ts,last_obs_ts,security_flagged,meta_json)
           VALUES (?,?,?,?,?,0,NULL)
           ON CONFLICT(token_id) DO NOTHING""",
        (token_id, "DISCOVERED", now, now, None))
    if conn.total_changes:
        conn.execute("INSERT INTO lifecycle_events(token_id,ts,from_state,to_state,reason) VALUES (?,?,NULL,'DISCOVERED','first seen')",
                     (token_id, now))


def _get_state(conn, token_id) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM observation_state WHERE token_id=?", (token_id,)).fetchone()


def _move(conn, token_id: str, old: str | None, new: str, now: float, reason: str) -> None:
    conn.execute("UPDATE observation_state SET state=?, entered_ts=? WHERE token_id=?", (new, now, token_id))
    conn.execute("INSERT INTO lifecycle_events(token_id,ts,from_state,to_state,reason) VALUES (?,?,?,?,?)",
                 (token_id, now, old, new, reason))


def on_observation(conn: sqlite3.Connection, token_id: str, now: float) -> bool:
    """Feed a fresh observation at `now`. Returns True if state data was updated."""
    st = _get_state(conn, token_id)
    if st is None:
        return False
    conn.execute("UPDATE observation_state SET last_obs_ts=? WHERE token_id=?", (now, token_id))
    if st["state"] in ("DISCOVERED",):
        _move(conn, token_id, st["state"], "OBSERVING", now, "first snapshot ingested")
    elif st["state"] == "DEAD":
        _move(conn, token_id, "DEAD", "OBSERVING", now, "provider data resumed")
    return True


def flag_security(conn: sqlite3.Connection, token_id: str, now: float, reason: str) -> None:
    conn.execute("UPDATE observation_state SET security_flagged=1 WHERE token_id=?", (token_id,))
    conn.execute("INSERT INTO lifecycle_events(token_id,ts,from_state,to_state,reason) VALUES (?,?,?,?,?)",
                 (token_id, now, None, "SECURITY_FLAGGED", reason))


def tick(conn: sqlite3.Connection, token_id: str, now: float) -> str:
    """Advance machine for one token. Returns the state after evaluation."""
    st = _get_state(conn, token_id)
    if st is None:
        return "UNKNOWN"
    state = st["state"]
    if state == "RESOLVED":
        return state
    last = st["last_obs_ts"] if st["last_obs_ts"] is not None else st["first_seen_ts"]
    if state == "OBSERVING" and now - last > DEAD_AFTER:
        _move(conn, token_id, "OBSERVING", "DEAD", now, f"no observation for >{int(DEAD_AFTER//3600)}h")
        state = "DEAD"
    if now - st["first_seen_ts"] >= RESOLVE_AT and state in ("DISCOVERED", "OBSERVING", "DEAD"):
        _move(conn, token_id, state, "RESOLVED", now, "T+72h reached")
        return "RESOLVED"
    return state


def due_snapshots(conn: sqlite3.Connection, token_id: str, now: float) -> list[str]:
    """Which schedule slots are due-and-not-yet-covered (gap-proofing: missed slots are registered, not faked)."""
    st = _get_state(conn, token_id)
    if st is None or st["state"] == "RESOLVED":
        return []
    t0 = st["first_seen_ts"]
    rows = conn.execute(
        "SELECT retrieved_ts FROM discovery_observations WHERE token_id=? ORDER BY retrieved_ts", (token_id,)).fetchall()
    ts_list = [r["retrieved_ts"] for r in rows]
    due = []
    for label, off, tol in SNAPSHOT_SCHEDULE:
        if now >= t0 + off - tol:
            covered = any(abs(t - (t0 + off)) <= tol for t in ts_list)
            if not covered:
                due.append(label)
    return due


def register_gap(conn: sqlite3.Connection, token_id: str, kind: str, expected_ts: float | None,
                 now: float, detail: str) -> None:
    conn.execute("INSERT INTO gap_register(token_id,kind,expected_ts,noted_ts,detail) VALUES (?,?,?,?,?)",
                 (token_id, kind, expected_ts, now, detail))


def sweep(conn: sqlite3.Connection, now: float) -> dict:
    """Advance all active tokens; register overdue gaps. Returns counts by state (for audit)."""
    rows = conn.execute("SELECT token_id FROM observation_state WHERE state != 'RESOLVED'").fetchall()
    counts = {"DISCOVERED": 0, "OBSERVING": 0, "DEAD": 0, "RESOLVED": 0}
    for r in rows:
        tid = r["token_id"]
        for label in due_snapshots(conn, tid, now):
            st = _get_state(conn, tid)
            off = next(o for l, o, tol in SNAPSHOT_SCHEDULE if l == label)
            expected = st["first_seen_ts"] + off if st else None
            # register each overdue slot once
            dup = conn.execute("SELECT 1 FROM gap_register WHERE token_id=? AND kind=? LIMIT 1",
                               (tid, f"missed:{label}")).fetchone()
            if not dup and now > (expected or now) + next(t for l, o, t in SNAPSHOT_SCHEDULE if l == label):
                register_gap(conn, tid, f"missed:{label}", expected, now, "snapshot slot overdue")
        final = tick(conn, tid, now)
        counts[final] = counts.get(final, 0) + 1
    return counts
