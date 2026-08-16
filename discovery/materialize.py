#!/usr/bin/env python3
"""Batch materializer — Wave-7. Freezes the research dataset from live tables:

  materialize_features: for every discovered token whose join point (first_seen + JOIN_OFFSET)
      has passed, compute fs_v0.2 features AT the frozen as_of and upsert into feature_vector.
      Leakage laws run inside feature_store (L1 retrieved<=as_of, L3 availability<=as_of).
  materialize_outcomes: for every RESOLVED token, compute outcome labels (horizon-closure
      no-peeking law runs inside outcomes.compute_outcomes via `now`).

Idempotent: both writers use ON CONFLICT upserts; re-running changes nothing.
This module is the ONLY place that glues features and outcomes in one process — the
direction law (feature_store never imports outcomes) is unchanged and test-pinned.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from . import feature_store, lifecycle, outcomes

JOIN_OFFSET = 3600.0  # locked constant — mirrors research/baseline_stats.JOIN_OFFSET


def materialize_features(conn: sqlite3.Connection, now: float | None = None,
                         join_offset: float = JOIN_OFFSET,
                         feature_set: str = feature_store.FEATURE_SET_V02) -> dict:
    now = time.time() if now is None else now
    feature_store.register_definitions(conn)
    rows = conn.execute(
        "SELECT token_id, first_seen_ts FROM observation_state ORDER BY first_seen_ts").fetchall()
    done, rows_written, immature = 0, 0, 0
    for r in rows:
        as_of = r["first_seen_ts"] + join_offset
        if as_of > now:
            immature += 1
            continue
        feats = (feature_store.compute_features_v02(conn, r["token_id"], as_of)
                 if feature_set == feature_store.FEATURE_SET_V02
                 else feature_store.compute_features(conn, r["token_id"], as_of))
        rows_written += feature_store.persist_features(conn, r["token_id"], as_of, feats, feature_set)
        done += 1
    conn.commit()
    return {"features_tokens": done, "features_rows": rows_written,
            "features_immature_skipped": immature, "feature_set": feature_set,
            "join_offset": join_offset, "now": now}


def materialize_outcomes(conn: sqlite3.Connection, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    # lifecycle first: any token past T+72h must be RESOLVED before labeling
    lifecycle.sweep(conn, now)
    conn.commit()
    rows = conn.execute(
        "SELECT token_id FROM observation_state WHERE state='RESOLVED'").fetchall()
    written = 0
    for r in rows:
        written += outcomes.compute_outcomes(conn, r["token_id"], now)
    conn.commit()
    labels = conn.execute("SELECT COUNT(*) c FROM outcome_label").fetchone()["c"]
    return {"outcome_tokens_resolved": len(rows), "outcome_rows_written": written,
            "outcome_labels_total": labels, "now": now}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(Path(__file__).resolve().parents[1]
                                           / "data" / "e01_discovery.sqlite"))
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)
    conn = sqlite3.connect(args.store)
    conn.row_factory = sqlite3.Row
    rep = {"ts": time.time(), "store": args.store,
           **materialize_features(conn), **materialize_outcomes(conn)}
    conn.close()
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
