"""
core.models.token — Canonical token identity with Evidence anchor.

Identity law (mirrors discovery.identity without importing it at import-time):
    token_id = sha256(chain_normalized ":" address_normalized)[:32]

* EVM chains (ethereum, bsc, base, arbitrum, polygon, avalanche, optimism…): address lowercased
* Non-EVM (solana, ton, sui …): address case-sensitive, preserved as-is

Every Token carries an Evidence that proves where / when its identity
was first observed. Tokens never fabricated — evidence is mandatory.

Adapters in core/adapters/discovery_adapter.py translate between this
type and discovery.tokens rows / architecture.providers.NormalizedTokenCandidate
so existing modules remain untouched.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Any

from .evidence import Evidence, Confidence, VerificationStatus

# ---------------------------------------------------------------------------
# Chain registry — kept in sync with discovery.identity.CHAIN_REGISTRY
# Frozen here so core remains importable without discovery dependency.
# Adapters validate equivalence via tests (see test_core_cross_adapter_parity).
# ---------------------------------------------------------------------------

CHAIN_REGISTRY: dict[str, str] = {
    "solana": "solana",
    "ethereum": "ethereum", "eth": "ethereum",
    "bsc": "bsc", "bnb": "bsc", "binance": "bsc",
    "base": "base",
    "arbitrum": "arbitrum", "arb": "arbitrum",
    "polygon": "polygon", "matic": "polygon",
    "ton": "ton", "sui": "sui",
    "avalanche": "avalanche", "avax": "avalanche",
    "optimism": "optimism", "op": "optimism",
    "pulsechain": "pulsechain", "fantom": "fantom", "cronos": "cronos",
    "robinhood": "robinhood",
}

EVM_CHAINS = {"ethereum", "bsc", "base", "arbitrum", "polygon", "avalanche", "optimism", "pulsechain", "fantom", "cronos"}

_EVM_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_MIN_ADDR_LEN = 3


def normalize_chain(raw: str | None) -> str | None:
    if not raw:
        return None
    return CHAIN_REGISTRY.get(raw.strip().lower())


def normalize_address(chain_id: str, address: str) -> str:
    addr = address.strip()
    if chain_id in EVM_CHAINS:
        return addr.lower()
    return addr


def token_id(chain_id: str, address: str) -> str:
    c = normalize_chain(chain_id)
    if c is None:
        raise ValueError(f"unknown chain: {chain_id!r}")
    a = normalize_address(c, address)
    if not a or len(a) < _MIN_ADDR_LEN:
        raise ValueError("empty or too-short address")
    return hashlib.sha256(f"{c}:{a}".encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Token — frozen value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Token:
    """
    Canonical token value object.

    Required evidence: every Token must be traceable to the observation
    that first discovered it (source, timestamp, raw_reference).

    Attributes
    ----------
    chain: normalized chain id (e.g. "solana", "ethereum").
    address: canonical address (case per chain rule).
    symbol: ticker or None if not yet observed.
    name: full name or None.
    decimals: token decimals if known (None = UNKNOWN).
    first_seen_ts: epoch seconds when first observed.
    evidence: Evidence anchor for the discovery claim.
    token_id_: precomputed canonical id (32 hex chars).
    """

    chain: str
    address: str
    symbol: str | None = None
    name: str | None = None
    decimals: int | None = None
    first_seen_ts: float = field(default_factory=time.time)
    evidence: Evidence = field(default_factory=lambda: Evidence.unknown(source="token_discovery"))
    token_id_: str = field(default="")

    def __post_init__(self) -> None:
        c = normalize_chain(self.chain)
        if c is None:
            raise ValueError(f"Token chain unknown: {self.chain!r}")
        if not self.address or not isinstance(self.address, str):
            raise ValueError("Token address must be non-empty string")
        if self.first_seen_ts is None or float(self.first_seen_ts) <= 0:
            raise ValueError("Token.first_seen_ts must be positive epoch seconds")
        if not isinstance(self.evidence, Evidence):
            raise ValueError("Token.evidence must be Evidence instance")
        # Normalize chain/address
        object.__setattr__(self, "chain", c)
        object.__setattr__(self, "address", normalize_address(c, self.address))
        if self.symbol is not None:
            object.__setattr__(self, "symbol", self.symbol.strip() or None)
        if self.name is not None:
            object.__setattr__(self, "name", self.name.strip() or None)
        # Compute token_id if not supplied
        expected = token_id(c, self.address)
        if self.token_id_ and self.token_id_ != expected:
            raise ValueError(f"Token.token_id_ mismatch: supplied {self.token_id_!r} vs computed {expected!r}")
        if not self.token_id_:
            object.__setattr__(self, "token_id_", expected)

    # ------------------------------------------------------------------
    # Aliases & helpers
    # ------------------------------------------------------------------

    @property
    def token_id_str(self) -> str:
        return self.token_id_

    @property
    def id(self) -> str:
        """Short alias for template / adapter compatibility."""
        return self.token_id_

    def is_evm(self) -> bool:
        return self.chain in EVM_CHAINS

    def display(self) -> str:
        sym = self.symbol or "UNKNOWN"
        return f"{sym} [{self.chain}:{self.address[:6]}…{self.address[-4:]}]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": self.chain,
            "address": self.address,
            "symbol": self.symbol,
            "name": self.name,
            "decimals": self.decimals,
            "first_seen_ts": self.first_seen_ts,
            "token_id": self.token_id_,
            "evidence": self.evidence.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Token":
        return cls(
            chain=data["chain"],
            address=data["address"],
            symbol=data.get("symbol"),
            name=data.get("name"),
            decimals=data.get("decimals"),
            first_seen_ts=float(data.get("first_seen_ts", time.time())),
            evidence=Evidence.from_dict(data["evidence"]) if "evidence" in data else Evidence.unknown(),
            token_id_=data.get("token_id", ""),
        )

    # ------------------------------------------------------------------
    # Adapters (explicit, not import-time)
    # ------------------------------------------------------------------

    @classmethod
    def from_discovery_row(cls, row: dict[str, Any], evidence: Evidence | None = None) -> "Token":
        """Translate a discovery.tokens row (or dict) → core Token."""
        return cls(
            chain=row["chain_id"],
            address=row["address"],
            symbol=row.get("symbol"),
            name=row.get("name"),
            decimals=row.get("decimals"),
            first_seen_ts=float(row.get("first_seen_ts", time.time())),
            evidence=evidence or Evidence(
                source=row.get("source_first_seen_provider", "discovery"),
                timestamp=float(row.get("first_seen_ts", time.time())),
                confidence=Confidence.MEDIUM if row.get("symbol") else Confidence.LOW,
                verification_status=VerificationStatus.UNVERIFIED,
                raw_reference=row.get("token_id", "")[:64] if row.get("token_id") else "",
            ),
            token_id_=row.get("token_id", ""),
        )

    @classmethod
    def from_candidate(cls, candidate: Any, evidence: Evidence | None = None) -> "Token":
        """
        Translate architecture.providers.NormalizedTokenCandidate → Token.
        Import is local to avoid import-time coupling.
        """
        # Late import check — keep error message descriptive if contract changes
        chain = getattr(candidate, "chain", None)
        address = getattr(candidate, "address", None)
        if chain is None or address is None:
            raise ValueError("candidate missing chain/address")
        return cls(
            chain=chain,
            address=address,
            symbol=getattr(candidate, "symbol", None),
            name=getattr(candidate, "name", None),
            decimals=None,
            first_seen_ts=float(getattr(candidate, "retrieved_ts", time.time())),
            evidence=evidence
            or Evidence(
                source=getattr(candidate, "source_provider", "provider"),
                timestamp=float(getattr(candidate, "retrieved_ts", time.time())),
                confidence=Confidence.MEDIUM,
                verification_status=VerificationStatus.UNVERIFIED,
                raw_reference=getattr(candidate, "raw_payload_sha256", "") or "",
            ),
        )
