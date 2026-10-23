#!/usr/bin/env python3
"""Export M65 Persian Teaching Mode & Hooman Decision Journal snapshot to reports/grok/M65/teaching_journal_snapshot.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.teaching_mode_m65 import generate_teaching_journal_snapshot


def main() -> int:
    payload = generate_teaching_journal_snapshot()
    out_dir = ROOT / "reports" / "grok" / "M65"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "teaching_journal_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} lessons={payload['lessons_count']} journal={payload['journal_entries_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
