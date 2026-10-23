#!/usr/bin/env python3
"""Export M60.E self-evolution closed-loop snapshot."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.cognitive.self_evolution_cycle_runner import run_self_evolution_cycle_snapshot

ASSETS_COPY = Path(r"G:\robat\ahos_assets\m60_self_evolution_cycle_snapshot.json")


def main() -> int:
    payload = run_self_evolution_cycle_snapshot(root=ROOT)
    out = ROOT / "reports" / "grok" / "M60" / "self_evolution_cycle_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    if ASSETS_COPY.parent.is_dir():
        ASSETS_COPY.write_text(text, encoding="utf-8")
    print(f"wrote {out} stages={len(payload.get('stages') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
