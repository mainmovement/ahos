#!/usr/bin/env python3
"""Paper Trading Lab — data access + monitoring helpers. ALL reads are as_of-honest:
the lab sees observation row r only if r.retrieved_ts <= decision/assessment time T.
Discovery store is read-only (ledger.open_discovery_ro). Security:
  - SOL: live RugCheck summary via discovery PAL → checks_from_rugcheck → evaluate (probe-verified provider).
  - EVM: no normalized check mapping exists (GoPlus raw fields → VETO registry semantics is
    council work, wave-8). Honest state: zero checks ⇒ PASS_WITH_UNKNOWN, coverage 0, flagged.
"""
from __future__ import annotations

from discovery.pal import PAL
from discovery.security_gate import checks_from_rugcheck, evaluate


def latest_observation(disc: "sqlite3.Connection", token_id: str, as_of: float) -> dict | None:
    r = disc.execute(
        """SELECT obs_id, retrieved_ts, price_usd, liquidity_usd, volume_24h,
                  txns_5m_buys, txns_5m_sells, market_cap
           FROM discovery_observations
           WHERE token_id=? AND retrieved_ts<=? AND error_state IS NULL
           ORDER BY retrieved_ts DESC LIMIT 1""", (token_id, as_of)).fetchone()
    return dict(r) if r else None


def obs_path(disc, token_id: str, t_from: float, t_to: float) -> list[dict]:
    rows = disc.execute(
        """SELECT retrieved_ts, price_usd, liquidity_usd FROM discovery_observations
           WHERE token_id=? AND retrieved_ts>? AND retrieved_ts<=? AND error_state IS NULL
             AND price_usd IS NOT NULL
           ORDER BY retrieved_ts""", (token_id, t_from, t_to)).fetchall()
    return [dict(r) for r in rows]


def security_now(pal: PAL, chain: str, address: str, now: float) -> dict:
    """Evaluate security AT decision time and return the full check evidence for the snapshot.
    No future timestamps can exist in a live call; the returned dict is the immutable evidence."""
    if chain == "solana":
        env = pal.call("security_sol", "summary", address=address, now=now)
        if env["availability"] != "OK":
            return {"verdict": "PASS_WITH_UNKNOWN", "veto_reasons": [], "coverage": 0.0,
                    "unknown_critical": ["ALL"], "provider": "rugcheck",
                    "state": "PROVIDER_DOWN", "attempts": env.get("attempts"),
                    "checks": []}
        checks = checks_from_rugcheck(env["payload"] or {})
        res = evaluate(checks)
        return {**res, "provider": "rugcheck", "endpoint": env.get("endpoint"),
                "raw_sha256": env.get("raw_sha256"), "checks": checks, "state": "LIVE_EVALUATED"}
    # EVM: no normalizer (recorded honestly)
    return {"verdict": "PASS_WITH_UNKNOWN", "veto_reasons": [], "coverage": 0.0,
            "unknown_critical": ["ALL_EVM_UNNORMALIZED"], "provider": None,
            "state": "NO_EVM_NORMALIZER", "checks": []}


def security_recheck(pal: PAL | None, chain: str, address: str, now: float,
                     baseline_security: dict) -> dict | None:
    """Re-evaluation for SECURITY_EVENT exits. SOL only; EVM rechecks return
    {'state':'UNKNOWN'} — never guessed (directive §11/§15). Provider down ⇒ UNKNOWN state."""
    if chain != "solana" or pal is None:
        return {"state": "UNKNOWN", "verdict": "UNKNOWN",
                "note": "EVM security recheck unavailable (no normalizer) — state UNKNOWN, not guessed"}
    env = pal.call("security_sol", "summary", address=address, now=now)
    if env["availability"] != "OK":
        return {"state": "UNKNOWN", "verdict": "UNKNOWN",
                "note": "rugcheck unavailable at recheck — preserved, monitoring continues"}
    checks = checks_from_rugcheck(env["payload"] or {})
    return {**evaluate(checks), "state": "LIVE_EVALUATED", "raw_sha256": env.get("raw_sha256")}
