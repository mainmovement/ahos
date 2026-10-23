#!/usr/bin/env python3
"""Export M13 edge expectancy bootstrap & MGC/MCL margin education snapshot."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.edge_and_margin_sim import build_edge_margin_snapshot


def main() -> int:
    payload = build_edge_margin_snapshot()
    payload["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_dir = ROOT / "reports" / "grok" / "M13"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "edge_margin_sim_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} verdict={payload['expectancy_gate']['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
