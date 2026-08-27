#!/usr/bin/env python3
"""Phase 1 — canonical token identity (single authority, fail-closed)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.canonical.identity import (
    canonical_token_id, canonical_chain, canonical_address,
)
from discovery.identity import token_id as lane_a_token_id  # parity check only


EVM = "0xAbCd000000000000000000000000000000001234"
SOL = "So11111111111111111111111111111111111111112"


def test_delegates_to_lane_a_authority():
    assert canonical_token_id("ethereum", EVM) == lane_a_token_id("ethereum", EVM)


def test_evm_address_casing_is_normalized():
    assert canonical_token_id("ethereum", EVM) == canonical_token_id("ethereum", EVM.lower())
    assert canonical_token_id("ethereum", EVM) == canonical_token_id("ethereum", EVM.upper())


def test_chain_alias_normalization():
    assert canonical_token_id("eth", EVM) == canonical_token_id("ethereum", EVM)
    assert canonical_token_id("bnb", EVM) == canonical_token_id("bsc", EVM)


def test_solana_identity_is_case_sensitive():
    assert canonical_token_id("solana", SOL) is not None
    assert canonical_token_id("solana", SOL) != canonical_token_id("solana", SOL.lower())


def test_same_contract_different_symbol_is_same_identity():
    # identity has no symbol input → same contract yields same id regardless of symbol
    assert canonical_token_id("ethereum", EVM) == canonical_token_id("ethereum", EVM)


def test_same_symbol_different_contract_is_different_identity():
    other = "0xdead000000000000000000000000000000009999"
    assert canonical_token_id("ethereum", EVM) != canonical_token_id("ethereum", other)


def test_fail_closed_on_missing_or_malformed():
    assert canonical_token_id(None, EVM) is None
    assert canonical_token_id("ethereum", None) is None
    assert canonical_token_id("", EVM) is None
    assert canonical_token_id("ethereum", "") is None
    assert canonical_token_id("not-a-chain", EVM) is None
    assert canonical_token_id(123, EVM) is None  # type: ignore[arg-type]


def test_canonical_chain_and_address_helpers_fail_closed():
    assert canonical_chain("eth") == "ethereum"
    assert canonical_chain("nope") is None
    assert canonical_chain(None) is None
    assert canonical_address("ethereum", EVM) == EVM.lower()
    assert canonical_address("solana", SOL) == SOL
    assert canonical_address("nope", EVM) is None
    assert canonical_address("ethereum", "") is None
