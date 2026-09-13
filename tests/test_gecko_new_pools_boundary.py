"""W4 Slice 3 — Gecko new_pools token/pool boundary."""
from __future__ import annotations

import json
from pathlib import Path

from architecture.identity.fusion import is_canonical_verified
from architecture.providers.adapters import GeckoTerminalAdapter
from architecture.providers.contracts import NormalizedTokenCandidate

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = (ROOT / "architecture" / "providers" / "adapters.py").read_text(encoding="utf-8")

SOL = "So11111111111111111111111111111111111111112"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDC_LOWER = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

GECKO_FETCH_START = ADAPTER_SRC.index("class GeckoTerminalAdapter")
GECKO_FETCH_END = ADAPTER_SRC.index("def fetch_token_metrics", GECKO_FETCH_START)
GECKO_NEW_POOLS_SRC = ADAPTER_SRC[GECKO_FETCH_START:GECKO_FETCH_END]


def _raw_transport(payload: dict | list | str, status_code: int = 200):
    raw = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode("utf-8")

    class Resp:
        def __init__(self):
            self.status = status_code

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return raw

    return lambda req, timeout=None: Resp()


def _pool(
    *,
    pool_id: str = f"solana_{POOL}",
    pool_address: str | None = POOL,
    name: str = "SOL / USDC",
    base_id: str | None = f"solana_{SOL}",
    quote_id: str | None = f"solana_{SOL_USDC}",
    include_relationships: bool = True,
    extra_attrs: dict | None = None,
    relationships: dict | None = None,
    item_type: str = "pool",
) -> dict:
    attrs: dict = {"name": name}
    if pool_address is not None:
        attrs["address"] = pool_address
    if extra_attrs:
        attrs.update(extra_attrs)
    item: dict = {"id": pool_id, "type": item_type, "attributes": attrs}
    if relationships is not None:
        item["relationships"] = relationships
    elif include_relationships:
        rels: dict = {}
        if base_id is not None:
            rels["base_token"] = {"data": {"id": base_id, "type": "token"}}
        if quote_id is not None:
            rels["quote_token"] = {"data": {"id": quote_id, "type": "token"}}
        item["relationships"] = rels
    return item


def _fetch(payload, chain: str = "solana", limit: int = 20):
    adapter = GeckoTerminalAdapter(transport=_raw_transport(payload))
    return adapter.fetch_candidate_tokens(chain, limit=limit)


def test_slice_does_not_join_on_symbol_or_pool_name():
    assert 'split("/")' not in GECKO_NEW_POOLS_SRC
    assert "split('/')" not in GECKO_NEW_POOLS_SRC
    assert "resolve_identity" not in GECKO_NEW_POOLS_SRC
    assert "discovery." not in GECKO_NEW_POOLS_SRC
    assert "token_id(" not in GECKO_NEW_POOLS_SRC


def test_attributes_address_becomes_pair_address():
    resp = _fetch({"data": [_pool()]})
    assert resp.status == "OK"
    assert len(resp.tokens) == 1
    tok = resp.tokens[0]
    assert tok.pair_address == POOL
    assert tok.address == SOL
    assert tok.address != tok.pair_address


def test_base_token_relationship_supplies_candidate_address():
    resp = _fetch({"data": [_pool(base_id=f"solana_{SOL_USDC}", quote_id=f"solana_{SOL}")]})
    assert resp.tokens[0].address == SOL_USDC
    assert resp.tokens[0].pair_address == POOL


def test_quote_token_does_not_replace_base_token():
    resp = _fetch({"data": [_pool()]})
    tok = resp.tokens[0]
    assert tok.address == SOL
    assert tok.address != SOL_USDC
    assert tok.pair_address == POOL


def test_data_id_remains_provider_resource_id():
    provider_id = f"solana_{POOL}"
    resp = _fetch({"data": [_pool(pool_id=provider_id)]})
    tok = resp.tokens[0]
    assert tok.address != provider_id
    assert tok.pair_address != provider_id
    assert tok.pair_address == POOL
    assert tok.address == SOL


