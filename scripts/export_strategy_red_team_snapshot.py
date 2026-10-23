#!/usr/bin/env python3
"""Export Strategy Red Team & 2x/3x Cost Stress Tester snapshot to reports/grok/M56/strategy_red_team_snapshot.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.strategy_red_team import run_strategy_red_team_suite


def main() -> int:
    payload = run_strategy_red_team_suite()
    out_dir = ROOT / "reports" / "grok" / "M56"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "strategy_red_team_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {out_path} tested={payload['candidates_tested']} "
        f"survived={payload['survived_count']} vetoed={payload['vetoed_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
