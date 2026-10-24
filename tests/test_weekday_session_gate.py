from __future__ import annotations

from datetime import datetime, timezone

from architecture.markets.weekday_session_gate import is_weekend_tehran, session_report, tehran_now


def test_saturday_tehran_is_weekend():
    # 2026-10-24 08:00 UTC = 11:30 Tehran Saturday
    u = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)
    assert is_weekend_tehran(u) is True
    rep = session_report(u)
    assert rep["weekend_tehran"] is True
    assert rep["cash_desks_expected"] == "CLOSED_OR_STALE"


def test_tehran_offset():
    u = datetime(2026, 10, 24, 4, 30, tzinfo=timezone.utc)
    t = tehran_now(u)
    assert t.hour == 8
