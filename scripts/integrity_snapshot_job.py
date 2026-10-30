"""Bounded snapshot integrity for the two large stores. Does not touch the live soak."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.persistence.store_integrity import (  # noqa: E402
    SNAPSHOT_TIMEOUT_S,
    snapshot_integrity,
)
from config.paths import get_discovery_db_path, get_local_db_path  # noqa: E402

OUT = ROOT / "reports" / "grok" / "PAPER" / "store_integrity_snapshot.json"
PID = ROOT / "data" / "integrity_snapshots" / "job.pid"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    snap_dir = PID.parent
    snap_dir.mkdir(parents=True, exist_ok=True)
    sources = {
        "ahos_local": Path(get_local_db_path()),
        "e01_discovery": Path(get_discovery_db_path()),
    }
    stores: dict[str, str] = {}
    try:
        for name, source in sources.items():
            stores[name] = snapshot_integrity(
                source, snap_dir / f"{name}.sqlite", timeout_s=SNAPSHOT_TIMEOUT_S,
            )
    finally:
        PID.unlink(missing_ok=True)
    doc = {
        "schema": "ahos.store_integrity_snapshot.v1",
        "paper_only": True,
        "checked_at": _utc(),
        "method": "backup_api_snapshot",
        "timeout_s": SNAPSHOT_TIMEOUT_S,
        "stores": stores,
        "every_large_ok": all(word == "ok" for word in stores.values()),
        "live_switch": False,
        "decides": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked_at": doc["checked_at"], "stores": stores}))
    return 0 if doc["every_large_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
