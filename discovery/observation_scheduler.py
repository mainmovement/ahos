#!/usr/bin/env python3
"""F12-O2a — COVERAGE-AWARE OBSERVATION SCHEDULER (owner directive 2026-08-13).

WHAT CHANGED vs observe_active:v1 selection: v1 selected tokens by `ORDER BY first_seen_ts
LIMIT cap` whenever lifecycle.due_snapshots was non-empty — and due_snapshots stays non-empty
for slots whose tolerance windows have ALREADY CLOSED (they are honestly due-missed, not
coverable). That made the oldest, permanently-uncoverable cohort a re-attempted queue head
(measured live: identical 40-token attempted set across consecutive runs, R-41).

THIS MODULE: pure, clock-injected, READ-ONLY classification + selection planning.
  * Slots are classified against the FROZEN schedule (lifecycle.SNAPSHOT_SCHEDULE) with the
    FROZEN coverage rule (an obs within ±tolerance of the slot target covers it) — this module
    re-derives, never redefines, those laws; tests pin an exact equivalence property against
    lifecycle.due_snapshots on randomized fixtures.
  * Only WINDOW_OPEN slots produce candidates (a fresh observation can lawfully cover them).
    COVERABLE slots (window not yet open) are NOT served now — a current observation could not
    fall inside their window. MISSED / UNRECOVERABLE slots are NEVER attempted — they are
    already honestly classified and are registered as gaps by the existing sweep path
    (materialize). No backfill, ever: this module only reads.
  * Priority tiers (owner order): ① near-expiry open windows (close_time − now ≤
    near_expiry_s) ② tracked positions with a legal open window (tracked set is INJECTED —
    this module is generic, no paper-trading coupling) ③ every other open window.
    Within a tier: soonest close_time, then oldest cohort, then token_id (deterministic).

VOCABULARY (owner-mandated states): ALREADY_OBSERVED · WINDOW_OPEN · WINDOW_CLOSED (group:
MISSED | UNRECOVERABLE) · COVERABLE · MISSED · UNRECOVERABLE · STALE (token-level metadata
when stale_after is injected). Operational outcome states PROVIDER_FAILED / RATE_LIMITED are
distinguished by the poller (observe_active:v2) at attempt time and reported explicitly.
"""
from __future__ import annotations

import sqlite3

from . import lifecycle  # frozen schedule + coverage law (read-only reuse)

SCHEDULER_VERSION = "observation_scheduler:v1"

ALREADY_OBSERVED = "ALREADY_OBSERVED"
WINDOW_OPEN = "WINDOW_OPEN"
COVERABLE = "COVERABLE"          # window opens in the future — still salvageable, not yet
MISSED = "MISSED"                # window closed uncovered; token not DEAD
UNRECOVERABLE = "UNRECOVERABLE"  # window closed uncovered; token DEAD (no obs >24h)
WINDOW_CLOSED_STATES = frozenset((MISSED, UNRECOVERABLE))
COVERABLE_STATES = frozenset((WINDOW_OPEN, COVERABLE))

NEAR_EXPIRY_DEFAULT = 1800.0     # an open window closing within 30 min is priority-1


def classify_slot(covered: bool, target_ts: float, tol_s: float, now: float,
                  token_dead: bool) -> str:
    """Frozen coverage + window geometry → state. Mirror of lifecycle semantics, nothing more."""
    if covered:
        return ALREADY_OBSERVED
    if now < target_ts - tol_s:
        return COVERABLE
    if now <= target_ts + tol_s:
        return WINDOW_OPEN
    return UNRECOVERABLE if token_dead else MISSED


def slot_states_for_token(conn: sqlite3.Connection, token_id: str, now: float) -> list[dict]:
    st = conn.execute("SELECT state, first_seen_ts FROM observation_state WHERE token_id=?",
                      (token_id,)).fetchone()
    if st is None:
        return []
    t0 = st["first_seen_ts"]
    dead = st["state"] == "DEAD"
    ts_list = [r["retrieved_ts"] for r in conn.execute(
        "SELECT retrieved_ts FROM discovery_observations WHERE token_id=? ORDER BY retrieved_ts",
        (token_id,)).fetchall()]
    out = []
    for label, off, tol in lifecycle.SNAPSHOT_SCHEDULE:
        target = t0 + off
        covered = any(abs(t - target) <= tol for t in ts_list)   # EXACT frozen coverage rule
        out.append({"label": label, "target_ts": target, "tol_s": tol,
                    "open_from": target - tol, "close_ts": target + tol,
                    "state": classify_slot(covered, target, tol, now, dead)})
    return out


