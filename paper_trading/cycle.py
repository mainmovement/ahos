#!/usr/bin/env python3
"""Track-B cycle runner (Wave-8). One call = one full paper cycle:
  v2 (PT-BANKROLL-v2) entries+monitoring first (experiment priority),
  then v1 monitoring-only for its legacy open trades (no new fantasy-notional entries),
  then the two-track periodic report artifact.
Security-call budget is split deterministically: v2 gets 10, v1 gets 5 (PAL discipline).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from . import engine, engine_v3, reports

ROOT = Path(__file__).resolve().parents[1]
V1_BUDGET = 5
V2_BUDGET = 10


def run_full_cycle(paper_db: str, discovery_db: str, pal=None, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    # Wave-8 continuation (register R-26): PT-X3-v1 autonomous management replaces the v2
    # monitoring path FORWARD-ONLY; entries stay PT-BANKROLL-v2. v1 legacy: monitored-only.
    v3 = engine_v3.run_cycle_v3(paper_db, discovery_db, now=now, pal=pal, security_budget=V2_BUDGET)
    v1 = engine.run_cycle(paper_db, discovery_db, now=now, pal=pal, security_budget=V1_BUDGET,
                          allow_new_entries=False)
    paper = reports.paper_report_experiment(paper_db)
    equity = reports.experiment_equity(paper_db)
    research = _research_counters(discovery_db)
    return {"cycle_ts": now, "v3": v3, "v1_monitor": v1, "research": research,
            "experiment": paper, "equity": equity}


def _research_counters(discovery_db: str) -> dict:
    con = sqlite3.connect(discovery_db)
    c = lambda q: con.execute(q).fetchone()[0]
    out = {"tokens": c("SELECT COUNT(*) FROM tokens"),
           "observations": c("SELECT COUNT(*) FROM discovery_observations"),
           "resolved": c("SELECT COUNT(*) FROM observation_state WHERE state='RESOLVED'"),
           "cohort_readiness": "WALL-CLOCK GATED (first 72h closure 2026-08-14 18:00Z)",
           "h14_h20_gate": "pre-registered only; untouched by Track-B"}
    con.close()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(ROOT / "data" / "paper_trading.sqlite"))
    ap.add_argument("--discovery", default=str(ROOT / "data" / "e01_discovery.sqlite"))
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--report-dir", default=str(ROOT / "reports"))
    args = ap.parse_args(argv)
    from discovery.pal import PAL
    pal = None if args.offline else PAL()
    res = run_full_cycle(args.store, args.discovery, pal=pal)
    day = time.strftime("%Y%m%d_%H%M%S", time.gmtime(res["cycle_ts"]))
    out = Path(args.report_dir) / f"paper_cycle_{day}.json"
    out.write_text(json.dumps(res, indent=1, default=str))
    txt = reports.render_two_track(res["research"], res["experiment"])
    learning = res["v3"].get("learning") or {}
    n_lessons = learning.get("lessons_recorded", 0)
    txt += reports.render_autonomous_status(res["equity"], learning, n_lessons)
    (Path(args.report_dir) / f"periodic_report_{day}.txt").write_text(txt + "\n")
    print(json.dumps({"v3": res["v3"], "v1_monitor": res["v1_monitor"]}, indent=1, default=str))
    print("report ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
