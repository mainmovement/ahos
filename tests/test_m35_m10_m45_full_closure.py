"""Tests for M35.3 Telegram/Kian Closure, M10 Stage 1-5 DB Migration Closure, and M45 Sandbox Isolation."""
from __future__ import annotations

from architecture.ai.telegram_bridge_verifier import verify_m35_telegram_and_kian_closure
from architecture.health.db_migration_m10 import verify_m10_db_migration_closure
from architecture.health.lab_gate import lab_status, verify_m45_sandbox_isolation


def test_m35_telegram_bridge_verifier_redacts_secrets() -> None:
    fake_tok = "123456789:AAH_test_secret_token_value_1234567890"
    res = verify_m35_telegram_and_kian_closure(
        env_override={
            "TELEGRAM_BOT_TOKEN": fake_tok,
            "TELEGRAM_ALLOWED_CHAT_IDS": "111222333",
            "AHOS_TELEGRAM_GATEWAY_SECRET": "a" * 32,
        }
    )
    assert res["paper_only"] is True
    assert res["status"] == "VERIFIED_CONFIGURED"
    assert res["token_redacted"] is True
    assert res["credentials_audit"]["telegram_bot_token_format_valid"] is True
    assert res["credentials_audit"]["raw_secrets_exposed"] is False
    # Ensure the raw token string never appears anywhere in the serialized output
    assert fake_tok not in str(res)


def test_m10_db_migration_all_five_stages_done() -> None:
    res = verify_m10_db_migration_closure(env_override={"DATABASE_URL": "postgresql://local/ahos"})
    assert res["paper_only"] is True
    assert res["status"] == "DONE"
    assert res["stages_completed"] == [1, 2, 3, 4, 5]
    assert res["docker_daemon_required"] is False


def test_m45_sandbox_isolation_enforced_clean() -> None:
    assert lab_status(low_priv_configured=False).spawned is False
    assert lab_status(low_priv_configured=True).spawned is False
    res = verify_m45_sandbox_isolation()
    assert res["paper_only"] is True
    assert res["status"] == "ENFORCED_CLEAN"
    assert res["subprocess_spawn_blocked"] is True
    assert res["env_write_blocked"] is True
    assert res["safety_file_write_blocked"] is True
