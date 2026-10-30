#!/usr/bin/env python3
"""Export weekly shadow scorecard to M57 + refresh M65 teaching journal."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.university.research_prediction_scoring import (
    backfill_outcomes_from_log,
    export_weekly_shadow_scorecard_to_m57,
)


def main() -> int:
    backfill_outcomes_from_log(ROOT)
    export_weekly_shadow_scorecard_to_m57(ROOT)
    print("wrote reports/grok/M57/weekly_research_shadow_scorecard.json")
    print("updated reports/grok/M65/teaching_journal_snapshot.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