def test_pool_address_never_appears_as_candidate_token_address():
    resp = _fetch({"data": [_pool()]})
    assert resp.tokens[0].address != POOL
    assert resp.tokens[0].address == SOL


def test_missing_base_token_never_falls_back_to_pool_address():
    cases = [
        _pool(include_relationships=False),
        _pool(relationships={}),
        _pool(relationships={"base_token": {}}),
        _pool(relationships={"base_token": {"data": {}}}),
        _pool(relationships={"base_token": {"data": {"type": "token"}}}),
        _pool(base_id=None, quote_id=f"solana_{SOL_USDC}"),
        _pool(relationships={"quote_token": {"data": {"id": f"solana_{SOL_USDC}"}}}),
    ]
    for item in cases:
        resp = _fetch({"data": [item]})
        assert resp.status == "OK"
        assert resp.tokens == []
        assert all(t.address != POOL for t in resp.tokens)


def test_symbol_is_not_used_as_identity():
    item = _pool(name="PEPE / SOL")
    resp = _fetch({"data": [item]})
    tok = resp.tokens[0]
    assert tok.address == SOL
    assert tok.address != "PEPE"
    assert tok.address != "PEPE / SOL"
    assert tok.symbol != SOL
    payload = {
        "data": [_pool()],
        "included": [{
            "id": f"solana_{SOL}",
            "type": "token",
            "attributes": {"symbol": "WSOL", "name": "Wrapped SOL"},
        }],
    }
    labeled = _fetch(payload)
    assert labeled.tokens[0].address == SOL
    assert labeled.tokens[0].symbol == "WSOL"
    assert labeled.tokens[0].address != "WSOL"


def test_malformed_payload_fails_closed():
    payloads = [
        {"data": [_pool(base_id="not-a-resource-id")]},
        {"data": [_pool(base_id="solana_")]},
        {"data": [_pool(base_id="solana_!!!")]},
        {"data": [_pool(relationships="bad")]},
        {"data": [_pool(relationships={"base_token": "x"})]},
        {"data": [{"id": f"solana_{POOL}", "attributes": None, "relationships": {}}]},
        {"data": [{"not": "a pool"}]},
        {"data": [None, "x", 1]},
        {"data": {}},
        {"included": []},
        None,
    ]
    for payload in payloads:
        if payload is None:
            adapter = GeckoTerminalAdapter(transport=_raw_transport("null"))
            resp = adapter.fetch_candidate_tokens("solana")
        else:
            resp = _fetch(payload)
        assert resp.status in {"OK", "ERROR"}
        assert all(t.address != POOL for t in resp.tokens)
        for tok in resp.tokens:
            assert tok.address
            assert tok.address != tok.symbol


def test_valid_gecko_payload_still_emits_base_token():
    resp = _fetch({
        "data": [_pool(extra_attrs={
            "reserve_in_usd": "123.4",
            "volume_usd": {"h24": "10"},
            "pool_created_at": "2026-09-09T14:53:02Z",
        })]
    })
    assert resp.status == "OK"
    tok = resp.tokens[0]
    assert tok.address == SOL
    assert tok.pair_address == POOL
    assert tok.metrics.liquidity_usd == 123.4
    assert tok.metrics.volume_24h == 10.0
    assert tok.source_provider == "geckoterminal"
    assert is_canonical_verified(tok) is False


def test_solana_base_token_preserves_exact_case():
    resp = _fetch({"data": [_pool()]})
    assert resp.tokens[0].address == SOL
    assert resp.tokens[0].address != SOL.lower()
    folded = _fetch({"data": [_pool(base_id=f"solana_{SOL.lower()}")]})
    assert folded.tokens == [] or folded.tokens[0].address != SOL


def test_adversarial_token_like_pool_still_selects_base_token():
    item = _pool(
        pool_id="POOL-LIKE-VALUE",
        pool_address="TOKEN-LIKE-VALUE",
        base_id=f"solana_{SOL}",
        quote_id=f"solana_{SOL_USDC}",
    )
    resp = _fetch({"data": [item]})
    assert len(resp.tokens) == 1
    tok = resp.tokens[0]
    assert tok.address == SOL
    assert tok.address != "TOKEN-LIKE-VALUE"
    assert tok.address != "POOL-LIKE-VALUE"
    assert tok.pair_address != "POOL-LIKE-VALUE"
    assert tok.pair_address != tok.address


