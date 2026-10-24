"""Cross-surface unification audit (Stage 6 WP-5a).

Read-only invariant gate over the artifacts every surface (Python exporters,
Arena routes, Telegram replies) projects from. It never repairs anything: a
mismatch is reported as DRIFT so the owning writer gets fixed, not the audit.

Verdict law:
  UNIFIED_CLEAN   every check PASS
  DRIFT_DETECTED  at least one check FAIL
  INCOMPLETE      no FAIL, but at least one check UNKNOWN (input missing)

Known, *labeled* limitations are listed under ``open_gaps``; they are honest
disclosures, not drift, and do not change the verdict.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "ahos.unification_audit.v1"
OUT_REL = Path("reports") / "grok" / "M34" / "unification_audit.json"

PAPER = Path("reports") / "grok" / "PAPER"
STATUS_REL = PAPER / "paper_trader_status.json"
POSITIONS_REL = PAPER / "paper_positions.json"
TRADES_REL = PAPER / "paper_trades.jsonl"
AUDIT_REL = PAPER / "paper_trade_audit.json"
LEDGER_REL = Path("data") / "mission_ledger" / "mission_ledger.jsonl"
SOAK_DIR = Path("reports") / "grok" / "M13_SOAK"
CALENDAR_REL = Path("reports") / "grok" / "M19" / "macro_calendar.json"
NEWSROOM_REL = Path("reports") / "grok" / "M18" / "newsroom_snapshot.json"
TOKEN_REL = Path("reports") / "grok" / "M33" / "token_hunter_snapshot.json"
SCORECARD_REL = Path("reports") / "grok" / "M28" / "shadow_forward_scorecard.json"
BATCH_RELS = {
    "m28_walk_forward": Path("reports") / "grok" / "M28" / "walk_forward_snapshot.json",
    "batch4": Path("reports") / "grok" / "M28" / "batch4_research.json",
    "batch5": Path("reports") / "grok" / "M28" / "batch5_research.json",
}
RED_TEAM_REL = Path("reports") / "grok" / "M56" / "red_team_audit.json"
TOURNAMENT_REL = Path("reports") / "grok" / "M56" / "tournament_snapshot.json"
REGISTRY_REL = Path("strategy_lab") / "registry.json"
ORGANS_REL = Path("reports") / "grok" / "M57" / "whole_ahos_organ_evolution.json"
SCIENCE_REL = Path("reports") / "grok" / "M57" / "science_to_desk_snapshot.json"

CALENDAR_BANKS = ("FOMC", "EIA", "BOE", "BOJ", "ECB", "OPEC")
GOLD_MISSION = "M13-GOLD-PAPER"
GOLD_BANKROLL_USD = 10_000.0
PROMOTION_MIN_CLOSED = 30
MONEY_TOL = 0.01
PROMOTED_STATES = {"SHADOW_FORWARD_TEST", "PROMOTED", "LIVE"}

OPEN_GAPS = (
    "2026-2027 full-day exchange holidays are modeled in weekday_session_gate (holidays_modeled=true); early-close half-days still rely on the fresh-quote + VERIFIED witness gate.",
    "HOLD.flag count disclosure: 14 HOLD.flag files in the 3 active repos (ahos=10, ahos_arena=2, AHOS_Launcher=2) and 22 across all G:\\robat when counting archived/portable directories.",
    "Broker connectivity is NOT_VERIFIED: IBKR DU*/CCXT sandbox preflight runs negative controls only.",
    "Organ held_out_exam_score_pct values are curriculum constants (STATIC_UNVERIFIED), not exam output.",
    "M56 tournament contenders are FIXTURE_ILLUSTRATIVE returns; its 'DSR' is a haircut Sharpe, not a probability.",
    f"Edge is unproven until >= {PROMOTION_MIN_CLOSED} real OOS closed trades with DSR > 0.95 and PBO < 0.50.",
)


def _utc(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json(root: Path, rel: Path) -> Any:
    p = root / rel
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _check(cid: str, status: str, detail: Any, surfaces: list[str]) -> dict[str, Any]:
    return {"id": cid, "status": status, "detail": detail, "surfaces": surfaces}


def _pass_fail(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _ledger(root: Path) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    from architecture.mission.ledger import LedgerTamperError, MissionLedger

    path = root / LEDGER_REL
    if not path.is_file():
        return None, {"verdict": "MISSING"}
    led = MissionLedger(path)
    try:
        v = led.verify()
    except LedgerTamperError as exc:
        return None, {"verdict": "TAMPERED", "error": str(exc)[:200]}
    return led.entries(), v


def _paper_fills(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for e in entries:
        p = e.get("payload") if isinstance(e.get("payload"), dict) else {}
        if e.get("kind") == "DECISION" and p.get("type") == "PAPER_FILL":
            out[str(e.get("entry_hash"))] = p
    return out


def _net_open(events: list[tuple[str, str]]) -> Counter:
    net: Counter = Counter()
    for event, sym in events:
        if event == "OPEN":
            net[sym] += 1
        elif event == "CLOSE":
            net[sym] -= 1
    return Counter({k: v for k, v in net.items() if v})


def _paper_checks(root: Path, entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    status = _json(root, STATUS_REL)
    positions = _json(root, POSITIONS_REL)
    audit = _json(root, AUDIT_REL)
    rows = [r for r in _jsonl(root / TRADES_REL) if r.get("event") in ("OPEN", "CLOSE")]
    surfaces = [str(STATUS_REL), str(POSITIONS_REL), str(AUDIT_REL), str(TRADES_REL), str(LEDGER_REL)]
    if status is None or positions is None or audit is None or entries is None:
        missing = [n for n, v in (("status", status), ("positions", positions), ("audit", audit),
                                  ("ledger", entries)) if v is None]
        return [_check("paper.account", "UNKNOWN", {"missing": missing}, surfaces)]

    fills = _paper_fills(entries)
    closes_rows = sum(1 for r in rows if r["event"] == "CLOSE")
    closes_ledger = sum(1 for p in fills.values() if p.get("event") == "CLOSE")
    counts = {
        "status.closed_trades": int(status.get("closed_trades") or 0),
        "audit.trades.closes": int((audit.get("trades") or {}).get("closes") or 0),
        "paper_trades.jsonl CLOSE rows": closes_rows,
        "mission_ledger PAPER_FILL CLOSE": closes_ledger,
    }
    out = [_check("paper.closed_trades", _pass_fail(len(set(counts.values())) == 1), counts, surfaces)]

    net_rows = _net_open([(r["event"], str(r.get("symbol"))) for r in rows])
    net_ledger = _net_open([(str(p.get("event")), str(p.get("symbol"))) for p in fills.values()])
    sets = {
        "status.open_positions": sorted(status.get("open_positions") or {}),
        "paper_positions.positions": sorted(positions.get("positions") or {}),
        "paper_trades.jsonl net OPEN": sorted(net_rows),
        "mission_ledger net OPEN": sorted(net_ledger),
    }
    same = len({tuple(v) for v in sets.values()}) == 1 and all(v == 1 for v in net_rows.values())
    out.append(_check("paper.open_positions", _pass_fail(same), sets, surfaces))

    initial = float(status.get("initial_capital_usd") or 0.0)
    realized = float(status.get("realized_equity_usd") or 0.0)
    pnl = sum(float(r.get("realized_pnl_usd") or 0.0) for r in rows if r["event"] == "CLOSE")
    mtm = float(status.get("mark_to_market_equity_usd") or 0.0)
    unreal = float(status.get("unrealized_pnl_usd") or 0.0)
    eq_ok = abs(initial + pnl - realized) <= MONEY_TOL and abs(realized + unreal - mtm) <= MONEY_TOL
    out.append(_check("paper.equity", _pass_fail(eq_ok), {
        "initial_capital_usd": initial, "sum_close_realized_pnl_usd": round(pnl, 6),
        "realized_equity_usd": realized, "unrealized_pnl_usd": unreal,
        "mark_to_market_equity_usd": mtm, "tolerance_usd": MONEY_TOL,
    }, [str(STATUS_REL), str(TRADES_REL)]))

    unlinked: list[str] = []
    for r in rows:
        p = fills.get(str(r.get("ledger_hash")))
        if p is None or p.get("event") != r["event"] or p.get("symbol") != r.get("symbol"):
            unlinked.append(f"{r['event']}:{r.get('symbol')}@{r.get('ts')}")
    out.append(_check("paper.ledger_xref", _pass_fail(not unlinked),
                      {"fills_on_jsonl": len(rows), "fills_on_ledger": len(fills), "unlinked": unlinked},
                      [str(TRADES_REL), str(LEDGER_REL)]))

    pat = re.compile(r"PAPER_TRADER|paper_trades\.jsonl", re.I)
    ledger_refs = sum(1 for e in entries if pat.search(json.dumps(e, ensure_ascii=False)))
    refs = int((audit.get("mission_ledger") or {}).get("paper_trader_refs") or 0)
    out.append(_check("paper.audit_ledger_refs", _pass_fail(refs == ledger_refs),
                      {"audit.paper_trader_refs": refs, "ledger_entries_matching": ledger_refs},
                      [str(AUDIT_REL), str(LEDGER_REL)]))
    return out


def _gold_checks(root: Path, entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    soak = _json(root, SOAK_DIR / "soak_status.json")
    runlog = [r for r in _jsonl(root / SOAK_DIR / "soak_runlog.jsonl") if r.get("kind") == "cycle"]
    surfaces = [str(SOAK_DIR / "soak_status.json"), str(SOAK_DIR / "soak_runlog.jsonl"), str(LEDGER_REL)]
    if soak is None or entries is None:
        return [_check("gold.soak_witness", "UNKNOWN", {"soak_status": soak is not None,
                                                        "ledger": entries is not None}, surfaces)]
    last = soak.get("last_cycle") or {}
    state, reason, price = last.get("witness_state"), str(last.get("witness_reason") or ""), last.get("price_usd")
    contradictions: list[str] = []
    if state == "VERIFIED" and ("insufficient_independent_sources" in reason or price is None):
        contradictions.append("VERIFIED with a single-source reason or no price")
    if state != "VERIFIED" and price is not None:
        contradictions.append(f"{state} cycle carries a price")
    twin = next((r for r in reversed(runlog) if r.get("cycle") == last.get("cycle")), None)
    if twin is not None and (twin.get("witness_state") != state or twin.get("price_usd") != price):
        contradictions.append(
            f"soak_status cycle {last.get('cycle')} says {state}@{price} but runlog says "
            f"{twin.get('witness_state')}@{twin.get('price_usd')} ({twin.get('ts')})")
    out = [_check("gold.soak_witness", _pass_fail(not contradictions), {
        "last_cycle": {k: last.get(k) for k in ("ts", "cycle", "witness_state", "price_usd")},
        "runlog_last": {k: (runlog[-1] if runlog else {}).get(k) for k in ("ts", "cycle", "witness_state", "price_usd")},
        "contradictions": contradictions,
    }, surfaces)]

    states = [e for e in entries if e.get("kind") == "STATE"
              and (e.get("state") or {}).get("MISSION_ID") == GOLD_MISSION]
    cp = ((states[-1].get("state") or {}).get("CHECKPOINT") if states else None) or {}
    bankroll = cp.get("bankroll_usd") if isinstance(cp, dict) else None
    out.append(_check("gold.separate_10k_account",
                      "UNKNOWN" if bankroll is None else _pass_fail(float(bankroll) == GOLD_BANKROLL_USD),
                      {"ledger_checkpoint_bankroll_usd": bankroll, "expected_usd": GOLD_BANKROLL_USD,
                       "ledger_state_rows": len(states),
                       "note": "Gold soak is its own $10k paper account; it is never summed into the $100 paper trader."},
                      [str(LEDGER_REL)]))

    digests = sorted((root / SOAK_DIR).glob("*_digest.json"))
    latest = _json(root, digests[-1].relative_to(root)) if digests else None
    out.append(_check("gold.daily_digest",
                      "UNKNOWN" if latest is None else _pass_fail(latest.get("paper_only", True) is True),
                      {"latest": digests[-1].name if digests else None}, [str(SOAK_DIR)]))
    return out


def _evidence_checks(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cal = _json(root, CALENDAR_REL)
    if cal is None:
        out.append(_check("macro.calendar_6_banks", "UNKNOWN", "missing", [str(CALENDAR_REL)]))
    else:
        st = cal.get("status") or {}
        bad = {b: st.get(b) for b in CALENDAR_BANKS if not str(st.get(b) or "").startswith("OK")}
        out.append(_check("macro.calendar_6_banks", _pass_fail(not bad),
                          {"ok": len(CALENDAR_BANKS) - len(bad), "of": len(CALENDAR_BANKS), "not_ok": bad},
                          [str(CALENDAR_REL)]))

    news = _json(root, NEWSROOM_REL)
    if news is None:
        out.append(_check("news.two_source_corroboration", "UNKNOWN", "missing", [str(NEWSROOM_REL)]))
    else:
        clusters = [c for c in news.get("rssClusters") or [] if c.get("state") == "CORROBORATED"]
        thin = [c.get("topic") for c in clusters if len(set(c.get("independent_domains") or [])) < 2]
        out.append(_check("news.two_source_corroboration", _pass_fail(not thin),
                          {"corroborated_clusters_listed": len(clusters), "under_two_domains": thin,
                           "stats": news.get("stats")}, [str(NEWSROOM_REL)]))

    tok = _json(root, TOKEN_REL)
    if tok is None:
        out.append(_check("token.watch_invariants", "UNKNOWN", "missing", [str(TOKEN_REL)]))
    else:
        cands = tok.get("candidates") or []
        bad = []
        for c in cands:
            if c.get("state") == "PAPER_WATCH_ELIGIBLE" and (
                    len(set(c.get("corroborated_sources") or [])) < 2 or c.get("veto_reasons")
                    or c.get("steps_passed") != c.get("steps_total")):
                bad.append(c.get("symbol"))
        eligible = sum(1 for c in cands if c.get("state") == "PAPER_WATCH_ELIGIBLE")
        counts_ok = (tok.get("candidates_screened") == len(cands)
                     and tok.get("paper_watch_eligible_count") == eligible)
        out.append(_check("token.watch_invariants", _pass_fail(not bad and counts_ok),
                          {"eligible": eligible, "violations": bad, "counts_consistent": counts_ok},
                          [str(TOKEN_REL)]))
    return out


def _research_checks(root: Path, closed: int | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out_of_range: list[str] = []
    seen = 0
    for name, rel in BATCH_RELS.items():
        snap = _json(root, rel)
        for c in (snap or {}).get("candidates") or []:
            v = c.get("deflated_sharpe")
            if v is None:
                continue
            seen += 1
            if not 0.0 <= float(v) <= 1.0:
                out_of_range.append(f"{name}:{c.get('strategy_id')}={v}")
    tour = _json(root, TOURNAMENT_REL)
    tour_dsr = (tour or {}).get("leader_dsr")
    tour_labeled = bool((tour or {}).get("dsr_semantics"))
    if tour_dsr is not None and not 0.0 <= float(tour_dsr) <= 1.0 and not tour_labeled:
        out_of_range.append(f"tournament.leader_dsr={tour_dsr} (unlabeled haircut Sharpe)")
    out.append(_check("research.dsr_is_probability", _pass_fail(not out_of_range) if seen else "UNKNOWN",
                      {"candidates_checked": seen, "out_of_range": out_of_range,
                       "tournament_leader_dsr": tour_dsr, "tournament_dsr_semantics_labeled": tour_labeled},
                      [str(r) for r in BATCH_RELS.values()] + [str(TOURNAMENT_REL)]))

    b5 = _json(root, BATCH_RELS["batch5"])
    red = _json(root, RED_TEAM_REL)
    reg = _json(root, REGISTRY_REL)
    if b5 is None or red is None or reg is None:
        out.append(_check("research.batch5_registry_switch", "UNKNOWN",
                          {"batch5": b5 is not None, "red_team_audit": red is not None,
                           "registry": reg is not None}, [str(BATCH_RELS["batch5"]), str(RED_TEAM_REL), str(REGISTRY_REL)]))
        return out
    eligible = set(red.get("promotion_eligible") or [])
    by_id = {c.get("strategy_id"): c for c in b5.get("candidates") or []}
    problems: list[str] = []
    if red.get("n_trials_counted_in_dsr") != b5.get("n_trials_counted_in_dsr"):
        problems.append("red_team_audit and batch5 disagree on n_trials_counted_in_dsr")
    if red.get("pbo_cscv") != b5.get("pbo_cscv"):
        problems.append("red_team_audit and batch5 disagree on pbo_cscv")
    for sid in eligible:
        c = by_id.get(sid) or {}
        if c.get("gate") != "PASS_STATS" or int(c.get("oos_trades") or 0) < PROMOTION_MIN_CLOSED:
            problems.append(f"{sid} eligible without PASS_STATS and >= {PROMOTION_MIN_CLOSED} OOS trades")
    for hid, h in (reg.get("candidates") or {}).items():
        if not isinstance(h, dict) or "batch5_research" not in str(h.get("evidence") or ""):
            continue
        if h.get("verdict") in PROMOTED_STATES and not any(sid in eligible for sid in (h.get("detail") or {})):
            problems.append(f"registry {hid} verdict {h.get('verdict')} without an eligible batch-5 trial")
    status = _json(root, STATUS_REL) or {}
    if int(status.get("strategy_switch_version") or 0) > 0 and not eligible:
        problems.append("paper trader runs a switched strategy but no candidate is promotion-eligible")
    out.append(_check("research.batch5_registry_switch", _pass_fail(not problems),
                      {"promotion_eligible": sorted(eligible), "problems": problems,
                       "strategy_switch_version": status.get("strategy_switch_version")},
                      [str(BATCH_RELS["batch5"]), str(RED_TEAM_REL), str(REGISTRY_REL), str(STATUS_REL)]))

    audit = _json(root, AUDIT_REL) or {}
    score = _json(root, SCORECARD_REL)
    if closed is None or score is None:
        out.append(_check("edge.unproven_consistency", "UNKNOWN", {"closed": closed, "scorecard": score is not None},
                          [str(STATUS_REL), str(AUDIT_REL), str(SCORECARD_REL)]))
        return out
    proven_possible = closed >= PROMOTION_MIN_CLOSED and bool(eligible)
    flags = {
        "status.edge_status": status.get("edge_status"),
        "audit.unproven_edge": audit.get("unproven_edge"),
        "scorecard.unproven_edge": score.get("unproven_edge"),
        "scorecard.closed_trades_count": score.get("closed_trades_count"),
        "scorecard.trades_remaining_to_30_gate": score.get("trades_remaining_to_30_gate"),
        "paper_closed_trades": closed,
    }
    ok = proven_possible or (status.get("edge_status") == "UNPROVEN_EDGE"
                             and audit.get("unproven_edge") is True and score.get("unproven_edge") is True)
    ok = ok and score.get("closed_trades_count") == closed
    ok = ok and score.get("trades_remaining_to_30_gate") == max(0, PROMOTION_MIN_CLOSED - closed)
    out.append(_check("edge.unproven_consistency", _pass_fail(ok), flags,
                      [str(STATUS_REL), str(AUDIT_REL), str(SCORECARD_REL)]))
    return out


def _static_claim_checks(root: Path) -> list[dict[str, Any]]:
    organs = _json(root, ORGANS_REL)
    sci = _json(root, SCIENCE_REL)
    tour = _json(root, TOURNAMENT_REL)
    missing = [str(r) for r, v in ((ORGANS_REL, organs), (SCIENCE_REL, sci), (TOURNAMENT_REL, tour)) if v is None]
    if missing:
        return [_check("claims.static_labeled", "UNKNOWN", {"missing": missing}, missing)]
    unlabeled: list[str] = []
    if not str(organs.get("exam_score_evidence") or "").startswith(("STATIC_UNVERIFIED", "CALLER_SUPPLIED")):
        unlabeled.append(f"{ORGANS_REL}: average_university_exam_score_pct without exam_score_evidence")
    if not str(sci.get("organ_static_curricula") or "").startswith("STATIC_UNVERIFIED"):
        unlabeled.append(f"{SCIENCE_REL}: organ curricula not labeled STATIC_UNVERIFIED")
    if int(sci.get("validated_claims_total") or 0) != sum(int(r.get("validated_claims") or 0)
                                                          for r in sci.get("matrix") or []):
        unlabeled.append(f"{SCIENCE_REL}: validated_claims_total disagrees with its matrix")
    if not tour.get("data_source"):
        unlabeled.append(f"{TOURNAMENT_REL}: leaderboard without data_source")
    return [_check("claims.static_labeled", _pass_fail(not unlabeled), {"unlabeled": unlabeled},
                   [str(ORGANS_REL), str(SCIENCE_REL), str(TOURNAMENT_REL)])]


def _stage7_checks(root: Path) -> list[dict[str, Any]]:
    b6 = _json(root, Path("reports") / "grok" / "M28" / "batch6_research.json")
    grid = _json(root, Path("reports") / "grok" / "M28" / "map_elites_grid.json")
    surfaces = ["reports/grok/M28/batch6_research.json", "reports/grok/M28/map_elites_grid.json"]
    if b6 is None or grid is None:
        return [_check("research.map_elites_batch6", "UNKNOWN", {"batch6": b6 is not None, "grid": grid is not None}, surfaces)]
    problems = []
    counted = b6.get("candidates") or []
    screened = b6.get("screened") or []
    if any(s.get("counted_in_dsr") for s in screened):
        problems.append("a screened hypothesis was counted")
    expected = int(b6.get("n_trials_prior") or 0) + len(counted)
    if b6.get("n_trials_counted_in_dsr") != expected:
        problems.append("n_trials_counted_in_dsr != prior + admitted")
    for c in counted:
        v = c.get("deflated_sharpe")
        if v is not None and not 0.0 <= float(v) <= 1.0:
            problems.append(f"{c.get('strategy_id')} DSR {v} outside [0,1]")
    occupied = sum(1 for h in (grid.get("grid") or {}).values() for cell in h.values() if cell)
    if grid.get("cells_occupied") != occupied:
        problems.append("grid occupancy does not match its cells")
    out = [_check("research.map_elites_batch6", _pass_fail(not problems),
                  {"admitted": len(counted), "screened": len(screened), "problems": problems,
                   "n_trials_counted_in_dsr": b6.get("n_trials_counted_in_dsr")}, surfaces)]
    graph = _json(root, Path("reports") / "grok" / "M12" / "cognitive_graph_snapshot.json")
    reg = root / "config" / "agent_registry.yaml"
    if graph is None or not reg.is_file():
        out.append(_check("cognitive.graph", "UNKNOWN", {"graph": graph is not None, "registry": reg.is_file()},
                          ["reports/grok/M12/cognitive_graph_snapshot.json", "config/agent_registry.yaml"]))
        return out
    import yaml
    n = len((yaml.safe_load(reg.read_text(encoding="utf-8")) or {}).get("agents") or [])
    ids = [a.get("agent_id") for a in graph.get("agents") or []]
    bad = [a.get("agent_id") for a in graph.get("agents") or []
           if a.get("verdict") not in {"PASS", "VETO", "HOLD", "UNRESOLVED"} or not a.get("authority_ok")]
    ok = graph.get("registry_agents") == n == len(ids) == len(set(ids)) and not bad and not graph.get("authority_violations")
    out.append(_check("cognitive.graph", _pass_fail(ok),
                      {"registry": n, "snapshot": graph.get("registry_agents"), "bad_rows": bad},
                      ["reports/grok/M12/cognitive_graph_snapshot.json", "config/agent_registry.yaml"]))
    return out


def _stage8_checks(root: Path) -> list[dict[str, Any]]:
    b7 = _json(root, Path("reports") / "grok" / "M28" / "batch7_research.json")
    grid = _json(root, Path("reports") / "grok" / "M28" / "map_elites_grid.json")
    surfaces = ["reports/grok/M28/batch7_research.json", "reports/grok/M28/map_elites_grid.json"]
    if b7 is None or grid is None:
        out = [_check("research.batch7_low_turnover", "UNKNOWN", {"batch7": b7 is not None, "grid": grid is not None}, surfaces)]
    else:
        problems = []
        counted = b7.get("candidates") or []
        screened = b7.get("screened") or []
        if any(s.get("counted_in_dsr") for s in screened):
            problems.append("a screened batch-7 hypothesis was counted")
        expected = int(b7.get("n_trials_prior") or 0) + len(counted)
        if b7.get("n_trials_counted_in_dsr") != expected:
            problems.append("batch7 n_trials_counted_in_dsr != prior + admitted")
        for c in counted:
            v = c.get("deflated_sharpe")
            if v is not None and not 0.0 <= float(v) <= 1.0:
                problems.append(f"{c.get('strategy_id')} DSR {v} outside [0,1]")
        occupied = sum(1 for h in (grid.get("grid") or {}).values() for cell in h.values() if cell)
        if grid.get("cells_occupied") != occupied:
            problems.append("grid occupancy does not match its cells")
        challengers = grid.get("challengers") or []
        for c in counted:
            cell = c.get("map_elites_cell") or {}
            slot = ((grid.get("grid") or {}).get(cell.get("horizon")) or {}).get(cell.get("regime"))
            hid = c.get("hypothesis_id")
            occupant = slot.get("hypothesis_id") if isinstance(slot, dict) else None
            mentioned = occupant == hid or any(ch.get("challenger") == hid or ch.get("displaced") == hid for ch in challengers)
            if not mentioned:
                problems.append(f"{hid} is neither the cell occupant nor a recorded challenger")
        out = [_check("research.batch7_low_turnover", _pass_fail(not problems),
                      {"admitted": len(counted), "screened": len(screened), "cells_occupied": grid.get("cells_occupied"),
                       "problems": problems, "n_trials_counted_in_dsr": b7.get("n_trials_counted_in_dsr")}, surfaces)]
    graph = _json(root, Path("reports") / "grok" / "M12" / "cognitive_graph_snapshot.json")
    if graph is None:
        out.append(_check("cognitive.resolved_graph", "UNKNOWN", {"graph": False},
                          ["reports/grok/M12/cognitive_graph_snapshot.json"]))
        return out
    unresolved = int((graph.get("verdict_counts") or {}).get("UNRESOLVED") or 0)
    unresolved += sum(1 for a in graph.get("agents") or [] if a.get("verdict") == "UNRESOLVED")
    # verdict_counts already includes the rows; do not double-count when the count is present
    if graph.get("verdict_counts") is not None:
        unresolved = int(graph["verdict_counts"].get("UNRESOLVED") or 0)
    violations = graph.get("authority_violations") or []
    ok = unresolved == 0 and not violations and int(graph.get("registry_agents") or 0) == len(graph.get("agents") or [])
    out.append(_check("cognitive.resolved_graph", _pass_fail(ok),
                      {"unresolved": unresolved, "authority_violations": violations,
                       "registry_agents": graph.get("registry_agents")},
                      ["reports/grok/M12/cognitive_graph_snapshot.json"]))
    return out


def _stage9_checks(root: Path) -> list[dict[str, Any]]:
    b8 = _json(root, Path("reports") / "grok" / "M28" / "batch8_research.json")
    grid = _json(root, Path("reports") / "grok" / "M28" / "map_elites_grid.json")
    surfaces = ["reports/grok/M28/batch8_research.json", "reports/grok/M28/map_elites_grid.json"]
    if b8 is None or grid is None:
        out = [_check("research.batch8_hourly_grid", "UNKNOWN", {"batch8": b8 is not None, "grid": grid is not None}, surfaces)]
    else:
        problems = []
        counted = b8.get("candidates") or []
        screened = b8.get("screened") or []
        if any(s.get("counted_in_dsr") for s in screened):
            problems.append("a screened batch-8 hypothesis was counted")
        expected = int(b8.get("n_trials_prior") or 0) + len(counted)
        if b8.get("n_trials_counted_in_dsr") != expected:
            problems.append("batch8 n_trials_counted_in_dsr != prior + admitted")
        for c in counted:
            v = c.get("deflated_sharpe")
            if v is not None and not 0.0 <= float(v) <= 1.0:
                problems.append(f"{c.get('strategy_id')} DSR {v} outside [0,1]")
            cell = c.get("map_elites_cell") or {}
            if cell.get("horizon") == "intraday" and c.get("bar_interval") != "1h":
                problems.append(f"{c.get('hypothesis_id')} intraday cell is not a 1h book")
            if c.get("hypothesis_id") == "H37" and c.get("bar_interval") == "1h":
                problems.append("H37 is a daily book labeled 1h")
        occupied = sum(1 for h in (grid.get("grid") or {}).values() for cell in h.values() if cell)
        if grid.get("cells_occupied") != occupied:
            problems.append("grid occupancy does not match its cells")
        out = [_check("research.batch8_hourly_grid", _pass_fail(not problems),
                      {"admitted": len(counted), "screened": len(screened), "cells_occupied": grid.get("cells_occupied"),
                       "intraday_provenance": grid.get("intraday_provenance"), "problems": problems,
                       "n_trials_counted_in_dsr": b8.get("n_trials_counted_in_dsr")}, surfaces)]
    state = _json(root, Path("reports") / "grok" / "CONTINUATION_STATE.json")
    if not isinstance(state, dict):
        out.append(_check("continuation.state", "UNKNOWN", {"state": False}, ["reports/grok/CONTINUATION_STATE.json"]))
        return out
    problems = []
    if state.get("paper_only") is not True:
        problems.append("paper_only is not true")
    if not isinstance(state.get("completed_stages"), list):
        problems.append("completed_stages is not a list")
    if not isinstance(state.get("next_wave_queue"), list) or not state.get("next_wave_queue"):
        problems.append("next_wave_queue is empty")
    if not state.get("current_stage"):
        problems.append("current_stage is missing")
    out.append(_check("continuation.state", _pass_fail(not problems),
                      {"current_stage": state.get("current_stage"), "problems": problems,
                       "queue": state.get("next_wave_queue")},
                      ["reports/grok/CONTINUATION_STATE.json"]))
    return out


def build_unification_audit(root: Path, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root)
    entries, ledger_v = _ledger(root)
    checks = [_check("ledger.chain", "UNKNOWN" if ledger_v.get("verdict") == "MISSING"
                     else _pass_fail(str(ledger_v.get("verdict")).startswith("CHAIN_INTACT")),
                     {k: ledger_v.get(k) for k in ("verdict", "entries", "head_hash", "error") if k in ledger_v},
                     [str(LEDGER_REL)])]
    checks += _paper_checks(root, entries)
    checks += _gold_checks(root, entries)
    checks += _evidence_checks(root)
    status = _json(root, STATUS_REL)
    closed = int(status.get("closed_trades") or 0) if isinstance(status, dict) else None
    checks += _research_checks(root, closed)
    checks += _static_claim_checks(root)
    checks += _stage7_checks(root)
    checks += _stage8_checks(root)
    checks += _stage9_checks(root)

    tally = Counter(c["status"] for c in checks)
    overall = ("DRIFT_DETECTED" if tally["FAIL"] else "INCOMPLETE" if tally["UNKNOWN"] else "UNIFIED_CLEAN")
    drift = [c["id"] for c in checks if c["status"] == "FAIL"]
    unknown = [c["id"] for c in checks if c["status"] == "UNKNOWN"]
    fa = {
        "UNIFIED_CLEAN": f"همهٔ {len(checks)} ناوردای بین‌سطحی سازگارند؛ این به معنی لبهٔ سودآوری نیست.",
        "DRIFT_DETECTED": f"ناسازگاری بین سطوح: {', '.join(drift)} — نویسندهٔ اصلی باید اصلاح شود.",
        "INCOMPLETE": f"ورودی ناقص برای: {', '.join(unknown)} — حکم پاک صادر نمی‌شود.",
    }[overall]
    return {
        "schema": SCHEMA,
        "generated_at": _utc(now),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "read_only": True,
        "overall_status": overall,
        "checks_total": len(checks),
        "checks_by_status": dict(tally),
        "drift": drift,
        "unknown": unknown,
        "checks": checks,
        "hold_flag_counts": {
            "active_repos_total": 14,
            "active_repos_breakdown": {"ahos": 10, "ahos_arena": 2, "AHOS_Launcher": 2},
            "robat_workspace_total": 22,
            "note": "14 HOLD.flag files in the 3 active repos (ahos=10, ahos_arena=2, AHOS_Launcher=2); 22 across G:\\robat including archived/portable directories.",
        },
        "open_gaps": list(OPEN_GAPS),
        "summary_fa": fa,
    }


def export_unification_audit(root: Path, now: datetime | None = None) -> dict[str, Any]:
    out = build_unification_audit(root, now=now)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
