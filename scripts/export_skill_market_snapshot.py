#!/usr/bin/env python3
"""Export M52 Vetted Skill Market snapshot for Arena using architecture/security/skill_vet.py."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.security.skill_vet import vet


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    reg_path = ROOT / "config" / "skills_registry.json"
    raw = json.loads(reg_path.read_text(encoding="utf-8"))
    entries = []
    for item in raw.get("skills", []):
        spdx = item.get("spdx", "")
        v = vet(spdx="" if spdx in ("NONE", "PROPRIETARY") else spdx, requested_install=False)
        review_state = item.get("reviewState", "REVIEWED" if v.accepted else "REJECTED")
        if not v.accepted:
            review_state = "REJECTED"
        entries.append(
            {
                "id": item["id"],
                "name": item["name"],
                "kind": item.get("kind", "skill"),
                "version": item.get("version"),
                "source": item.get("source"),
                "installState": item.get("installState", "BLOCKED"),
                "permissions": list(item.get("permissions", [])),
                "reviewState": review_state,
                "reason": item.get("reason") or v.reason,
                "demo": False,
            }
        )

    out_dir = ROOT / "reports" / "grok" / "M52"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "skillMarket",
        "executionMode": "PAPER_ONLY",
        "realTrading": False,
        "source": "config/skills_registry.json + M52 skill_vet.py + proposals/prop_*.json",
        "generatedAt": _utc_now(),
        "demo": False,
        "entries": entries,
    }
    out_path = out_dir / "skill_market_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
