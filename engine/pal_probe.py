#!/usr/bin/env python3
"""AHOS PAL probe tool — systemic capability probing with probe-id evidence.

Law (Council D2, made permanent by Wave-7 directive §20):
    NO CAPABILITY CLAIM WITHOUT A PROBE ID.

This tool probes every PAL capability chain (and a curated EXTRA endpoint list
of known-degraded services) against LIVE endpoints and emits a JSON report in
which every availability statement carries a deterministic probe id.

Usage:
    python3 engine/pal_probe.py                      # probe everything (sandbox site)
    python3 engine/pal_probe.py --site user-iran     # user-side run from Iran network
    python3 engine/pal_probe.py --capability security_evm
    python3 engine/pal_probe.py --out reports/pal_probe_<auto>.json

The SAME script serves as the Iran-network probe: run it on the user's machine
with --site user-iran and return the JSON; it requires no API keys.

Probe id format: PRB-<YYYYMMDD>-<SEQ> (SEQ = stable order of the probe table).
Deterministic: same table order always yields the same ids for the same day.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from discovery.pal import PAL  # noqa: E402

UA = {"User-Agent": "ahos-pal-probe/1.0"}

# Canonical, stable, well-known probe targets (no keys required anywhere).
BONK_SOL = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"     # long-lived SPL mint
WETH_ETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"     # WETH mainnet

# PAL chain probes: (capability, path_key, fmt kwargs, note)
CHAIN_PROBES = [
    ("discovery_stream", "new_pools", {"chain": "solana", "page": 1}, "GT solana new pools"),
    ("pair_enrich", "token_pairs", {"chain": "solana", "address": BONK_SOL}, "DexScreener token pairs (BONK)"),
    ("security_sol", "summary", {"address": BONK_SOL}, "RugCheck summary (BONK)"),
    ("security_evm", "token_security", {"chain": "ethereum", "address": WETH_ETH}, "GoPlus token_security (WETH)"),
]

# RSS providers carry no path_templates; the base_url IS the endpoint.
RSS_PROBES = [
    ("narrative_rss", "https://cointelegraph.com/rss", "CoinTelegraph RSS"),
    ("narrative_rss", "https://www.theblock.co/rss.xml", "TheBlock RSS"),
]

# Direct extra probes for endpoints NOT in a PAL chain (degraded history).
# (probe_key, method, url, jsonrpc_body|None, note)
EXTRA_PROBES = [
    ("llamarpc_eth", "POST", "https://eth.llamarpc.com",
     {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
     "LlamaRPC — FAILED 521 on 2026-08-11; re-probe"),
    ("cloudflare_eth", "POST", "https://cloudflare-eth.com",
     {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
     "Cloudflare ETH — returned -32046 on 2026-08-11; re-probe"),
    ("ankr_eth", "POST", "https://rpc.ankr.com/eth",
     {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
     "Ankr — began requiring API key 2026-08-11; re-probe"),
    ("helius_public", "POST", "https://mainnet.helius-rpc.com/?api-key=public",
     {"jsonrpc": "2.0", "id": 1, "method": "getSlot", "params": []},
     "Helius 'public' key — 401 on 2026-08-11; re-probe"),
    ("cryptopanic_posts", "GET", "https://cryptopanic.com/api/free/v1/posts/?kind=news", None,
     "CryptoPanic free API — 404 ×2 on 2026-08-11 (endpoint changed?); re-probe"),
    ("coindesk_rss", "GET", "https://www.coindesk.com/arc/outboundfeeds/rss/", None,
     "CoinDesk RSS — 308 redirect chain on 2026-08-11; re-probe"),
]

# JSON-RPC probes for PAL rpc_* capability providers (transport: jsonrpc).
RPC_PROBES = [
    ("rpc_sol", "https://api.mainnet-beta.solana.com", "getSlot", "solana mainnet-beta"),
    ("rpc_sol", "https://solana-rpc.publicnode.com", "getSlot", "solana publicnode"),
    ("rpc_eth", "https://ethereum-rpc.publicnode.com", "eth_blockNumber", "publicnode ETH"),
    ("rpc_bsc", "https://bsc-rpc.publicnode.com", "eth_blockNumber", "publicnode BSC"),
    ("rpc_base", "https://base-rpc.publicnode.com", "eth_blockNumber", "publicnode Base"),
]


def _post_jsonrpc(url: str, method: str, timeout: int = 12) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": []}).encode()
    req = urllib.request.Request(url, data=body, headers={**UA, "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            dt_ms = round((time.time() - t0) * 1000)
            payload = json.loads(raw)
            if isinstance(payload, dict) and payload.get("error"):
                return {"availability": "DEGRADED", "http_status": r.status, "latency_ms": dt_ms,
                        "error_kind": "rpc_error", "error_message": str(payload["error"])[:200]}
            return {"availability": "OK", "http_status": r.status, "latency_ms": dt_ms,
                    "error_kind": None, "error_message": None}
    except urllib.error.HTTPError as e:
        return {"availability": "DOWN", "http_status": e.code,
                "latency_ms": round((time.time() - t0) * 1000),
                "error_kind": "http_error", "error_message": str(e)[:200]}
    except Exception as e:
        return {"availability": "DOWN", "http_status": None,
                "latency_ms": round((time.time() - t0) * 1000),
                "error_kind": "network_error", "error_message": f"{type(e).__name__}: {e}"[:200]}


def _get(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers=UA)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
            return {"availability": "OK", "http_status": r.status,
                    "latency_ms": round((time.time() - t0) * 1000),
                    "error_kind": None, "error_message": None}
    except urllib.error.HTTPError as e:
        return {"availability": "DOWN", "http_status": e.code,
                "latency_ms": round((time.time() - t0) * 1000),
                "error_kind": "http_error", "error_message": str(e)[:200]}
    except Exception as e:
        return {"availability": "DOWN", "http_status": None,
                "latency_ms": round((time.time() - t0) * 1000),
                "error_kind": "network_error", "error_message": f"{type(e).__name__}: {e}"[:200]}


def make_probe_id(day: str, seq: int) -> str:
    return f"PRB-{day}-{seq:03d}"


def _record(probe_id: str, site: str, capability: str, target: str, note: str, res: dict) -> dict:
    rec = {
        "probe_id": probe_id,
        "ts_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "site": site,
        "capability": capability,
        "target": target,
        "note": note,
        "availability": res["availability"],
        "http_status": res.get("http_status"),
        "latency_ms": res.get("latency_ms"),
        "error_kind": res.get("error_kind"),
        "error_message": res.get("error_message"),
    }
    rec["evidence_sha256"] = hashlib.sha256(
        json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


def run_probes(site: str = "sandbox", only_capability: str | None = None,
               pal: PAL | None = None, day: str | None = None) -> dict:
    day = day or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d")
    pal = pal or PAL()
    records: list[dict] = []
    seq = 0

    for capability, path_key, fmt, note in CHAIN_PROBES:
        if only_capability and capability != only_capability:
            continue
        seq += 1
        t0 = time.time()
        env = pal.call(capability, path_key, data_type="json", **fmt)
        res = {"availability": env["availability"], "http_status": env.get("http_status"),
               "latency_ms": round((time.time() - t0) * 1000),
               "error_kind": (env.get("error_state") or {}).get("kind"),
               "error_message": ((env.get("error_state") or {}).get("message") or "")[:200]}
        rec = _record(make_probe_id(day, seq), site, capability,
                      env.get("endpoint") or capability, note, res)
        rec["attempts"] = env.get("attempts")
        records.append(rec)

    for capability, url, label in RSS_PROBES:
        if only_capability and capability != only_capability:
            continue
        seq += 1
        res = _get(url)
        records.append(_record(make_probe_id(day, seq), site, capability, url, label, res))

    for capability, url, method, label in RPC_PROBES:
        if only_capability and capability != only_capability:
            continue
        seq += 1
        res = _post_jsonrpc(url, method)
        records.append(_record(make_probe_id(day, seq), site, capability, url, label, res))

    for key, method, url, body, note in EXTRA_PROBES:
        if only_capability and key != only_capability:
            continue
        seq += 1
        if method == "POST" and body:
            res = _post_jsonrpc(url, body["method"])
        else:
            res = _get(url)
        records.append(_record(make_probe_id(day, seq), site, f"extra:{key}", url, note, res))

    ok = sum(1 for r in records if r["availability"] == "OK")
    return {
        "report": "pal_probe",
        "schema": 1,
        "site": site,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "total": len(records), "ok": ok,
        "down_or_degraded": len(records) - ok,
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="sandbox", help="probe site label, e.g. sandbox | user-iran")
    ap.add_argument("--capability", default=None, help="probe a single capability/extra key only")
    ap.add_argument("--out", default=None, help="report path (default reports/pal_probe_<ts>_<site>.json)")
    args = ap.parse_args(argv)

    rep = run_probes(site=args.site, only_capability=args.capability)
    out = Path(args.out) if args.out else Path(__file__).resolve().parents[1] / "reports" / (
        f"pal_probe_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%d_%H%M%S')}_{args.site}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(f"[pal_probe] site={args.site} total={rep['total']} OK={rep['ok']} "
          f"DOWN/DEGRADED={rep['down_or_degraded']} -> {out}")
    for r in rep["records"]:
        print(f"  {r['probe_id']} {r['capability']:<22} {r['availability']:<9} "
              f"{str(r['http_status']):<5} {r['latency_ms']}ms  {r['target']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
