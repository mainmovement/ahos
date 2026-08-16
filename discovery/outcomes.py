#!/usr/bin/env python3
"""AHOS STEP 8 — Outcome labeler for the discovery research dataset.
Labels are written ONLY for RESOLVED tokens, from stored observations, availability-consistent:
entry price = closest observation with retrieved_ts <= first_seen + 15min; horizons measured
from first_seen_ts; event grid pre-registered (F §6): classes × horizons below.
This module never reads feature_vector (direction law: features ← observations; labels ← observations;
research combines them ONLY at as_of/availability join time — Quant rule).
"""
from __future__ import annotations
import sqlite3

HORIZONS = {"15m": 900, "1h": 3600, "4h": 14400, "12h": 43200, "24h": 86400, "72h": 259200, "7d": 604800}
EVENT_CLASSES = {"+25%": 0.25, "+50%": 0.50, "+100%": 1.00, "+200%": 2.00}
ENTRY_WINDOW = 900  # closest-to-discovery price within 15 minutes


def _price_series(conn, token_id):
    return conn.execute(
        """SELECT retrieved_ts, price_usd FROM discovery_observations
           WHERE token_id=? AND price_usd IS NOT NULL AND price_usd>0 AND error_state IS NULL
           ORDER BY retrieved_ts""", (token_id,)).fetchall()


def compute_outcomes(conn: sqlite3.Connection, token_id: str, now: float) -> int:
    st = conn.execute("SELECT state, first_seen_ts FROM observation_state WHERE token_id=?",
                      (token_id,)).fetchone()
    if st is None or st["state"] != "RESOLVED":
        return 0
    t0 = st["first_seen_ts"]
    series = _price_series(conn, token_id)
    if not series:
        return 0
    # entry: first obs within window after first_seen (availability-honest)
    candidates = [(r["retrieved_ts"], r["price_usd"]) for r in series
                  if t0 - 60 <= r["retrieved_ts"] <= t0 + ENTRY_WINDOW]
    if not candidates:
        return 0
    entry_ts, entry = candidates[0]
    written = 0
    for hlabel, hsec in HORIZONS.items():
        if now < t0 + hsec:
            continue  # horizon not closed yet (no peeking: labels appear only when fully observed)
        window = [(t, p) for t, p in [(r["retrieved_ts"], r["price_usd"]) for r in series]
                  if t0 <= t <= t0 + hsec]
        if len(window) < 2:
            continue
        prices = [p for _, p in window]
        max_fav = max(prices) / entry - 1.0
        max_adv = min(prices) / entry - 1.0
        for eclass, thr in EVENT_CLASSES.items():
            hit = 1 if max_fav >= thr else 0
            conn.execute(
                """INSERT INTO outcome_label(token_id,horizon,event_class,hit,max_favorable,max_adverse,
                                           entry_price,entry_price_ts,resolved_ts)
                   VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(token_id,horizon,event_class) DO UPDATE SET
                     hit=excluded.hit, max_favorable=excluded.max_favorable,
                     max_adverse=excluded.max_adverse, resolved_ts=excluded.resolved_ts""",
                (token_id, hlabel, eclass, hit, max_fav, max_adv, entry, entry_ts, now))
            written += 1
    return written
