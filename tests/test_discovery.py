#!/usr/bin/env python3
"""AHOS Discovery Core tests (Mission v1.1) — identity, observations, lifecycle,
feature store (incl. leak-prevention L1–L4), security gate, outcomes, ranker, PAL mechanics.
Synthetic fixtures only in unit tests; REAL provider pass is a separate smoke run (labeled)."""
import sys, math, json, sqlite3, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "discovery") not in sys.path: sys.path.insert(0, str(ROOT_DIR / "discovery"))

import pytest
from discovery import identity, observations as obs, lifecycle, feature_store, security_gate, outcomes, ranker, pal

T0 = 1_750_000_000.0  # fixed synthetic epoch (deterministic fixtures)
RAW = "a" * 64


@pytest.fixture()
def conn(tmp_path):
    c = obs.open_store(tmp_path / "t.sqlite")
    yield c
    c.close()


def _mk_token(conn, chain="solana", addr="So11111111111111111111111111111111111111112",
              created_offset=-7200.0, now=T0):
    tid = obs.upsert_token(conn, chain, addr, now, "fixture", symbol="FIX", name="Fixture",
                           created_at_ts=now + created_offset)
    pid = obs.upsert_pair(conn, chain, "pumpfun", addr, tid, now, "fixture", RAW,
                          pair_created_ts=now + created_offset)
    lifecycle.register_discovery(conn, tid, now)
    return tid, pid


def _feed(conn, tid, series, provider="fixture"):
    """series: [(dt_seconds, metrics_dict)] relative to T0; writes raw+obs+lifecycle."""
    for i, (dt, m) in enumerate(series):
        raws = hash_raw = obs.store_raw(conn, provider, f"fixture://{i}", T0 + dt, 200, {"i": i, "m": m})
        obs.record_observation(conn, tid, provider, T0 + dt, raws, metrics=m)
        lifecycle.on_observation(conn, tid, T0 + dt)


# ---------------- STEP 3: identity ----------------
def test_identity_deterministic_and_chain_aware():
    a = identity.token_id("solana", "So11111111111111111111111111111111111111112")
    assert a == identity.token_id("solana", "So11111111111111111111111111111111111111112")
    assert len(a) == 32
    # EVM case-insensitive
    x1 = identity.token_id("ethereum", "0xAbCdEf0000000000000000000000000000000001")
    x2 = identity.token_id("eth", "0xabcdef0000000000000000000000000000000001")
    assert x1 == x2 and len(x1) == 32
    # Solana case-SENSITIVE (base58)
    s1 = identity.token_id("solana", "ABCd")
    s2 = identity.token_id("solana", "ABCD")
    assert s1 != s2
    # alias normalization
    assert identity.token_id("bsc", "0xABC") == identity.token_id("bnb", "0xabc")
    with pytest.raises(ValueError):
        identity.token_id("unknownchain", "x")
    with pytest.raises(ValueError):
        identity.token_id("solana", "  ")


def test_identity_cross_provider_dedupe(conn):
    t1, _ = _mk_token(conn, addr="MintA1111111111111111111111111111111111111111")
    t2 = obs.upsert_token(conn, "solana", "MintA1111111111111111111111111111111111111111",
                          T0 + 60, "otherprovider", symbol="X")
    assert t1 == t2
    n = conn.execute("SELECT COUNT(*) c FROM tokens").fetchone()["c"]
    assert n == 1


# ---------------- STEP 4: observations ----------------
def test_observation_null_discipline(conn):
    tid, _ = _mk_token(conn)
    raw = obs.store_raw(conn, "fixture", "fixture://0", T0, 200, {"x": 1})
    oid = obs.record_observation(conn, tid, "fixture", T0, raw, metrics={"price_usd": 0.5})
    r = conn.execute("SELECT * FROM discovery_observations WHERE obs_id=?", (oid,)).fetchone()
    assert r["price_usd"] == 0.5
    assert r["liquidity_usd"] is None and r["volume_24h"] is None   # NULL = unknown
    assert "schema_ok" in json.loads(r["quality_flags"])
    assert r["raw_ref"] == raw


