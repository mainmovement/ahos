#!/usr/bin/env python3
"""Configuration validation: every operator-facing env key read by the
canonical runtime packages must be documented in `.env.example` (or be an
explicit, reason-carrying legacy exception).

Why: a key added in code but never documented silently becomes an
undiscoverable operator knob; a key documented but never read is dead
documentation. This test pins the first direction — the drift that actually
causes operator confusion (e.g. COINGECKO_API_KEY existed in code but not in
.env.example until 2026-08-20).

Scope: architecture/, telegram_ai/, scripts/, run_bot.py, and the
One-Brain TypeScript surface that reads process.env (alerts.ts,
web_api_client.ts, …).
`engine/` (legacy lane, documented-excluded entrypoints) and
`config/paths.py` overrides (AHOS_DATA_DIR / AHOS_ROOT / AHOS_ENV /
AHOS_IN_DOCKER — test/ops knobs) are explicit exceptions with reasons.

The test scans SOURCE, not imports: it lists every `os.environ.get("KEY")`
literal (Python) and `process.env.KEY` (TypeScript) so a new env read
fails loudly until it is documented.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENV_READ_RE = re.compile(r'os\.environ\.(?:get|getenv)\(\s*["\']([A-Z_][A-Z0-9_]*)["\']')
TS_ENV_READ_RE = re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)')
# Mission 9.5: chat_auth.ts reads env through an injected EnvMap
# (`readSecret(env, "KEY")`) so tests can pass a fake env — the key is a quoted
# literal, not a `process.env.KEY` member access. Catch that form too, or an
# injected env read would silently escape the documentation law.
TS_INJECTED_ENV_READ_RE = re.compile(
    r'readSecret\(\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*["\']([A-Z_][A-Z0-9_]*)["\']')

SCAN_DIRS = (
    "architecture",
    "telegram_ai",
    "scripts",
)
SCAN_FILES = ("run_bot.py",)
# One-Brain TypeScript modules at repo root (pinned by architecture tests).
# Mission 9.5: web_api_client.ts no longer reads any token — the dashboard
# authenticates with a server-issued httpOnly session cookie + CSRF header
# (chat_auth.ts), because a NEXT_PUBLIC_* value was compiled into the browser
# bundle and readable by anyone who could load the page (review BLOCKER B1).
# canonical_read_model.ts is the only TypeScript reader of
# AHOS_CANONICAL_READ_MODEL (Python writes; TS must not invent BUY).
SCAN_TS_FILES = (
    "alerts.ts",
    "engine.ts",
    "providers.ts",
    "conversation_gateway.ts",
    "chat.ts",
    "web_api_client.ts",
    "canonical_read_model.ts",
    "web_api_auth.ts",
    "chat_auth.ts",
)

#: Explicit exceptions — every entry must carry a reason.
LEGACY_ENV_KEYS: dict[str, str] = {
    "TELEGRAM_ALLOWED_CHATS": "legacy alias for TELEGRAM_ALLOWED_CHAT_IDS "
                              "(runtime reads both for back-compat)",
    "TELEGRAM_ADMIN_CHAT_ID": "legacy alias for TELEGRAM_ADMIN_USER_IDS",
    "AHOS_LOCAL_DB": "legacy lane only (engine/bot_skeleton.py, a documented "
                     "excluded entrypoint)",
    "NEXT_PUBLIC_AHOS_WEB_API_TOKEN": "still written/synced by operator scripts "
                                      "(windows_ensure_web_api_token.ps1) and used as a "
                                      "server-side bearer by probes; no browser code reads "
                                      "it since the Mission 9.5 session-cookie switch",
}


def _documented_keys() -> set[str]:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Z_][A-Z0-9_]*)=.*$", text, flags=re.M))


def _scanned_source_keys() -> set[str]:
    keys: set[str] = set()
    for d in SCAN_DIRS:
        for p in (ROOT / d).rglob("*.py"):
            if "__pycache__" in str(p):
                continue
            keys.update(ENV_READ_RE.findall(p.read_text(encoding="utf-8")))
    for f in SCAN_FILES:
        p = ROOT / f
        if p.exists():
            keys.update(ENV_READ_RE.findall(p.read_text(encoding="utf-8")))
    for f in SCAN_TS_FILES:
        p = ROOT / f
        if p.exists():
            text = p.read_text(encoding="utf-8")
            keys.update(TS_ENV_READ_RE.findall(text))
            keys.update(TS_INJECTED_ENV_READ_RE.findall(text))
    # AI providers consume keys through `key_env:` fields in the two provider
    # registries (architecture/ai/clients.py reads them) — same documentation
    # law applies.
    for yaml_name in ("ai_provider_registry.yaml", "ai_council_providers.yaml"):
        yaml_path = ROOT / "config" / yaml_name
        if yaml_path.exists():
            keys.update(re.findall(r"key_env:\s*([A-Z_][A-Z0-9_]*)",
                                   yaml_path.read_text(encoding="utf-8")))
    return keys


def test_every_canonical_env_key_is_documented_or_explicit_exception():
    documented = _documented_keys()
    scanned = _scanned_source_keys()

    missing = sorted(k for k in scanned
                     if k not in documented and k not in LEGACY_ENV_KEYS)
    assert not missing, (
        f"env key(s) read by canonical code but absent from .env.example and "
        f"LEGACY_ENV_KEYS: {missing} — document them in .env.example or add a "
        "reasoned exception in tests/test_config_validation.py")


def test_legacy_exceptions_are_reasoned():
    for key, reason in LEGACY_ENV_KEYS.items():
        assert len(reason) > 20, f"{key} exception lacks a real reason"


def test_documented_keys_are_actually_read_or_legacy():
    """Dead documentation is also drift: every .env.example key must be read
    somewhere in the canonical surface (or be an intentional alias set)."""
    scanned = _scanned_source_keys()
    # keys read only via config/paths.py or the ai provider registry
    paths_keys = {"AHOS_DATA_DIR", "AHOS_ROOT", "AHOS_ENV", "AHOS_IN_DOCKER"}
    documented = _documented_keys()
    dead = sorted(k for k in documented
                  if k not in scanned and k not in paths_keys
                  and k not in LEGACY_ENV_KEYS)
    # keys that are only read by legacy engine/ lane are intentional
    engine_only = {
        "AHOS_LOCAL_DB",  # legacy lane
    }
    dead = [k for k in dead if k not in engine_only]
    assert not dead, (
        f".env.example documents key(s) no canonical code reads: {dead} — "
        "remove them or document where they are consumed")
