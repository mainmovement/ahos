from __future__ import annotations

import json
from pathlib import Path

from architecture.health.unification_audit import build_unification_audit
from architecture.markets.edge_desk_policy import export_desk_policy
from architecture.university.desk_signal_feed import export_desk_signal_feed
from scripts.export_edge_report import build_edge_report


def _minimal_edge_bundle(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        json.dumps(
            {
                "event": "CLOSE",
                "symbol": "BTC",
                "desk": "CRYPTO",
                "realized_pnl_usd": -0.02,
                "fees_usd": 0.001,
                "entry_brain": {"contributions": [{"signal": "mtf_trend", "weight": 0.4, "score": 0.5}]},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.export_edge_report.export_paper_trade_audit_snapshot",
        lambda _r: {"status": "GREEN"},
    )
    report = build_edge_report(tmp_path)
    edge_path = tmp_path / "reports" / "grok" / "PAPER" / "edge_report.json"
    edge_path.write_text(json.dumps(report, ensure_ascii=False) + "\n", encoding="utf-8")
    export_desk_policy(tmp_path, report)
    export_desk_signal_feed(tmp_path)


def test_unification_skips_desk_artifacts_without_edge_report(tmp_path: Path):
    audit = build_unification_audit(tmp_path)
    ids = [c["id"] for c in audit["checks"]]
    assert "edge.desk_artifacts" not in ids


def test_unification_passes_when_desk_artifacts_match_edge(tmp_path: Path, monkeypatch):
    _minimal_edge_bundle(tmp_path, monkeypatch)
    audit = build_unification_audit(tmp_path)
    row = next(c for c in audit["checks"] if c["id"] == "edge.desk_artifacts")
    assert row["status"] == "PASS"


def test_unification_fails_when_desk_policy_drifts(tmp_path: Path, monkeypatch):
    _minimal_edge_bundle(tmp_path, monkeypatch)
    policy = tmp_path / "reports" / "grok" / "PAPER" / "desk_policy.json"
    doc = json.loads(policy.read_text(encoding="utf-8"))
    doc["edge_status"] = "PROVEN_EDGE"
    policy.write_text(json.dumps(doc), encoding="utf-8")
    audit = build_unification_audit(tmp_path)
    row = next(c for c in audit["checks"] if c["id"] == "edge.desk_artifacts")
    assert row["status"] == "FAIL"
