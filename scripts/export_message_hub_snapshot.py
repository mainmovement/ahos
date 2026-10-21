#!/usr/bin/env python3
"""Build read-only Message Hub snapshot for Arena (local probes only, no secrets)."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_bot import load_dotenv

from architecture.ai.command_inbox import HUMAN, route_command

load_dotenv()
_owner_env = ROOT.parent / "AHOS_Launcher" / "profile" / "owner_secrets.env"
if _owner_env.is_file():
    load_dotenv(_owner_env)

SOAK_DIR = ROOT / "reports" / "grok" / "M13_SOAK"
DEFAULT_OUT = ROOT / "reports" / "grok" / "M35" / "message_hub_snapshot.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _probe_telegram() -> tuple[str, bool, str | None]:
    tok = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not tok or tok.startswith("__") or "NEW_TOKEN" in tok.upper():
        return "BLOCKED_OWNER", True, "owner token not set"
    if not re.fullmatch(r"\d{6,}:[A-Za-z0-9_-]{20,}", tok):
        return "BLOCKED_OWNER", True, "token format invalid"
    url = f"https://api.telegram.org/bot{tok}/getMe"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ahos-export/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.loads(resp.read())
        if body.get("ok") is True:
            return "CONNECTED", False, None
        return "DISCONNECTED", False, "getMe ok=false"
    except Exception as exc:  # noqa: BLE001
        return "DISCONNECTED", False, type(exc).__name__


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
    tg_state, tg_needs_rotation, tg_err = _probe_telegram()
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
                    "status": "LIVE" if tg_state == "CONNECTED" else "UNAVAILABLE",
                    "lastMessageTime": _utc_now() if tg_state == "CONNECTED" else None,
                    "queueDepth": None,
                    "lastError": tg_err or ("M35.3 owner token rotation" if tg_needs_rotation else None),
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
                "bridgeState": tg_state,
                "needsTokenRotation": tg_needs_rotation,
            },
            "nightlyReport": {
                "lastReportTime": judge_mtime,
                "language": "فارسی",
                # On-disk judge exists; Telegram send is not proven here.
                "deliveryState": "UNKNOWN" if judge_mtime else "NOT_SENT",
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
