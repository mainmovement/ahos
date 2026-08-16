#!/usr/bin/env python3
"""AHOS STEP 9 — PAPER opportunity ranking (rank-first; NO numeric score, NO probability).
Law (Mission §10 / OPPORTUNITY_SCORE_DESIGN v0.1 validation path): until E-01 calibration passes the
research gate, surfaces show RANKS + plain-language evidence bullets. The security verdict bounds
every ranking (veto → excluded with reason; unknown-critical → never top bucket).
Ordering heuristic is documented & versioned (engine_version) — NOT a learned model.
"NO OPPORTUNITY" is a first-class successful output (empty ranked list is valid).
"""
from __future__ import annotations
import json, sqlite3
from . import feature_store

ENGINE_VERSION = "ranker_v0.1_rank-first"
MIN_FEATURES_FOR_RANK = 4
TOP_BUCKET_MAX_COVERAGE_GAP = 0.5   # if security coverage below 50% → cannot enter RANKED-TOP


def _gate_state(conn, token_id, as_of):
    r = conn.execute(
        "SELECT verdict, coverage FROM gate_summary WHERE token_id=? AND ts<=? ORDER BY ts DESC LIMIT 1",
        (token_id, as_of)).fetchone()
    if r:
        return r["verdict"], r["coverage"]
    return None, None


def rank(conn: sqlite3.Connection, as_of: float, limit: int = 25) -> dict:
    """Returns {as_of, engine_version, ranked:[…], excluded:[…], summary}. Pure from stored rows."""
    tokens = conn.execute(
        """SELECT t.token_id, t.symbol, t.chain_id, s.state, s.security_flagged, s.first_seen_ts
           FROM tokens t JOIN observation_state s ON s.token_id=t.token_id
           WHERE s.state IN ('OBSERVING','DISCOVERED')""").fetchall()
    ranked, excluded = [], []
    for t in tokens:
        tid = t["token_id"]
        gverdict, gcov = _gate_state(conn, tid, as_of)
        if gverdict == "SECURITY_VETO" or t["security_flagged"]:
            excluded.append({"token_id": tid, "symbol": t["symbol"],
                             "reason": "SECURITY_VETO", "layer": "security_gate"})
            continue
        feats = feature_store.compute_features(conn, tid, as_of)
        coverage_n = len(feats)
        if coverage_n < MIN_FEATURES_FOR_RANK:
            excluded.append({"token_id": tid, "symbol": t["symbol"],
                             "reason": f"insufficient_features({coverage_n}<{MIN_FEATURES_FOR_RANK})",
                             "layer": "feature_store"})
            continue
        # ---- documented ordering heuristic (NOT a score): evidence counting with bounds ----
        bullets, risks, invalidation = [], [], []
        pts = 0
        lg1 = feats.get("liquidity_growth_1h", {}).get("value_num")
        if lg1 is not None:
            if lg1 > 0.10: pts += 2; bullets.append(f"liquidity_growth_1h={lg1:+.2f}")
            elif lg1 < -0.25: risks.append(f"liquidity draining ({lg1:+.2f}/1h)")
        bsi = feats.get("buy_sell_imbalance_1h", {}).get("value_num")
        if bsi is not None:
            if bsi > 0.15: pts += 1; bullets.append(f"buy_sell_imbalance_1h={bsi:+.2f}")
            elif bsi < -0.15: risks.append(f"sellers dominate ({bsi:+.2f})")
        va = feats.get("volume_acceleration", {}).get("value_num")
        if va is not None:
            if va > 1.5: pts += 1; bullets.append(f"volume_acceleration={va:.2f}x")
            if va > 8: risks.append(f"extreme burst x{va:.1f} (manipulation watch)")
        l2v = feats.get("liquidity_to_volume_24h", {}).get("value_num")
        if l2v is not None and l2v < 0.05:
            risks.append(f"thin depth vs volume ({l2v:.3f})")
        elif l2v is not None and l2v >= 0.2:
            pts += 1; bullets.append(f"liquidity_to_volume_24h={l2v:.2f}")
        mdd = feats.get("max_drawdown_since_first_seen", {}).get("value_num")
        if mdd is not None and mdd > 0.8:
            risks.append(f"max drawdown {mdd:.0%} since first seen")
        age = feats.get("token_age_hours", {}).get("value_num")
        if age is not None and age < 1:
            risks.append(f"pool age {age*60:.0f}m — sniper window")
        sec_clear = feats.get("security_all_hard_veto_clear", {}).get("value_num")
        if sec_clear == 1.0: pts += 1; bullets.append("security checks clear (within coverage)")
        if gverdict == "PASS_WITH_UNKNOWN":
            risks.append(f"security coverage {gcov:.0%} — UNKNOWN checks remain")
        if gcov is not None and (1.0 - gcov) > TOP_BUCKET_MAX_COVERAGE_GAP:
            excluded.append({"token_id": tid, "symbol": t["symbol"], "reason": "security_coverage_gap",
                             "layer": "security_gate"})
            continue
        invalidation = ["liquidity_growth_1h < -0.30", "buy_sell_imbalance_1h < -0.25",
                        "any CRITICAL security check → TRUE"]
        ranked.append({"token_id": tid, "symbol": t["symbol"], "chain_id": t["chain_id"],
                       "evidence_count": pts, "feature_coverage": coverage_n,
                       "security_verdict": gverdict, "bullets": bullets[:5],
                       "risks": risks[:3], "invalidation": invalidation})
    ranked.sort(key=lambda r: (-r["evidence_count"], -r["feature_coverage"], r["token_id"]))
    out = []
    for i, r in enumerate(ranked[:limit], start=1):
        out.append({"rank": i, **r})
    result = {"as_of": as_of, "engine_version": ENGINE_VERSION, "ranked": out, "excluded": excluded,
              "note": "rank-first output; NO numeric probability — calibration pending E-01 research gate",
              "summary": f"{len(out)} ranked / {len(excluded)} excluded"
                         + (" — NO OPPORTUNITY is a valid empty result" if not out else "")}
    # persist snapshot (append on new as_of)
    for r in out:
        conn.execute(
            """INSERT INTO opportunity_rank(as_of_ts,token_id,rank,bullets_json,risks_json,invalidation_json,engine_version)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(as_of_ts,token_id) DO UPDATE SET rank=excluded.rank""",
            (as_of, r["token_id"], r["rank"], json.dumps(r["bullets"], ensure_ascii=False),
             json.dumps(r["risks"], ensure_ascii=False), json.dumps(r["invalidation"], ensure_ascii=False),
             ENGINE_VERSION))
    return result
