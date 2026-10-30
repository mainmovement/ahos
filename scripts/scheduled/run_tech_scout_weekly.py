#!/usr/bin/env python3
"""Weekly tech scout. Writes the ledger under the repo on G:. Does not push."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.scheduled_jobs import run_scheduled_job
from architecture.university.tech_scout import run_live
from config.paths import get_project_root


def _job(root: Path) -> dict:
    rows = run_live(root)
    return {
        "paper_only": True,
        "rows": len(rows),
        "decisions": {row["decision"]: sum(1 for item in rows if item["decision"] == row["decision"]) for row in rows},
        "applied_to_live_weights": False,
    }


if __name__ == "__main__":
    raise SystemExit(run_scheduled_job(get_project_root(), "AHOS_tech_scout_weekly", _job))
