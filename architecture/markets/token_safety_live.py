"""M13.6 / M33.1-M33.7 / TS-4: live DEX token discovery + 3-source hard safety veto (PAPER_ONLY).

Discovery (free, keyless): GeckoTerminal ``networks/eth/trending_pools`` + DexScreener ``token-boosts/top`` (ethereum
rows only). Funnel: pool age >= 7 days, 24h volume >= $250,000, liquidity >= $100,000.

Veto sources:
  1. GoPlus Security v1 (honeypot, taxes, open source, mint, proxy/owner authority, holder concentration)
  2. Honeypot.is v2 (EVM buy/sell simulation, taxes, open source)
  3. DexScreener pools (+ GeckoTerminal for discovered pools): liquidity, FDV/liquidity, pool count

Fail-closed rules (Trading Skills v2 §4, Master Map law 6): fewer than 2 security sources, any missing critical field,
tax > 5%, closed source, mintable supply, honeypot / failed simulation, or liquidity < $100,000 vetoes the token.
``strict=True`` (used for discovered long-tail tokens) also vetoes missing authority flags or holder data.
Missing evidence is never mapped to "safe". Policy breaches -> VETOED_SECURITY; missing evidence -> VETOED_FAIL_CLOSED.

Price witness for discovered tokens: two aggregators reading the same pool are ONE on-chain source, so a DEX token
price is VERIFIED only when >= 2 distinct pools agree within 1% (POOL_WITNESS_VERIFIED).
PAPER_ONLY: never signs, never executes on-chain transactions.
"""
from __future__ import annotations

import json
import math
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PAPER_ONLY: bool = True
UA = {"User-Agent": "Mozilla/5.0 (AHOS paper token safety veto)"}

