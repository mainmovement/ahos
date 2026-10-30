#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.next_tranche import build_negahban_receipt
from architecture.continuation.scheduled_jobs import run_scheduled_job
from config.paths import get_project_root


def _job(root: Path) -> dict:
    return build_negahban_receipt(root)


if __name__ == "__main__":
    raise SystemExit(run_scheduled_job(get_project_root(), "AHOS_negahban_daily", _job))
