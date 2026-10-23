#!/usr/bin/env python3
"""Export M60.R multi-horizon risk shield snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.multi_horizon_risk_shield import build_multi_horizon_risk_shield_snapshot

ASSETS = Path(r"G:\robat\ahos_assets\m60_multi_horizon_risk_shield.json")


def main() -> int:
    payload = build_multi_horizon_risk_shield_snapshot(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "multi_horizon_risk_shield.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    if ASSETS.parent.is_dir():
        ASSETS.write_text(text, encoding="utf-8")
    print(f"wrote {out} verdict={payload.get('shield_verdict')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