def test_adversarial_valid_pool_without_base_is_not_emitted():
    item = _pool(include_relationships=False, pool_address=SOL)
    resp = _fetch({"data": [item]})
    assert resp.tokens == []


def test_adversarial_provider_id_resembling_token_stays_provider_identity():
    item = _pool(pool_id=f"solana_{SOL}")
    resp = _fetch({"data": [item]})
    tok = resp.tokens[0]
    assert tok.address == SOL
    assert tok.pair_address == POOL
    assert tok.pair_address != f"solana_{SOL}"
    assert tok.address != f"solana_{SOL}"


def test_unsupported_chain_fails_closed():
    resp = _fetch({"data": [_pool(base_id=f"aptos_{SOL}", quote_id=None)]}, chain="aptos")
    assert resp.status == "OK"
    assert resp.tokens == []
    sol_req = _fetch({"data": [_pool(base_id=f"aptos_{SOL}")]}, chain="solana")
    assert sol_req.tokens == []


def test_missing_attributes_or_address_does_not_invent_token():
    no_attrs = {
        "id": f"solana_{POOL}",
        "type": "pool",
        "relationships": {"base_token": {"data": {"id": f"solana_{SOL}", "type": "token"}}},
    }
    no_pool_addr = _pool(pool_address=None)
    resp = _fetch({"data": [no_attrs, no_pool_addr]})
    assert resp.status == "OK"
    assert [t.address for t in resp.tokens] == [SOL, SOL]
    assert all(t.address != POOL for t in resp.tokens)
    assert all(t.pair_address != f"solana_{POOL}" for t in resp.tokens)


def test_evm_base_token_uses_existing_validator_semantics():
    item = {
        "id": f"eth_{POOL}",
        "type": "pool",
        "attributes": {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "name": "USDC / WETH"},
        "relationships": {
            "base_token": {"data": {"id": f"eth_{USDC}", "type": "token"}},
            "quote_token": {"data": {"id": "eth_0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "type": "token"}},
        },
    }
    resp = _fetch({"data": [item]}, chain="eth")
    assert len(resp.tokens) == 1
    assert resp.tokens[0].chain == "eth"
    assert resp.tokens[0].address == USDC_LOWER
    assert resp.tokens[0].address != resp.tokens[0].pair_address


def test_adapter_does_not_claim_verified_identity():
    resp = _fetch({"data": [_pool()]})
    tok = resp.tokens[0]
    assert is_canonical_verified(tok) is False
    assert is_canonical_verified(resp) is False
    assert tok.address == SOL


def test_operational_dedupe_key_now_refers_to_token_not_pool():
    """Collector/router still fold (chain, address.lower()) operationally.

    This slice does not redesign that fold. After the fix the folded key
    is the token mint, not the pool address.
    """
    other_pool = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    resp = _fetch({
        "data": [
            _pool(),
            _pool(pool_id=f"solana_{other_pool}", pool_address=other_pool),
        ]
    })
    assert [t.address for t in resp.tokens] == [SOL, SOL]
    assert {t.pair_address for t in resp.tokens} == {POOL, other_pool}
    seen = set()
    unique: list[NormalizedTokenCandidate] = []
    for cand in resp.tokens:
        key = (cand.chain, cand.address.lower())
        if key not in seen:
            seen.add(key)
            unique.append(cand)
    assert [(c.chain, c.address.lower()) for c in unique] == [("solana", SOL.lower())]
    assert POOL.lower() not in {k[1] for k in seen}
    assert SOL != SOL.lower()


def test_limit_still_applies_to_raw_items_not_skipped_inventions():
    items = [_pool(include_relationships=False) for _ in range(3)]
    items.append(_pool())
    resp = _fetch({"data": items}, limit=4)
    assert len(resp.tokens) == 1
    assert resp.tokens[0].address == SOL
