#!/usr/bin/env python3
"""Export M64 & M80 Part B (Negahban) White-Hat Security Audit JSON for Arena."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.security.negahban import run_whitehat_security_audit


def main() -> int:
    audit = run_whitehat_security_audit(ROOT)
    out_dir = ROOT / "reports" / "grok" / "M64"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "whitehat_security_audit.json"
    out_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} verdict={audit['overall_verdict']} checks={len(audit['checks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
