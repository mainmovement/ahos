#!/usr/bin/env python3
"""Multi-provider identity resolver (Lane B).

`architecture.decision.authority.identity_from_candidate` is deliberately
fail-closed: it builds exactly ONE `IdentitySource` from the merged candidate,
so `resolve_identity`'s independence gate (`_independent_enough`: >=2 distinct
provider names) can never be satisfied and every token resolves UNRESOLVED.
That is the correct default for a single-source world.

The system is not single-source. `MARKET_PROVIDER_ORDER` in
`architecture/providers/collect.py` already fans out across dexscreener,
geckoterminal, coingecko and coinmarketcap, and each adapter answers a
per-address question (`fetch_token_metrics`). This resolver is the bridge: it
asks every independent market provider the SAME question about the SAME
address, emits one `IdentitySource` per provider that answered, and hands them
to the *same* `resolve_identity` with the *same* policy version. It adds no
identity rule of its own. The independence gate, the conflict detection and
the staleness policy all stay exactly where they are, in `resolution.py`.

Why a live per-address fan-out rather than the observation store: the store's
two providers observe DISJOINT token populations (verified 2026-10-08 against
data/e01_discovery.sqlite: 67 tokens with DexScreener evidence, 26,563 with
GeckoTerminal evidence, intersection 0). The discovery fan-out queries a
different endpoint per provider, so two providers rarely land on the same row.
Corroboration that a token exists at an address requires asking both providers
about that address.

Fail-closed by construction. A provider contributes a source ONLY when it
returned status OK with a token; every other outcome contributes nothing:

  * provider error / timeout / rate limit      -> no source
  * provider returned zero tokens ("not indexed is a fact, not a failure")
                                                -> no source
  * provider returned a DIFFERENT chain/address -> the source is emitted with
    the provider's own claim and `resolve_identity` classifies it CONFLICT
                                                -> never PASS
  * fewer than two independent providers answered -> UNRESOLVED -> never PASS
  * the two providers disagree on the evidence  -> CONFLICT      -> never PASS

Nothing in this module can upgrade a token the evidence does not support. It
cannot emit WATCH/PAPER_CANDIDATE and it cannot score; it only supplies
evidence to the existing arbiter.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Sequence

from architecture.identity.resolution import resolve_identity
from architecture.identity.types import IdentityResolution, IdentitySource

# The providers that answer a per-address market question. Order is irrelevant
# to the verdict (resolve_identity arbitrates) but is kept stable so the
# provenance tuple is deterministic. These are genuinely independent upstreams
# -- separate APIs, separate rate budgets -- not one provider through two
# wrappers.
DEFAULT_MARKET_PROVIDER_IDS: tuple[str, ...] = ("dexscreener", "geckoterminal")


def _default_providers(transport: Callable | None) -> dict[str, object]:
    """Construct the default independent market providers.

    Imported lazily so `architecture.identity` does not gain a hard import-time
    dependency on the provider layer; importing this module must not require
    network configuration.
    """
    from architecture.providers.adapters import (
        DexScreenerAdapter,
        GeckoTerminalAdapter,
    )

    kwargs = {"transport": transport} if transport is not None else {}
    return {
        "dexscreener": DexScreenerAdapter(**kwargs),
        "geckoterminal": GeckoTerminalAdapter(**kwargs),
    }


@dataclass(frozen=True)
class _ProviderAnswer:
    """One provider's answer to `what do you know about this address?`."""

    provider_id: str
    chain: str | None
    address: str | None
    retrieved_ts: float | None
    answered: bool

    @staticmethod
    def empty(provider_id: str) -> "_ProviderAnswer":
        return _ProviderAnswer(provider_id, None, None, None, answered=False)

    def to_source(self) -> IdentitySource | None:
        """An answer is only identity evidence when it actually named an
        address. A provider that returned no token, or returned one without an
        address, contributes nothing -- it is not a confirmation."""
        if not self.answered or not self.address or not str(self.address).strip():
            return None
        return IdentitySource(
            provider=self.provider_id,
            chain=self.chain,
            address=str(self.address).strip(),
            retrieved_ts=self.retrieved_ts,
            source_ts=None,
            kind="market",
        )


