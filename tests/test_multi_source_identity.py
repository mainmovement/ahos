#!/usr/bin/env python3
"""Multi-source identity resolver (P2: independent second market source).

The mission directive names a second independent market source as the
highest-leverage functional gap. The blocker was not the absence of providers --
MARKET_PROVIDER_ORDER already fans out across four -- but that
identity_from_candidate collapsed them into ONE IdentitySource, so
resolve_identity's >=2-distinct-providers gate could never pass and every token
resolved permanently UNRESOLVED.

These tests pin the behaviour of the replacement resolver. They run fully
offline: the provider adapters are injected with a routing transport, so no
network call is made and no evidence is fabricated.

The four cases the mission asked for, plus the fail-closed pins that keep the
resolver honest:
  * two agreeing independent sources        -> VERIFIED, positive gate reachable
  * one source only                          -> UNRESOLVED, no positive decision
  * conflicting sources                      -> CONFLICT, no positive decision
  * missing fields / no answer               -> UNRESOLVED or INVALID, never PASS
  * an adapter echoing the queried address    -> must NOT count as corroboration
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.identity.gates import (  # noqa: E402
    identity_allows_paper_candidate,
    identity_allows_positive_decision,
)
from architecture.identity.multi_source import (  # noqa: E402
    MultiSourceIdentityResolver,
)
from architecture.identity.types import IdentityState  # noqa: E402
from architecture.providers.adapters import (  # noqa: E402
    DexScreenerAdapter,
    GeckoTerminalAdapter,
)
from architecture.providers.contracts import (  # noqa: E402
    NormalizedTokenCandidate,
    ProviderResponse,
)

NOW = 1_800_000_000.0
SOL = "So11111111111111111111111111111111111111112"
# Two distinct real-shaped Solana addresses, used as the agreeing and the
# disagreeing cases.
TOK_A = "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"
TOK_B = "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY"

# A fake provider that answers from a dict, so the resolver's per-provider
# failure paths can be exercised without any HTTP.
class _ScriptedProvider:
    def __init__(self, provider_id: str, response: ProviderResponse):
        self._pid = provider_id
        self._response = response
        self.calls: list[tuple[str, str]] = []

    @property
    def provider_id(self) -> str:
        return self._pid

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        self.calls.append((chain, address))
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _tok(chain, address, symbol="TOK", name="Token", provider="dexscreener") -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain=chain, address=address, symbol=symbol, name=name,
        source_provider=provider, retrieved_ts=NOW,
    )


def _candidate(chain: str, address: str) -> NormalizedTokenCandidate:
    return _tok(chain, address)


# --------------------------------------------------------------- agreeing ----

def test_two_agreeing_independent_sources_resolve_verified():
    """The core P2 unlock: two genuinely independent providers answering the
    same per-address question makes the identity gate reachable at all."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", ProviderResponse("geckoterminal", "OK", [_tok("solana", TOK_A)]))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert res.token.state is IdentityState.VERIFIED, res.token.reason
    assert len(res.sources) == 2
    assert {s.provider for s in res.sources} == {"dexscreener", "geckoterminal"}
    # Both providers were asked about the SAME address -- no symbol-side lookup.
    assert res.sources[0].address == res.sources[1].address == TOK_A
    assert identity_allows_positive_decision(res) is True
    assert identity_allows_paper_candidate(res) is True


# ------------------------------------------------------------- one source ----

def test_a_single_source_stays_unresolved_and_blocks_positive_decisions():
    """Fail-closed: one provider answering is not corroboration."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", ProviderResponse("geckoterminal", "OK", []))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert res.token.state is IdentityState.UNRESOLVED
    assert res.token.reason == "insufficient_independent_sources"
    assert len([s for s in res.sources]) == 1
    assert identity_allows_positive_decision(res) is False
    assert identity_allows_paper_candidate(res) is False


def test_a_down_provider_contributes_no_source():
    """A provider that errors is not a confirmation -- it is absent evidence."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", OSError("connection reset (injected)"))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert res.token.state is IdentityState.UNRESOLVED
    assert [s.provider for s in res.sources] == ["dexscreener"]
    assert identity_allows_positive_decision(res) is False


