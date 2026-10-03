"""MN-4 static guards for the Gemini egress approval record.

Self-test, not independent verification. Pure file reads: no network, no DB,
no services, no key. Pins the committed record so a silent substitution or a
tamper is caught, and pins the gate wiring so a later edit cannot re-enable
Gemini egress without the owner's approval record.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "config" / "gemini_egress.json"

# Pinned by hand at Mission 9.6 commit time. The record is small (681 bytes) and
# human-auditable; if the owner deliberately edits it (e.g. revokes a channel),
# this pin must be updated in the same change — that is the point.
PINNED_SHA256 = "763aa1a53dca2785be5ef90f4d0420f95931af4a93b946834a8d2ad88759a507"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_record_is_committed_and_schema_valid() -> None:
    assert RECORD.is_file(), "config/gemini_egress.json must be committed"
    raw = json.loads(RECORD.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    assert raw["approved"] is True
    assert isinstance(raw["approvedAt"], str) and raw["approvedAt"]
    assert isinstance(raw["approvedBy"], str) and raw["approvedBy"]
    assert isinstance(raw["scope"], list)
    assert all(isinstance(s, str) for s in raw["scope"])
    assert set(raw["scope"]) >= {"phraser", "chat_agent"}
    assert isinstance(raw["recipients"], list)
    assert all(isinstance(s, str) for s in raw["recipients"])
    assert raw["revokedAt"] is None


def test_record_sha256_is_pinned() -> None:
    digest = hashlib.sha256(RECORD.read_bytes()).hexdigest()
    assert digest == PINNED_SHA256, (
        "config/gemini_egress.json changed; update PINNED_SHA256 deliberately "
        "in the same change (and re-audit the new file by hand)"
    )


def test_record_holds_no_secret_material() -> None:
    blob = RECORD.read_text(encoding="utf-8")
    assert len(blob) < 2000, "the record must stay small enough to audit by hand"
    for banned in (
        r"AIza[0-9A-Za-z_-]{20,}",          # Gemini API key prefix
        r"\bsk-[A-Za-z0-9]{16,}",           # OpenAI-style key
        r"Bearer\s+[A-Za-z0-9._-]{8,}",     # bearer token
        r"-----BEGIN[A-Z ]*KEY-----",       # PEM private key
        r"[0-9A-Fa-f]{40,}",                # hex secret / hash
        r"[A-Za-z0-9_-]{32,}",              # opaque high-entropy token
    ):
        assert not re.search(banned, blob), f"record must not contain {banned}"


def test_gate_module_fails_closed() -> None:
    src = _read("gemini_egress_config.ts")
    fn = src[src.index("export function egressApproved"):]
    fn = fn[: fn.index("\n}\n")]
    # Every disabling condition is checked before any approval.
    assert "if (killed(scope, src)) return false;" in fn
    assert "if (!rec) return false;" in fn
    assert "if (!rec.approved) return false;" in fn
    assert "if (rec.revokedAt !== null) return false;" in fn
    assert "return rec.scope.includes(scope)" in fn
    # The kill switch helper treats only explicit off-values as off.
    killed = src[src.index("function killed("):]
    killed = killed[: killed.index("\n}\n")]
    assert '["off", "0", "false", "none"]' in killed


def test_both_egress_channels_go_through_the_gate() -> None:
    phraser = _read("gemini_phraser.ts")
    assert 'egressApproved("phraser", src)' in phraser
    agent = _read("chat_agent.ts")
    assert 'egressApproved("chat_agent", src)' in agent
    # Nothing else in the TS surface calls Gemini directly.
    for rel in ("gemini_phraser.ts", "chat_agent.ts"):
        assert "gemini.googleapis.com" not in _read(rel)


def test_npm_selftest_registered() -> None:
    pkg = _read("package.json")
    assert '"test:gemini-egress"' in pkg
    assert "scripts/gemini_egress_selftest.ts" in pkg
    assert (ROOT / "scripts" / "gemini_egress_selftest.ts").is_file()
