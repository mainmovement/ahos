"""M41 mocked broker-key self-check. No key file is opened."""
from __future__ import annotations

from pathlib import Path

from architecture.security.broker_keys import check_key, check_permissions, location_allowed


def test_withdraw_permission_halts():
    row = check_permissions(["trade", "read", "withdraw"], ip_locked=True)
    assert row.level == "HALT"
    assert row.allowed is False


def test_missing_ip_lock_halts():
    row = check_permissions(["trade", "read"], ip_locked=False)
    assert row.level == "HALT"


def test_trade_and_read_with_ip_lock_is_allowed():
    row = check_permissions(["trade", "read"], ip_locked=True)
    assert row.level == "READ"
    assert row.allowed is True


def test_key_must_live_under_broker_and_is_not_opened(tmp_path: Path):
    broker = tmp_path / "broker"
    broker.mkdir()
    key = broker / "desk.key"
    key.write_text("do-not-read-this\n", encoding="utf-8")
    before = key.read_bytes()
    assert location_allowed(key, tmp_path) is True
    outside = tmp_path / "elsewhere" / "desk.key"
    outside.parent.mkdir()
    outside.write_text("x\n", encoding="utf-8")
    assert location_allowed(outside, tmp_path) is False
    halted = check_key(outside, tmp_path, ["trade", "read"], ip_locked=True)
    assert halted.level == "HALT"
    assert key.read_bytes() == before
    envish = broker / ".env"
    envish.write_text("nope\n", encoding="utf-8")
    assert location_allowed(envish, tmp_path) is False