# Canonical ERC-20 contracts on Ethereum mainnet (chain_id=1) for M13.6 PB-TOKEN desk
VETTED_TOKEN_CONTRACTS: dict[str, dict[str, str]] = {
    "UNI": {"symbol": "UNI", "name": "Uniswap", "chain_id": "1", "address": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"},
    "LINK": {"symbol": "LINK", "name": "Chainlink", "chain_id": "1", "address": "0x514910771af9ca656af840dff83e8264ecf986ca"},
    "AAVE": {"symbol": "AAVE", "name": "Aave", "chain_id": "1", "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"},
}

MAX_TAX = 0.05
MIN_LIQUIDITY_USD = 100_000.0
MIN_VOLUME_24H_USD = 250_000.0
MIN_POOL_AGE_DAYS = 7.0
MAX_FDV_TO_LIQUIDITY = 1000.0
MAX_SINGLE_HOLDER_PCT = 0.30
MAX_TOP10_HOLDER_PCT = 0.70
POOL_PRICE_TOL = 0.01
SNAPSHOT_REL = Path("reports") / "grok" / "M33" / "live_token_safety_snapshot.json"
BURN_ADDRESSES = {"0x000000000000000000000000000000000000dead", "0x0000000000000000000000000000000000000000"}
GECKO_TRENDING_URL = "https://api.geckoterminal.com/api/v2/networks/eth/trending_pools?page=1"
DEXS_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/top/v1"
AUTHORITY_FLAGS = ("is_proxy", "hidden_owner", "can_take_back_ownership", "owner_change_balance", "selfdestruct",
                   "cannot_sell_all", "transfer_pausable", "slippage_modifiable", "personal_slippage_modifiable",
                   "cannot_buy")
_VETO_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _http_json(url: str, timeout: float = 7.0) -> Any:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _f(v: Any) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _flag(v: Any) -> bool | None:
    if v is None or v == "":
        return None
    return str(v).strip() == "1"


def _holder_concentration(holders: Any, exclude: set[str]) -> dict[str, Any] | None:
    if not isinstance(holders, list) or not holders:
        return None
    rows = []
    for h in holders:
        addr = str(h.get("address") or "").lower()
        pct = _f(h.get("percent"))
        if pct is None or addr in BURN_ADDRESSES or addr in exclude or str(h.get("is_locked")) == "1":
            continue
        rows.append((addr, pct, bool(int(h.get("is_contract") or 0))))
    rows.sort(key=lambda r: -r[1])
    return {"top1_pct": round(rows[0][1], 4) if rows else 0.0, "top10_pct": round(sum(r[1] for r in rows[:10]), 4),
            "top1_is_contract": rows[0][2] if rows else None, "excluded": "burn, locked, known LP pools"}


def fetch_goplus(address: str, chain_id: str = "1", getter: Callable[[str], Any] = _http_json,
                 lp_pools: set[str] | None = None) -> dict[str, Any] | None:
    addr = address.lower()
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={addr}"
    d = getter(url)
    res = (d or {}).get("result") or {} if isinstance(d, dict) else {}
    tok = res.get(addr) or res.get(address)
    if not isinstance(tok, dict) or not tok:
        return None
    hp = _flag(tok.get("is_honeypot"))
    return {
        "source": "goplus_v1",
        "is_honeypot": True if hp is None else hp,
        "buy_tax": _f(tok.get("buy_tax")),
        "sell_tax": _f(tok.get("sell_tax")),
        "is_open_source": _flag(tok.get("is_open_source")),
        "is_mintable": _flag(tok.get("is_mintable")),
        "authority": {k: _flag(tok.get(k)) for k in AUTHORITY_FLAGS},
        "cannot_sell_all": _flag(tok.get("cannot_sell_all")),
        "holder_count": int(_f(tok.get("holder_count")) or 0),
        "holder_concentration": _holder_concentration(tok.get("holders"), {p.lower() for p in (lp_pools or set())}),
    }


def fetch_honeypot_is(address: str, chain_id: str = "1", getter: Callable[[str], Any] = _http_json) -> dict[str, Any] | None:
    url = f"https://api.honeypot.is/v2/IsHoneypot?address={address.lower()}&chainID={chain_id}"
    d = getter(url)
    if not isinstance(d, dict) or "honeypotResult" not in d:
        return None
    sim = d.get("simulationResult") or {}
    code = d.get("contractCode") or {}
    hp = d.get("honeypotResult") or {}
    bt, st = _f(sim.get("buyTax")), _f(sim.get("sellTax"))
    # Honeypot.is reports taxes in percent (0..100)
    bt = bt / 100.0 if bt is not None else None
    st = st / 100.0 if st is not None else None
    os_flag = code.get("openSource")
    return {
        "source": "honeypot_is_v2",
        "simulation_success": bool(d.get("simulationSuccess", False)),
        "is_honeypot": bool(hp.get("isHoneypot", True)),
        "buy_tax": bt,
        "sell_tax": st,
        "is_open_source": bool(os_flag) if isinstance(os_flag, bool) else None,
    }


def fetch_dexscreener(address: str, getter: Callable[[str], Any] = _http_json) -> dict[str, Any] | None:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{address.lower()}"
    d = getter(url)
    pairs = (d or {}).get("pairs") if isinstance(d, dict) else None
    if not isinstance(pairs, list) or not pairs:
        return None
    pools = []
    for p in pairs[:15]:
        base = str(((p.get("baseToken") or {}).get("address")) or "").lower()
        if base and base != address.lower():
            continue  # token is the quote side: priceUsd refers to the other token
        pools.append({"pool": str(p.get("pairAddress") or "").lower() or None, "dex": p.get("dexId"),
                      "price_usd": _f(p.get("priceUsd")), "liquidity_usd": _f((p.get("liquidity") or {}).get("usd")) or 0.0,
                      "volume_24h_usd": _f((p.get("volume") or {}).get("h24")) or 0.0, "fdv": _f(p.get("fdv")),
                      "created_ms": p.get("pairCreatedAt")})
    if not pools:
        return None
    total_liq = sum(p["liquidity_usd"] for p in pools)
    best = max(pools, key=lambda p: p["liquidity_usd"])
    fdv = next((p["fdv"] for p in sorted(pools, key=lambda p: -p["liquidity_usd"]) if p["fdv"]), None)
    return {
        "source": "dexscreener_v1",
        "pairs_count": len(pools),
        "liquidity_usd": round(total_liq, 2),
        "volume_24h_usd": round(sum(p["volume_24h_usd"] for p in pools), 2),
        "price_usd": best["price_usd"],
        "fdv_usd": fdv,
        "largest_pool_share": round(best["liquidity_usd"] / total_liq, 4) if total_liq > 0 else None,
        "pools": pools,
    }


def pool_price_witness(dx: dict[str, Any] | None, tol: float = POOL_PRICE_TOL) -> dict[str, Any]:
    """TS-0 for DEX tokens: distinct pools (with >= $50k each) must agree; one pool read by two indexers is one source."""
    pools = [p for p in (dx or {}).get("pools") or [] if p.get("pool") and p.get("price_usd") and p["liquidity_usd"] >= 50_000]
    uniq = {p["pool"]: p for p in pools}
    if len(uniq) < 2:
        return {"verdict": "SINGLE_POOL_UNRESOLVED", "distinct_pools": len(uniq), "gap": None}
    top = sorted(uniq.values(), key=lambda p: -p["liquidity_usd"])[:2]
    a, b = top[0]["price_usd"], top[1]["price_usd"]
    gap = abs(a - b) / ((a + b) / 2.0)
    return {"verdict": "POOL_WITNESS_VERIFIED" if gap <= tol else "POOL_CONFLICT", "distinct_pools": len(uniq),
            "gap": round(gap, 5), "pools": [{k: p[k] for k in ("pool", "dex", "price_usd", "liquidity_usd")} for p in top]}


def veto_check(
    symbol: str,
    address: str | None = None,
    chain_id: str = "1",
    *,
    getter: Callable[[str], Any] = _http_json,
    ttl_s: float = 1800.0,
    strict: bool = False,
) -> dict[str, Any]:
    """Run the hard safety veto. Fail-closed on any missing source, missing critical field, or policy breach."""
    meta = VETTED_TOKEN_CONTRACTS.get(symbol.upper(), {})
    addr = (address or meta.get("address") or "").strip().lower()
    cid = chain_id or meta.get("chain_id", "1")
    if not addr:
        return {"symbol": symbol, "address": None, "allowed": False, "verdict": "VETOED_FAIL_CLOSED",
                "reasons": ["missing_contract_address"], "sources_verified": 0, "paper_only": True}

    cache_key = f"{cid}:{addr}:{int(strict)}"
    if getter is _http_json and cache_key in _VETO_CACHE:
        ts, cached = _VETO_CACHE[cache_key]
        if time.time() - ts < ttl_s:
            return cached

    dx = fetch_dexscreener(addr, getter=getter)
    lp = {p["pool"] for p in (dx or {}).get("pools") or [] if p.get("pool")}
    gp = fetch_goplus(addr, cid, getter=getter, lp_pools=lp)
    hp = fetch_honeypot_is(addr, cid, getter=getter)

    missing: list[str] = []
    breach: list[str] = []
    sec_sources = [s["source"] for s in (gp, hp) if s is not None]
    if len(sec_sources) < 2:
        missing.append(f"insufficient_security_sources:{len(sec_sources)}_of_2")

    if gp is not None:
        for k in ("buy_tax", "sell_tax", "is_open_source", "is_mintable"):
            if gp[k] is None:
                missing.append(f"goplus:missing_{k}")
        if gp["is_honeypot"]:
            breach.append("goplus:is_honeypot")
        if (gp["buy_tax"] or 0) > MAX_TAX or (gp["sell_tax"] or 0) > MAX_TAX:
            breach.append(f"goplus:high_tax(buy={gp['buy_tax']},sell={gp['sell_tax']})")
        if gp["is_open_source"] is False:
            breach.append("goplus:not_open_source")
        if gp["is_mintable"]:
            breach.append("goplus:mintable_supply")
        for k, v in gp["authority"].items():
            if v:
                breach.append(f"goplus:{k}")
            elif v is None and strict:
                missing.append(f"goplus:missing_{k}")
        conc = gp["holder_concentration"]
        if conc is None:
            if strict:
                missing.append("goplus:missing_holders")
        elif conc["top1_pct"] > MAX_SINGLE_HOLDER_PCT or conc["top10_pct"] > MAX_TOP10_HOLDER_PCT:
            breach.append(f"goplus:holder_concentration(top1={conc['top1_pct']},top10={conc['top10_pct']})")

    if hp is not None:
        if not hp["simulation_success"]:
            breach.append("honeypot_is:evm_simulation_failed")
        if hp["is_honeypot"]:
            breach.append("honeypot_is:is_honeypot")
        if hp["buy_tax"] is None or hp["sell_tax"] is None:
            missing.append("honeypot_is:missing_tax")
        elif hp["buy_tax"] > MAX_TAX or hp["sell_tax"] > MAX_TAX:
            breach.append(f"honeypot_is:high_tax(buy={hp['buy_tax']:.3f},sell={hp['sell_tax']:.3f})")
        if hp["is_open_source"] is None:
            missing.append("honeypot_is:missing_open_source")
        elif not hp["is_open_source"]:
            breach.append("honeypot_is:not_open_source")

    liq_usd = (dx or {}).get("liquidity_usd") or 0.0
    if dx is None:
        missing.append("dexscreener:unavailable")
    elif liq_usd < MIN_LIQUIDITY_USD:
        breach.append(f"dexscreener:insufficient_liquidity({liq_usd:.0f}<{MIN_LIQUIDITY_USD:.0f})")
    fdv = (dx or {}).get("fdv_usd")
    if fdv and liq_usd > 0 and fdv / liq_usd > MAX_FDV_TO_LIQUIDITY:
        breach.append(f"dexscreener:fdv_to_liquidity({fdv / liq_usd:.0f}>{MAX_FDV_TO_LIQUIDITY:.0f})")

    reasons = breach + missing
    allowed = not reasons
    verdict = "ELIGIBLE_PAPER_TOKEN" if allowed else ("VETOED_SECURITY" if breach else "VETOED_FAIL_CLOSED")
    res = {
        "symbol": symbol.upper(),
        "address": addr,
        "chain_id": cid,
        "allowed": allowed,
        "verdict": verdict,
        "reasons": reasons,
        "strict": strict,
        "sources_verified": len(sec_sources) + (1 if dx is not None else 0),
        "security_sources": sec_sources,
        "goplus": gp,
        "honeypot_is": hp,
        "dexscreener": {k: v for k, v in (dx or {}).items() if k != "pools"} if dx else None,
        "pool_witness": pool_price_witness(dx),
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
    }
    if getter is _http_json:
        _VETO_CACHE[cache_key] = (time.time(), res)
    return res


# ---------------- M33.1-M33.3 live discovery funnel ----------------
def _age_days(created_iso: str | None, now: datetime) -> float | None:
    if not created_iso:
        return None
    try:
        t = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (now - t).total_seconds() / 86400.0


def discover_candidates(getter: Callable[[str], Any] = _http_json, *, now: datetime | None = None) -> dict[str, Any]:
    """GeckoTerminal trending ETH pools + DexScreener boosted ethereum tokens -> funnel-filtered candidates."""
    now = now or datetime.now(timezone.utc)
    raw: list[dict[str, Any]] = []
    gt = getter(GECKO_TRENDING_URL)
    for p in (gt or {}).get("data") or [] if isinstance(gt, dict) else []:
        at = p.get("attributes") or {}
        base_id = ((((p.get("relationships") or {}).get("base_token") or {}).get("data") or {}).get("id")) or ""
        addr = base_id.split("_", 1)[-1].lower() if base_id.startswith("eth_") else None
        tx = (at.get("transactions") or {}).get("h24") or {}
        raw.append({"address": addr, "symbol": str(at.get("name") or "").split(" / ")[0].strip().upper()[:16],
                    "pool": str(at.get("address") or "").lower(), "source": "geckoterminal_trending",
                    "pool_age_days": _age_days(at.get("pool_created_at"), now),
                    "volume_24h_usd": _f((at.get("volume_usd") or {}).get("h24")), "liquidity_usd": _f(at.get("reserve_in_usd")),
                    "fdv_usd": _f(at.get("fdv_usd")), "price_change_h6_pct": _f((at.get("price_change_percentage") or {}).get("h6")),
                    "buys_24h": tx.get("buys"), "sells_24h": tx.get("sells")})
    boosts = getter(DEXS_BOOSTS_URL)
    boosted_eth = [b for b in boosts if isinstance(b, dict) and b.get("chainId") == "ethereum"] if isinstance(boosts, list) else []
    seen = {r["address"] for r in raw if r["address"]}
    for b in boosted_eth[:10]:
        addr = str(b.get("tokenAddress") or "").lower()
        if addr and addr not in seen:
            raw.append({"address": addr, "symbol": None, "pool": None, "source": "dexscreener_boost", "pool_age_days": None,
                        "volume_24h_usd": None, "liquidity_usd": None, "fdv_usd": None})
            seen.add(addr)
    passed, rejected = [], []
    for r in raw:
        why = []
        if not r["address"]:
            why.append("no_eth_base_token")
        if r["pool_age_days"] is None or r["pool_age_days"] < MIN_POOL_AGE_DAYS:
            why.append(f"pool_age<{MIN_POOL_AGE_DAYS:.0f}d_or_unknown")
        if (r["volume_24h_usd"] or 0) < MIN_VOLUME_24H_USD:
            why.append("volume_24h<250k_or_unknown")
        if (r["liquidity_usd"] or 0) < MIN_LIQUIDITY_USD:
            why.append("liquidity<100k_or_unknown")
        (rejected if why else passed).append({**r, "funnel_reasons": why})
    return {"raw_count": len(raw), "gecko_trending": sum(1 for r in raw if r["source"] == "geckoterminal_trending"),
            "dexscreener_boosted_eth": len(boosted_eth), "passed": passed, "rejected": rejected,
            "feeds_ok": {"geckoterminal": isinstance(gt, dict), "dexscreener_boosts": isinstance(boosts, list)}}


def discovery_rank_score(c: dict[str, Any]) -> float:
    """Ranking heuristic only (no edge claim): 24h buy pressure, turnover, 6h momentum, each bounded to [-1, 1]."""
    b, s = float(c.get("buys_24h") or 0), float(c.get("sells_24h") or 0)
    pressure = (b - s) / (b + s) if b + s else 0.0
    turnover = math.tanh(math.log1p((c.get("volume_24h_usd") or 0) / max(1.0, c.get("liquidity_usd") or 1.0)) - 1.0)
    mom = math.tanh((c.get("price_change_h6_pct") or 0.0) / 10.0)
    return round(0.4 * pressure + 0.3 * turnover + 0.3 * mom, 4)


def run_discovery_funnel(getter: Callable[[str], Any] = _http_json, *, max_vet: int = 8,
                         now: datetime | None = None) -> dict[str, Any]:
    disc = discover_candidates(getter, now=now)
    ranked = sorted(disc["passed"], key=lambda c: -discovery_rank_score(c))[:max_vet]
    vetted = []
    for c in ranked:
        v = veto_check(c["symbol"] or c["address"][:8], c["address"], getter=getter, strict=True)
        vetted.append({**v, "discovery": {k: c.get(k) for k in ("source", "pool", "pool_age_days", "volume_24h_usd",
                                                                   "liquidity_usd", "fdv_usd")},
                       "discovery_rank_score": discovery_rank_score(c),
                       "paper_tradable": bool(v["allowed"] and v["pool_witness"]["verdict"] == "POOL_WITNESS_VERIFIED")})
    return {**{k: disc[k] for k in ("raw_count", "gecko_trending", "dexscreener_boosted_eth", "feeds_ok")},
            "funnel_passed": len(disc["passed"]), "funnel_rejected": len(disc["rejected"]),
            "funnel_rejected_sample": [{k: r.get(k) for k in ("symbol", "address", "funnel_reasons")} for r in disc["rejected"][:12]],
            "vetted": vetted}


def export_token_safety_snapshot(root: Path | None = None, *, getter: Callable[[str], Any] = _http_json) -> dict[str, Any]:
    base = (root or Path(__file__).resolve().parents[2]).resolve()
    static = [veto_check(sym, getter=getter) for sym in ("UNI", "LINK", "AAVE")]
    funnel = run_discovery_funnel(getter)
    # Deterministic fail-closed canary (single source, bad tax): must always stay vetoed.
    canary = veto_check(
        "RUG_TEST",
        "0x000000000000000000000000000000000000dead",
        getter=lambda u: {"result": {"0x000000000000000000000000000000000000dead": {"is_honeypot": "1", "buy_tax": "0.45", "sell_tax": "0.99", "is_open_source": "0", "is_mintable": "1"}}} if "goplus" in u else None,
    )
    tokens = static + funnel["vetted"] + [canary]
    eligible = sorted((t for t in funnel["vetted"] if t["paper_tradable"]), key=lambda t: -t["discovery_rank_score"])
    snap = {
        "schema": "ahos.token_safety_live.v2",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "spec": "TRADING_SKILLS_v2 §4 + M13.6 + M33.1-M33.7 + TS-4",
        "funnel_rules": {"min_pool_age_days": MIN_POOL_AGE_DAYS, "min_volume_24h_usd": MIN_VOLUME_24H_USD,
                         "min_liquidity_usd": MIN_LIQUIDITY_USD, "max_tax": MAX_TAX,
                         "max_single_holder_pct": MAX_SINGLE_HOLDER_PCT, "max_top10_holder_pct": MAX_TOP10_HOLDER_PCT,
                         "max_fdv_to_liquidity": MAX_FDV_TO_LIQUIDITY, "pool_price_tol": POOL_PRICE_TOL},
        "discovery": {k: v for k, v in funnel.items() if k != "vetted"},
        "eligible_count": sum(1 for t in tokens if t["allowed"]),
        "vetoed_count": sum(1 for t in tokens if not t["allowed"]),
        "vetoed_security_count": sum(1 for t in tokens if t["verdict"] == "VETOED_SECURITY"),
        "paper_tradable_dynamic": [{"symbol": t["symbol"], "address": t["address"], "rank_score": t["discovery_rank_score"],
                                    "pool": (t.get("discovery") or {}).get("pool")} for t in eligible],
        "tokens": tokens,
        "honesty_note": "Discovery rank is a heuristic, not an edge. Eligible means 'not vetoed', never 'buy'.",
    }
    out = base / SNAPSHOT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snap


# ---------------- PB_TOKEN desk feed ----------------
def load_eligible_paper_tokens(root: Path, *, max_age_h: float = 6.0, max_n: int = 2) -> list[dict[str, Any]]:
    """Dynamic tokens the paper trader may consider: only from a fresh snapshot (stale -> none, fail closed)."""
    try:
        snap = json.loads((Path(root) / SNAPSHOT_REL).read_text(encoding="utf-8"))
        age = (datetime.now(timezone.utc) - datetime.strptime(snap["generated_at"], "%Y-%m-%dT%H:%M:%SZ")
               .replace(tzinfo=timezone.utc)).total_seconds() / 3600
    except Exception:
        return []
    if age > max_age_h:
        return []
    return [t for t in snap.get("paper_tradable_dynamic") or [] if t.get("address") and t.get("pool")][:max_n]


def dex_paper_quote(token: dict[str, Any], getter: Callable[[str], Any] = _http_json) -> tuple[dict[str, Any], dict[str, Any]]:
    """(quote, witness) for a discovered token: GeckoTerminal 5m OHLCV of its main pool + distinct-pool price witness."""
    pool, addr = token["pool"], token["address"]
    o = getter(f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool}/ohlcv/minute?aggregate=5&limit=288")
    rows = (((o or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or [] if isinstance(o, dict) else []
    rows = sorted(r for r in rows if isinstance(r, list) and len(r) >= 6)
    dx = fetch_dexscreener(addr, getter=getter)
    pw = pool_price_witness(dx)
    src = f"geckoterminal:{pool}"
    if not rows:
        return ({"price": None, "source": src, "freshness": "UNAVAILABLE"},
                {"verdict": "UNRESOLVED", "source_a": src, "price_a": None, "source_b": None, "price_b": None, "gap": None})
    last = rows[-1]
    mt = datetime.fromtimestamp(int(last[0]), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    quote = {"price": float(last[4]), "source": src, "market_time": mt, "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "ohlcv_5m": [[float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])] for r in rows],
             "ohlcv_5m_ts": [int(r[0]) for r in rows], "token_address": addr, "dex_pool": pool, "freshness": "LIVE"}
    others = sorted((p for p in (dx or {}).get("pools") or [] if p.get("pool") and p["pool"] != pool
                     and p.get("price_usd") and p["liquidity_usd"] >= 50_000), key=lambda p: -p["liquidity_usd"])
    if not others:
        verdict, gap, other = "UNRESOLVED", None, {}
    else:
        other = others[0]
        gap = abs(quote["price"] - other["price_usd"]) / ((quote["price"] + other["price_usd"]) / 2.0)
        verdict = "VERIFIED" if gap <= POOL_PRICE_TOL else "CONFLICT"
    wit = {"verdict": verdict, "source_a": src, "price_a": quote["price"],
           "source_b": f"dexscreener:{other.get('dex')}:{other.get('pool')}" if other else None,
           "price_b": other.get("price_usd"), "gap": round(gap, 5) if gap is not None else None, "tolerance": POOL_PRICE_TOL,
           "pair": "POOL-POOL", "diagnostics": {"pool_witness": pw["verdict"], "distinct_pools": pw["distinct_pools"]}}
    return quote, wit
