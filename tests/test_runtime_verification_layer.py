"""W56 runtime verification (static / mock)."""
from __future__ import annotations
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_metrics_api_route_exists():
    assert (ROOT / "app" / "api" / "metrics" / "route.ts").is_file()


def test_no_real_telegram_token_outside_tests():
    pattern = re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}")
    for path in ROOT.rglob("*"):
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".json"}:
            continue
        if any(x in path.parts for x in (".git", "node_modules", "tests")):
            continue
        if path.name.endswith(".example"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        matches = [m for m in pattern.findall(text) if not m.startswith("123456789:")]
        if matches:
            pytest.fail(f"Possible bot token in {path}")


def test_gateway_env_and_contracts():
    assert "AHOS_GATEWAY_URL" in (ROOT / "telegram_ai" / "service.py").read_text()
    assert "createAlertEvent" in (ROOT / "alert_canonical.ts").read_text()
    assert "fromScored" in (ROOT / "opportunity_canonical.ts").read_text()
    assert "mayEmitCritical" in (ROOT / "opportunity_canonical.ts").read_text()
