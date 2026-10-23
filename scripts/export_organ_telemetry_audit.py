#!/usr/bin/env python3
"""Export M60.L organ telemetry and icon audit snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.organ_telemetry_and_icon_audit import build_organ_telemetry_and_icon_audit_snapshot

ASSETS = Path(r"G:\robat\ahos_assets\m60_organ_telemetry_audit.json")


def main() -> int:
    payload = build_organ_telemetry_and_icon_audit_snapshot(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "organ_telemetry_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    if ASSETS.parent.is_dir():
        ASSETS.write_text(text, encoding="utf-8")
    print(f"wrote {out} organs={payload.get('organs_count')} icons={payload.get('icon_audit_pass')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
