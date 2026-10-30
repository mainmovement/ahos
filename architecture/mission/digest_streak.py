"""Local nightly-digest file streak. Telegram send stays BLOCKED. PAPER_ONLY."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

OUT_REL = Path("reports") / "grok" / "M31" / "digest_streak.json"
TARGET_SENDS = 30


def _dates_from_names(root: Path) -> set[date]:
    found: set[date] = set()
    soak = root / "reports" / "grok" / "M13_SOAK"
    if soak.is_dir():
        for path in soak.glob("*digest*.json"):
            m = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
            if m:
                found.add(date.fromisoformat(m.group(1)))
    snap = root / "reports" / "grok" / "M31" / "nightly_digest_snapshot.json"
    if snap.is_file():
        try:
            doc = json.loads(snap.read_text(encoding="utf-8"))
            raw = str(doc.get("generated_at") or "")
            if raw:
                found.add(datetime.fromisoformat(raw.replace("Z", "+00:00")).date())
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    return found


def _consecutive_ending(days: set[date], end: date) -> int:
    n = 0
    cursor = end
    while cursor in days:
        n += 1
        cursor -= timedelta(days=1)
    return n


def build_digest_streak(root: Path, *, today: date | None = None) -> dict[str, Any]:
    days = _dates_from_names(Path(root))
    end = today or datetime.now(timezone.utc).date()
    streak = _consecutive_ending(days, end)
    if streak == 0 and days:
        streak = _consecutive_ending(days, max(days))
        end = max(days)
    return {
        "schema": "ahos.digest_streak.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "local_digest_nights": len(days),
        "consecutive_local_nights": streak,
        "streak_ends": end.isoformat() if days else None,
        "sends": 0,
        "send_status": "BLOCKED",
        "target_consecutive_sends": TARGET_SENDS,
        "m31_gap": "OPEN",
        "honesty": "A file on disk is not a send. The Telegram bridge stays BLOCKED until the owner opens it.",
    }


def export_digest_streak(root: Path) -> dict[str, Any]:
    doc = build_digest_streak(root)
    out = Path(root) / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
