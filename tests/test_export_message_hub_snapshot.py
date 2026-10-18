from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from architecture.ai.command_inbox import route_command


def test_export_message_hub_writes_valid_json(tmp_path: Path):
    out = tmp_path / "hub.json"
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "export_message_hub_snapshot.py"), "--out", str(out)],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    hub = payload["messageHub"]
    assert hub["demo"] is False
    assert hub["telegram"]["bridgeState"] == "BLOCKED_OWNER"
    assert len(hub["humanGateInbox"]) >= 5
    for cmd in ("trade", "withdraw"):
        assert route_command(cmd).executed is False
