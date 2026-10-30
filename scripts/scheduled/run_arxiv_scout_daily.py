#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.scheduled_jobs import run_scheduled_job
from architecture.university.arxiv_scout import scout
from config.paths import get_project_root


def _job(root):
    return scout(root)


if __name__ == "__main__":
    raise SystemExit(run_scheduled_job(get_project_root(), "AHOS_arxiv_scout_daily", _job))