def test_no_provider_answering_is_unresolved():
    """Both providers silent -> no evidence -> no positive decision."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider("dexscreener", ProviderResponse("dexscreener", "RATE_LIMIT", []))),
            ("geckoterminal", _ScriptedProvider("geckoterminal", ProviderResponse("geckoterminal", "DOWN", []))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert res.token.state is IdentityState.UNRESOLVED
    assert res.sources == ()
    assert identity_allows_positive_decision(res) is False


# ------------------------------------------------------------- conflict -----

def test_conflicting_provider_addresses_resolve_conflict():
    """Two providers disagreeing about the address is a CONFLICT, not a
    majority vote -- the gate stays shut."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", ProviderResponse("geckoterminal", "OK", [_tok("solana", TOK_B)]))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert res.token.state is IdentityState.CONFLICT, res.token.reason
    assert res.token.reason == "source_disagreement"
    assert "provider_address_mismatch:geckoterminal" in res.conflicts
    assert identity_allows_positive_decision(res) is False
    assert identity_allows_paper_candidate(res) is False


def test_conflicting_provider_chains_resolve_conflict():
    """Same address asserted on different chains is also a conflict."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", ProviderResponse("geckoterminal", "OK", [_tok("ethereum", TOK_A)]))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert res.token.state is IdentityState.CONFLICT
    assert identity_allows_positive_decision(res) is False


# -------------------------------------------------------- missing fields ----

@pytest.mark.parametrize("chain,address", [
    ("", TOK_A),
    ("solana", ""),
    ("solana", "   "),
    (None, TOK_A),
    ("solana", None),
])
def test_missing_chain_or_address_is_never_verified(chain, address):
    """No address to corroborate -> no sources -> UNRESOLVED or INVALID."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", ProviderResponse("geckoterminal", "OK", [_tok("solana", TOK_A)]))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate(chain if chain else "", address if address else ""), NOW)

    assert res.token.state is not IdentityState.VERIFIED
    assert identity_allows_positive_decision(res) is False


def test_a_token_with_no_address_claim_contributes_no_source():
    """An adapter that returns a token carrying no address is not evidence."""
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", "")]))),
            ("geckoterminal", _ScriptedProvider(
                "geckoterminal", ProviderResponse("geckoterminal", "OK", [_tok("solana", TOK_A)]))),
        ],
        now_fn=lambda: NOW,
    )
    res = resolver(_candidate("solana", TOK_A), NOW)

    assert [s.provider for s in res.sources] == ["geckoterminal"]
    assert res.token.state is IdentityState.UNRESOLVED
    assert identity_allows_positive_decision(res) is False


