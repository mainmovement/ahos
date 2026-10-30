#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.org_lifecycle import export_org_lifecycle


def main() -> int:
    doc = export_org_lifecycle(ROOT)
    print(json.dumps({
        "agents": doc["registry_agents"],
        "filled": doc["filled_seats"],
        "unfilled": len(doc["unfilled_seats"]),
        "counts": doc["lifecycle_counts"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
