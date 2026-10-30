from architecture.runtime.soak_gap_accounting import (
    build_m36_72h_receipt,
    parse_relaunch_lines,
    verify_logon_lightstart,
)


def test_oct_26_gap_is_host_downtime_not_naive_19h():
    text = (
        "- Soak daemon via VBS 2026-10-27T14:18:46 (+03:30): soak was not running; "
        "last cycle ts 2026-10-26T18:45:36Z UTC.\n"
    )
    rows = parse_relaunch_lines(text)
    assert len(rows) == 1
    assert rows[0]["kind"] == "HOST_DOWNTIME"
    assert 15.5 < rows[0]["gap_hours"] < 16.5


def test_short_relaunch_under_one_hour():
    text = (
        "- Auto-restart at logon 2026-10-21T17:13:49 (+03:30): soak was not running; "
        "last cycle ts 2026-10-21T13:43:13Z UTC.\n"
    )
    rows = parse_relaunch_lines(text)
    assert rows[0]["kind"] == "SHORT_RELAUNCH"


def test_logon_lightstart_chain(tmp_path):
    (tmp_path / "logon.log").write_text(
        "2026-10-29T00:56:02 lightstart invoke begin\n2026-10-29T01:00:21 lightstart invoke end ok=True lastExit=0\n",
        encoding="utf-8",
    )
    (tmp_path / "light_start.log").write_text("2026-10-29T00:56:03 begin\n", encoding="utf-8")
    doc = verify_logon_lightstart(tmp_path)
    assert doc["chain_seen"] is True


def test_m36_receipt_does_not_claim_72h():
    doc = build_m36_72h_receipt({"longest_gap_hours": 16.05, "relaunch_rows_parsed": 27}, {"stale": False, "last_cycle_utc": "2026-10-30T00:32:29Z"})
    assert doc["status"] == "NOT_MET"
    assert doc["target_continuous_hours"] == 72
