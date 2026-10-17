"""M40 negative tests. No withdrawal function is called."""
from __future__ import annotations

from pathlib import Path

from architecture.treasury.requests import TransferRequest, submit_request


def _req(**kwargs) -> TransferRequest:
    base = dict(
        request_id="r1",
        amount_usd=100.0,
        network="owner-whitelist",
        message="move paper budget note",
        now_ts="2026-10-18T00:00:00Z",
        expires_ts="2026-10-18T06:00:00Z",
    )
    base.update(kwargs)
    return TransferRequest(**base)


def test_clean_request_is_recorded_and_does_not_execute():
    row = submit_request(_req(), seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0)
    assert row.accepted is True
    assert row.executes is False


def test_replay_cap_expiry_address_and_network_are_rejected():
    seen = {"r1"}
    assert submit_request(_req(), seen_ids=seen, spent_ahos_usd=0, spent_broker_usd=0).reason == "replay"
    assert submit_request(
        _req(request_id="r2", amount_usd=50), seen_ids=set(), spent_ahos_usd=960, spent_broker_usd=0
    ).reason == "ahos daily cap"
    assert submit_request(
        _req(request_id="r3", amount_usd=50), seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=960
    ).reason == "broker daily cap"
    assert submit_request(
        _req(request_id="r4", now_ts="2026-10-18T06:00:00Z"),
        seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0,
    ).reason == "expired"
    assert submit_request(
        _req(request_id="r5", message="pay 0x" + "ab" * 20),
        seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0,
    ).reason == "address in message"
    assert submit_request(
        _req(request_id="r6", network="tron"),
        seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0,
    ).reason == "wrong network"


def test_source_has_no_withdrawal_endpoint():
    text = (Path(__file__).resolve().parents[1] / "architecture" / "treasury" / "requests.py").read_text(encoding="utf-8")
    lowered = text.lower()
    for banned in ("def withdraw", "send_transaction", "@app.route", "broadcast"):
        assert banned not in lowered