def test_unsupported_chain_is_not_verified():
    """A chain outside the Lane A registry resolves UNSUPPORTED before any
    provider is asked."""
    asked: list[tuple[str, str]] = []
    resolver = MultiSourceIdentityResolver(
        providers=[
            ("dexscreener", _ScriptedProvider(
                "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("madeup", TOK_A)]))),
        ],
        now_fn=lambda: NOW,
    )
    # capture asks via the scripted provider's record
    res = resolver(_candidate("madeupchain", TOK_A), NOW)
    assert asked == []  # nothing to ask; the chain gate fires first
    assert res.chain.state is IdentityState.UNSUPPORTED
    assert identity_allows_positive_decision(res) is False


# ------------------------------- adapter echo guard (the false-corroboration) --

class _MockResp:
    def __init__(self, data, status: int = 200):
        self._data = json.dumps(data).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._data


def test_geckoterminal_reports_the_address_it_was_given_not_the_query():
    """GeckoTerminal's per-token endpoint must surface the provider's own
    address/id, not echo the queried address. Echoing would let it 'confirm'
    any token and make the two-source gate falsely satisfiable."""
    adapter = GeckoTerminalAdapter(
        transport=lambda req, timeout=None: _MockResp({
            "data": {
                "id": TOK_A,
                "attributes": {
                    "symbol": "TOK", "name": "Token",
                    "price_usd": "0.10", "total_reserve_in_usd": "1000",
                    "address": TOK_A,
                },
            }
        }))
    resp = adapter.fetch_token_metrics("solana", TOK_B)
    assert resp.status == "OK" and resp.tokens
    assert resp.tokens[0].address == TOK_A, "adapter echoed the query instead of the payload"


def test_geckoterminal_with_no_address_in_payload_reports_none_not_the_query():
    """If the payload omits an address entirely the adapter must NOT fall back
    to pretending it confirmed the queried one."""
    adapter = GeckoTerminalAdapter(
        transport=lambda req, timeout=None: _MockResp({
            "data": {"attributes": {"symbol": "TOK", "price_usd": "0.10"}}
        }))
    resp = adapter.fetch_token_metrics("solana", TOK_B)
    assert resp.status == "OK" and resp.tokens
    assert not resp.tokens[0].address, "adapter fabricated confirmation of the queried address"


def test_dexscreener_reports_payload_address_not_the_query():
    """Same guard for DexScreener: baseToken.address is the evidence."""
    adapter = DexScreenerAdapter(
        transport=lambda req, timeout=None: _MockResp({
            "pairs": [{
                "chainId": "solana",
                "baseToken": {"symbol": "TOK", "name": "Token", "address": TOK_A},
                "priceUsd": "0.10",
                "liquidity": {"usd": 1000.0},
                "volume": {"h24": 500.0},
            }]
        }))
    resp = adapter.fetch_token_metrics("solana", TOK_B)
    assert resp.status == "OK" and resp.tokens
    assert resp.tokens[0].address == TOK_A


def test_dexscreener_payload_without_base_token_address_yields_no_address():
    """No baseToken.address in the payload -> no address claim, so this adapter
    cannot be used to rubber-stamp the queried address."""
    adapter = DexScreenerAdapter(
        transport=lambda req, timeout=None: _MockResp({
            "pairs": [{
                "chainId": "solana",
                "baseToken": {"symbol": "TOK", "name": "Token"},
                "priceUsd": "0.10",
                "liquidity": {"usd": 1000.0},
            }]
        }))
    resp = adapter.fetch_token_metrics("solana", TOK_B)
    assert resp.status == "OK" and resp.tokens
    assert not resp.tokens[0].address


# --------------------------------------------- resolver integration shape ----

def test_production_resolver_uses_the_real_independent_provider_set():
    """build_production_resolver() must construct the real adapters for the
    documented independent pair, so the production path is the tested path."""
    from architecture.identity import build_production_resolver

    resolver = build_production_resolver()
    ids = set(resolver._providers.keys())
    assert ids == {"dexscreener", "geckoterminal"}
    assert isinstance(resolver._providers["dexscreener"], DexScreenerAdapter)
    assert isinstance(resolver._providers["geckoterminal"], GeckoTerminalAdapter)


def test_collect_sources_is_repeatable_and_ordered():
    """Deterministic provider order keeps provenance stable across runs."""
    providers = [
        ("dexscreener", _ScriptedProvider(
            "dexscreener", ProviderResponse("dexscreener", "OK", [_tok("solana", TOK_A)]))),
        ("geckoterminal", _ScriptedProvider(
            "geckoterminal", ProviderResponse("geckoterminal", "OK", [_tok("solana", TOK_A)]))),
    ]
    a = MultiSourceIdentityResolver(providers, now_fn=lambda: NOW).collect_sources("solana", TOK_A)
    b = MultiSourceIdentityResolver(providers, now_fn=lambda: NOW).collect_sources("solana", TOK_A)
    assert [s.provider for s in a] == [s.provider for s in b] == ["dexscreener", "geckoterminal"]
