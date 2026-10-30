from pathlib import Path

from architecture.mission.mehrdad_status import build_mehrdad_status
from architecture.mission.owner_gap_census import parse_gap_register, parse_vision_audit
from config.paths import load_path_config
from core.idea_shelf.hardware import detect_hardware


def test_open_gaps_stay_open_and_the_vision_audit_is_not_relabelled():
    gaps = parse_gap_register(
        "| M-GAP-003 | x | x | x | x | x | x | x | **OPEN** |\n"
        "| M-GAP-001 | x | x | x | x | x | x | x | **CLOSED** |\n"
    )
    assert gaps[0]["kind"] == "PARTIAL"
    assert gaps[0]["register_status"] == "OPEN"
    assert gaps[1]["kind"] == "REAL"
    audit = (
        "| CAPABILITY | A | B | C | T | V | I | OPERATIONAL | E | GAP | PRIORITY | L |\n"
        "| **Telegram** | chat | tg | PART | ✅ | NO | PART | NO | M-GAP-009 | token | P0 | MUST |\n"
        "| **Paper trading** | paper | lane | IMPL | ✅ | PART | PART | PART | tests | — | P0 | MUST |\n"
    )
    rows = parse_vision_audit(audit)
    assert rows[0]["kind"] == "MISSING"
    assert rows[1]["kind"] == "PARTIAL"
    assert all(row["kind"] != "REAL" for row in rows)


def test_mehrdad_page_keeps_the_live_switch_off(tmp_path: Path):
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trader_status.json").write_text(
        '{"mark_to_market_equity_usd": 98.9, "open_positions": {"DAX": {"side": "LONG"}}, '
        '"performance": {"max_drawdown_pct": 1.88}}',
        encoding="utf-8",
    )
    (paper / "intelligence_metric.json").write_text(
        '{"weeks": [{"expectancy_usd": -0.01, "n": 30}]}',
        encoding="utf-8",
    )
    (paper / "daily_diagnosis.json").write_text(
        '{"top_causes": [{"cause": "NEWS_TRAP", "n": 2}]}',
        encoding="utf-8",
    )
    doc = build_mehrdad_status(tmp_path)
    assert doc["live_switch"] is False
    assert doc["real_trading"] is False
    assert doc["readiness_pct"] < 50
    assert any(item["id"] == "max_drawdown" and item["met"] for item in doc["items"])
    assert any(item["id"] == "dsr_pbo" and not item["met"] for item in doc["items"])
    assert doc["lessons_fa"]


def test_the_path_file_stays_on_g_and_hardware_measures_ram():
    doc = load_path_config()
    assert str(doc["root"]).lower().startswith("g:\\")
    assert doc["installer_plan"]["id"] == "M-PORT"
    assert doc["installer_plan"]["copies_env"] is False
    probe = detect_hardware()
    assert probe.ram_gb is not None
    assert probe.tier in {"T8", "T16", "T32", "GPU"}