class MultiSourceIdentityResolver:
    """Resolves identity from N independent market providers.

    Callable with the `(candidate, now)` signature the pipeline expects
    (`architecture/pipeline/orchestrator.py`), so it drops into the existing
    `identity_resolver` injection point without touching the authority.
    """

    def __init__(
        self,
        providers: Sequence[tuple[str, object]] | None = None,
        *,
        transport: Callable | None = None,
        provider_ids: Sequence[str] = DEFAULT_MARKET_PROVIDER_IDS,
        now_fn: Callable[[], float] = time.time,
    ) -> None:
        self._now = now_fn
        if providers is not None:
            self._providers: dict[str, object] = {
                str(pid): provider for pid, provider in providers
            }
        else:
            built = _default_providers(transport)
            self._providers = {pid: built[pid] for pid in provider_ids if pid in built}

    # -- collection ---------------------------------------------------------

    def _ask(self, provider_id: str, provider: object, chain: str, address: str) -> _ProviderAnswer:
        """Ask one provider about (chain, address). Any failure is 'no answer'."""
        fetch = getattr(provider, "fetch_token_metrics", None)
        if fetch is None:
            return _ProviderAnswer.empty(provider_id)
        try:
            resp = fetch(chain, address)
        except Exception:  # noqa: BLE001 -- a down provider is not a confirmation
            return _ProviderAnswer.empty(provider_id)
        status = getattr(resp, "status", None)
        tokens = getattr(resp, "tokens", None) or []
        if status != "OK" or not tokens:
            return _ProviderAnswer.empty(provider_id)
        tok = tokens[0]
        return _ProviderAnswer(
            provider_id=provider_id,
            chain=getattr(tok, "chain", None),
            address=getattr(tok, "address", None),
            retrieved_ts=getattr(tok, "retrieved_ts", None),
            answered=True,
        )

    def collect_sources(
        self, chain: str | None, address: str | None, now: float | None = None
    ) -> tuple[IdentitySource, ...]:
        """One IdentitySource per provider that answered, in provider order."""
        if not chain or not address or not str(address).strip():
            return ()
        chain_s, address_s = str(chain).strip(), str(address).strip()
        sources: list[IdentitySource] = []
        for provider_id, provider in self._providers.items():
            src = self._ask(provider_id, provider, chain_s, address_s).to_source()
            if src is not None:
                sources.append(src)
        return tuple(sources)

    # -- resolver interface --------------------------------------------------

    def __call__(
        self, candidate: object, now: float | None = None
    ) -> IdentityResolution:
        ts = self._now() if now is None else now
        chain = getattr(candidate, "chain", None)
        address = getattr(candidate, "address", None)
        sources = self.collect_sources(chain, address, now=ts)
        return resolve_identity(
            chain=chain,
            address=address,
            symbol=getattr(candidate, "symbol", None),
            name=getattr(candidate, "name", None),
            sources=sources,
            pool_dex=getattr(candidate, "dex_id", None),
            pool_address=getattr(candidate, "pair_address", None),
            # Mirror identity_from_candidate: a pool is only claimed when the
            # candidate actually carries one, so pool_base_token can bind.
            pool_base_token=address if getattr(candidate, "pair_address", None) else None,
            now=ts,
        )


def build_production_resolver(transport: Callable | None = None) -> MultiSourceIdentityResolver:
    """The resolver the daemon wires into the opportunity pipeline.

    Uses the real adapters and the real (default) independent provider set.
    Keep this construction in ONE place so the production provider set is never
    silently different from the tested one.
    """
    return MultiSourceIdentityResolver(transport=transport)