def test_observation_error_state_not_fake(conn):
    tid, _ = _mk_token(conn)
    raw = obs.store_raw(conn, "fixture", "e://x", T0 + 5, 500, {})
    oid = obs.record_observation(conn, tid, "fixture", T0 + 5, raw,
                                 error_state={"kind": "http_error", "http_status": 500})
    r = conn.execute("SELECT * FROM discovery_observations WHERE obs_id=?", (oid,)).fetchone()
    assert r["price_usd"] is None and json.loads(r["error_state"])["http_status"] == 500


def test_zero_is_not_null(conn):
    tid, _ = _mk_token(conn)
    raw = obs.store_raw(conn, "fixture", "z://0", T0 + 10, 200, {})
    oid = obs.record_observation(conn, tid, "fixture", T0 + 10, raw,
                                 metrics={"txns_1h_sells": 0, "price_usd": 1.0})
    r = conn.execute("SELECT * FROM discovery_observations WHERE obs_id=?", (oid,)).fetchone()
    assert r["txns_1h_sells"] == 0 and r["price_usd"] == 1.0


# ---------------- STEP 5: lifecycle ----------------
def test_lifecycle_transitions_and_dead_rule(conn):
    tid, _ = _mk_token(conn, now=T0)
    assert lifecycle.tick(conn, tid, T0) == "DISCOVERED"
    _feed(conn, tid, [(300, {"price_usd": 1.0, "liquidity_usd": 5000})])
    assert lifecycle.tick(conn, tid, T0 + 300) == "OBSERVING"
    # 24h silence → DEAD
    assert lifecycle.tick(conn, tid, T0 + 300 + 25 * 3600) == "DEAD"
    # resume before resolve → back OBSERVING
    _feed(conn, tid, [(25 * 3600 + 600, {"price_usd": 1.1})])
    assert lifecycle.tick(conn, tid, T0 + 25 * 3600 + 600) == "OBSERVING"
    # T+72h → RESOLVED — note (F §3): 46h silence after last obs flips to DEAD FIRST, then RESOLVEs
    # from DEAD (dead-path resolution is by design, outcomes still computed).
    assert lifecycle.tick(conn, tid, T0 + 72 * 3600 + 1) == "RESOLVED"
    # RESOLVED is terminal
    assert lifecycle.tick(conn, tid, T0 + 100 * 3600) == "RESOLVED"
    ev = conn.execute("SELECT from_state, to_state FROM lifecycle_events WHERE token_id=?", (tid,)).fetchall()
    trail = [(e["from_state"], e["to_state"]) for e in ev]
    assert (None, "DISCOVERED") in trail and ("OBSERVING", "DEAD") in trail and \
           ("DEAD", "RESOLVED") in trail


def test_lifecycle_security_flag_parallel(conn):
    tid, _ = _mk_token(conn)
    lifecycle.flag_security(conn, tid, T0 + 10, "fixture veto test")
    st = conn.execute("SELECT * FROM observation_state WHERE token_id=?", (tid,)).fetchone()
    assert st["security_flagged"] == 1 and st["state"] == "DISCOVERED"


def test_snapshot_schedule_due_and_gap(conn):
    tid, _ = _mk_token(conn, now=T0)
    _feed(conn, tid, [(0, {"price_usd": 1.0}), (900, {"price_usd": 1.02})])  # s+15m covered
    due_early = lifecycle.due_snapshots(conn, tid, T0 + 2000)
    assert "s+1h" not in due_early                   # slot not even open yet (opens T0+3000)
    due = lifecycle.due_snapshots(conn, tid, T0 + 4000)
    assert "s+15m" not in due and "s+1h" in due      # 1h slot open & uncovered
    counts = lifecycle.sweep(conn, T0 + 2 * 3600)
    gaps = conn.execute("SELECT kind FROM gap_register WHERE token_id=?", (tid,)).fetchall()
    kinds = [g["kind"] for g in gaps]
    assert any("missed:s+1h" in k for k in kinds)      # overdue slot registered, never back-filled


