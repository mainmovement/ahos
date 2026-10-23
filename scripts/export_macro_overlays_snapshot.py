#!/usr/bin/env python3
"""Export Free Macro & Positioning Intelligence Overlay snapshot to reports/grok/M19/macro_overlays_snapshot.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.macro_overlays import evaluate_macro_overlays


def main() -> int:
    payload = evaluate_macro_overlays()
    out_dir = ROOT / "reports" / "grok" / "M19"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "macro_overlays_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} gold={payload['gold_macro_bias']} oil={payload['oil_macro_bias']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
