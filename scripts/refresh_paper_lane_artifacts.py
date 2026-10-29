#!/usr/bin/env python3
"""Refresh EDGE-derived desk_policy + desk_signal_feed from live paper log (PAPER_ONLY)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.export_edge_report import main


if __name__ == "__main__":
    raise SystemExit(main())
