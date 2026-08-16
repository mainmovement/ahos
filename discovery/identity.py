#!/usr/bin/env python3
"""AHOS STEP 3 — Canonical Token Identity.
token_id = sha256(chain_id ":" address-normalized)[:32]  (hex chars)
EVM chains: address lowercased (checksum-insensitive). Solana & base58 chains: exact case preserved.
pair_id  = sha256(chain_id ":" dex ":" pair_address)[:32]
Chain vocabulary is a controlled registry; provider spellings normalized here and ONLY here.
"""
from __future__ import annotations
import hashlib

CHAIN_REGISTRY = {
    "solana": "solana",
    "ethereum": "ethereum", "eth": "ethereum",
    "bsc": "bsc", "bnb": "bsc", "binance": "bsc",
    "base": "base",
    "arbitrum": "arbitrum", "arb": "arbitrum",
    "polygon": "polygon", "matic": "polygon",
    "ton": "ton", "sui": "sui", "avalanche": "avalanche", "avax": "avalanche",
    "optimism": "optimism", "op": "optimism",
    "pulsechain": "pulsechain", "fantom": "fantom", "cronos": "cronos",
    "robinhood": "robinhood",    # observed in live DexScreener payload 2026-08-11
}
EVM_CHAINS = {"ethereum", "bsc", "base", "arbitrum", "polygon", "avalanche",
              "optimism", "pulsechain", "fantom", "cronos"}


def normalize_chain(raw: str | None) -> str | None:
    if not raw:
        return None
    return CHAIN_REGISTRY.get(raw.strip().lower())


def normalize_address(chain_id: str, address: str) -> str:
    address = address.strip()
    if chain_id in EVM_CHAINS:
        return address.lower()
    return address  # solana/ton/sui: base58/base64 case-sensitive — preserve


def token_id(chain_id: str, address: str) -> str:
    c = normalize_chain(chain_id)
    if c is None:
        raise ValueError(f"unknown chain: {chain_id!r}")
    a = normalize_address(c, address)
    if not a:
        raise ValueError("empty address")
    return hashlib.sha256(f"{c}:{a}".encode()).hexdigest()[:32]


def pair_id(chain_id: str, dex_id: str, pair_address: str) -> str:
    c = normalize_chain(chain_id)
    if c is None:
        raise ValueError(f"unknown chain: {chain_id!r}")
    d = (dex_id or "unknown").strip().lower()
    p = normalize_address(c, pair_address)
    return hashlib.sha256(f"{c}:{d}:{p}".encode()).hexdigest()[:32]


def obs_id(token: str, pair: str | None, provider: str, retrieved_ts: float, raw_sha: str) -> str:
    return hashlib.sha256(f"{token}|{pair or ''}|{provider}|{retrieved_ts}|{raw_sha}".encode()).hexdigest()[:32]
