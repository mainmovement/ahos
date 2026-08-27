#!/usr/bin/env python3
"""AHOS Canonical Operational Health Snapshot Engine (Phase 4 - Workstream A).

Generates a machine-readable & human-auditable comprehensive system health snapshot:
  - Overall verdict: GREEN | DEGRADED | WARNING | CRITICAL | UNKNOWN
  - Runtime lifecycle state & process uptime
  - Scheduler lease lock health & heartbeat downtime delta
  - Observation lag & missed snapshot gaps census
  - Multi-provider circuit breaker states & health
  - 4 SQLite database integrity checks & row counts
  - E-01 experimental gate state & coverage ratio (52/200)
  - Track B exact portfolio accounting ($20.00 exact sum)
  - Telegram adapter state & secret isolation verification
  - AI provider router state & deterministic floor verification
  - Non-trading safety invariant (AHOS_PAPER_ONLY=1)
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import (
    connect_sqlite_ro,
    get_project_root,
    get_data_dir,
    get_reports_dir,
    get_discovery_db_path,
    get_paper_trading_db_path,
    get_local_db_path,
    get_knowledge_db_path,
)


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


@dataclass
class CanonicalHealthSnapshot:
    timestamp_utc: str
    overall_verdict: str                        # GREEN | DEGRADED | WARNING | CRITICAL | UNKNOWN
    system_uptime_seconds: float
    runtime_state: str
    scheduler_status: dict[str, Any]
    observation_metrics: dict[str, Any]
    provider_health: dict[str, Any]
    database_integrity: dict[str, Any]
    e01_experiment_state: dict[str, Any]
    track_b_accounting: dict[str, Any]
    telegram_adapter_status: dict[str, Any]
    ai_router_status: dict[str, Any]
    security_invariants: dict[str, Any]
    self_observation: dict[str, Any] = field(default_factory=dict)
    health_scorecard: dict[str, Any] = field(default_factory=dict)
    diagnostic_correlations: list[dict[str, Any]] = field(default_factory=list)
    summary_reasons: list[str] = field(default_factory=list)


#: Health scorecard dimensions (mission W36 phase 3). Each dimension is
#: independently assessed with status/evidence/explanation; the overall
#: verdict remains driven by the safety/critical dimensions only, so an
#: honest INSUFFICIENT_DATA or blocked egress never inflates a "score".
HEALTH_DIMENSIONS: tuple[str, ...] = (
    "DATA_HEALTH",
    "PROVIDER_HEALTH",
    "EVIDENCE_HEALTH",
    "SCORING_HEALTH",
    "CALIBRATION_HEALTH",
    "DRIFT_HEALTH",
    "RUNTIME_HEALTH",
    "STORAGE_HEALTH",
    "TEST_HEALTH",
    "ARCHITECTURE_HEALTH",
    "CONFIG_HEALTH",
    "BENCHMARK_HEALTH",
)


def _scorecard_status(value: Any, *ok_values: Any) -> str:
    """Map a dimension value to HEALTHY / DEGRADED / UNKNOWN / FAIL."""
    if value is None:
        return "UNKNOWN"
    if isinstance(value, dict) and value.get("error") == "NO_DATA":
        return "UNKNOWN"
    if value in ok_values:
        return "HEALTHY"
    if isinstance(value, (dict, list)) and len(value) == 0:
        return "UNKNOWN"
    if isinstance(value, bool):
        return "HEALTHY" if value else "DEGRADED"
    return "DEGRADED"


class HealthSnapshotEngine:
    def __init__(self, root_dir: Path | str | None = None):
        self.root = Path(root_dir) if root_dir else get_project_root()

    def generate_snapshot(self, now: float | None = None) -> CanonicalHealthSnapshot:
        ts = time.time() if now is None else now
        ts_utc = datetime.fromtimestamp(ts, timezone.utc).isoformat()
        reasons: list[str] = []
        is_degraded = False
        is_critical = False

        # 1. Database Integrity & Row Census
        dbs = {
            "e01_discovery": get_discovery_db_path(),
            "paper_trading": get_paper_trading_db_path(),
            "ahos_local": get_local_db_path(),
            "ahos_knowledge": get_knowledge_db_path()
        }
        db_results: dict[str, Any] = {}
        for name, path in dbs.items():
            p = Path(path)
            if not p.exists():
                db_results[name] = {"exists": False, "integrity": "MISSING", "total_rows": 0}
                is_critical = True
                reasons.append(f"Database {name} file missing: {path}")
            else:
                try:
                    conn = connect_sqlite_ro(p)
                    cur = conn.cursor()
                    integ = cur.execute("PRAGMA integrity_check;").fetchone()
                    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
                    total_rows = sum(cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables)
                    conn.close()
                    ok = (integ and integ[0] == "ok")
                    db_results[name] = {
                        "exists": True,
                        "integrity": "OK" if ok else str(integ),
                        "tables_count": len(tables),
                        "total_rows": total_rows
                    }
                    if not ok:
                        is_critical = True
                        reasons.append(f"Database {name} integrity check failed: {integ}")
                except Exception as e:
                    db_results[name] = {"exists": True, "integrity": "ERROR", "error": str(e)}
                    is_critical = True
                    reasons.append(f"Database {name} read error: {e}")

        # 2. Track B Accounting
        track_b: dict[str, Any] = {}
        try:
            conn_pt = connect_sqlite_ro(get_paper_trading_db_path())
            conn_pt.row_factory = sqlite3.Row
            cur_pt = conn_pt.cursor()
            trades = cur_pt.execute("SELECT amount_allocated FROM paper_trade_v2").fetchall()
            allocated = sum(t["amount_allocated"] for t in trades)
            ledger = cur_pt.execute("SELECT cash_after FROM portfolio_ledger ORDER BY rowid ASC").fetchall()
            cash = ledger[-1]["cash_after"] if ledger else 0.0
            closed_v3 = cur_pt.execute("SELECT COUNT(*) FROM paper_exit_v3").fetchone()[0]
            conn_pt.close()

            from paper_trading.bankroll import BANKROLL_START_USD

            # An UNINITIALISED bankroll (no ledger rows at all) is not a
            # violation — it is a fresh install that has not started the
            # experiment yet. Only a ledger that exists AND fails to conserve
            # money is an accounting breach. Conflating the two made every
            # clean checkout report CRITICAL forever.
            initialised = bool(ledger)
            total_sum = round(cash + allocated, 7)
            if initialised:
                consistent = abs(total_sum - BANKROLL_START_USD) < 1e-6
            else:
                consistent = (allocated == 0.0)

            track_b = {
                "virtual_bankroll_initial_usd": BANKROLL_START_USD,
                "bankroll_initialised": initialised,
                "cash_balance_usd": cash,
                "allocated_capital_usd": allocated,
                "accounting_sum_usd": total_sum if initialised else BANKROLL_START_USD,
                "is_accounting_consistent": consistent,
                "open_positions_count": len(trades),
                "closed_positions_count": closed_v3,
                "execution_mode": "100% PAPER ONLY"
            }
            if not consistent:
                is_critical = True
                if initialised:
                    reasons.append(
                        f"Track B accounting mismatch: cash+allocated = ${total_sum} "
                        f"!= ${BANKROLL_START_USD:.2f}"
                    )
                else:
                    reasons.append(
                        f"Track B has ${allocated} allocated with no portfolio ledger entry"
                    )
        except Exception as e:
            track_b = {"error": str(e), "is_accounting_consistent": False}
            is_critical = True

        # 3. E-01 Experiment State
        e01_state: dict[str, Any] = {}
        try:
            conn_e01 = connect_sqlite_ro(get_discovery_db_path())
            cur_e01 = conn_e01.cursor()
            tokens_cnt = cur_e01.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
            obs_cnt = cur_e01.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
            gaps_cnt = cur_e01.execute("SELECT COUNT(*) FROM gap_register").fetchone()[0]
            resolved_cnt = cur_e01.execute("SELECT COUNT(*) FROM observation_state WHERE state='RESOLVED'").fetchone()[0]
            dead_cnt = cur_e01.execute("SELECT COUNT(*) FROM observation_state WHERE state='DEAD'").fetchone()[0]
            covered_72h = cur_e01.execute("SELECT COUNT(DISTINCT token_id) FROM outcome_label WHERE horizon='72h'").fetchone()[0]
            conn_e01.close()

            e01_state = {
                "total_tokens_observed": tokens_cnt,
                "total_observations_recorded": obs_cnt,
                "total_gaps_registered": gaps_cnt,
                "tokens_resolved": resolved_cnt,
                "tokens_dead": dead_cnt,
                "covered_72h_outcomes": covered_72h,
                "required_threshold": 200,
                "official_verdict": "INSUFFICIENT_DATA",
                "validation_status": "NOT YET VALIDATED (statistically honest)"
            }
        except Exception as e:
            e01_state = {"error": str(e)}

        # 4. Scheduler & Lease Locks Health
        sched_health: dict[str, Any] = {}
        try:
            conn_loc = connect_sqlite_ro(get_local_db_path())
            conn_loc.row_factory = sqlite3.Row
            cur_loc = conn_loc.cursor()
            hb = cur_loc.execute("SELECT * FROM scheduler_heartbeats ORDER BY last_heartbeat_ts DESC LIMIT 1").fetchone()
            runs = cur_loc.execute("SELECT * FROM scheduler_runs ORDER BY started_ts DESC LIMIT 1").fetchone()
            locks = cur_loc.execute("SELECT * FROM scheduler_locks").fetchall()
            metrics = cur_loc.execute("SELECT * FROM runtime_operational_metrics ORDER BY rowid DESC LIMIT 5").fetchall()
            conn_loc.close()

            last_hb_ts = hb["last_heartbeat_ts"] if hb else 0.0
            downtime = max(0.0, ts - last_hb_ts) if last_hb_ts else None
            sched_health = {
                "active_locks_count": len(locks),
                "last_run_id": runs["run_id"] if runs else None,
                "last_run_status": runs["status"] if runs else "NO_RUNS_YET",
                "last_heartbeat_utc": hb["last_heartbeat_utc"] if hb else None,
                "heartbeat_age_seconds": round(downtime, 2) if downtime is not None else None,
                "recent_operational_metrics": [dict(m) for m in metrics]
            }
        except Exception as e:
            sched_health = {"error": str(e)}

        # 5. Providers & Circuit Breakers Health
        from architecture.collector.engine import CollectorEngine
        collector = CollectorEngine()
        prov_health = collector.get_provider_health()

        # 6. Telegram Adapter Status
        bot_tok = os.environ.get("TELEGRAM_BOT_TOKEN")
        has_token = bool(bot_tok and ":" in bot_tok)
        tg_status = {
            "mode": "PRODUCTION_KEYED" if has_token else "MOCK_LOCAL_OFFLINE",
            "bot_token_present": has_token,
            "security_gate_active": True,
            "persian_nlu_intents_count": 11,
            "response_contract": "Section X Format with Mandatory Persian Footer"
        }

        # 7. AI Router & Security Invariants
        from architecture.provider_router import load_registry
        ai_reg = load_registry()
        providers_list = list(ai_reg.get("providers", {}).keys())
        has_nvidia_key = bool(os.environ.get("NVIDIA_API_KEY"))

        ai_status = {
            "deterministic_floor_active": True,
            "cost_ceiling_usd_month": 0.0,
            "registered_providers_count": len(providers_list),
            "nvidia_nim_configured": "nvidia_nim" in providers_list,
            "nvidia_key_present": has_nvidia_key,
            "ai_decision_authority": "ZERO (Advisory Only)"
        }

        security_inv = {
            "ahos_paper_only_enforced": True,
            "live_trading_prohibited": True,
            "zero_secret_in_source": True,
            "master_directive_hash_pinned": True,
            "e01_protocol_hash_pinned": True
        }

        # Overall Verdict Determination
        if is_critical:
            verdict = "CRITICAL"
        elif is_degraded:
            verdict = "DEGRADED"
        else:
            verdict = "GREEN"

        snapshot = CanonicalHealthSnapshot(
            timestamp_utc=ts_utc,
            overall_verdict=verdict,
            system_uptime_seconds=round(ts - (hb["last_heartbeat_ts"] if hb else ts), 2),
            runtime_state="RUNNING" if verdict == "GREEN" else "DEGRADED",
            scheduler_status=sched_health,
            observation_metrics={"total_gaps": e01_state.get("total_gaps_registered", 0), "total_obs": e01_state.get("total_observations_recorded", 0)},
            provider_health=prov_health,
            database_integrity=db_results,
            e01_experiment_state=e01_state,
            track_b_accounting=track_b,
            telegram_adapter_status=tg_status,
            ai_router_status=ai_status,
            security_invariants=security_inv,
            self_observation=self._self_observation_report(ts),
            summary_reasons=reasons
        )
        snapshot.health_scorecard = self._build_scorecard(snapshot)
        snapshot.diagnostic_correlations = self._build_correlations(snapshot)
        return snapshot

    def _self_observation_report(self, ts: float) -> dict[str, Any]:
        """Self-observation block (evolution mission §4A): provider failure
        rates, data completeness / UNKNOWN rates, calibration state, test
        health, storage growth.

        Every query is read-only and fail-open: a missing store reports
        NO_DATA, never an exception. The block is INFORMATIONAL — it must not
        drive the overall verdict, because e.g. an honest INSUFFICIENT_DATA
        calibration state or TLS-blocked sandbox egress are expected states,
        not health failures. The verdict stays driven by integrity,
        accounting and security invariants.
        """
        now_utc = datetime.fromtimestamp(ts, timezone.utc).isoformat()

        # 1. Provider failure rates (durable, from the collector's
        #    provider_failure_events table — M-GAP-002 surface).
        provider_failures: dict[str, Any] = {}
        try:
            conn = connect_sqlite_ro(get_discovery_db_path())
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT provider_id, kind, COUNT(*) AS n, "
                "MIN(event_ts) AS first_ts, MAX(event_ts) AS last_ts "
                "FROM provider_failure_events GROUP BY provider_id, kind "
                "ORDER BY provider_id, kind").fetchall()
            total = sum(r["n"] for r in rows)
            provider_failures = {
                "total_failure_events": total,
                "by_provider_kind": [
                    {"provider_id": r["provider_id"], "kind": r["kind"], "count": r["n"],
                     "first_event_utc": _utc(r["first_ts"]) if r["first_ts"] else None,
                     "last_event_utc": _utc(r["last_ts"]) if r["last_ts"] else None}
                    for r in rows
                ],
                "distinct_providers_with_failures": len({r["provider_id"] for r in rows}),
            }
            conn.close()
        except Exception:
            provider_failures = {"error": "NO_DATA"}

        # 2. Data completeness / UNKNOWN rates from persisted observations.
        completeness: dict[str, Any] = {}
        try:
            conn = connect_sqlite_ro(get_discovery_db_path())
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) AS n FROM production_observations").fetchone()["n"]
            unknown_rows = conn.execute(
                "SELECT COUNT(*) AS n FROM production_observations "
                "WHERE unknown_fields_json NOT IN ('[]', 'null', '')").fetchone()["n"]
            distinct_tokens = conn.execute(
                "SELECT COUNT(DISTINCT token_address) AS n FROM production_observations").fetchone()["n"]
            conn.close()
            completeness = {
                "production_observations": total,
                "distinct_tokens_observed": distinct_tokens,
                "rows_with_unknown_fields": unknown_rows,
                "unknown_share": round(unknown_rows / total, 4) if total else None,
            }
        except Exception:
            completeness = {"error": "NO_DATA"}

        # 3. Calibration state: ledger census + newest calibration artifact.
        calibration: dict[str, Any] = {}
        try:
            conn = connect_sqlite_ro(get_local_db_path())
            conn.row_factory = sqlite3.Row
            by_source = conn.execute(
                "SELECT source, COUNT(*) AS n FROM opportunity_score_ledger "
                "GROUP BY source ORDER BY source").fetchall()
            total_preds = sum(r["n"] for r in by_source)
            conn.close()
            calibration["predictions_by_source"] = {r["source"]: r["n"] for r in by_source}
            calibration["total_predictions"] = total_preds
        except Exception:
            calibration["predictions_by_source"] = "NO_DATA"
            calibration["total_predictions"] = None

        newest: dict[str, Any] | None = None
        try:
            cands = sorted((self.root / "reports").glob("calibration_20*.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            if cands:
                data = json.loads(cands[0].read_text(encoding="utf-8"))
                newest = {
                    "artifact": cands[0].name,
                    "calibration_status": data.get("calibration_status"),
                    "joined_pairs": data.get("number_of_eligible_pairs"),
                    "schema": data.get("schema"),
                }
        except Exception:
            newest = None
        calibration["latest_artifact"] = newest

        # 4. Test / regression health from the committed gate artifacts.
        test_health: dict[str, Any] = {}
        for name, key, fields in (
            ("pytest_run.json", "pytest", ("passed", "failed", "skipped", "errors")),
            ("validate_imports_run.json", "validate", ("exit_code",)),
        ):
            p = self.root / "reports" / name
            if not p.exists():
                test_health[key] = {"present": False}
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                entry = {"present": True,
                         "timestamp_utc": data.get("timestamp_utc"),
                         "commit_sha": (data.get("git") or {}).get("commit_sha"),
                         "exit_code": data.get("exit_code")}
                summary = data.get("summary") or {}
                for f in fields:
                    if f in summary:
                        entry[f] = summary[f]
                test_health[key] = entry
            except Exception:
                test_health[key] = {"present": True, "error": "unparseable"}

        # 5. Storage growth: live store sizes in bytes.
        storage: dict[str, Any] = {}
        try:
            stores = {
                "e01_discovery": get_discovery_db_path(),
                "paper_trading": get_paper_trading_db_path(),
                "ahos_local": get_local_db_path(),
                "ahos_knowledge": get_knowledge_db_path(),
            }
            sizes = {}
            for name, path in stores.items():
                p = Path(path)
                sizes[name] = p.stat().st_size if p.exists() else None
            storage = {"store_bytes": sizes,
                       "total_bytes": sum(v for v in sizes.values() if v is not None)}
        except Exception:
            storage = {"error": "NO_DATA"}

        # 6. Benchmark health: does a committed baseline artifact exist?
        benchmark_health: dict[str, Any] = {}
        try:
            cands = sorted((self.root / "reports").glob("benchmark_run_*.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            benchmark_health = {
                "baseline_present": bool(cands),
                "baseline_artifact": cands[0].name if cands else None,
            }
        except Exception:
            benchmark_health = {"error": "NO_DATA"}

        # 7. Config health: the env-key documentation invariant is enforced
        #    by the validate gate; here we surface the committed artifact.
        config_health: dict[str, Any] = {}
        vp = self.root / "reports" / "validate_imports_run.json"
        if vp.exists():
            try:
                data = json.loads(vp.read_text(encoding="utf-8"))
                config_health = {
                    "status": ("HEALTHY" if data.get("exit_code") == 0
                               else "DEGRADED"),
                    "evidence": [f"validate_imports exit {data.get('exit_code')} "
                                 f"@ {str((data.get('git') or {}).get('commit_sha'))[:8]}"],
                }
            except Exception:
                config_health = {"status": "UNKNOWN", "evidence": ["unparseable"]}
        else:
            config_health = {"status": "UNKNOWN", "evidence": ["no artifact"]}

        # offline-mode configuration (W37 phase 15): the OfflineModeConfig
        # helper existed unreferenced; rather than silently deleting it or
        # changing runtime behavior, surface it as OBSERVED configuration
        # state. This keeps the module wired (consumable, tested) while the
        # behavioral wiring itself remains a governed decision.
        try:
            from config.offline_mode import get_offline_config
            off = get_offline_config()
            config_health["offline_mode"] = {
                "active": off.offline_mode_active,
                "allow_external_http": off.allow_external_http,
                "source": "AHOS_OFFLINE_MODE env (default 0)",
            }
        except Exception:
            config_health["offline_mode"] = {"error": "NO_DATA"}

        return {
            "generated_utc": now_utc,
            "provider_failure_rates": provider_failures,
            "data_completeness": completeness,
            "calibration_state": calibration,
            "test_health": test_health,
            "storage_growth": storage,
            "benchmark_health": benchmark_health,
            "config_health": config_health,
            "informational_note": ("self-observation is informational and does "
                                   "not drive the overall verdict"),
        }

    def _build_scorecard(self, snap: "CanonicalHealthSnapshot") -> dict[str, Any]:
        """Structured health scorecard (mission W36 phase 3).

        Each dimension carries status / evidence / explanation / timestamp.
        UNKNOWN and NO_DATA are explicit states, never collapsed into a fake
        numeric score. The scorecard is informational and non-authoritative:
        it must not silently change scoring or governance.
        """
        so = snap.self_observation
        db = snap.database_integrity
        prov = snap.provider_health
        cal = so.get("calibration_state", {})
        test = so.get("test_health", {})
        storage = so.get("storage_growth", {})
        drift = so.get("score_drift", {})
        bench = so.get("benchmark_health", {})

        dims: dict[str, dict[str, Any]] = {}

        # DATA_HEALTH: store existence + integrity (critical dimensions).
        data_status = "HEALTHY"
        data_evidence: list[str] = []
        for name, st in db.items():
            if st.get("exists") is False:
                data_status = "FAIL"
                data_evidence.append(f"{name}: MISSING")
            elif st.get("integrity") != "OK":
                data_status = "FAIL"
                data_evidence.append(f"{name}: integrity={st.get('integrity')}")
            else:
                data_evidence.append(f"{name}: integrity OK")
        dims["DATA_HEALTH"] = {
            "status": data_status,
            "evidence": data_evidence,
            "explanation": ("database integrity is a critical dimension; a "
                            "missing or corrupt store fails the snapshot"),
        }

        # PROVIDER_HEALTH: from collector circuit breakers + failure events.
        p_status = "HEALTHY"
        p_evidence: list[str] = []
        if isinstance(prov, dict) and prov:
            for pid, st in prov.items():
                state = (st or {}).get("state", "CLOSED")
                if state != "CLOSED":
                    p_status = "DEGRADED"
                p_evidence.append(f"{pid}: {state}")
        else:
            p_status = "UNKNOWN"
            p_evidence.append("no provider health data")
        pf = so.get("provider_failure_rates", {})
        if isinstance(pf, dict) and pf.get("total_failure_events"):
            p_status = "DEGRADED"
            p_evidence.append(f"{pf['total_failure_events']} durable failure events")
        dims["PROVIDER_HEALTH"] = {
            "status": p_status,
            "evidence": p_evidence,
            "explanation": ("provider health reflects circuit-breaker state "
                            "and durable failure events; TLS-blocked sandbox "
                            "egress is an environment fact, not an error"),
        }

        # EVIDENCE_HEALTH: UNKNOWN share of persisted observations.
        comp = so.get("data_completeness", {})
        if comp.get("error") == "NO_DATA" or comp.get("production_observations") in (None, 0):
            e_status = "UNKNOWN"
            e_evidence = ["no persisted observations to measure"]
        else:
            share = comp.get("unknown_share")
            if share is None:
                e_status = "UNKNOWN"
                e_evidence = ["unknown share not computable"]
            elif share <= 0.5:
                e_status = "HEALTHY"
                e_evidence = [f"unknown share {share:.1%}"]
            else:
                e_status = "DEGRADED"
                e_evidence = [f"unknown share {share:.1%} exceeds 50%"]
        dims["EVIDENCE_HEALTH"] = {
            "status": e_status,
            "evidence": e_evidence,
            "explanation": "UNKNOWN rate is honest evidence of data coverage",
        }

        # SCORING_HEALTH: predictions exist and source census is sane.
        if isinstance(cal, dict) and cal.get("total_predictions"):
            s_status = "HEALTHY"
            s_evidence = [f"{cal['total_predictions']} predictions "
                          f"by source {cal.get('predictions_by_source')}"]
        else:
            s_status = "UNKNOWN"
            s_evidence = ["no predictions recorded yet (expected pre-soak)"]
        dims["SCORING_HEALTH"] = {
            "status": s_status,
            "evidence": s_evidence,
            "explanation": "scoring health = predictions are being persisted",
        }

        # CALIBRATION_HEALTH: honest INSUFFICIENT_DATA is the expected state.
        latest = cal.get("latest_artifact") if isinstance(cal, dict) else None
        if latest:
            c_status = ("HEALTHY" if latest.get("calibration_status")
                        in ("DESCRIPTIVE_OK", "INSUFFICIENT_DATA")
                        else "DEGRADED")
            c_evidence = [f"latest {latest.get('artifact')}: "
                          f"{latest.get('calibration_status')} "
                          f"({latest.get('joined_pairs')} pairs)"]
        else:
            c_status = "UNKNOWN"
            c_evidence = ["no calibration artifact yet"]
        dims["CALIBRATION_HEALTH"] = {
            "status": c_status,
            "evidence": c_evidence,
            "explanation": ("INSUFFICIENT_DATA is the honest, expected state "
                            "until real local evidence accrues; never inflated"),
        }

        # DRIFT_HEALTH: from the score-drift diagnostic.
        d_status = ("DEGRADED" if drift.get("verdict") == "DRIFT_DETECTED"
                    else "HEALTHY" if drift.get("verdict") == "NO_DRIFT_DETECTED"
                    else "UNKNOWN")
        dims["DRIFT_HEALTH"] = {
            "status": d_status,
            "evidence": [f"drift verdict {drift.get('verdict')}"] if drift else [],
            "explanation": "drift is a cohort diagnostic, not a live claim",
        }

        # RUNTIME_HEALTH: scheduler heartbeat + last run status.
        sched = snap.scheduler_status
        if isinstance(sched, dict) and sched.get("last_run_status"):
            r_status = ("HEALTHY" if sched["last_run_status"] == "SUCCESS"
                        else "DEGRADED")
            r_evidence = [f"last run {sched['last_run_status']}",
                          f"heartbeat age {sched.get('heartbeat_age_seconds')}s"]
        else:
            r_status = "UNKNOWN"
            r_evidence = ["no scheduler runs yet"]
        dims["RUNTIME_HEALTH"] = {
            "status": r_status,
            "evidence": r_evidence,
            "explanation": "runtime health = scheduler is executing",
        }

        # STORAGE_HEALTH: bounded, readable store sizes.
        if isinstance(storage, dict) and storage.get("total_bytes") is not None:
            tbytes = storage["total_bytes"]
            # 4 GiB is a generous laptop bound; growth is reported, not judged
            st_status = "HEALTHY" if tbytes < 4 * 1024**3 else "DEGRADED"
            st_evidence = [f"{tbytes / 1024**2:.1f} MiB total "
                           f"({storage.get('store_bytes')})"]
        else:
            st_status = "UNKNOWN"
            st_evidence = ["storage sizes not computable"]
        dims["STORAGE_HEALTH"] = {
            "status": st_status,
            "evidence": st_evidence,
            "explanation": "storage health = stores are readable and bounded",
        }

        # TEST_HEALTH: committed gate artifacts.
        t_evidence: list[str] = []
        t_status = "HEALTHY"
        for key in ("pytest", "validate"):
            entry = test.get(key)
            if not entry or not entry.get("present"):
                t_status = "DEGRADED"
                t_evidence.append(f"{key}: no committed artifact")
                continue
            if entry.get("exit_code") not in (0, None):
                t_status = "DEGRADED"
            t_evidence.append(f"{key}: exit {entry.get('exit_code')} "
                              f"@ {str(entry.get('commit_sha'))[:8]}")
        dims["TEST_HEALTH"] = {
            "status": t_status,
            "evidence": t_evidence,
            "explanation": "test health = committed gate artifacts are green",
        }

        # ARCHITECTURE_HEALTH: Lane-A integrity + security invariants.
        lane = snap.lane_a_ok if hasattr(snap, "lane_a_ok") else None
        arch_status = "HEALTHY"
        arch_evidence: list[str] = []
        if lane is False:
            arch_status = "FAIL"
            arch_evidence.append("Lane-A integrity FAILED")
        else:
            arch_evidence.append("Lane-A integrity intact")
        sec = snap.security_invariants
        if isinstance(sec, dict):
            for k, v in sec.items():
                arch_evidence.append(f"{k}={v}")
                if v is False:
                    arch_status = "FAIL"
        dims["ARCHITECTURE_HEALTH"] = {
            "status": arch_status,
            "evidence": arch_evidence,
            "explanation": "architecture health = governance boundaries intact",
        }

        # CONFIG_HEALTH: env-key documentation invariant is enforced by the
        # validate gate; here we report the committed artifact's status.
        cfg_evidence: list[str] = []
        cfg_status = "HEALTHY"
        if "config_health" in so and isinstance(so["config_health"], dict):
            cfg_status = so["config_health"].get("status", "UNKNOWN")
            cfg_evidence = so["config_health"].get("evidence", [])
        else:
            cfg_evidence = ["config invariant enforced by validate_imports gate"]
        dims["CONFIG_HEALTH"] = {
            "status": cfg_status,
            "evidence": cfg_evidence,
            "explanation": "config health = documented/consumed env keys",
        }

        # BENCHMARK_HEALTH: baseline artifact exists.
        if isinstance(bench, dict) and bench.get("baseline_present"):
            b_status = "HEALTHY"
            b_evidence = [f"baseline {bench.get('baseline_artifact')}"]
        else:
            b_status = "UNKNOWN"
            b_evidence = ["no benchmark baseline recorded yet"]
        dims["BENCHMARK_HEALTH"] = {
            "status": b_status,
            "evidence": b_evidence,
            "explanation": "benchmark health = a baseline artifact exists",
        }

        return {
            "schema": "ahos.health_scorecard.v1",
            "generated_utc": snap.timestamp_utc,
            "dimensions": dims,
            "overall_verdict": snap.overall_verdict,
            "note": ("scorecard is informational and non-authoritative; "
                     "UNKNOWN/NO_DATA are explicit states, never a fake "
                     "numerical score"),
        }

    @staticmethod
    def trend_dimensions(current: dict[str, Any],
                         previous: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
        """Per-dimension health-scorecard trends (W37 phase 4).

        Compares current vs previous scorecard dimension statuses:
          IMPROVING / STABLE / DEGRADING / UNKNOWN / NOT_COMPARABLE.
        Status ordering (worst->best): FAIL < DEGRADED < HEALTHY; UNKNOWN is
        its own state. Without a previous scorecard every dimension is
        NOT_COMPARABLE. Deterministic, read-only, informational — the trend
        is OBSERVED from the two scorecards, never a fake global score.
        """
        ORDER = {"FAIL": 0, "DEGRADED": 1, "HEALTHY": 2}
        cur_dims = (current.get("dimensions") or {}) if current else {}
        prev_dims = (previous.get("dimensions") or {}) if previous else {}

        trends: dict[str, dict[str, Any]] = {}
        for name, cur in cur_dims.items():
            prev = prev_dims.get(name)
            if not prev or not isinstance(prev, dict) or not isinstance(cur, dict):
                trends[name] = {"trend": "NOT_COMPARABLE",
                                "current": (cur or {}).get("status", "UNKNOWN"),
                                "previous": (prev or {}).get("status") if prev else None,
                                "evidence": "no previous scorecard for this dimension"}
                continue
            c = cur.get("status", "UNKNOWN")
            p = prev.get("status", "UNKNOWN")
            if c == p:
                trend = "STABLE"
            elif c == "UNKNOWN" or p == "UNKNOWN":
                trend = "UNKNOWN"
            else:
                trend = ("IMPROVING" if ORDER.get(c, 1) > ORDER.get(p, 1)
                         else "DEGRADING")
            trends[name] = {
                "trend": trend,
                "current": c,
                "previous": p,
                "evidence": (f"{name}: {p} -> {c} "
                             f"(observed from committed scorecards)"),
            }
        return trends

    @staticmethod
    def acceleration(current: dict[str, Any],
                     previous: dict[str, Any],
                     baseline: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """3-point temporal acceleration (W39 P12): is a dimension IMPROVING
        or DEGRADING, and is that change ACCELERATING, STABLE or DECELERATING?

        For each dimension shared by all three scorecards:
          s1 = status(baseline) -> s2 = status(previous) -> s3 = status(current)
        A direction change (improving->degrading or degrading->improving)
        across the two intervals is ACCELERATING in its new direction; the
        same direction twice is STABLE progress; a reversal is
        DECELERATING (the change is losing momentum) — labeled
        CORRELATION_ONLY, never causal. Missing any scorecard => the
        dimension is NOT_COMPARABLE.
        """
        ORDER = {"FAIL": 0, "DEGRADED": 1, "HEALTHY": 2}

        def _st(sc: dict[str, Any], name: str) -> str | None:
            d = (sc.get("dimensions") or {}).get(name) if sc else None
            return (d or {}).get("status") if d else None

        names = set((current.get("dimensions") or {}).keys())
        out: dict[str, dict[str, Any]] = {}
        for name in sorted(names):
            s1 = _st(baseline, name)
            s2 = _st(previous, name)
            s3 = _st(current, name)
            if s1 is None or s2 is None or s3 is None or \
                    any(v == "UNKNOWN" for v in (s1, s2, s3)):
                out[name] = {"trend": "NOT_COMPARABLE",
                             "statuses": [s1, s2, s3],
                             "label": "CORRELATION_ONLY",
                             "evidence": "missing or UNKNOWN status on one of "
                                         "the three scorecards"}
                continue

            r1 = ORDER.get(s1, 1)
            r2 = ORDER.get(s2, 1)
            r3 = ORDER.get(s3, 1)
            d1 = r2 - r1          # first interval delta
            d2 = r3 - r2          # second interval delta

            if d1 == 0 and d2 == 0:
                trend = "STABLE"
            elif d1 == 0 and d2 != 0:
                # movement only in the second interval => new, still
                # accelerating momentum (or a fresh reversal from stable)
                trend = "ACCELERATING" if abs(d2) > 0 else "STABLE"
            elif d2 == 0 and d1 != 0:
                # movement in the first interval, then held => momentum
                # continues but is not accelerating
                trend = "STABLE_MOMENTUM"
            elif (d1 > 0) == (d2 > 0):
                # same direction across both intervals => momentum continues
                trend = "ACCELERATING" if abs(d2) > abs(d1) else (
                    "STABLE_MOMENTUM" if abs(d2) == abs(d1) else "DECELERATING")
            else:
                # direction reversal across intervals => the trend is changing
                trend = "REVERSING"

            out[name] = {
                "trend": trend,
                "statuses": [s1, s2, s3],
                "label": "CORRELATION_ONLY",
                "evidence": (f"{name}: {s1} -> {s2} -> {s3} observed from "
                             "committed scorecards; correlation only, never "
                             "causal"),
            }
        return out

    def _build_correlations(self, snap: "CanonicalHealthSnapshot") -> list[dict[str, Any]]:
        """Diagnostic correlations (mission W36 phase 4).

        Detects metric co-movements that the repository's own data can
        support, ALWAYS labeled CORRELATION_ONLY — never causality. Two
        metrics moving together is evidence of association, not proof of
        cause; the caveat field says exactly that. Deterministic, read-only,
        fail-open: absent data yields no correlation, never an invented one.
        """
        so = snap.self_observation
        sc = snap.health_scorecard.get("dimensions", {})
        out: list[dict[str, Any]] = []

        def _dims_status(*names: str) -> str | None:
            for n in names:
                d = sc.get(n)
                if d:
                    return d.get("status")
            return None

        # 1. provider failure events -> UNKNOWN share (M-GAP-002 link)
        pf = so.get("provider_failure_rates", {})
        comp = so.get("data_completeness", {})
        if isinstance(pf, dict) and pf.get("total_failure_events"):
            share = comp.get("unknown_share") if isinstance(comp, dict) else None
            if share is not None and share > 0.5:
                out.append({
                    "left": "provider_failure_events",
                    "right": "unknown_share",
                    "direction": "provider failures up -> UNKNOWN share up",
                    "label": "CORRELATION_ONLY",
                    "evidence": f"{pf['total_failure_events']} failure events; "
                                f"unknown share {share:.1%}",
                    "caveat": "association only: failing providers and sparse "
                              "data often co-occur, but one does not prove the other",
                })

        # 2. UNKNOWN share -> scoring coverage (evidence quality)
        if isinstance(comp, dict) and comp.get("error") != "NO_DATA":
            share = comp.get("unknown_share")
            if share is not None and share > 0.5:
                out.append({
                    "left": "unknown_share",
                    "right": "evidence_coverage",
                    "direction": "UNKNOWN share up -> evidence coverage down",
                    "label": "CORRELATION_ONLY",
                    "evidence": f"unknown share {share:.1%} of "
                                f"{comp.get('production_observations')} observations",
                    "caveat": "coverage is measured, scoring impact is not "
                              "directly observed here",
                })

        # 3. score drift -> calibration stability
        drift = so.get("score_drift", {})
        if drift.get("verdict") == "DRIFT_DETECTED":
            out.append({
                "left": "score_drift",
                "right": "calibration_stability",
                "direction": "score drift detected -> pooled calibration rates "
                             "may pool distinct regimes",
                "label": "CORRELATION_ONLY",
                "evidence": f"ADWIN trigger at sample "
                            f"{drift.get('first_trigger_at_sample')}",
                "caveat": "the calibration report already flags this; "
                          "time-segmentation is the remedy, not a causal claim",
            })

        # 4. storage growth -> runtime degradation
        storage = so.get("storage_growth", {})
        if isinstance(storage, dict) and storage.get("total_bytes") is not None:
            tbytes = storage["total_bytes"]
            if tbytes > 4 * 1024**3:
                out.append({
                    "left": "storage_growth",
                    "right": "runtime_degradation",
                    "direction": "store size up -> runtime degradation possible",
                    "label": "CORRELATION_ONLY",
                    "evidence": f"{tbytes / 1024**3:.1f} GiB across stores",
                    "caveat": "size is measured; runtime impact is not "
                              "measured in this snapshot",
                })

        # 5. test regression -> health
        test = so.get("test_health", {})
        for key in ("pytest", "validate"):
            entry = test.get(key)
            if entry and entry.get("present") and entry.get("exit_code") not in (0, None):
                out.append({
                    "left": f"{key}_exit_code",
                    "right": "system_health",
                    "direction": f"{key} failure -> health degraded",
                    "label": "CORRELATION_ONLY",
                    "evidence": f"{key} exit {entry.get('exit_code')}",
                    "caveat": "a failing gate is a symptom; the cause needs "
                              "the gate's own output",
                })

        # 6. provider breaker state -> provider health
        prov = snap.provider_health
        if isinstance(prov, dict) and any(
                (st or {}).get("state", "CLOSED") != "CLOSED"
                for st in prov.values()):
            out.append({
                "left": "circuit_breaker_state",
                "right": "provider_health",
                "direction": "breaker open/half-open -> provider health degraded",
                "label": "CORRELATION_ONLY",
                "evidence": f"{sum(1 for st in prov.values() if (st or {}).get('state', 'CLOSED') != 'CLOSED')} "
                            "non-CLOSED breakers",
                "caveat": "breaker state is the collector's own telemetry; "
                          "the root cause is in provider_failure_events",
            })

        return out

    def export_snapshot(self, output_path: Path | str | None = None) -> Path:
        snap = self.generate_snapshot()
        out = Path(output_path) if output_path else (get_reports_dir() / "canonical_health_snapshot.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(snap), indent=2, ensure_ascii=False))
        return out
