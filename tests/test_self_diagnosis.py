from architecture.university.self_diagnosis import diagnose_day, shadow_test


def _row(pnl, cause_kind, symbol="BTC"):
    row = {
        "symbol": symbol,
        "desk": "CRYPTO",
        "side": "LONG",
        "realized_pnl_usd": pnl,
        "fees_usd": 0.01,
        "reason": "STOP",
        "closed_at": "2026-10-30T12:00:00Z",
        "entry_brain": {"signals": [{"name": "candles", "score": 0.4, "available": True, "evidence": {}}]},
    }
    if cause_kind == "FEE_DRAG":
        row["realized_pnl_usd"] = -0.2
        row["fees_usd"] = 0.3
        row["reason"] = "TAKE_PROFIT"
    if cause_kind == "BAD_TIMING":
        row["reason"] = "TIME_STOP"
        row["entry_brain"] = {"signals": []}
    return row


def test_the_day_names_the_most_common_loss_and_tests_the_fix_in_shadow():
    closes = [
        _row(-1.0, "WRONG_FAMILY"),
        _row(-1.0, "WRONG_FAMILY", symbol="ETH"),
        _row(-0.2, "FEE_DRAG", symbol="SOL"),
        {"symbol": "XAU", "desk": "GOLD", "side": "LONG", "realized_pnl_usd": 2.0,
         "fees_usd": 0.01, "reason": "TAKE_PROFIT", "closed_at": "2026-10-30T13:00:00Z",
         "entry_brain": {}},
        _row(-5.0, "WRONG_FAMILY", symbol="OTHER"),
    ]
    closes[-1]["closed_at"] = "2026-10-29T12:00:00Z"
    report = shadow_test(closes, "2026-10-30")
    assert report["primary_cause"] == "WRONG_FAMILY"
    assert [row["cause"] for row in report["top_causes"][:2]] == ["WRONG_FAMILY", "FEE_DRAG"]
    assert all(row["applied_to_live"] is False for row in report["top_causes"] if row["fix_status"] == "SHADOW")
    assert report["fix_status"] == "SHADOW"
    assert report["applied_to_live"] is False
    assert report["loss_count"] == 3
    assert report["shadow_minus_live_usd"] > 0
    assert "weight in shadow" in report["fix_proposal"]


def test_a_day_without_a_loss_proposes_no_fix():
    report = diagnose_day([
        {"symbol": "BTC", "side": "LONG", "realized_pnl_usd": 1.0, "fees_usd": 0.01,
         "reason": "TAKE_PROFIT", "closed_at": "2026-10-30T00:00:00Z", "entry_brain": {}},
    ], "2026-10-30")
    assert report["primary_cause"] is None
    assert report["fix_status"] == "NO_FIX"
    assert report["applied_to_live"] is False
