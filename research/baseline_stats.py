#!/usr/bin/env python3
"""AHOS research — baseline / lift analysis (Wave-6 doc G implementation).
LAW: never evaluate a signal without a baseline. Rates carry Wilson CIs; sample guards are hard-coded
and NOT tunable at call time. Verdict INSUFFICIENT_DATA is the expected honest output on young cohorts.
Join semantics: features as_of a FIXED pre-outcome timestamp (default T0+1h) vs labels — leakage law:
labels never touch feature computation; this module only JOINs frozen vectors to labels.
"""
from __future__ import annotations
import json, math, sqlite3, sys
from pathlib import Path
from datetime import datetime, timezone

MIN_N_STRATUM = 200      # F §5 / G §2 — pre-registered guards (not user-settable at runtime)
MIN_POSITIVES = 20
JOIN_OFFSET = 3600.0     # features measured at T0+1h (after at least the s+15m slot can exist)


def wilson_ci(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def rates_and_lift(k1: int, n1: int, k0: int, n0: int) -> dict:
    """conditioned (k1,n1) vs baseline (k0,n0)."""
    out = {"n_conditioned": n1, "pos_conditioned": k1, "n_baseline": n0, "pos_baseline": k0}
    if n1 == 0 or n0 == 0:
        out.update(verdict="INSUFFICIENT_DATA", reason="empty cell")
        return out
    p1, p0 = k1 / n1, k0 / n0
    c1 = wilson_ci(k1, n1)
    c0 = wilson_ci(k0, n0)
    out.update(rate_conditioned=p1, ci_conditioned=list(c1), rate_baseline=p0, ci_baseline=list(c0),
               lift=(p1 / p0 if p0 > 0 else None),
               precision=p1 if n1 else None,  # predicted-positive precision == conditioned rate
               )
    guards = []
    if n0 < MIN_N_STRATUM or n1 < MIN_N_STRATUM:
        guards.append(f"n<{MIN_N_STRATUM}")
    if k0 < MIN_POSITIVES or k1 < MIN_POSITIVES:
        guards.append(f"positives<{MIN_POSITIVES}")
    out["verdict"] = "INSUFFICIENT_DATA" if guards else "DESCRIPTIVE_OK"
    if guards:
        out["reason"] = ";".join(guards)
    return out


# ---- Wave-7: conjunctive (multi-feature) cells ---------------------------------------------
# Composite H-cards (H14/H15/H18/H20) are conjunctions over DISTINCT feature keys, which a single
# feature_vector row can never satisfy (key='a' AND key='b' on one row is impossible). Clauses are
# parameterized (values bound, ops whitelisted) — string interpolation of user data prohibited.
_ALLOWED_OPS = {">", ">=", "<", "<=", "=", "!="}
_KEY_RE = __import__("re").compile(r"^[a-z0-9_]+$")


def _validate_clause(clause: dict) -> tuple[str, str, float]:
    key, op, value = clause.get("key"), clause.get("op"), clause.get("value")
    if not isinstance(key, str) or not _KEY_RE.match(key):
        raise ValueError(f"clause key invalid: {key!r}")
    if op not in _ALLOWED_OPS:
        raise ValueError(f"clause op not whitelisted: {op!r}")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"clause value must be numeric: {value!r}")
    return key, op, float(value)


def evaluate_conjunction(conn: sqlite3.Connection, clauses: list[dict],
                         horizon: str, event_class: str,
                         join_offset: float = JOIN_OFFSET) -> dict:
    """clauses: pre-registered [{key, op, value}] — token qualifies iff ALL clauses hold on its
    frozen feature vector at as_of = first_seen + join_offset (leakage law identical to
    evaluate_condition). Baseline = all RESOLVED candidates with a label (same as single cells)."""
    validated = [_validate_clause(c) for c in clauses]
    if not validated:
        raise ValueError("conjunction requires >=1 clause")
    q_base = """
        SELECT ol.hit FROM outcome_label ol
        JOIN observation_state s ON s.token_id=ol.token_id
        WHERE ol.horizon=? AND ol.event_class=? AND s.state='RESOLVED'"""
    base = conn.execute(q_base, (horizon, event_class)).fetchall()
    n0 = len(base); k0 = sum(r["hit"] for r in base)
    joins, where, offsets, cond_params = [], [], [], []
    for i, (key, op, value) in enumerate(validated):
        a = f"fv{i}"
        joins.append(f"""JOIN feature_vector {a} ON {a}.token_id=ol.token_id
           AND {a}.as_of_ts = s.first_seen_ts + ?""")
        offsets.append(join_offset)
        where.append(f"{a}.key=? AND {a}.value_num{op}?")
        cond_params.extend([key, value])
    q_cond = f"""
        SELECT ol.hit FROM outcome_label ol
        JOIN observation_state s ON s.token_id=ol.token_id AND s.state='RESOLVED'
        {' '.join(joins)}
        WHERE ol.horizon=? AND ol.event_class=? AND {' AND '.join(where)}"""
    cond = conn.execute(q_cond, (*offsets, horizon, event_class, *cond_params)).fetchall()
    n1 = len(cond); k1 = sum(r["hit"] for r in cond)
    res = rates_and_lift(k1, n1, k0, n0)
    res.update(horizon=horizon, event_class=event_class,
               condition={"conjunction": clauses}, join_offset=join_offset)
    return res


