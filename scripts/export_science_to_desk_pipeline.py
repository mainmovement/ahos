#!/usr/bin/env python3
"""Export M57 science-to-desk pipeline snapshot."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.university.science_to_desk_pipeline import run_science_to_desk_pipeline


def main() -> int:
    payload = run_science_to_desk_pipeline()
    payload["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = ROOT / "reports" / "grok" / "M57" / "science_to_desk_pipeline_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} sources={payload['sources_count']} desks={payload['desks_trained']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
