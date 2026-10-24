"""M13.6 / M33 / M33.4 / TS-4: Live 2-Source DEX Token Safety Hard Veto.

Queries free, keyless public security & DEX APIs:
  1. GoPlus Security API (contract audit: honeypot, buy/sell tax, open_source, mintable, proxy/owner privileges)
  2. Honeypot.is v2 API (EVM call/bytecode transfer simulation, buy/sell tax, openSource)
  3. DexScreener API (live on-chain pool liquidity USD & 24h volume)

Hard fail-closed rule (Trading Skills v2 §4 & Master Map Law 6):
  - Requires >= 2 independent security sources (GoPlus + Honeypot.is) reachable and agreeing.
  - Any single-source response, unreachable API, simulation failure, tax > 5%, closed-source contract,
    mintable supply, or liquidity < $100,000 triggers VETOED_FAIL_CLOSED (allowed=False).
  - PAPER_ONLY: never signs, never executes on-chain transactions.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PAPER_ONLY: bool = True
UA = {"User-Agent": "Mozilla/5.0 (AHOS paper token safety veto)"}

# Canonical ERC-20 contracts on Ethereum mainnet (chain_id=1) for M13.6 PB-TOKEN desk
VETTED_TOKEN_CONTRACTS: dict[str, dict[str, str]] = {
    "UNI": {
        "symbol": "UNI",
        "name": "Uniswap",
        "chain_id": "1",
        "address": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
    },
    "LINK": {
        "symbol": "LINK",
        "name": "Chainlink",
        "chain_id": "1",
        "address": "0x514910771af9ca656af840dff83e8264ecf986ca",
    },
    "AAVE": {
        "symbol": "AAVE",
        "name": "Aave",
        "chain_id": "1",
        "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
    },
}

MAX_TAX = 0.05
MIN_LIQUIDITY_USD = 100_000.0
_VETO_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _http_json(url: str, timeout: float = 7.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def fetch_goplus(address: str, chain_id: str = "1", getter: Callable[[str], dict[str, Any] | None] = _http_json) -> dict[str, Any] | None:
    addr = address.lower()
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={addr}"
    d = getter(url)
    res = (d or {}).get("result") or {}
    tok = res.get(addr) or res.get(address)
    if not isinstance(tok, dict) or not tok:
        return None
    try:
        return {
            "source": "goplus_v1",
            "is_honeypot": str(tok.get("is_honeypot", "1")) != "0",
            "buy_tax": float(tok.get("buy_tax") or 0.0),
            "sell_tax": float(tok.get("sell_tax") or 0.0),
            "is_open_source": str(tok.get("is_open_source", "0")) == "1",
            "is_mintable": str(tok.get("is_mintable", "0")) == "1",
            "cannot_sell_all": str(tok.get("cannot_sell_all", "0")) == "1",
            "holder_count": int(float(tok.get("holder_count") or 0)),
        }
    except Exception:
        return None


def fetch_honeypot_is(address: str, chain_id: str = "1", getter: Callable[[str], dict[str, Any] | None] = _http_json) -> dict[str, Any] | None:
    url = f"https://api.honeypot.is/v2/IsHoneypot?address={address.lower()}&chainID={chain_id}"
    d = getter(url)
    if not isinstance(d, dict) or "honeypotResult" not in d:
        return None
    try:
        sim = d.get("simulationResult") or {}
        code = d.get("contractCode") or {}
        hp = d.get("honeypotResult") or {}
        # Honeypot.is reports taxes in percent (0..100)
        bt = float(sim.get("buyTax") or 0.0)
        st = float(sim.get("sellTax") or 0.0)
        if bt > 1.0 or st > 1.0:
            bt, st = bt / 100.0, st / 100.0
        return {
            "source": "honeypot_is_v2",
            "simulation_success": bool(d.get("simulationSuccess", False)),
            "is_honeypot": bool(hp.get("isHoneypot", True)),
            "buy_tax": bt,
            "sell_tax": st,
            "is_open_source": bool(code.get("openSource", True)),
        }
    except Exception:
        return None


def fetch_dexscreener(address: str, getter: Callable[[str], dict[str, Any] | None] = _http_json) -> dict[str, Any] | None:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{address.lower()}"
    d = getter(url)
    pairs = (d or {}).get("pairs")
    if not isinstance(pairs, list) or not pairs:
        return None
    total_liq = 0.0
    total_vol = 0.0
    best_px = None
    best_liq = -1.0
    for p in pairs[:15]:
        liq = float(((p.get("liquidity") or {}).get("usd")) or 0.0)
        vol = float(((p.get("volume") or {}).get("h24")) or 0.0)
        total_liq += liq
        total_vol += vol
        if liq > best_liq and p.get("priceUsd"):
            try:
                best_px = float(p["priceUsd"])
                best_liq = liq
            except ValueError:
                pass
    return {
        "source": "dexscreener_v1",
        "pairs_count": len(pairs),
        "liquidity_usd": round(total_liq, 2),
        "volume_24h_usd": round(total_vol, 2),
        "price_usd": best_px,
    }


def veto_check(
    symbol: str,
    address: str | None = None,
    chain_id: str = "1",
    *,
    getter: Callable[[str], dict[str, Any] | None] = _http_json,
    ttl_s: float = 1800.0,
) -> dict[str, Any]:
    """Run the 2-source hard safety veto. Fail-closed on any missing source or policy breach."""
    meta = VETTED_TOKEN_CONTRACTS.get(symbol.upper(), {})
    addr = (address or meta.get("address") or "").strip().lower()
    cid = chain_id or meta.get("chain_id", "1")
    if not addr:
        return {
            "symbol": symbol,
            "address": None,
            "allowed": False,
            "verdict": "VETOED_FAIL_CLOSED",
            "reasons": ["missing_contract_address"],
            "sources_verified": 0,
            "paper_only": True,
        }

    cache_key = f"{cid}:{addr}"
    if getter is _http_json and cache_key in _VETO_CACHE:
        ts, cached = _VETO_CACHE[cache_key]
        if time.time() - ts < ttl_s:
            return cached

    gp = fetch_goplus(addr, cid, getter=getter)
    hp = fetch_honeypot_is(addr, cid, getter=getter)
    dx = fetch_dexscreener(addr, getter=getter)

    reasons: list[str] = []
    sec_sources = [s["source"] for s in (gp, hp) if s is not None]
    if len(sec_sources) < 2:
        reasons.append(f"insufficient_security_sources:{len(sec_sources)}_of_2")

    if gp is not None:
        if gp["is_honeypot"]:
            reasons.append("goplus:is_honeypot")
        if gp["buy_tax"] > MAX_TAX or gp["sell_tax"] > MAX_TAX:
            reasons.append(f"goplus:high_tax(buy={gp['buy_tax']:.3f},sell={gp['sell_tax']:.3f})")
        if not gp["is_open_source"]:
            reasons.append("goplus:not_open_source")
        if gp["is_mintable"]:
            reasons.append("goplus:mintable_supply")
        if gp["cannot_sell_all"]:
            reasons.append("goplus:cannot_sell_all")

    if hp is not None:
        if not hp["simulation_success"]:
            reasons.append("honeypot_is:evm_simulation_failed")
        if hp["is_honeypot"]:
            reasons.append("honeypot_is:is_honeypot")
        if hp["buy_tax"] > MAX_TAX or hp["sell_tax"] > MAX_TAX:
            reasons.append(f"honeypot_is:high_tax(buy={hp['buy_tax']:.3f},sell={hp['sell_tax']:.3f})")
        if not hp["is_open_source"]:
            reasons.append("honeypot_is:not_open_source")

    liq_usd = (dx or {}).get("liquidity_usd") or 0.0
    if dx is None or liq_usd < MIN_LIQUIDITY_USD:
        reasons.append(f"dexscreener:insufficient_liquidity({liq_usd:.0f}<{MIN_LIQUIDITY_USD:.0f})")

    allowed = len(reasons) == 0
    res = {
        "symbol": symbol.upper(),
        "address": addr,
        "chain_id": cid,
        "allowed": allowed,
        "verdict": "ELIGIBLE_PAPER_TOKEN" if allowed else "VETOED_FAIL_CLOSED",
        "reasons": reasons,
        "sources_verified": len(sec_sources) + (1 if dx is not None else 0),
        "security_sources": sec_sources,
        "goplus": gp,
        "honeypot_is": hp,
        "dexscreener": dx,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
    }
    if getter is _http_json:
        _VETO_CACHE[cache_key] = (time.time(), res)
    return res


def export_token_safety_snapshot(root: Path | None = None) -> dict[str, Any]:
    base = (root or Path(__file__).resolve().parents[2]).resolve()
    results = [veto_check(sym) for sym in ("UNI", "LINK", "AAVE")]
    # Also include a deterministic fail-closed test record (single-source / bad tax)
    bad_fixture = veto_check(
        "RUG_TEST",
        "0x000000000000000000000000000000000000dead",
        getter=lambda u: {"result": {"0x000000000000000000000000000000000000dead": {"is_honeypot": "1", "buy_tax": "0.45", "sell_tax": "0.99", "is_open_source": "0", "is_mintable": "1"}}} if "goplus" in u else None,
    )
    results.append(bad_fixture)
    snap = {
        "schema": "ahos.token_safety_live.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "spec": "TRADING_SKILLS_v2 §4 + M13.6 + M33.4",
        "eligible_count": sum(1 for r in results if r["allowed"]),
        "vetoed_count": sum(1 for r in results if not r["allowed"]),
        "tokens": results,
    }
    out = base / "reports" / "grok" / "M33" / "live_token_safety_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snap
