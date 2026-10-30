#!/usr/bin/env python3
"""Run NEXT TRANCHE receipts (scheduling, M58, exam, Didehban, Negahban, ideas). PAPER_ONLY."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.next_tranche import run_next_tranche


def main() -> int:
    doc = run_next_tranche(ROOT)
    print(json.dumps({"schema": doc["schema"], "tracks": list(doc.get("tracks", {}).keys())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