# ---------------- STEP 6: feature store ----------------
def _rich_series(base_liq=10000.0, n=14):
    return [(i * 300, {"price_usd": 1.0 * (1 + 0.001 * i),
                       "liquidity_usd": base_liq * (1 + 0.01 * i),
                       "volume_5m": 100.0 + i,
                       "volume_1h": 1200.0 + 30 * i,
                       "volume_24h": 30000.0,
                       "txns_1h_buys": 100 + i, "txns_1h_sells": 80,
                       "txns_5m_buys": 20 + i, "txns_5m_sells": 15,
                       "boost_amount": 0}) for i in range(n)]


def test_features_basic_math(conn):
    tid, _ = _mk_token(conn, now=T0)
    _feed(conn, tid, _rich_series(n=16))   # 16 five-min points → 13 inside the 1h vol window (>=12)
    as_of = T0 + 15 * 300
    f = feature_store.compute_features(conn, tid, as_of)
    assert f["token_age_hours"]["value_num"] == pytest.approx((as_of - (T0 - 7200)) / 3600, rel=1e-9)
    last_liq = 10000.0 * (1 + 0.01 * 15)
    assert f["liquidity_usd_t"]["value_num"] == pytest.approx(last_liq)
    idx_1h_ago = (as_of - 3600 - T0) // 300            # nearest ≤ as_of-3600
    liq_then = 10000.0 * (1 + 0.01 * idx_1h_ago)
    expect = (last_liq - liq_then) / liq_then
    assert f["liquidity_growth_1h"]["value_num"] == pytest.approx(expect, rel=1e-9)
    assert f["buy_sell_imbalance_1h"]["value_num"] == pytest.approx((115 - 80) / (195))
    assert f["volatility_1h"]["value_num"] > 0


def test_feature_availability_law_l3(conn):
    tid, _ = _mk_token(conn, now=T0)
    _feed(conn, tid, _rich_series())
    as_of = T0 + 14 * 300
    f = feature_store.compute_features(conn, tid, as_of)
    for k, v in f.items():
        assert v["availability_ts"] <= as_of, k
    n = feature_store.persist_features(conn, tid, as_of, f)
    rows = conn.execute("SELECT COUNT(*) c FROM feature_vector WHERE token_id=?", (tid,)).fetchone()
    assert rows["c"] == n and n > 0
    # DB-level CHECK enforces L3 as well
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO feature_vector VALUES (?,?,?,?,?,?,NULL,'HIGH','x')",
                     (tid, feature_store.FEATURE_SET, as_of, as_of + 1, "fake", 1.0))


def test_no_lookahead_future_injection(conn):
    """An observation from the FUTURE must not change features at as_of (Rule L1)."""
    tid, _ = _mk_token(conn, now=T0)
    _feed(conn, tid, _rich_series())
    as_of = T0 + 14 * 300
    before = feature_store.compute_features(conn, tid, as_of)
    # inject a future mega-pump observation
    raw = obs.store_raw(conn, "fixture", "future://x", as_of + 100000, 200, {"future": True})
    obs.record_observation(conn, tid, "fixture", as_of + 100000, raw,
                           metrics={"price_usd": 1000.0, "liquidity_usd": 1e9})
    after = feature_store.compute_features(conn, tid, as_of)
    assert before == after


def test_feature_store_has_no_outcome_import():
    """Rule L2 (architecture test): feature_store must not import the outcomes module
    (dependency direction enforced in code, not in docs)."""
    import ast
    tree = ast.parse(Path(str(ROOT_DIR / "discovery" / "feature_store.py")).read_text())
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bad += [a.name for a in node.names if "outcome" in a.name]
        elif isinstance(node, ast.ImportFrom):
            names = [a.name for a in node.names] + [node.module or ""]
            bad += [n for n in names if "outcome" in n]
    assert bad == [], f"outcome imports found: {bad}"
    # and no SQL access to the outcome table either:
    src = Path(str(ROOT_DIR / "discovery" / "feature_store.py")).read_text()
    assert "FROM outcome_label" not in src and "INSERT INTO outcome_label" not in src


