#!/usr/bin/env python3
"""Export M33 full-market crypto universe scanner snapshot."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.crypto_full_universe_scanner import build_crypto_universe_snapshot


def main() -> int:
    payload = build_crypto_universe_snapshot()
    payload["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = ROOT / "reports" / "grok" / "M33" / "crypto_universe_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} indexed={payload['total_indexed_universe']} gems={payload['eligible_gems_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
