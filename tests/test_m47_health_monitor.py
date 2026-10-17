"""M47 health monitor tests."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.health.monitor import assess_soak_health, load_and_assess


def test_halt_when_not_paper_only():
    rep = assess_soak_health({"paper_only": False})
    assert rep.level == "HALT"


def test_read_fresh_ok_cycle():
    now = datetime(2026, 10, 17, 22, 30, tzinfo=timezone.utc)
    status = {
        "paper_only": True,
        "cycles_failed": 0,
        "last_cycle": {
            "ts": "2026-10-17T22:19:32Z",
            "ok": True,
            "breaker": {"allowed": True},
        },
    }
    rep = assess_soak_health(status, now=now, stale_after_sec=3600)
    assert rep.level == "READ"
    assert rep.paper_only is True


def test_downgrade_on_stale_cycle():
    now = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)
    status = {
        "paper_only": True,
        "cycles_failed": 0,
        "last_cycle": {"ts": "2026-10-17T22:19:32Z", "ok": True, "breaker": {"allowed": True}},
    }
    rep = assess_soak_health(status, now=now, stale_after_sec=3600)
    assert rep.level == "DOWNGRADE"


def test_load_committed_soak_status():
    rep = load_and_assess()
    assert rep.level in ("READ", "DOWNGRADE", "UNKNOWN")
    assert rep.paper_only in (True, None)