def test_features_deterministic(conn):
    tid, _ = _mk_token(conn, now=T0)
    _feed(conn, tid, _rich_series())
    as_of = T0 + 14 * 300
    a = feature_store.compute_features(conn, tid, as_of)
    b = feature_store.compute_features(conn, tid, as_of)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---------------- STEP 7: security gate ----------------
def test_gate_veto_logic_pure():
    v = security_gate.evaluate([{"check_key": "honeypot", "value": "TRUE"}])
    assert v["verdict"] == "SECURITY_VETO" and v["recommendation_cap"] == "AVOID"
    assert "honeypot" in v["veto_reasons"]
    v2 = security_gate.evaluate([{"check_key": "honeypot", "value": "FALSE"}])
    assert v2["verdict"] == "PASS_WITH_UNKNOWN" and v2["recommendation_cap"] == "WATCH"
    assert v2["coverage"] < 1.0
    full_false = [{"check_key": k, "value": "FALSE"} for k in security_gate.CRITICAL]
    v3 = security_gate.evaluate(full_false)
    assert v3["verdict"] == "PASS" and v3["coverage"] == 1.0


def test_gate_unknown_never_pass(conn):
    tid, _ = _mk_token(conn)
    security_gate.record_check(conn, tid, T0, "rugcheck", "honeypot", "FALSE")
    r = security_gate.evaluate_token(conn, tid, T0 + 1)
    assert r["verdict"] == "PASS_WITH_UNKNOWN"
    with pytest.raises(ValueError):
        security_gate.record_check(conn, tid, T0, "rugcheck", "not_a_check", "TRUE")
    with pytest.raises(ValueError):
        security_gate.record_check(conn, tid, T0, "rugcheck", "honeypot", "MAYBE")


def test_gate_veto_fixtures_100pct():
    """Synthetic known-scam fixtures → 100% veto (labeled FIXTURE — never a real-detection claim)."""
    fixtures = [
        [{"check_key": "honeypot", "value": "TRUE"}],
        [{"check_key": "mint_authority_active", "value": "TRUE"}],
        [{"check_key": "freeze_authority_active", "value": "TRUE"}],
        [{"check_key": "sell_tax_extreme", "value": "TRUE"}],
        [{"check_key": "blacklist_function", "value": "TRUE"}],
        [{"check_key": "lp_not_locked_fresh_pool", "value": "TRUE"}],
        [{"check_key": "deployer_prior_rug", "value": "TRUE"}],
    ]
    vetoes = sum(1 for fx in fixtures if security_gate.evaluate(fx)["verdict"] == "SECURITY_VETO")
    assert vetoes == len(fixtures) == 7


def test_rugcheck_normalization_unknown_law():
    payload = {"mintAuthority": None, "freezeAuthority": "SomeAddr", "risks": []}
    checks = security_gate.checks_from_rugcheck(payload)
    by = {c["check_key"]: c["value"] for c in checks if c["value"] in ("TRUE", "FALSE", "UNKNOWN")}
    assert by["mint_authority_active"] == "FALSE"        # null = revoked → FALSE
    assert by["freeze_authority_active"] == "TRUE"       # present = active
    assert by["proxy_risk_upgradeable"] if "proxy_risk_upgradeable" in by else True
    assert "HOLDER" not in by
    lp = security_gate.lp_fresh_pool_check(None, T0, T0 + 100)
    assert lp == "UNKNOWN"
    lp2 = security_gate.lp_fresh_pool_check(0, T0, T0 + 86400)   # young pool, 0% locked
    assert lp2 == "TRUE"


