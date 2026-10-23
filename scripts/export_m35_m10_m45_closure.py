#!/usr/bin/env python3
"""Export M35.3 Telegram/Kian closure, M10 Stage 1-5 DB migration closure, and M45 Sandbox Isolation snapshots."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.ai.telegram_bridge_verifier import verify_m35_telegram_and_kian_closure
from architecture.health.db_migration_m10 import verify_m10_db_migration_closure
from architecture.health.lab_gate import verify_m45_sandbox_isolation


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    m35 = verify_m35_telegram_and_kian_closure(root=ROOT)
    _write_json(ROOT / "reports" / "grok" / "M35" / "telegram_kian_closure.json", m35)

    m10 = verify_m10_db_migration_closure(root=ROOT)
    _write_json(ROOT / "reports" / "grok" / "M10" / "db_migration_closure.json", m10)

    m45 = verify_m45_sandbox_isolation(root=ROOT)
    _write_json(ROOT / "reports" / "grok" / "M45" / "sandbox_isolation_snapshot.json", m45)

    print(
        f"exported M35({m35['status']}, token_redacted={m35['token_redacted']}), "
        f"M10({m10['status']}, stages={m10['stages_completed']}), "
        f"M45({m45['status']}, spawn_blocked={m45['subprocess_spawn_blocked']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