def evaluate_condition(conn: sqlite3.Connection, condition_sql_where: str,
                       horizon: str, event_class: str,
                       join_offset: float = JOIN_OFFSET) -> dict:
    """condition_sql_where: SQL fragment over feature_vector rows (fv alias), e.g.
    \"key='liquidity_growth_1h' AND value_num>0.10\". Baseline = all resolved candidates with a label."""
    q_base = """
        SELECT ol.hit FROM outcome_label ol
        JOIN observation_state s ON s.token_id=ol.token_id
        WHERE ol.horizon=? AND ol.event_class=? AND s.state='RESOLVED'"""
    base = conn.execute(q_base, (horizon, event_class)).fetchall()
    n0 = len(base); k0 = sum(r["hit"] for r in base)
    q_cond = f"""
        SELECT ol.hit FROM outcome_label ol
        JOIN observation_state s ON s.token_id=ol.token_id AND s.state='RESOLVED'
        JOIN feature_vector fv ON fv.token_id=ol.token_id
           AND fv.as_of_ts = s.first_seen_ts + ?
        WHERE ol.horizon=? AND ol.event_class=? AND {condition_sql_where}"""
    cond = conn.execute(q_cond, (join_offset, horizon, event_class)).fetchall()
    n1 = len(cond); k1 = sum(r["hit"] for r in cond)
    res = rates_and_lift(k1, n1, k0, n0)
    res.update(horizon=horizon, event_class=event_class, condition=condition_sql_where,
               join_offset=join_offset)
    return res


def scan(sqlite_path: str, cells: list[dict], out_path: Path | None = None) -> dict:
    """cells: pre-registered [{condition, horizon, event_class, cell_id}] — each cell is logged
    into the search-space registry (doc H §2) by the caller/CLI."""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    results = []
    for cell in cells:
        if "clauses" in cell:  # Wave-7 conjunctive cell (pre-registered composites)
            r = evaluate_conjunction(conn, cell["clauses"], cell["horizon"], cell["event_class"],
                                     cell.get("join_offset", JOIN_OFFSET))
        else:
            r = evaluate_condition(conn, cell["condition"], cell["horizon"], cell["event_class"],
                                   cell.get("join_offset", JOIN_OFFSET))
        r["cell_id"] = cell["cell_id"]
        results.append(r)
    summary = {"ts": datetime.now(timezone.utc).isoformat(), "cells": len(results),
               "verdicts": {r["verdict"] for r in results},
               "guards": {"min_n": MIN_N_STRATUM, "min_pos": MIN_POSITIVES},
               "results": results}
    summary["verdicts"] = sorted(summary["verdicts"])
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    conn.close()
    return summary


def register_search_cells(cells: list[dict], batch_id: str,
                          registry_path: str | Path | None = None):
    from config.paths import get_research_dir
    p = Path(registry_path) if registry_path else (get_research_dir() / "SEARCH_SPACE_REGISTRY.json")
    reg = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"batches": [], "cells": []}
    reg["batches"].append({"batch_id": batch_id, "n_cells": len(cells),
                           "ts": datetime.now(timezone.utc).isoformat()})
    for c in cells:
        reg["cells"].append({"batch_id": batch_id, **c})
    p.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(reg["cells"])


if __name__ == "__main__":
    from config.paths import get_discovery_db_path, get_research_dir
    # REPORT-mode scan of a pre-registered empty-cell demo on the current store (honest INSUFFICIENT_DATA)
    demo_cells = [
        {"cell_id": "B1-lg1h-pos-24h-50", "condition": "key='liquidity_growth_1h' AND value_num>0.10",
         "horizon": "24h", "event_class": "+50%"},
        {"cell_id": "B1-bsi-pos-24h-50", "condition": "key='buy_sell_imbalance_1h' AND value_num>0.15",
         "horizon": "24h", "event_class": "+50%"},
    ]
    store = get_discovery_db_path()
    out = get_research_dir() / "reports" / "baseline_stats_latest.json"
    summary = scan(store, demo_cells, out)
    register_search_cells(demo_cells, batch_id="B1-pre-registered")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    for r in summary["results"]:
        print(f"  {r['cell_id']}: {r['verdict']} base {r['pos_baseline']}/{r['n_baseline']} "
              f"cond {r['pos_conditioned']}/{r['n_conditioned']} lift={r.get('lift')}")
