#!/usr/bin/env python3
"""Build read-only Message Hub snapshot for Arena (local probes only, no secrets)."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.ai.command_inbox import HUMAN, route_command

SOAK_DIR = ROOT / "reports" / "grok" / "M13_SOAK"
DEFAULT_OUT = ROOT / "reports" / "grok" / "M35" / "message_hub_snapshot.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _probe_bridge(url: str = "http://127.0.0.1:8787/health") -> tuple[str, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ahos-export/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = json.loads(resp.read())
        if body.get("ok") is True:
            return "CONNECTED", None
        return "DISCONNECTED", "health ok=false"
    except Exception as exc:  # noqa: BLE001 - bridge down is normal export input
        return "DISCONNECTED", type(exc).__name__


def _read_soak_status() -> dict | None:
    path = SOAK_DIR / "soak_status.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _latest_judge_day() -> tuple[str | None, str | None]:
    try:
        candidates = sorted(SOAK_DIR.glob("*_judge.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None, None
    if not candidates:
        return None, None
    p = candidates[0]
    day = p.stem.replace("_judge", "")
    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return day, mtime


def build_snapshot() -> dict:
    bridge, bridge_err = _probe_bridge()
    soak = _read_soak_status() or {}
    last_cycle = soak.get("last_cycle") or {}
    cycle_ts = last_cycle.get("ts") if isinstance(last_cycle, dict) else None
    judge_day, judge_mtime = _latest_judge_day()

    bridge_channel = "LIVE" if bridge == "CONNECTED" else "UNAVAILABLE"
    inbox = [
        {
            "id": f"HG-{name}",
            "title": f"Owner gate: {name}",
            "requestedByAgent": "M35.5-inbox",
            "age": "-",
            "state": "PARTIAL",
        }
        for name in sorted(HUMAN)
    ]
    log: list[dict] = []
    if cycle_ts:
        log.append(
            {
                "time": cycle_ts,
                "direction": "out",
                "channel": "nightly report",
                "summary": f"soak cycle {last_cycle.get('cycle')} witness={last_cycle.get('witness_state')}",
                "deliveryState": "DELIVERED",
            }
        )

    return {
        "generated_at": _utc_now(),
        "paper_only": True,
        "messageHub": {
            "executionMode": "PAPER_ONLY",
            "realTrading": False,
            "source": "export_message_hub_snapshot.py (bridge probe + M13_SOAK + M35.5 inbox)",
            "generatedAt": _utc_now(),
            "demo": False,
            "channels": [
                {
                    "channel": "Kian chat",
                    "status": "PARTIAL",
                    "lastMessageTime": None,
                    "queueDepth": None,
                    "lastError": "M35.2 UI not wired; core only",
                },
                {
                    "channel": "Telegram",
                    "status": "UNAVAILABLE",
                    "lastMessageTime": None,
                    "queueDepth": None,
                    "lastError": "M35.3 owner token rotation",
                },
                {
                    "channel": "nightly report",
                    "status": "LIVE" if judge_mtime else "UNKNOWN",
                    "lastMessageTime": judge_mtime,
                    "queueDepth": None,
                    "lastError": None,
                },
                {
                    "channel": "command router",
                    "status": "LIVE",
                    "lastMessageTime": _utc_now(),
                    "queueDepth": len(inbox),
                    "lastError": None,
                },
            ],
            "telegram": {
                "bridgeState": "BLOCKED_OWNER",
                "needsTokenRotation": True,
            },
            "nightlyReport": {
                "lastReportTime": judge_mtime,
                "language": "فارسی",
                "deliveryState": "NOT_SENT" if judge_mtime else "UNKNOWN",
                "evidenceLink": f"reports/grok/M13_SOAK/{judge_day}_judge.md" if judge_day else None,
            },
            "humanGateInbox": inbox,
            "messageLog": log,
        },
        "bridge_llm": {"state": bridge, "lastError": bridge_err},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export Message Hub snapshot for Arena")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    payload = build_snapshot()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} bridge={payload['bridge_llm']['state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
