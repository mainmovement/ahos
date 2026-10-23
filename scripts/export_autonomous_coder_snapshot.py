#!/usr/bin/env python3
"""Export M60.C 4-Brain Autonomous Coder snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.cognitive.autonomous_coder_bridge import run_autonomous_coder_cycle


def main() -> int:
    payload = run_autonomous_coder_cycle(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "autonomous_coder_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    eng = payload["four_brain_engine"]
    print(
        f"wrote {out} bridge={eng['brain_1_bridge_8787']} "
        f"patches={eng['synthesized_patches_verified']} briefs={eng['persian_briefs_generated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