def build_plan(conn: sqlite3.Connection, now: float, *, tracked=frozenset(),
               min_interval: float = 240.0, near_expiry_s: float = NEAR_EXPIRY_DEFAULT,
               stale_after: float | None = None) -> dict:
    """Ranked selection plan + full state census. READ-ONLY.

    Cooldown law: a token whose LATEST observation row (success or explicit failure) is younger
    than min_interval is skipped — failures count too (anti retry-storm; v1 only cooled on
    success). Cooldown never erases slot states; it only defers an attempt to the next run.
    """
    rows = conn.execute(
        """SELECT s.token_id, s.first_seen_ts, s.state, s.last_obs_ts, t.chain_id, t.address
           FROM observation_state s JOIN tokens t ON t.token_id = s.token_id
           WHERE s.state != 'RESOLVED'""").fetchall()
    ts_by_token: dict[str, list[float]] = {}
    for r in conn.execute("SELECT token_id, retrieved_ts FROM discovery_observations "
                          "ORDER BY token_id, retrieved_ts").fetchall():
        ts_by_token.setdefault(r["token_id"], []).append(r["retrieved_ts"])
    tracked = frozenset(tracked or ())
    by_state: dict[str, int] = {ALREADY_OBSERVED: 0, WINDOW_OPEN: 0, COVERABLE: 0,
                                MISSED: 0, UNRECOVERABLE: 0}
    candidates = []
    skipped_cooldown = 0
    near_expiry_open = 0
    tracked_open = 0
    for r in rows:
        tid = r["token_id"]
        dead = r["state"] == "DEAD"
        ts_list = ts_by_token.get(tid, [])
        open_slots = []
        for label, off, tol in lifecycle.SNAPSHOT_SCHEDULE:
            target = r["first_seen_ts"] + off
            covered = any(abs(t - target) <= tol for t in ts_list)
            state = classify_slot(covered, target, tol, now, dead)
            by_state[state] += 1
            if state == WINDOW_OPEN:
                open_slots.append((label, target + tol))
        last = ts_list[-1] if ts_list else r["first_seen_ts"]
        stale = None if stale_after is None else (now - last) >= stale_after
        if not open_slots:
            continue
        close_ts = min(c for _, c in open_slots)
        if r["token_id"] in tracked:
            tracked_open += 1
        if close_ts - now <= near_expiry_s:
            near_expiry_open += 1
        if now - last < min_interval:
            skipped_cooldown += 1
            continue
        tier = 1 if close_ts - now <= near_expiry_s else (2 if tid in tracked else 3)
        candidates.append({"token_id": tid, "chain_id": r["chain_id"], "address": r["address"],
                           "first_seen_ts": r["first_seen_ts"], "dead": dead, "stale": stale,
                           "open_slots": [l for l, _ in open_slots],
                           "open_slots_full": [{"label": l, "close_ts": c}
                                               for l, c in sorted(open_slots, key=lambda x: x[1])],
                           "close_ts": close_ts, "tier": tier})
    candidates.sort(key=lambda c: (c["tier"], c["close_ts"], c["first_seen_ts"], c["token_id"]))
    return {"scheduler_version": SCHEDULER_VERSION, "now": now,
            "near_expiry_s": near_expiry_s, "min_interval": min_interval,
            "tracked_size": len(tracked), "candidates": candidates,
            "counts": {"by_state": by_state,
                       "tokens_with_open_windows": len(candidates) + 0,
                       "near_expiry_open": near_expiry_open, "tracked_open": tracked_open,
                       "skipped_cooldown": skipped_cooldown,
                       "eligible_total": len(candidates)}}
