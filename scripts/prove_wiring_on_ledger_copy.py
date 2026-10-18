#!/usr/bin/env python3
"""Copy the live mission ledger, run one paper cycle on the copy, print wiring fields.

Never writes the default live ledger path. The source is read-only copy (file copy).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.gold_paper import (
    GOLD_PAPER_MISSION,
    _track_from_ledger,
)
from architecture.markets.judge import judge_paper_ledger
from architecture.mission.ledger import MissionLedger, default_ledger_path
from architecture.providers.gold import VERIFIED, GoldPriceWitness


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prove gold path wiring on a ledger copy")
    ap.add_argument(
        "--source",
        type=Path,
        default=None,
        help="live ledger to copy (default: mission ledger path, read-only copy)",
    )
    ap.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="scratch ledger path (default: temp file)",
    )
    ap.add_argument("--price", type=float, default=4200.0)
    ap.add_argument(
        "--settle-tp",
        action="store_true",
        help="if flat, enter at --price then run a second cycle at --tp-price to prove close_eval",
    )
    ap.add_argument("--tp-price", type=float, default=6400.0)
    args = ap.parse_args(argv)

    live = (args.source or default_ledger_path(create=False)).resolve()
    dest = args.dest
    if dest is None:
        dest = Path(tempfile.gettempdir()) / f"ahos_ledger_wiring_probe_{live.stat().st_mtime_ns}.jsonl"
    dest = dest.resolve()
    if dest == live:
        print("refusing to write the live ledger path", file=sys.stderr)
        return 2

    if not live.is_file():
        print(f"source missing: {live}", file=sys.stderr)
        return 2

    shutil.copy2(live, dest)
    ledger = MissionLedger(dest)
    track = _track_from_ledger(ledger)
    base_now = 1_700_000_000.0 + track.cycles * 70.0
    result = track.run_cycle(
        GoldPriceWitness(
            state=VERIFIED,
            reason="wiring_probe",
            price_usd=args.price,
            spread_pct=0.1,
            checked_at=base_now,
        ),
        now=base_now,
        ledger=ledger,
    )
    if args.settle_tp:
        track = _track_from_ledger(ledger)
        if track.position is None:
            entry_now = base_now + 60.0
            result = track.run_cycle(
                GoldPriceWitness(
                    state=VERIFIED,
                    reason="wiring_probe_entry",
                    price_usd=args.price,
                    spread_pct=0.1,
                    checked_at=entry_now,
                ),
                now=entry_now,
                ledger=ledger,
            )
            track = _track_from_ledger(ledger)
        if track.position is not None:
            tp_now = base_now + 180.0
            result = track.run_cycle(
                GoldPriceWitness(
                    state=VERIFIED,
                    reason="wiring_probe_tp",
                    price_usd=args.tp_price,
                    spread_pct=0.1,
                    checked_at=tp_now,
                ),
                now=tp_now,
                ledger=ledger,
            )
    cp = ledger.latest(GOLD_PAPER_MISSION) or {}
    checkpoint = cp.get("CHECKPOINT") or {}
    path = checkpoint.get("path") or {}
    out = {
        "dest": str(dest),
        "source": str(live),
        "cycle": result.cycle,
        "recorded": result.recorded,
        "path_oms": path.get("oms"),
        "m51": path.get("m51"),
        "lessons_keys": sorted((path.get("lessons") or {}).keys()),
        "close_eval": checkpoint.get("close_eval"),
    }
    report = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    out["judge"] = report.verdict
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if report.verdict != "BROKEN_CHAIN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
