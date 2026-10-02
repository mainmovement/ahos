#!/usr/bin/env python3
"""Read-only CLI for the GM-08 mission ledger (verify / list / show).

    python scripts/mission_ledger.py verify [--path P]
    python scripts/mission_ledger.py list   [--path P]
    python scripts/mission_ledger.py show MISSION_ID [--path P]

Never writes. Exit 0 = chain intact, 3 = tamper detected, 4 = no ledger file.
The ledger is NOT a decision authority.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.ledger import (  # noqa: E402
    LedgerTamperError, MissionLedger, default_ledger_path,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("verify", "list", "show"))
    ap.add_argument("mission_id", nargs="?")
    ap.add_argument("--path", default=None)
    ap.add_argument("--anchor", default=None, help="externally recorded head_hash to check against")
    a = ap.parse_args(argv)
    path = Path(a.path) if a.path else default_ledger_path(create=False)
    if not path.is_file():
        print(json.dumps({"verdict": "NO_LEDGER", "path": str(path)}))
        return 4
    led = MissionLedger(path)
    try:
        if a.cmd == "verify":
            print(json.dumps(led.verify(anchor_hash=a.anchor), indent=2))
        elif a.cmd == "list":
            print(json.dumps(led.missions(), indent=2, ensure_ascii=False))
        else:
            if not a.mission_id:
                ap.error("show needs MISSION_ID")
            print(json.dumps(led.latest(a.mission_id), indent=2, ensure_ascii=False))
    except LedgerTamperError as exc:
        print(json.dumps({"verdict": "TAMPER_DETECTED", "detail": str(exc)}))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
