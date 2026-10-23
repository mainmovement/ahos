#!/usr/bin/env python3
"""Identity → observation contract characterization (PAPER_ONLY fixtures).

Documents CURRENT behavior for a future canonical paper bridge. These tests do
not implement that bridge and do not claim host-runtime VERIFIED / OPERATOR_READY.

Distinctions pinned here:
  * identity matching (same token_id across resolve/upsert/register)
  * observation retrieval (as_of + token_id) vs price eligibility (caller must
    reject NULL price_usd — latest_observation itself does not)
  * pair/pool: latest_observation is token-level only (no pair validation)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.collector.engine import CollectedObservationRecord  # noqa: E402
from architecture.learning.prediction_lifecycle import register_for_observation  # noqa: E402
from discovery import observations as obs  # noqa: E402
from discovery.identity import token_id  # noqa: E402
from paper_trading.position_monitor import latest_observation  # noqa: E402


def _rec(**kw) -> CollectedObservationRecord:
    base = dict(
        obs_id="contract_obs",
        token_address="ContractTestMint1111111111111111111111111",
        chain="solana",
        symbol="CTR",
        name="Contract",
        provider_source="dexscreener",
        retrieved_ts=1_700_000_100.0,
        raw_evidence_hash="cafebabe" * 8,
        confidence_level="HIGH",
        metrics={
            "price_usd": 2.5,
            "liquidity_usd": 12_000.0,
            "volume_24h": 3_000.0,
        },
        security={},
        unknown_fields=[],
    )
    base.update(kw)
    return CollectedObservationRecord(**base)


def test_register_and_upsert_match_discovery_token_id(tmp_path):
    """Identity consistency: register / upsert / token_id agree for same chain+address."""
    disc = tmp_path / "id_obs.sqlite"
    addr = "ContractTestMint1111111111111111111111111"
    chain = "solana"
    expected = token_id(chain, addr)

    result = register_for_observation([_rec()], discovery_db=str(disc), now=1_700_000_100.0)
    assert result.errors == []
    assert result.observations_written == 1

    conn = obs.open_store(str(disc))
    try:
        upserted = obs.upsert_token(
            conn, chain, addr, first_seen_ts=1_700_000_000.0, provider="fixture"
        )
        assert upserted == expected
        row = conn.execute(
            "SELECT token_id FROM discovery_observations WHERE token_id=?", (expected,)
        ).fetchone()
        assert row is not None
        assert row["token_id"] == expected
        if result.token_ids:
            assert expected in result.token_ids
        n = conn.execute(
            "SELECT COUNT(*) c FROM tokens WHERE token_id=?", (expected,)
        ).fetchone()["c"]
        assert n == 1
    finally:
        conn.close()


def test_latest_observation_respects_token_id_and_as_of(tmp_path):
    """Observation retrieval: correct token; retrieved_ts <= as_of picks latest eligible."""
    disc = tmp_path / "asof.sqlite"
    addr = "AsOfMint2222222222222222222222222222222222"
    t0 = 1_700_000_000.0
    register_for_observation(
        [_rec(token_address=addr, retrieved_ts=t0, metrics={"price_usd": 1.0, "liquidity_usd": 9_000.0})],
        discovery_db=str(disc),
        now=t0,
    )
    tid = token_id("solana", addr)
    conn = obs.open_store(str(disc))
    try:
        raw = "asof_raw_sha256_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        conn.execute(
            "INSERT OR IGNORE INTO raw_payloads(payload_sha256,provider,endpoint,retrieved_ts,payload_json)"
            " VALUES (?,?,?,?,?)",
            (raw, "dexscreener", "t", t0 + 100.0, "{}"),
        )
        obs.record_observation(
            conn,
            tid,
            "dexscreener",
            t0 + 100.0,
            raw,
            metrics={"price_usd": 3.0, "liquidity_usd": 10_000.0},
        )
        conn.commit()

        older = latest_observation(conn, tid, as_of=t0 + 50.0)
        assert older is not None
        assert older["price_usd"] == 1.0
        assert older["retrieved_ts"] == t0

        newer = latest_observation(conn, tid, as_of=t0 + 200.0)
        assert newer is not None
        assert newer["price_usd"] == 3.0
        assert newer["retrieved_ts"] == t0 + 100.0

        other = token_id("solana", "OtherMint3333333333333333333333333333333333")
        assert latest_observation(conn, other, as_of=t0 + 200.0) is None
    finally:
        conn.close()


def test_latest_observation_may_return_null_price_usd(tmp_path):
    """Null price: API returns the row; it does NOT reject NULL price_usd itself.

    Price eligibility for paper entry is a caller responsibility, not this query.
    """
    disc = tmp_path / "null_price.sqlite"
    addr = "NullPriceMint4444444444444444444444444444444"
    t0 = 1_700_000_000.0
    tid = token_id("solana", addr)
    conn = obs.open_store(str(disc))
    try:
        obs.upsert_token(conn, "solana", addr, t0, "fixture")
        raw = "null_price_raw_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        conn.execute(
            "INSERT OR IGNORE INTO raw_payloads(payload_sha256,provider,endpoint,retrieved_ts,payload_json)"
            " VALUES (?,?,?,?,?)",
            (raw, "dexscreener", "t", t0, "{}"),
        )
        obs.record_observation(
            conn,
            tid,
            "dexscreener",
            t0,
            raw,
            metrics={"price_usd": None, "liquidity_usd": 5_000.0},
        )
        conn.commit()
        got = latest_observation(conn, tid, as_of=t0 + 1.0)
        assert got is not None
        assert got["price_usd"] is None
        assert got["liquidity_usd"] == 5_000.0
    finally:
        conn.close()


def test_evm_address_case_variants_share_token_id():
    """EVM normalization: case variants map to the same token_id under registry rules."""
    a = "0xAbCdEf0000000000000000000000000000000099"
    b = "0xabcdef0000000000000000000000000000000099"
    assert token_id("ethereum", a) == token_id("ethereum", b)
    assert token_id("eth", a) == token_id("ethereum", b)
    # upsert uses the same helper — both cases collide on one token_id
    # (isolated in-memory path via open_store would also dedupe; pure function pin here)


def test_latest_observation_is_token_level_not_pair_validated(tmp_path):
    """Pair limitation: lookup keys only on token_id; pair_id is not filtered or validated.

    Two observations for the same token with different pair_id values still compete
    solely by retrieved_ts. This documents the architectural gap for pool-aware entry.
    """
    disc = tmp_path / "pair_gap.sqlite"
    addr = "PairGapMint5555555555555555555555555555555"
    t0 = 1_700_000_000.0
    tid = token_id("solana", addr)
    conn = obs.open_store(str(disc))
    try:
        obs.upsert_token(conn, "solana", addr, t0, "fixture")
        p1 = obs.upsert_pair(
            conn, "solana", "raydium", "PairAAAA555555555555555555555555555555555",
            tid, t0, "fixture", "raw1",
        )
        p2 = obs.upsert_pair(
            conn, "solana", "orca", "PairBBBB555555555555555555555555555555555",
            tid, t0, "fixture", "raw2",
        )
        assert p1 != p2
        for i, (pair, price, ts) in enumerate(
            ((p1, 1.0, t0), (p2, 9.0, t0 + 10.0))
        ):
            raw = f"pair_raw_{i}_cccccccccccccccccccccccccccccccc"
            conn.execute(
                "INSERT OR IGNORE INTO raw_payloads(payload_sha256,provider,endpoint,retrieved_ts,payload_json)"
                " VALUES (?,?,?,?,?)",
                (raw, "dexscreener", "t", ts, "{}"),
            )
            obs.record_observation(
                conn, tid, "dexscreener", ts, raw, pair=pair,
                metrics={"price_usd": price, "liquidity_usd": 8_000.0},
            )
        conn.commit()
        got = latest_observation(conn, tid, as_of=t0 + 100.0)
        assert got is not None
        # Wins by newer retrieved_ts only — no pair_id in SELECT / WHERE
        assert got["price_usd"] == 9.0
        assert "pair_id" not in got
    finally:
        conn.close()
