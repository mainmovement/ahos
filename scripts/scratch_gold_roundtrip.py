#!/usr/bin/env python3
"""Scratch gold round-trip on a COPY ledger path. Never the live default."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.gold_paper import (
    GOLD_PAPER_AGENT,
    GOLD_PAPER_MISSION,
    GoldPaperTrack,
)
from architecture.markets.judge import judge_paper_ledger
from architecture.mission.ledger import MissionLedger, default_ledger_path
from architecture.providers.gold import VERIFIED, GoldPriceWitness

T0 = 1_700_000_000.0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="One scratch gold cycle + judge on a copy ledger")
    ap.add_argument("--ledger", required=True, help="path to a scratch ledger file")
    args = ap.parse_args(argv)
    path = Path(args.ledger)
    if path.resolve() == default_ledger_path(create=False).resolve():
        print("refusing the live default ledger path", file=sys.stderr)
        return 2
    ledger = MissionLedger(path)
    if ledger.latest(GOLD_PAPER_MISSION) is None:
        ledger.start(
            GOLD_PAPER_MISSION,
            phase="paper_trading",
            task="scratch round-trip",
            agent=GOLD_PAPER_AGENT,
        )
    witness = GoldPriceWitness(
        state=VERIFIED, reason="scratch", price_usd=4200.0, spread_pct=0.1, checked_at=T0,
    )
    track = GoldPaperTrack()
    result = track.run_cycle(witness, now=T0, ledger=ledger)
    report = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    path_field = (ledger.latest(GOLD_PAPER_MISSION) or {}).get("CHECKPOINT", {}).get("path", {})
    print(
        f"cycle={result.cycle} oms={path_field.get('oms')} "
        f"judge={report.verdict} findings={len(report.findings)}"
    )
    return 0 if report.verdict != "BROKEN_CHAIN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
