import json
from pathlib import Path

from architecture.learning.mistakes import record_losing_close
from architecture.university.certification_ladder import run_l0_l4_dry_run
from architecture.university.helpdesk import ask


def test_losing_close_is_unverified_and_idempotent(tmp_path: Path):
    a = record_losing_close(tmp_path, case_id="PT-BTC-1", pnl_usd=-1.2, symbol="BTC", desk="CRYPTO", closed_at="2026-10-30T00:00:00Z")
    b = record_losing_close(tmp_path, case_id="PT-BTC-1", pnl_usd=-1.2, symbol="BTC", desk="CRYPTO", closed_at="2026-10-30T00:00:00Z")
    win = record_losing_close(tmp_path, case_id="PT-BTC-2", pnl_usd=0.4, symbol="BTC", desk="CRYPTO", closed_at="2026-10-30T01:00:00Z")
    assert a["appended"] is True and a["threshold_changed"] is False and a["status"] == "UNVERIFIED"
    assert b["appended"] is False
    assert win["status"] == "IGNORED"
    lines = (tmp_path / "reports/grok/M58/loss_eval_cases.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_ladder_does_not_raise_ceiling(tmp_path: Path):
    (tmp_path / "reports/grok/M13_SOAK").mkdir(parents=True)
    (tmp_path / "reports/grok/PAPER").mkdir(parents=True)
    (tmp_path / "reports/grok/M13_SOAK/soak_heartbeat.json").write_text("{}", encoding="utf-8")
    (tmp_path / "reports/grok/PAPER/edge_report.json").write_text(
        json.dumps({"promotion_gate": {"eligible": False}}), encoding="utf-8"
    )
    (tmp_path / "architecture/markets").mkdir(parents=True)
    (tmp_path / "architecture/markets/council_gate.py").write_text("# x", encoding="utf-8")
    (tmp_path / "architecture/markets/paper_trader.py").write_text("# x", encoding="utf-8")
    (tmp_path / "strategy_lab").mkdir()
    (tmp_path / "strategy_lab/registry.json").write_text("{}", encoding="utf-8")
    doc = run_l0_l4_dry_run(tmp_path)
    assert doc["autonomy_ceiling"] == "L1_ANALYZE"
    assert doc["ceiling_unchanged"] is True
    granted = {row["level"]: row["granted"] for row in doc["levels"]}
    assert granted["L2_RECOMMEND"] is False
    assert granted["L3_AUTONOMOUS_EXPERIMENT"] is False
    assert granted["L4_PAPER_TRADING"] is False


def test_helpdesk_does_not_decide(tmp_path: Path):
    doc = ask("hypothesis calibration", root=tmp_path)
    assert doc["schema"] == "ahos.university.helpdesk.v1"
    assert doc["decides"] is False
    assert doc["authority"] == "ADVISORY_ONLY"
