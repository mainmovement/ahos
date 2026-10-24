from __future__ import annotations

from pathlib import Path

from architecture.markets.session_readiness_drill import build_session_readiness_drill


def test_session_drill_has_tehran_countdown(tmp_path: Path) -> None:
    payload = build_session_readiness_drill(tmp_path, quotes={})
    assert payload["schema"] == "ahos.session_readiness_drill.v1"
    assert payload["paper_only"] is True
    sessions = payload["cash_sessions"]
    assert len(sessions) == 3
    assert "countdown_fa" in sessions[0]
    assert "adapters" in payload
    out = tmp_path / "reports" / "grok" / "PAPER" / "session_readiness_drill.json"
    assert out.is_file()
