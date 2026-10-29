#!/usr/bin/env python3
"""Backfill research prediction outcomes from paper_trades.jsonl and refresh scorecard (PAPER_ONLY)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.university.research_prediction_scoring import backfill_outcomes_from_log


def main() -> int:
    n = backfill_outcomes_from_log(ROOT)
    print(f"appended_outcome_rows={n}")
    print(f"scorecard=reports/grok/PAPER/research_hypothesis_scorecard.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
