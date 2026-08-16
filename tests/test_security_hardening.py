#!/usr/bin/env python3
"""Security Hardening & Zero-Leakage Regression Tests (Phase XX)."""
import sys, os
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.security import (
    sanitize_secrets, sanitize_dict, assert_safe_environment, REDACTED_TEXT
)


def test_sanitize_telegram_bot_token():
    text = "Bot token: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567, please keep safe"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "123456789:ABCdef" not in clean


def test_sanitize_openai_api_key():
    text = "Using OpenAI key sk-1234567890abcdefghijklmnopqrstuvwxyz12 for inference"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "sk-1234567890" not in clean


def test_sanitize_groq_api_key():
    text = "Groq key: gsk_1234567890abcdefghijklmnopqrstuvwxyz123456"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "gsk_123456" not in clean


def test_sanitize_gemini_api_key():
    text = "Gemini key: AIzaSyD1234567890abcdefghijklmnopqr"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "AIzaSy" not in clean


def test_sanitize_github_token():
    text = "GitHub PAT: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "ghp_123456" not in clean


def test_sanitize_evm_private_key():
    text = "Private key: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "0x1234567890abcdef" not in clean


def test_sanitize_bearer_token():
    text = "Authorization: Bearer mySecretToken123456789"
    clean = sanitize_secrets(text)
    assert REDACTED_TEXT in clean
    assert "mySecretToken" not in clean


def test_sanitize_dict_recursive():
    payload = {
        "status": "OK",
        "api_key": "sk-secret123",
        "nested": {
            "token": "secret_token_123",
            "normal_field": "public_data",
            "list_items": [
                "normal",
                "contains Bearer abcdef1234567890",
                {"password": "super_secret_pwd"}
            ]
        }
    }
    clean = sanitize_dict(payload)
    assert clean["api_key"] == REDACTED_TEXT
    assert clean["nested"]["token"] == REDACTED_TEXT
    assert clean["nested"]["normal_field"] == "public_data"
    assert clean["nested"]["list_items"][0] == "normal"
    assert REDACTED_TEXT in clean["nested"]["list_items"][1]
    assert clean["nested"]["list_items"][2]["password"] == REDACTED_TEXT


def test_assert_safe_environment_live_trading_veto():
    os.environ["AHOS_ALLOW_REAL_FUNDS"] = "1"
    try:
        with pytest.raises(PermissionError) as exc:
            assert_safe_environment()
        assert "CRITICAL SECURITY VETO" in str(exc.value)
    finally:
        del os.environ["AHOS_ALLOW_REAL_FUNDS"]