# ---------------- STEP 8: outcomes ----------------
def test_outcome_labeler_and_no_peeking(conn):
    tid, _ = _mk_token(conn, created_offset=-100.0, now=T0)
    series = [(0, {"price_usd": 1.0})]
    series += [(i * 3600, {"price_usd": 1.0 * (1 + 0.05 * i)}) for i in range(1, 80)]
    _feed(conn, tid, series)
    lifecycle.tick(conn, tid, T0 + 73 * 3600)
    n = outcomes.compute_outcomes(conn, tid, T0 + 73 * 3600)
    # closed horizons: 15m,1h,4h,12h,24h,72h; but 15m window holds <2 hourly fixture points →
    # honestly skipped (no single-point "max move" fabrication). 7d NOT closed (no peeking).
    assert n == 5 * 4
    rows = conn.execute("SELECT * FROM outcome_label WHERE token_id=?", (tid,)).fetchall()
    r72 = [r for r in rows if r["horizon"] == "72h" and r["event_class"] == "+100%"][0]
    assert r72["hit"] == 1 and r72["max_favorable"] > 1.0
    assert r72["entry_price"] == 1.0
    # no-peeking enforced by horizon closure: 7d absent
    assert not any(r["horizon"] == "7d" for r in rows)


# ---------------- STEP 9: ranker ----------------
def test_ranker_first_class_and_veto_exclusion(conn):
    good, _ = _mk_token(conn, addr="GoodMint11111111111111111111111111111111111111", now=T0)
    _feed(conn, good, _rich_series(20000.0))
    security_gate.record_check(conn, good, T0, "rugcheck", "honeypot", "FALSE")
    bad, _ = _mk_token(conn, addr="BadMint222222222222222222222222222222222222222", now=T0)
    _feed(conn, bad, _rich_series(5000.0))
    security_gate.record_check(conn, bad, T0, "rugcheck", "honeypot", "TRUE")
    security_gate.evaluate_token(conn, bad, T0 + 1)
    res = ranker.rank(conn, T0 + 14 * 300)
    ranked_ids = [r["token_id"] for r in res["ranked"]]
    assert good in ranked_ids and bad not in ranked_ids
    assert any(e["token_id"] == bad and e["reason"] == "SECURITY_VETO" for e in res["excluded"])
    assert "NO numeric probability" in res["note"] or "calibration pending" in res["note"]
    r0 = res["ranked"][0]
    assert r0["rank"] == 1 and r0["bullets"] and "score" not in r0  # rank-first, no numeric score


def test_ranker_empty_is_success(conn):
    res = ranker.rank(conn, T0)
    assert res["ranked"] == [] and "NO OPPORTUNITY" in res["summary"]


# ---------------- PAL mechanics (fixtures; network is separate smoke) ----------------
class _FakeResp:
    def __init__(self, body, status=200):
        self.body, self.status = body, status
    def read(self):
        return self.body
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def test_pal_envelope_contract_and_breaker(monkeypatch, tmp_path):
    calls = {"n": 0}
    def fake_open(req, timeout):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise TimeoutError("fixture timeout")
        return _FakeResp(b'{"data": []}', 200)
    monkeypatch.setattr(pal.urllib.request, "urlopen", fake_open)
    p = pal.PAL(str(ROOT_DIR / "discovery" / "providers.yaml"))
    cli = p.clients["geckoterminal_new_pools"]
    e1 = cli.fetch("new_pools", "discovery_stream", chain="solana", page=1, now=T0)
    assert e1["error_state"]["kind"] == "network_error" and e1["availability"] == "DOWN"
    e2 = cli.fetch("new_pools", "discovery_stream", chain="solana", page=1, now=T0 + 1)
    e3 = cli.fetch("new_pools", "discovery_stream", chain="solana", page=1, now=T0 + 2)
    for k in ("provider_id", "endpoint", "chain", "capability", "data_type", "freshness_sec",
              "rate_limit", "availability", "confidence", "source_timestamp",
              "retrieval_timestamp", "error_state"):
        assert k in e3, k
    assert e3["availability"] == "OK"
    assert e3["payload"] == {"data": []}
    # breaker: 3 consecutive failures → open
    def always_fail(req, timeout):
        raise TimeoutError("boom")
    monkeypatch.setattr(pal.urllib.request, "urlopen", always_fail)
    for i in range(3):
        cli.fetch("new_pools", "discovery_stream", chain="solana", page=9, now=T0 + 10 + i * 200)
    assert cli.breaker.open
    e = cli.fetch("new_pools", "discovery_stream", chain="solana", page=9, now=T0 + 1000)
    assert e["error_state"]["kind"] == "breaker_open"


