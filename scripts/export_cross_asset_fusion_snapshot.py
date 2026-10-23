#!/usr/bin/env python3
"""Export M60.F cross-asset signal fusion snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.cross_asset_signal_fusion import build_cross_asset_signal_fusion_snapshot

ASSETS = Path(r"G:\robat\ahos_assets\m60_cross_asset_fusion_snapshot.json")


def main() -> int:
    payload = build_cross_asset_signal_fusion_snapshot(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "cross_asset_fusion_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    if ASSETS.parent.is_dir():
        ASSETS.write_text(text, encoding="utf-8")
    print(f"wrote {out} opps={len(payload.get('confluence_opportunities') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
