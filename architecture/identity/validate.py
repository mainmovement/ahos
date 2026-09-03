#!/usr/bin/env python3
"""Address and chain validators for Lane B identity resolution."""
from __future__ import annotations

import re

from architecture.identity.keccak256 import keccak256
from architecture.identity.types import IdentityState

EVM_HEX = re.compile(r"^(0[xX])?[0-9a-fA-F]{40}$")
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE58_MAP = {c: i for i, c in enumerate(BASE58_ALPHABET)}

# Mirror of frozen Lane A EVM set — charset checks stay local; hashing still
# goes through discovery.identity.
EVM_CHAINS = {
    "ethereum", "bsc", "base", "arbitrum", "polygon", "avalanche",
    "optimism", "pulsechain", "fantom", "cronos",
}


def strip_0x(address: str) -> str:
    a = address.strip()
    if a[:2].lower() == "0x":
        return a[2:]
    return a


def eip55_checksum(address: str) -> str:
    body = strip_0x(address).lower()
    hashed = keccak256(body.encode("ascii")).hex()
    out = []
    for ch, hv in zip(body, hashed):
        if ch.isalpha() and int(hv, 16) >= 8:
            out.append(ch.upper())
        else:
            out.append(ch)
    return "0x" + "".join(out)


def validate_evm_address(
    address: str | None,
) -> tuple[IdentityState, str, str | None, bool | None]:
    """Return (state, reason, canonical_lowercase_0x, checksum_ok).

    checksum_ok is True/False only when mixed-case EIP-55 is supplied.
    All-lower / all-upper hex is length-valid but checksum-unverified (None).
    """
    if not address or not str(address).strip():
        return IdentityState.INVALID, "empty_address", None, None
    raw = address.strip()
    if not EVM_HEX.match(raw):
        return IdentityState.INVALID, "evm_address_not_20_bytes_hex", None, None
    body = strip_0x(raw)
    canonical = "0x" + body.lower()
    mixed = (
        any(c.isalpha() and c.isupper() for c in body)
        and any(c.isalpha() and c.islower() for c in body)
    )
    if mixed:
        expected = eip55_checksum(canonical)
        if body != expected[2:]:
            return IdentityState.INVALID, "evm_checksum_mismatch", canonical, False
        return IdentityState.UNRESOLVED, "evm_length_ok_checksum_ok", canonical, True
    return IdentityState.UNRESOLVED, "evm_length_ok", canonical, None


def decode_base58(value: str) -> bytes | None:
    n = 0
    for ch in value:
        if ch not in BASE58_MAP:
            return None
        n = n * 58 + BASE58_MAP[ch]
    pad = 0
    for ch in value:
        if ch == "1":
            pad += 1
        else:
            break
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    if n:
        return b"\x00" * pad + raw
    return b"\x00" * pad


def validate_solana_address(
    address: str | None,
) -> tuple[IdentityState, str, str | None]:
    """Preserve the supplied canonical base58 string. Do not lowercase."""
    if not address or not str(address).strip():
        return IdentityState.INVALID, "empty_address", None
    raw = address.strip()
    decoded = decode_base58(raw)
    if decoded is None:
        return IdentityState.INVALID, "solana_not_base58", None
    if len(decoded) != 32:
        return IdentityState.INVALID, "solana_not_32_byte_pubkey", None
    return IdentityState.UNRESOLVED, "solana_canonical_preserved", raw


def validate_address_for_chain(
    chain: str, address: str | None
) -> tuple[IdentityState, str, str | None, bool | None]:
    if chain in EVM_CHAINS:
        return validate_evm_address(address)
    if chain == "solana":
        st, reason, canonical = validate_solana_address(address)
        return st, reason, canonical, None
    if not address or not str(address).strip():
        return IdentityState.INVALID, "empty_address", None, None
    return IdentityState.UNRESOLVED, "chain_no_extra_validator", address.strip(), None