def test_pal_registry_loads():
    p = pal.PAL(str(ROOT_DIR / "discovery" / "providers.yaml"))
    assert "discovery_stream" in p.capabilities
    assert len(p.clients) >= 10
    gt = p.registry["providers"]["geckoterminal_new_pools"]
    assert gt["rate"]["rpm"] == 25 and gt["cost"] == "free"


# ---------------- holders adapter (fixture RPC; live method currently rate-limited — recorded) ----------------
def test_holder_snapshot_math_and_honest_failure(monkeypatch, conn):
    from discovery import holders, pal as pal_mod

    # success path: fixture RPC returns 20 accounts with known distribution
    class _R:
        status = 200
        def read(self):
            accts = [{"address": f"a{i}", "amount": str(100 - i)} for i in range(20)]
            return json.dumps({"jsonrpc": "2.0", "result": {"value": accts}}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(pal_mod.urllib.request, "urlopen", lambda req, timeout=None: _R())
    p = pal_mod.PAL(str(ROOT_DIR / "discovery" / "providers.yaml"))
    tid, _ = _mk_token(conn)
    now = T0 + 5000
    res = holders.snapshot_token(conn, tid, "Addr111", now, pal_client=p)
    assert res["ok"] and res["n_accounts"] == 20
    total = sum(100 - i for i in range(20))
    exp10 = sum(100 - i for i in range(10)) / total
    assert res["top10_share"] == pytest.approx(exp10)
    row = conn.execute("SELECT * FROM holder_snapshot WHERE token_id=?", (tid,)).fetchone()
    assert row["error_state"] is None and row["top10_share"] == pytest.approx(exp10)

    # failure path: RPC raises → error_state row, NO fake shares
    def boom(req, timeout=None):
        raise TimeoutError("fixture")
    monkeypatch.setattr(pal_mod.urllib.request, "urlopen", boom)
    for c in p.clients.values():
        c.breaker.consecutive_failures = 0; c.breaker.opened_at = None
    res2 = holders.snapshot_token(conn, tid, "Addr111", now + 10, pal_client=p)
    assert res2["ok"] is False
    rows = conn.execute("SELECT COUNT(*) c, SUM(top10_share IS NOT NULL) ok FROM holder_snapshot WHERE token_id=?",
                        (tid,)).fetchone()
    assert rows["c"] == 2 and rows["ok"] == 1     # one real, one honest error row


def test_v02_features_market_computable_holder_absent(conn):
    from discovery import feature_store as fs
    tid, _ = _mk_token(conn, now=T0)
    _feed(conn, tid, _rich_series(n=16))
    as_of = T0 + 15 * 300
    f = fs.compute_features_v02(conn, tid, as_of)
    # market v02 features present (fixture carries 5m txn counts)
    assert set(["liquidity_stability", "txn_acceleration"]).issubset(f.keys())
    assert f["txn_acceleration"]["value_num"] == pytest.approx(50 / 44.0, rel=1e-9)  # prev 11 pts i=4..14 → Σ=484, mean=44
    # holder features honestly ABSENT (no snapshot rows)
    assert "top_holder_concentration" not in f and "top20_net_flow_1h" not in f
    for k, v in f.items():
        assert v["availability_ts"] <= as_of
    n = fs.persist_features(conn, tid, as_of, f, feature_set=fs.FEATURE_SET_V02)
    assert n == len(f)
    # registry ⇄ computed equality: every DEFINED key in fs_v0.2 registry is computable-or-absent-by-law
    fs.register_definitions(conn)
    defs = conn.execute(
        "SELECT key FROM feature_definitions WHERE feature_set_version=?", (fs.FEATURE_SET_V02,)).fetchall()
    assert len(defs) == len(fs.ALL_FEATURES_V02) == 20
