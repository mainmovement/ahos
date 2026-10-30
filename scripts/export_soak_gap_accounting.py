#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.runtime.soak_gap_accounting import export_soak_gap_receipts


def main() -> int:
    doc = export_soak_gap_receipts(ROOT)
    print(json.dumps({
        "relaunches": doc["accounting"]["relaunch_rows_parsed"],
        "short": doc["accounting"]["short_relaunches_under_1h"],
        "host_gaps": doc["accounting"]["host_downtime_gaps"],
        "oct_26_27": doc["accounting"].get("oct_26_27_gap"),
        "m36": doc["m36"]["status"],
        "logon_lightstart": doc["accounting"].get("logon_lightstart"),
        "heartbeat_stale": doc["heartbeat"]["stale"],
        "last_cycle": doc["heartbeat"]["last_cycle_utc"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
