#!/usr/bin/env python3
"""Export M60.G owner live-switch readiness snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.owner_live_switch_readiness import build_owner_live_switch_readiness_snapshot

ASSETS = Path(r"G:\robat\ahos_assets\m60_owner_live_switch_readiness.json")


def main() -> int:
    payload = build_owner_live_switch_readiness_snapshot(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "owner_live_switch_readiness.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    if ASSETS.parent.is_dir():
        ASSETS.write_text(text, encoding="utf-8")
    print(f"wrote {out} green={payload.get('gates_green_count')}/6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
