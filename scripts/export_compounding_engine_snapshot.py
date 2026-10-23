#!/usr/bin/env python3
"""Export M60.P $100 compounding ladder snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.hundred_dollar_compounding_engine import build_hundred_dollar_compounding_snapshot

ASSETS_COPY = Path(r"G:\robat\ahos_assets\m60_hundred_dollar_compounding_snapshot.json")


def main() -> int:
    payload = build_hundred_dollar_compounding_snapshot(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "hundred_dollar_compounding_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    if ASSETS_COPY.parent.is_dir():
        ASSETS_COPY.write_text(text, encoding="utf-8")
    eq = payload["paper_compounding_ledger"]["current_equity_usd"]
    print(f"wrote {out} equity={eq}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
