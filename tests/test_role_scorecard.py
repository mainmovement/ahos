"""The role scorecard measures. It does not change a weight."""
import json
from datetime import datetime, timezone

from architecture.mission.role_scorecard import CHARTER_ROLES, role_scorecard_line, run_role_scorecard


def test_scorecard_flags_name_only_and_overloaded(tmp_path) -> None:
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "org_map.json").write_text(json.dumps({
        "mapping_only": {
            "GOLD-01": "AG-16",
            "GOLD-02": "AG-16",
            "GOLD-05": "AG-16",
            "JUDGE-01": "AG-11",
            "BRAIN-01": "AG-01",
        },
        "us_equity": {},
        "core_roles": {},
    }), encoding="utf-8")
    moment = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    stamp = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [
        {
            "sender_id": "GOLD-05",
            "agent_id": "AG-16",
            "step": "paper",
            "timestamp_utc": stamp,
            "experiment_id": "exp-gold-fixture",
            "confidence": 0.8,
            "payload": {},
        },
        {
            "sender_id": "JUDGE-01",
            "agent_id": "AG-11",
            "step": "judge",
            "timestamp_utc": stamp,
            "experiment_id": "exp-gold-fixture",
            "confidence": 0.9,
            "payload": {"paper_entry": "ALLOWED"},
        },
    ]
    with (paper / "charter_bus.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    (paper / "paper_trades.jsonl").write_text(json.dumps({
        "event": "CLOSE",
        "chain_experiment_id": "exp-gold-fixture",
        "realized_pnl_usd": -0.01,
        "desk": "GOLD",
    }) + "\n", encoding="utf-8")
    doc = run_role_scorecard(tmp_path, now=moment)
    assert doc["role_count"] == 67
    assert len(doc["roles"]) == 67
    assert set(row["role"] for row in doc["roles"]) == set(CHARTER_ROLES)
    gold5 = next(row for row in doc["roles"] if row["role"] == "GOLD-05")
    assert gold5["messages_24h"] == 1
    assert gold5["proven_wrong"] == 1
    assert "OVERLOADED" in gold5["flags"]
    name_only = next(row for row in doc["roles"] if row["role"] == "NEWS-02")
    assert name_only["messages_24h"] == 0
    assert "NAME_ONLY" in name_only["flags"]
    assert doc["applied_to_live_weights"] is False
    assert doc["promoted"] is False
    line = role_scorecard_line(tmp_path)
    assert "نقش‌های فعال" in line
    assert "فقط‌اسم" in line
    assert "پرکار" in line
    assert not any(ch.isascii() and ch.isalpha() for ch in line)
    assert not (paper / "signal_weights.json").exists()
