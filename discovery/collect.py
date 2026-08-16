#!/usr/bin/env python3
"""AHOS E-01 collector (STEP 4/8 integration) — REAL discovery pass.
Streams: GeckoTerminal new_pools (primary, richer payload) + DexScreener profiles/boosts (secondary).
Enrichment: DexScreener tokens/v1 per new token (fallback GT pool detail) — rate-budgeted via PAL.
Every record: dual timestamps + raw payload sha256. Failures → error_state observations, never fakes.
Usage:
  python3 -m discovery.collect [--store data/e01_discovery.sqlite] [--max-new 15] [--dry-run]
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from discovery import pal, identity, observations as obs, lifecycle

SUPPORTED_CHAINS = ["solana", "ethereum", "bsc", "base"]


# ---------------- adapters: provider payload → normalized records ----------------
def normalize_gt_new_pool(item: dict) -> dict | None:
    a = (item or {}).get("attributes", {})
    rel = (item or {}).get("relationships", {})
    pool_addr = a.get("address")
    base_rel = rel.get("base_token", {}).get("data", {})
    base_id = base_rel.get("id", "")           # format: "<chain>_<address>"
    chain_raw, _, addr = base_id.partition("_")
    if not (pool_addr and addr):
        return None
    chain = identity.normalize_chain(chain_raw) or None
    if not chain:
        # GT ids use its own network ids; fall back handled by caller (chain param of endpoint)
        return None
    tx = a.get("transactions") or {}
    vol = a.get("volume_usd") or {}
    chg = a.get("price_change_percentage") or {}
    return {
        "chain": chain, "address": addr, "symbol": (a.get("name") or "").split("/")[0].strip() or None,
        "name": a.get("name"), "dex": None, "pair_address": pool_addr,
        "quote_symbol": None,
        "pool_created_ts": _iso8601_to_ts(a.get("pool_created_at")),
        "metrics": {
            "price_usd": obs.f(a.get("base_token_price_usd")),
            "liquidity_usd": obs.f(a.get("reserve_in_usd")),
            "fdv": obs.f(a.get("fdv_usd")),
            "market_cap": obs.f(a.get("market_cap_usd")),
            "volume_5m": obs.f(vol.get("m5")), "volume_1h": obs.f(vol.get("h1")),
            "volume_6h": obs.f(vol.get("h6")), "volume_24h": obs.f(vol.get("h24")),
            "txns_5m_buys": obs.i((tx.get("m5") or {}).get("buys")),
            "txns_5m_sells": obs.i((tx.get("m5") or {}).get("sells")),
            "txns_1h_buys": obs.i((tx.get("h1") or {}).get("buys")),
            "txns_1h_sells": obs.i((tx.get("h1") or {}).get("sells")),
            "txns_24h_buys": obs.i((tx.get("h24") or {}).get("buys")),
            "txns_24h_sells": obs.i((tx.get("h24") or {}).get("sells")),
            "price_change_5m": obs.f(chg.get("m5")), "price_change_1h": obs.f(chg.get("h1")),
            "price_change_6h": obs.f(chg.get("h6")), "price_change_24h": obs.f(chg.get("h24")),
        },
    }


def normalize_dex_pairs(payload, chain: str) -> list[dict]:
    """DexScreener tokens/v1 → list of pair records (one token, possibly many pairs)."""
    out = []
    if not isinstance(payload, list):
        return out
    for p in payload:
        base = p.get("baseToken") or {}
        addr = base.get("address")
        pair_addr = p.get("pairAddress")
        if not (addr and pair_addr):
            continue
        liq = p.get("liquidity") or {}
        vol = p.get("volume") or {}
        tx = p.get("txns") or {}
        chg = p.get("priceChange") or {}
        boosts = p.get("boosts") or {}
        out.append({
            "chain": identity.normalize_chain(p.get("chainId") or chain),
            "address": addr, "symbol": base.get("symbol"), "name": base.get("name"),
            "dex": p.get("dexId"), "pair_address": pair_addr,
            "quote_symbol": (p.get("quoteToken") or {}).get("symbol"),
            "pool_created_ts": obs.ms_to_ts(p.get("pairCreatedAt")),
            "metrics": {
                "price_usd": obs.f(p.get("priceUsd")),
                "liquidity_usd": obs.f(liq.get("usd")),
                "fdv": obs.f(p.get("fdv")), "market_cap": obs.f(p.get("marketCap")),
                "volume_5m": obs.f(vol.get("m5")), "volume_1h": obs.f(vol.get("h1")),
                "volume_6h": obs.f(vol.get("h6")), "volume_24h": obs.f(vol.get("h24")),
                "txns_5m_buys": obs.i((tx.get("m5") or {}).get("buys")),
                "txns_5m_sells": obs.i((tx.get("m5") or {}).get("sells")),
                "txns_1h_buys": obs.i((tx.get("h1") or {}).get("buys")),
                "txns_1h_sells": obs.i((tx.get("h1") or {}).get("sells")),
                "txns_24h_buys": obs.i((tx.get("h24") or {}).get("buys")),
                "txns_24h_sells": obs.i((tx.get("h24") or {}).get("sells")),
                "price_change_5m": obs.f(chg.get("m5")), "price_change_1h": obs.f(chg.get("h1")),
                "price_change_6h": obs.f(chg.get("h6")), "price_change_24h": obs.f(chg.get("h24")),
                "boost_amount": obs.f(boosts.get("active")),
            },
        })
    return out


def _iso8601_to_ts(s):
    if not s:
        return None
    try:
        from datetime import datetime, timezone
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except Exception:
        return None


# ---------------- ingestion ----------------
def ingest_record(conn, rec: dict, provider: str, retrieved_ts: float, raw_sha: str,
                  endpoint: str, enrich_budget: dict | None = None) -> dict:
    """Upsert token+pair, record observation, advance lifecycle. Returns status dict."""
    tok = obs.upsert_token(conn, rec["chain"], rec["address"], first_seen_ts=retrieved_ts,
                           provider=provider, symbol=rec.get("symbol"), name=rec.get("name"),
                           created_at_ts=rec.get("pool_created_ts"))
    pid = None
    if rec.get("pair_address"):
        pid = obs.upsert_pair(conn, rec["chain"], rec.get("dex") or "unknown", rec["pair_address"],
                              tok, retrieved_ts, provider, raw_sha,
                              quote_symbol=rec.get("quote_symbol"),
                              pair_created_ts=rec.get("pool_created_ts"))
    lifecycle.register_discovery(conn, tok, retrieved_ts)
    age = None
    if rec.get("pool_created_ts"):
        age = max(0, int((retrieved_ts - rec["pool_created_ts"]) / 60))
    metrics = dict(rec.get("metrics") or {})
    metrics["pair_age_minutes"] = age
    oid = obs.record_observation(conn, tok, provider, retrieved_ts, raw_sha, pair=pid,
                                 source_ts=rec.get("pool_created_ts"), metrics=metrics)
    lifecycle.on_observation(conn, tok, retrieved_ts)
    return {"token_id": tok, "pair_id": pid, "obs_id": oid}


def run_collection(store_path: Path, max_new: int = 15, dry_run: bool = False,
                   now: float | None = None) -> dict:
    """One E-01 collection pass. Deterministic when `now` injected (fixtures); REAL when None."""
    now = now if now is not None else time.time()
    p = pal.PAL()
    conn = obs.open_store(store_path)
    report = {"ts": now, "store": str(store_path), "dry_run": dry_run,
              "streams": {}, "ingested": 0, "errors": [], "new_tokens": []}

    # -------- stream 1: GeckoTerminal new pools per supported chain --------
    for chain in SUPPORTED_CHAINS:
        env = p.clients["geckoterminal_new_pools"].fetch("new_pools", "discovery_stream",
                                                         chain=chain, page=1, now=now)
        stream = {"availability": env["availability"], "endpoint": env["endpoint"]}
        report["streams"][f"gt_new_pools_{chain}"] = stream
        if env["availability"] != "OK":
            report["errors"].append({"stream": f"gt:{chain}", "error": env.get("error_state")})
            continue
        raw_sha = obs.store_raw(conn, "geckoterminal", env["endpoint"], now,
                                env.get("http_status"), env["payload"])
        data = (env["payload"] or {}).get("data") or []
        taken = 0
        for item in data:
            if taken >= max_new:
                break
            rec = normalize_gt_new_pool(item)
            if rec is None or identity.normalize_chain(rec["chain"]) != chain:
                continue
            if dry_run:
                report["new_tokens"].append({"chain": rec["chain"], "address": rec["address"][:10] + "…"})
                taken += 1
                continue
            r = ingest_record(conn, rec, "geckoterminal", now, raw_sha, env["endpoint"])
            report["new_tokens"].append(r["token_id"])
            report["ingested"] += 1
            taken += 1
        stream["seen"] = len(data)
        stream["taken"] = taken

    # -------- stream 2: DexScreener latest profiles (cross-check signal + boost flag) --------
    env = p.clients["dexscreener_profiles"].fetch("profiles", "discovery_stream", now=now)
    report["streams"]["dex_profiles"] = {"availability": env["availability"]}
    if env["availability"] == "OK":
        raw_sha = obs.store_raw(conn, "dexscreener", env["endpoint"], now,
                                env.get("http_status"), env["payload"])
        profiles = [x for x in (env["payload"] or []) if identity.normalize_chain(x.get("chainId", ""))]
        report["streams"]["dex_profiles"]["seen"] = len(profiles)
        # enrich at most `max_new` NEWEST unseen via tokens/v1 (rate-safe)
        enriched = 0
        for x in profiles:
            if enriched >= max_new:
                break
            chain = identity.normalize_chain(x.get("chainId", ""))
            addr = x.get("tokenAddress")
            if not (chain and addr):
                continue
            if chain not in SUPPORTED_CHAINS:
                continue
            exists = conn.execute("SELECT 1 FROM tokens WHERE token_id=?",
                                  (identity.token_id(chain, addr),)).fetchone()
            if exists:
                continue
            env2 = p.clients["dexscreener_tokens"].fetch("token_pairs", "pair_enrich",
                                                         chain=chain, address=addr, now=now)
            if env2["availability"] != "OK":
                report["errors"].append({"stream": f"dex_enrich:{chain}", "error": env2.get("error_state")})
                continue
            raw2 = obs.store_raw(conn, "dexscreener", env2["endpoint"], now,
                                 env2.get("http_status"), env2["payload"])
            recs = normalize_dex_pairs(env2["payload"], chain)
            if not recs:
                continue
            best = max(recs, key=lambda r: (r["metrics"].get("liquidity_usd") or 0))
            if dry_run:
                report["new_tokens"].append({"chain": chain, "address": addr[:10] + "…"})
                enriched += 1
                continue
            r = ingest_record(conn, best, "dexscreener", now, raw2, env2["endpoint"])
            report["new_tokens"].append(r["token_id"])
            report["ingested"] += 1
            enriched += 1
        report["streams"]["dex_profiles"]["enriched"] = enriched
    else:
        report["errors"].append({"stream": "dex_profiles", "error": env.get("error_state")})

    if not dry_run:
        conn.commit()
    conn.close()
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="/home/user/ahos/data/e01_discovery.sqlite")
    ap.add_argument("--max-new", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default="/home/user/ahos/research/experiments/e01_collection_report.json")
    args = ap.parse_args()
    rep = run_collection(Path(args.store), max_new=args.max_new, dry_run=args.dry_run)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    print(json.dumps({k: (v if k != "new_tokens" else f"{len(v)} tokens") for k, v in rep.items()},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
