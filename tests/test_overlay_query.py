#!/usr/bin/env python3
"""Lane B overlay_query adapter — consumes evaluate_security, does not copy it."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.security.overlay_query import run, signals_from_dict
from tests.helpers_security import OLD_POOL_TS, passing_security_signals

NOW = 1_800_000_000.0


def test_missing_signals_are_incomplete():
    states = run({"tokens": [{"tokenKey": "solana:x", "signals": {}}]}, now=NOW)
    assert states["solana:x"] == "INCOMPLETE"


def test_passing_signals_with_age_can_pass():
    sec = passing_security_signals()
    payload = {
        "tokens": [{
            "tokenKey": "solana:ok",
            "signals": {
                "is_honeypot": sec.is_honeypot,
                "sell_tax_pct": sec.sell_tax_pct,
                "buy_tax_pct": sec.buy_tax_pct,
                "liquidity_locked_pct": sec.liquidity_locked_pct,
                "has_mint_authority": sec.has_mint_authority,
                "has_freeze_authority": sec.has_freeze_authority,
                "is_contract_verified": sec.is_contract_verified,
                "is_ownership_renounced": sec.is_ownership_renounced,
                "top10_holder_concentration_pct": sec.top10_holder_concentration_pct,
                "deployer_past_rug_count": sec.deployer_past_rug_count,
                "is_blacklisted": sec.is_blacklisted,
                "cannot_sell_all": sec.cannot_sell_all,
                "is_proxy": sec.is_proxy,
            },
            "pair_created_ts": OLD_POOL_TS,
            "retrieved_ts": NOW,
        }],
    }
    states = run(payload, now=NOW)
    assert states["solana:ok"] == "PASS"


def test_honeypot_true_is_reject():
    sec = passing_security_signals(is_honeypot=True)
    payload = {
        "tokens": [{
            "tokenKey": "solana:bad",
            "signals": {"is_honeypot": True, "cannot_sell_all": False,
                        "has_mint_authority": False, "has_freeze_authority": False,
                        "is_blacklisted": False, "sell_tax_pct": 1.0,
                        "deployer_past_rug_count": 0, "liquidity_locked_pct": 95.0},
            "pair_created_ts": OLD_POOL_TS,
            "retrieved_ts": NOW,
        }],
    }
    assert run(payload, now=NOW)["solana:bad"] == "REJECT"


def test_string_yes_does_not_become_false_or_true():
    sig = signals_from_dict({"is_honeypot": "YES"})
    assert sig.is_honeypot is None


def test_malformed_payload_is_empty():
    assert run({"tokens": "nope"}, now=NOW) == {}
    assert run({}, now=NOW) == {}


def test_typescript_goplus_snapshot_cannot_pass():
    """Typical TS GoPlus fields are not a complete overlay PASS."""
    payload = {
        "tokens": [{
            "tokenKey": "solana:ts",
            "signals": {
                "is_honeypot": False,
                "has_mint_authority": False,
                "has_freeze_authority": False,
                "is_ownership_renounced": True,
                "cannot_sell_all": False,
            },
            "pair_created_ts": OLD_POOL_TS,
            "retrieved_ts": NOW,
        }],
    }
    assert run(payload, now=NOW)["solana:ts"] == "INCOMPLETE"


def test_adapter_does_not_import_discovery():
    src = (ROOT / "architecture" / "security" / "overlay_query.py").read_text(encoding="utf-8")
    assert "from discovery" not in src
    assert "import discovery" not in src
    assert "evaluate_security" in src
    assert "VETO_REGISTRY" not in src
    assert "def evaluate(" not in src


def test_cli_malformed_does_not_emit_pass():
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "architecture.security.overlay_query"],
        input="not-json",
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    data = json.loads(proc.stdout)
    assert data.get("states") == {}
    assert "PASS" not in json.dumps(data)
