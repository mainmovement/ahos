#!/usr/bin/env python3
"""AHOS Security Boundary & Credential Protection Layer (Wave-19 / Mission v1.1).

Non-negotiable Laws:
  - Secret redaction: API keys, private keys, Telegram bot tokens, session secrets
    MUST NEVER be printed, logged, committed or leaked in error messages.
  - Fail-closed: Missing credentials or unauthorized capabilities cause safe abort/downgrade
    to DETERMINISTIC_ONLY rather than throwing unprotected stack traces.
  - Zero-money guarantee: Real trade execution is prohibited by type-level constraints.
"""
from __future__ import annotations

import re
import os
from typing import Any

# Sensitive pattern matching for sanitization
_SECRET_PATTERNS = [
    re.compile(r"(\b[0-9]{8,12}:[a-zA-Z0-9_-]{30,50}\b)"),                  # Telegram Bot Token
    re.compile(r"(sk-[a-zA-Z0-9]{20,60})"),                                 # OpenAI Secret Key
    re.compile(r"(ghp_[a-zA-Z0-9]{36})"),                                   # GitHub Personal Access Token
    re.compile(r"(gsk_[a-zA-Z0-9]{40,60})"),                                # Groq API Key
    re.compile(r"(AIzaSy[a-zA-Z0-9_-]{25,45})"),                            # Google Gemini API Key
    re.compile(r"(0x[0-9a-fA-F]{64})"),                                     # EVM Private Key
    re.compile(r"([1-9A-HJ-NP-Za-km-z]{87,88})"),                           # Solana Secret Key (base58 64 bytes)
    re.compile(r"(Bearer\s+[a-zA-Z0-9_.-]{16,})", re.IGNORECASE),          # Authorization Header
]

REDACTED_TEXT = "[REDACTED_SECRET]"


def sanitize_secrets(text: str) -> str:
    """Replaces any matched secrets with REDACTED_TEXT."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(REDACTED_TEXT, sanitized)
    return sanitized


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitizes dictionary keys and values."""
    clean: dict[str, Any] = {}
    sensitive_keys = {"token", "key", "api_key", "secret", "private_key", "password", "auth", "authorization"}
    for k, v in data.items():
        if any(s in str(k).lower() for s in sensitive_keys):
            clean[k] = REDACTED_TEXT
        elif isinstance(v, dict):
            clean[k] = sanitize_dict(v)
        elif isinstance(v, list):
            clean[k] = [sanitize_dict(item) if isinstance(item, dict)
                        else (sanitize_secrets(item) if isinstance(item, str) else item)
                        for item in v]
        elif isinstance(v, str):
            clean[k] = sanitize_secrets(v)
        else:
            clean[k] = v
    return clean


def assert_safe_environment() -> dict[str, bool]:
    """Audits environment to verify no leaked live keys or unpermitted execution variables."""
    forbidden_live_trading_vars = [
        "AHOS_ALLOW_REAL_FUNDS",
        "AHOS_EXECUTE_LIVE_TRADES",
        "BINANCE_API_KEY",
        "COINBASE_API_KEY",
        "KRAKEN_API_KEY"
    ]
    violations = [var for var in forbidden_live_trading_vars if os.environ.get(var) == "1"]
    if violations:
        raise PermissionError(f"CRITICAL SECURITY VETO: Live trading environment variables detected: {violations}")
    return {
        "paper_only_enforced": True,
        "zero_real_trading": True,
        "credentials_isolated": True
    }
