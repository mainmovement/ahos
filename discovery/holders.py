#!/usr/bin/env python3
"""AHOS Holder/Whale snapshot adapter (Phase-3 path, SOL first).
getTokenLargestAccounts via PAL rpc_sol chain. Current ground truth (wave-6 probes):
public free SOL RPC endpoints rate-limit/forbid this method → attempts record error_state rows,
NEVER fake concentrations. Feature computation guards on real snapshot rows.
"""
from __future__ import annotations
import json, sqlite3, time
from . import pal as pal_mod
from . import observations as obs


def snapshot_token(conn: sqlite3.Connection, token_id: str, address: str, now: float,
                   pal_client=None, chain_capability: str = "rpc_sol") -> dict:
    """Attempt one holder snapshot. Returns status dict; always leaves an auditable row."""
    p = pal_client or pal_mod.PAL()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts",
                       "params": [address]}).encode()
    last_env = None
    for name in (p.capabilities.get(chain_capability, {}).get("chain") or []):
        cli = p.clients[name]
        if cli.breaker.open:
            continue
        import urllib.request
        env = {"provider_id": cli.name, "endpoint": cli.spec["base_url"], "ts": now}
        req = urllib.request.Request(cli.spec["base_url"], data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "ahos-discovery/1.1"})
        if not cli.bucket.wait_for(timeout=5.0):
            env.update(result=None, error={"kind": "rate_starved"})
            last_env = env
            continue
        try:
            with urllib.request.urlopen(req, timeout=cli.timeout) as r:
                payload = json.loads(r.read())
            cli.breaker.on_success()
            env.update(result=(payload.get("result") or {}).get("value"),
                       error=(payload.get("error")))
            last_env = env
            if env["result"]:
                break
        except Exception as e:
            cli.breaker.on_failure()
            env.update(result=None, error={"kind": type(e).__name__, "message": str(e)[:200]})
            last_env = env
    # persist attempt (success OR failure), honest either way
    src = (last_env or {}).get("provider_id", "rpc_sol:none")
    accounts = (last_env or {}).get("result")
    if accounts:
        raw_sha = obs.store_raw(conn, src, (last_env or {}).get("endpoint", "?"), now, 200,
                                {"accounts": accounts})
        amounts = [float(a.get("amount", 0) or 0) for a in accounts]
        total = sum(amounts)
        top10 = sum(amounts[:10]) / total if total > 0 else None
        top20 = sum(amounts[:20]) / total if total > 0 else None
        conn.execute(
            """INSERT INTO holder_snapshot(token_id,ts,source,top_accounts_json,top10_share,top20_share,raw_ref)
               VALUES (?,?,?,?,?,?,?)""",
            (token_id, now, src, json.dumps(accounts), top10, top20, raw_sha))
        return {"ok": True, "top10_share": top10, "top20_share": top20, "n_accounts": len(accounts)}
    conn.execute(
        """INSERT INTO holder_snapshot(token_id,ts,source,error_state)
           VALUES (?,?,?,?)""",
        (token_id, now, src, json.dumps((last_env or {}).get("error",
                                        {"kind": "no_provider_attempted"}))))
    return {"ok": False, "error": (last_env or {}).get("error")}


def top_share_at(conn: sqlite3.Connection, token_id: str, as_of: float,
                 column: str = "top10_share"):
    """Latest snapshot share ≤ as_of (leakage-safe). Returns (value, ts) or (None, None)."""
    if column not in ("top10_share", "top20_share"):
        raise ValueError(column)
    r = conn.execute(
        f"""SELECT {column} v, ts FROM holder_snapshot
            WHERE token_id=? AND ts<=? AND {column} IS NOT NULL ORDER BY ts DESC LIMIT 1""",
        (token_id, as_of)).fetchone()
    return (r["v"], r["ts"]) if r else (None, None)


def top20_net_flow(conn: sqlite3.Connection, token_id: str, as_of: float, lookback: float = 3600):
    """Signed relative change of top-20 aggregate vs the latest snapshot ≥ lookback earlier."""
    now_row = conn.execute(
        """SELECT ts, top20_share FROM holder_snapshot
           WHERE token_id=? AND ts<=? AND top20_share IS NOT NULL ORDER BY ts DESC LIMIT 1""",
        (token_id, as_of)).fetchone()
    prev_row = conn.execute(
        """SELECT ts, top20_share FROM holder_snapshot
           WHERE token_id=? AND ts<=? AND top20_share IS NOT NULL
             AND ts<=(SELECT ts FROM holder_snapshot WHERE token_id=? AND top20_share IS NOT NULL
                      ORDER BY ts DESC LIMIT 1) - ?
           ORDER BY ts DESC LIMIT 1""",
        (token_id, as_of, token_id, lookback)).fetchone()
    if not now_row or not prev_row or prev_row["top20_share"] == 0:
        return None, None
    return (now_row["top20_share"] / prev_row["top20_share"] - 1.0,
            max(now_row["ts"], prev_row["ts"]))
