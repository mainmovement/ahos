"""W57 architecture invariants: One Brain routing."""
from __future__ import annotations
import ast
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_no_opportunity_scorer_import_in_telegram():
    src = (ROOT / "telegram_ai" / "service.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "scoring" in (node.module or ""):
            for alias in node.names or []:
                if alias.name == "OpportunityScorer":
                    pytest.fail("Telegram must not import OpportunityScorer")


def test_scorer_is_none_and_emergency_fallback():
    import telegram_ai.service as m
    from telegram_ai.service import TelegramDomainService

    assert TelegramDomainService().scorer is None
    old = m.AHOS_GATEWAY_URL
    m.AHOS_GATEWAY_URL = ""
    try:
        out = TelegramDomainService().handle_message("test", {})
        assert out.get("source") == "EMERGENCY_FALLBACK_ONLY"
        assert out.get("status") == "EMERGENCY_FALLBACK_ONLY"
    finally:
        m.AHOS_GATEWAY_URL = old


def test_gateway_and_canonical_modules_exist():
    for name in (
        "conversation_gateway.ts",
        "opportunity_canonical.ts",
        "alert_canonical.ts",
        "provider_health.ts",
        "engine_metrics.ts",
    ):
        assert (ROOT / name).is_file(), name
    assert "conversationGateway" in (ROOT / "app" / "api" / "chat" / "route.ts").read_text()
    body = (ROOT / "types.ts").read_text()
    for s in (
        "LIVE",
        "DEGRADED",
        "TIMEOUT",
        "RATE_LIMITED",
        "NO_KEY",
        "AUTH_FAILED",
        "NETWORK_UNAVAILABLE",
        "SOURCE_UNAVAILABLE",
        "UNKNOWN",
    ):
        assert s in body


def test_require_scorer_forbidden_raises():
    from telegram_ai.service import TelegramDomainService

    with pytest.raises(RuntimeError, match="W57"):
        TelegramDomainService()._require_scorer_forbidden()
