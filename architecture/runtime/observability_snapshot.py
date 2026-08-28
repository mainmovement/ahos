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

import hashlib
import json
import logging
import os
import re
import sqlite3
import subprocess
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

log = logging.getLogger("ahos.runtime.observability_snapshot")

# Governance pins (same values as lifecycle + test_e01_gate_protocol).
_MASTER_DIRECTIVE_SHA256 = (
    "e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79"
)
_E01_PROTOCOL_SHA256 = (
    "16b86b86e89392c3f84d82a1c2c6d87534fea988c4dff5a1454fcc137a168101"
)
_E01_PROTOCOL_REL = Path("docs/mission_v1_1/E01_GATE_PROTOCOL_v1.md")
_MASTER_DIRECTIVE_REL = Path("docs/canonical/MASTER_DIRECTIVE_v1.md")


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def _quote_sqlite_ident(name: str) -> str:
    """Validate + quote a SQLite identifier for dynamic FROM clauses."""
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"unsafe sqlite identifier: {name!r}")
    return '"' + name.replace('"', '""') + '"'


def _git_head_sha(root: Path) -> str | None:
    """Best-effort HEAD SHA for stale-artifact detection; None if unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode("utf-8").strip() or None
    except Exception:
        return None


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return None


def _lane_a_integrity(root: Path) -> tuple[bool | None, str]:
    """Verify Lane-A freeze. Fail-closed on unverifiable state (None => UNKNOWN).

    Newly discovered untracked Lane-A paths are NOT silently OK — they are
    UNKNOWN until the freeze manifest is deliberately re-anchored.
    """
    try:
        from scripts import freeze_lane_a as freeze_lane
        drift, missing, untracked = freeze_lane.verify(root=root)
        if drift or missing:
            detail = (
                f"lane_a_freeze_drift: drift={sorted(drift)}"
                if drift
                else f"lane_a_freeze_missing: {sorted(missing)}"
            )
            return False, detail
        if untracked:
            return None, f"lane_a_untracked_files: {sorted(untracked)}"
        return True, "lane_a_freeze_ok"
    except Exception as e:
        return None, f"lane_a_freeze_unverifiable: {type(e).__name__}: {e}"


@dataclass
class CanonicalHealthSnapshot:
    timestamp_utc: str
    overall_verdict: str                        # GREEN | DEGRADED | WARNING | CRITICAL | UNKNOWN
    system_uptime_seconds: float | None         # None when process start time is unknown
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
    # Explicit Lane-A freeze result for scorecard ARCHITECTURE_HEALTH.
    # None = unverifiable (UNKNOWN), never silently assumed intact.
    lane_a_ok: bool | None = None
    lane_a_detail: str = ""
    telemetry_health: dict[str, Any] = field(default_factory=dict)


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
    "TELEMETRY_HEALTH",
)

# Only recent durable provider failures degrade the overall verdict.
_PROVIDER_FAILURE_VERDICT_WINDOW_SEC = 24 * 3600.0


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
    def __init__(
        self,
        root_dir: Path | str | None = None,
        *,
        metrics_tracker: Any | None = None,
    ):
        self.root = Path(root_dir) if root_dir else get_project_root()
        # Optional live tracker; never constructed here (construction mutates DB).
        self._metrics_tracker = metrics_tracker

    def generate_snapshot(self, now: float | None = None) -> CanonicalHealthSnapshot:
        ts = time.time() if now is None else now
        ts_utc = datetime.fromtimestamp(ts, timezone.utc).isoformat()
        reasons: list[str] = []
        is_degraded = False
        is_critical = False
        is_warning = False
        # Process uptime is UNKNOWN unless a lifecycle start timestamp exists.
        # Heartbeat age is tracked separately under scheduler_status.
        process_uptime_seconds: float | None = None

        # 1. Database Integrity & Row Census (paths resolved WITHOUT mkdir)
        dbs = {
            "e01_discovery": get_discovery_db_path(create_dir=False),
            "paper_trading": get_paper_trading_db_path(create_dir=False),
            "ahos_local": get_local_db_path(create_dir=False),
            "ahos_knowledge": get_knowledge_db_path(create_dir=False),
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
                    tables = [
                        t[0]
                        for t in cur.execute(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        ).fetchall()
                    ]
                    total_rows = 0
                    unsafe_tables: list[str] = []
                    for t in tables:
                        try:
                            q = _quote_sqlite_ident(t)
                            total_rows += cur.execute(
                                f"SELECT COUNT(*) FROM {q}"
                            ).fetchone()[0]
                        except ValueError:
                            unsafe_tables.append(t)
                    conn.close()
                    ok = (integ and integ[0] == "ok")
                    db_results[name] = {
                        "exists": True,
                        "integrity": "OK" if ok else str(integ),
                        "tables_count": len(tables),
                        "total_rows": total_rows,
                        "unsafe_table_names_skipped": unsafe_tables,
                        # Integrity OK ≠ expected schema present.
                        "schema_census": "INTEGRITY_ONLY_NOT_SCHEMA_VERIFIED",
                    }
                    if not ok:
                        is_critical = True
                        reasons.append(f"Database {name} integrity check failed: {integ}")
                except Exception as e:
                    db_results[name] = {"exists": True, "integrity": "ERROR", "error": str(e)}
                    is_critical = True
                    reasons.append(f"Database {name} read error: {e}")

        # 2. Track B Accounting — remaining allocated + realized P&L.
        # Conservation: cash + remaining_basis == BANKROLL_START + SUM(realized_pnl).
        # Fresh install (no INIT ledger) is UNKNOWN consistency, not fabricated $20 OK.
        track_b: dict[str, Any] = {}
        try:
            conn_pt = connect_sqlite_ro(get_paper_trading_db_path(create_dir=False))
            conn_pt.row_factory = sqlite3.Row
            cur_pt = conn_pt.cursor()
            exit_cols = {
                r[1]
                for r in cur_pt.execute("PRAGMA table_info(paper_exit_v3)").fetchall()
            } if cur_pt.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_exit_v3'"
            ).fetchone() else set()
            trade_cols = {
                r[1] for r in cur_pt.execute("PRAGMA table_info(paper_trade_v2)").fetchall()
            }
            has_exit_v3 = "allocated_retired_usd" in exit_cols and "trade_id" in trade_cols
            if has_exit_v3:
                rows = cur_pt.execute(
                    "SELECT t.amount_allocated AS amount_allocated, "
                    "COALESCE((SELECT SUM(x.allocated_retired_usd) "
                    " FROM paper_exit_v3 x WHERE x.trade_id = t.trade_id), 0) "
                    " AS retired "
                    "FROM paper_trade_v2 t"
                ).fetchall()
                remaining = [
                    max(0.0, float(r["amount_allocated"]) - float(r["retired"]))
                    for r in rows
                ]
                allocated = sum(remaining)
                open_positions = sum(1 for rem in remaining if rem > 1e-9)
                closed_positions = sum(1 for rem in remaining if rem <= 1e-9)
                if "realized_pnl_usd" in exit_cols:
                    realized = float(
                        cur_pt.execute(
                            "SELECT COALESCE(SUM(realized_pnl_usd), 0) FROM paper_exit_v3"
                        ).fetchone()[0]
                    )
                else:
                    realized = 0.0
            else:
                trades = cur_pt.execute(
                    "SELECT amount_allocated FROM paper_trade_v2"
                ).fetchall()
                allocated = sum(float(t["amount_allocated"]) for t in trades)
                open_positions = len(trades)
                closed_positions = 0
                realized = 0.0
            ledger = cur_pt.execute(
                "SELECT cash_after FROM portfolio_ledger ORDER BY rowid ASC"
            ).fetchall()
            cash = float(ledger[-1]["cash_after"]) if ledger else 0.0
            conn_pt.close()

            from paper_trading.bankroll import BANKROLL_START_USD

            initialised = bool(ledger)
            total_sum = round(cash + allocated, 7)
            expected_equity = round(BANKROLL_START_USD + realized, 7)
            if not initialised:
                # No INIT event — consistency is UNKNOWN, not a fake $20 healthy.
                consistent: bool | None = None if allocated == 0.0 else False
            else:
                consistent = abs(total_sum - expected_equity) < 1e-6

            track_b = {
                "virtual_bankroll_initial_usd": BANKROLL_START_USD,
                "bankroll_initialised": initialised,
                "cash_balance_usd": cash,
                "allocated_capital_usd": allocated,
                "realized_pnl_usd": realized,
                "expected_equity_usd": expected_equity if initialised else None,
                "accounting_sum_usd": total_sum if initialised else None,
                "is_accounting_consistent": consistent,
                "open_positions_count": open_positions,
                "closed_positions_count": closed_positions,
                "allocated_basis": (
                    "remaining_after_exit_retirement"
                    if has_exit_v3
                    else "gross_paper_trade_v2"
                ),
                "conservation_law": (
                    "cash + remaining_allocated == BANKROLL_START + realized_pnl"
                ),
                "execution_mode": "PAPER_ONLY_CONTRACT",
            }
            if consistent is False:
                is_critical = True
                if initialised:
                    reasons.append(
                        f"Track B accounting mismatch: cash+allocated = ${total_sum} "
                        f"!= expected ${expected_equity} "
                        f"(start ${BANKROLL_START_USD} + realized ${realized})"
                    )
                else:
                    reasons.append(
                        f"Track B has ${allocated} allocated with no portfolio ledger entry"
                    )
            elif consistent is None:
                is_warning = True
                reasons.append("Track B bankroll not initialised (accounting UNKNOWN)")
        except Exception as e:
            track_b = {"error": str(e), "is_accounting_consistent": False}
            is_critical = True

        # 3. E-01 Experiment State
        e01_state: dict[str, Any] = {}
        try:
            conn_e01 = connect_sqlite_ro(get_discovery_db_path(create_dir=False))
            cur_e01 = conn_e01.cursor()
            tokens_cnt = cur_e01.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
            obs_cnt = cur_e01.execute(
                "SELECT COUNT(*) FROM discovery_observations"
            ).fetchone()[0]
            gaps_cnt = cur_e01.execute("SELECT COUNT(*) FROM gap_register").fetchone()[0]
            resolved_cnt = cur_e01.execute(
                "SELECT COUNT(*) FROM observation_state WHERE state='RESOLVED'"
            ).fetchone()[0]
            dead_cnt = cur_e01.execute(
                "SELECT COUNT(*) FROM observation_state WHERE state='DEAD'"
            ).fetchone()[0]
            covered_72h = cur_e01.execute(
                "SELECT COUNT(DISTINCT token_id) FROM outcome_label WHERE horizon='72h'"
            ).fetchone()[0]
            conn_e01.close()

            threshold = 200
            if covered_72h >= threshold:
                # Threshold met ≠ statistically validated gate pass.
                official = "THRESHOLD_MET_NOT_VALIDATED"
                validation = "THRESHOLD MET — NOT YET VALIDATED (gate decision required)"
            else:
                official = "INSUFFICIENT_DATA"
                validation = "NOT YET VALIDATED (statistically honest)"

            e01_state = {
                "total_tokens_observed": tokens_cnt,
                "total_observations_recorded": obs_cnt,
                "total_gaps_registered": gaps_cnt,
                "tokens_resolved": resolved_cnt,
                "tokens_dead": dead_cnt,
                "covered_72h_outcomes": covered_72h,
                "required_threshold": threshold,
                "official_verdict": official,
                "validation_status": validation,
            }
        except Exception as e:
            e01_state = {"error": str(e), "official_verdict": "UNKNOWN"}

        # 4. Scheduler & Lease Locks Health
        sched_health: dict[str, Any] = {}
        try:
            conn_loc = connect_sqlite_ro(get_local_db_path(create_dir=False))
            conn_loc.row_factory = sqlite3.Row
            cur_loc = conn_loc.cursor()
            hb = cur_loc.execute("SELECT * FROM scheduler_heartbeats ORDER BY last_heartbeat_ts DESC LIMIT 1").fetchone()
            runs = cur_loc.execute("SELECT * FROM scheduler_runs ORDER BY started_ts DESC LIMIT 1").fetchone()
            locks = cur_loc.execute("SELECT * FROM scheduler_locks").fetchall()
            metrics = cur_loc.execute("SELECT * FROM runtime_operational_metrics ORDER BY rowid DESC LIMIT 5").fetchall()
            conn_loc.close()

            last_hb_ts = hb["last_heartbeat_ts"] if hb else 0.0
            downtime = max(0.0, ts - last_hb_ts) if last_hb_ts else None
            last_status = runs["status"] if runs else "NO_RUNS_YET"
            sched_health = {
                "active_locks_count": len(locks),
                "last_run_id": runs["run_id"] if runs else None,
                "last_run_status": last_status,
                "last_heartbeat_utc": hb["last_heartbeat_utc"] if hb else None,
                "heartbeat_age_seconds": round(downtime, 2) if downtime is not None else None,
                "recent_operational_metrics": [dict(m) for m in metrics],
            }
            if last_status not in ("SUCCESS", "NO_RUNS_YET") and runs:
                is_degraded = True
                reasons.append(f"last scheduler run status={last_status}")
            if last_status == "SUCCESS" and downtime is None:
                is_warning = True
                reasons.append("last run SUCCESS but no heartbeat evidence")
        except Exception as e:
            sched_health = {"error": str(e)}
            is_warning = True
            reasons.append(f"scheduler status unreadable: {e}")

        # 5. Providers — NEVER invent CLOSED breakers from a fresh CollectorEngine
        #    (that also mutates discovery DB via CREATE TABLE). Prefer durable
        #    failure-event census; breaker state remains UNKNOWN without a live process.
        prov_health: dict[str, Any] = {
            "breaker_state_source": "UNAVAILABLE",
            "note": (
                "circuit breakers are process-local; snapshot does not construct "
                "a CollectorEngine (would mutate DB and fabricate CLOSED)"
            ),
            "providers": {},
        }
        try:
            conn_pf = connect_sqlite_ro(get_discovery_db_path(create_dir=False))
            conn_pf.row_factory = sqlite3.Row
            rows = conn_pf.execute(
                "SELECT provider_id, COUNT(*) AS n, MAX(event_ts) AS last_ts "
                "FROM provider_failure_events GROUP BY provider_id"
            ).fetchall()
            conn_pf.close()
            prov_health["durable_failure_events_by_provider"] = {
                r["provider_id"]: {
                    "count": r["n"],
                    "last_event_utc": _utc(r["last_ts"]) if r["last_ts"] else None,
                }
                for r in rows
            }
            prov_health["durable_failure_event_total"] = sum(r["n"] for r in rows)
            recent_fail_n = 0
            for r in rows:
                last_ts = r["last_ts"]
                if isinstance(last_ts, (int, float)) and (ts - float(last_ts)) <= _PROVIDER_FAILURE_VERDICT_WINDOW_SEC:
                    recent_fail_n += int(r["n"])
            prov_health["durable_failure_events_recent_window_sec"] = (
                _PROVIDER_FAILURE_VERDICT_WINDOW_SEC
            )
            prov_health["durable_failure_event_recent_total"] = recent_fail_n
            # Lifetime census is informational; only recent failures degrade overall.
            if recent_fail_n > 0:
                is_degraded = True
                reasons.append(
                    f"{recent_fail_n} durable provider failure events "
                    f"within {_PROVIDER_FAILURE_VERDICT_WINDOW_SEC:.0f}s"
                )
            elif rows:
                reasons.append(
                    f"{sum(r['n'] for r in rows)} lifetime durable provider "
                    "failure events (outside recent window; informational)"
                )
        except Exception as e:
            prov_health["durable_failure_events_error"] = str(e)

        # 6. Telegram Adapter Status — do not claim an active gate when open.
        bot_tok = os.environ.get("TELEGRAM_BOT_TOKEN")
        has_token = bool(bot_tok and ":" in bot_tok)
        allow_raw = (os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS") or "").strip()
        allow_configured = bool(allow_raw)
        tg_status = {
            "mode": "PRODUCTION_KEYED" if has_token else "MOCK_LOCAL_OFFLINE",
            "bot_token_present": has_token,
            "security_gate_mode": (
                "RESTRICTED" if allow_configured else "OPEN_ACCESS"
            ),
            "security_gate_active": allow_configured,
            "persian_nlu_intents_count": 11,
            "response_contract": "Section X Format with Mandatory Persian Footer",
        }

        # 7. AI Router — configured facts vs unobserved runtime claims.
        ai_status: dict[str, Any]
        try:
            from architecture.provider_router import load_registry
            ai_reg = load_registry()
            providers_list = list(ai_reg.get("providers", {}).keys()) if isinstance(ai_reg, dict) else []
            has_nvidia_key = bool(os.environ.get("NVIDIA_API_KEY"))
            cost_raw = (
                (ai_reg.get("governance") or {}).get("cost_ceiling_usd_month", 0.0)
                if isinstance(ai_reg, dict)
                else 0.0
            )
            try:
                cost_ceiling = float(cost_raw)
            except (TypeError, ValueError):
                cost_ceiling = None
            ai_status = {
                "deterministic_floor_configured": True,
                "deterministic_floor_active": None,  # not observed this snapshot
                "cost_ceiling_usd_month": cost_ceiling,
                "registered_providers_count": len(providers_list),
                "nvidia_nim_configured": "nvidia_nim" in providers_list,
                "nvidia_key_present": has_nvidia_key,
                "ai_decision_authority": "ZERO (Advisory Only — code contract)",
                "authority_observed_this_snapshot": False,
            }
        except Exception as e:
            ai_status = {
                "error": f"{type(e).__name__}",
                "ai_decision_authority": "ZERO (Advisory Only — code contract)",
                "authority_observed_this_snapshot": False,
            }
            is_warning = True
            reasons.append(f"AI registry unreadable: {type(e).__name__}")

        # 8. Security invariants — measured; unset paper flag => UNKNOWN not True.
        paper_ok: bool | None = None
        live_prohibited: bool | None = None
        paper_mode = "unknown"
        security_inv_extra: dict[str, Any] = {}
        try:
            from architecture.security import assert_safe_environment
            from architecture.security.hygiene import _env_flag_enabled

            env_audit = assert_safe_environment()
            paper_mode = str(env_audit.get("ahos_paper_only_env") or "unknown")
            raw_paper = os.environ.get("AHOS_PAPER_ONLY")
            if raw_paper is None or str(raw_paper).strip() == "":
                # Default-safe path exists, but the env flag is not explicitly set.
                paper_ok = None
            else:
                paper_ok = bool(_env_flag_enabled(raw_paper))
            live_prohibited = bool(env_audit.get("live_trading_flags_absent",
                                                 env_audit.get("zero_real_trading")))
            security_inv_extra = {
                "paper_only_explicit": bool(env_audit.get("paper_only_explicit")),
                "paper_only_unset": bool(env_audit.get("paper_only_unset")),
                "live_trading_flags_absent": bool(
                    env_audit.get("live_trading_flags_absent",
                                  env_audit.get("zero_real_trading"))
                ),
            }
        except PermissionError as e:
            is_critical = True
            reasons.append(f"security veto: {e}")
            paper_ok = False
            live_prohibited = False
            security_inv_extra = {
                "paper_only_explicit": False,
                "paper_only_unset": False,
                "live_trading_flags_absent": False,
            }
        except Exception as e:
            is_critical = True
            reasons.append(f"security audit failed: {type(e).__name__}: {e}")
            security_inv_extra = {}

        master_path = self.root / _MASTER_DIRECTIVE_REL
        master_sha = _file_sha256(master_path)
        master_pinned = master_sha == _MASTER_DIRECTIVE_SHA256
        if not master_pinned:
            is_critical = True
            reasons.append("master_directive_hash mismatch or missing")

        e01_path = self.root / _E01_PROTOCOL_REL
        e01_sha = _file_sha256(e01_path)
        e01_pinned = e01_sha == _E01_PROTOCOL_SHA256
        if not e01_pinned:
            is_critical = True
            reasons.append("e01_protocol_hash mismatch or missing")

        env_not_tracked: bool | None = None
        try:
            probe = subprocess.run(
                ["git", "ls-files", "--error-unmatch", ".env"],
                cwd=str(self.root),
                capture_output=True,
                timeout=5,
            )
            env_not_tracked = probe.returncode != 0
        except Exception:
            env_not_tracked = None  # UNKNOWN — never fail-open to True
        if env_not_tracked is False:
            is_critical = True
            reasons.append(".env is tracked by git (secret-in-source risk)")

        security_inv = {
            "ahos_paper_only_enforced": paper_ok,
            "ahos_paper_only_env": paper_mode,
            "live_trading_prohibited": live_prohibited,
            "zero_secret_in_source": env_not_tracked,
            "zero_secret_check_scope": "root_.env_untracked_only",
            "master_directive_hash_pinned": master_pinned,
            "e01_protocol_hash_pinned": e01_pinned,
            **security_inv_extra,
        }
        if paper_ok is None:
            is_warning = True
            reasons.append(
                "AHOS_PAPER_ONLY unset (default-safe assumed; not explicitly enforced)"
            )

        # 9. Lane-A freeze integrity (never assume intact via hasattr miss).
        lane_a_ok, lane_a_detail = _lane_a_integrity(self.root)
        if lane_a_ok is False:
            is_critical = True
            reasons.append(lane_a_detail)
        elif lane_a_ok is None:
            is_warning = True
            reasons.append(lane_a_detail)

        hb_age = (
            sched_health.get("heartbeat_age_seconds")
            if isinstance(sched_health, dict) else None
        )
        if isinstance(hb_age, (int, float)) and hb_age > 3600:
            is_warning = True
            reasons.append(f"scheduler heartbeat age {hb_age}s exceeds 1h")

        # 9b. Telemetry writer health — never invent OK without a live tracker.
        telemetry_health: dict[str, Any]
        try:
            from architecture.runtime.metrics import OperationalMetricsTracker
            if self._metrics_tracker is not None:
                telemetry_health = dict(self._metrics_tracker.telemetry_health())
                telemetry_health["source"] = "injected_tracker"
            else:
                registered = OperationalMetricsTracker.registered_telemetry_health()
                if registered is None:
                    telemetry_health = {
                        "status": "UNKNOWN",
                        "write_failures": None,
                        "recent_failures": [],
                        "source": "no_live_tracker",
                        "note": (
                            "snapshot does not construct OperationalMetricsTracker "
                            "(would mkdir/CREATE); no in-process tracker registered"
                        ),
                    }
                else:
                    telemetry_health = registered
            if telemetry_health.get("status") == "DEGRADED":
                is_warning = True
                reasons.append(
                    f"telemetry write failures="
                    f"{telemetry_health.get('write_failures')}"
                )
        except Exception as e:
            telemetry_health = {
                "status": "UNKNOWN",
                "error": f"{type(e).__name__}: {e}",
                "source": "probe_failed",
            }
            is_warning = True
            reasons.append(f"telemetry_health unreadable: {type(e).__name__}")

        # Overall verdict — GREEN | DEGRADED | WARNING | CRITICAL | UNKNOWN.
        if is_critical:
            verdict = "CRITICAL"
        elif is_degraded:
            verdict = "DEGRADED"
        elif is_warning:
            verdict = "WARNING"
        else:
            verdict = "GREEN"

        # runtime_state from scheduler evidence — never invent RUNNING from GREEN.
        if isinstance(sched_health, dict) and sched_health.get("error"):
            runtime_state = "UNKNOWN"
        else:
            last_run = (
                sched_health.get("last_run_status")
                if isinstance(sched_health, dict) else None
            )
            age = (
                sched_health.get("heartbeat_age_seconds")
                if isinstance(sched_health, dict) else None
            )
            if last_run in (None, "NO_RUNS_YET"):
                runtime_state = "IDLE"
            elif last_run == "SUCCESS":
                if not isinstance(age, (int, float)):
                    runtime_state = "UNKNOWN"  # success without heartbeat evidence
                elif age > 3600:
                    runtime_state = "STALE"
                else:
                    runtime_state = "RUNNING"
            else:
                runtime_state = "DEGRADED"

        obs_total = e01_state.get("total_observations_recorded")
        gap_total = e01_state.get("total_gaps_registered")
        snapshot = CanonicalHealthSnapshot(
            timestamp_utc=ts_utc,
            overall_verdict=verdict,
            system_uptime_seconds=process_uptime_seconds,
            runtime_state=runtime_state,
            scheduler_status=sched_health,
            observation_metrics={
                "total_gaps": gap_total,
                "total_obs": obs_total,
            },
            provider_health=prov_health,
            database_integrity=db_results,
            e01_experiment_state=e01_state,
            track_b_accounting=track_b,
            telegram_adapter_status=tg_status,
            ai_router_status=ai_status,
            security_invariants=security_inv,
            self_observation=self._self_observation_report(ts),
            summary_reasons=reasons,
            lane_a_ok=lane_a_ok,
            lane_a_detail=lane_a_detail,
            telemetry_health=telemetry_health,
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
            conn = connect_sqlite_ro(get_discovery_db_path(create_dir=False))
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
        # Treat NULL / empty / '[]' / 'null' / '{}' as "no unknown fields listed".
        completeness: dict[str, Any] = {}
        try:
            conn = connect_sqlite_ro(get_discovery_db_path(create_dir=False))
            conn.row_factory = sqlite3.Row
            total = conn.execute(
                "SELECT COUNT(*) AS n FROM production_observations"
            ).fetchone()["n"]
            unknown_rows = conn.execute(
                "SELECT COUNT(*) AS n FROM production_observations "
                "WHERE unknown_fields_json IS NOT NULL "
                "AND length(trim(unknown_fields_json)) > 0 "
                "AND lower(trim(unknown_fields_json)) NOT IN "
                "('[]', 'null', '{}', '\"\"')"
            ).fetchone()["n"]
            distinct_tokens = conn.execute(
                "SELECT COUNT(DISTINCT token_address) AS n "
                "FROM production_observations"
            ).fetchone()["n"]
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
        # score_drift is sourced from the same artifact (never a phantom key).
        calibration: dict[str, Any] = {}
        score_drift: dict[str, Any] = {"error": "NO_DATA", "verdict": None}
        try:
            conn = connect_sqlite_ro(get_local_db_path(create_dir=False))
            conn.row_factory = sqlite3.Row
            by_source = conn.execute(
                "SELECT source, COUNT(*) AS n FROM opportunity_score_ledger "
                "GROUP BY source ORDER BY source"
            ).fetchall()
            total_preds = sum(r["n"] for r in by_source)
            conn.close()
            calibration["predictions_by_source"] = {
                r["source"]: r["n"] for r in by_source
            }
            calibration["total_predictions"] = total_preds
        except Exception:
            calibration["predictions_by_source"] = "NO_DATA"
            calibration["total_predictions"] = None

        newest: dict[str, Any] | None = None
        try:
            cands = sorted(
                (self.root / "reports").glob("calibration_20*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if cands:
                data = json.loads(cands[0].read_text(encoding="utf-8"))
                newest = {
                    "artifact": cands[0].name,
                    "calibration_status": data.get("calibration_status"),
                    "joined_pairs": data.get("number_of_eligible_pairs"),
                    "schema": data.get("schema"),
                }
                raw_drift = data.get("score_drift")
                if isinstance(raw_drift, dict) and raw_drift:
                    score_drift = dict(raw_drift)
                    score_drift.setdefault("artifact", cands[0].name)
                else:
                    score_drift = {
                        "verdict": "INSUFFICIENT_DATA",
                        "reason": "calibration artifact lacks score_drift block",
                        "artifact": cands[0].name,
                    }
        except Exception:
            newest = None
        calibration["latest_artifact"] = newest

        # 4. Test / regression health — committed artifacts may be STALE vs HEAD.
        test_health: dict[str, Any] = {}
        head_sha = _git_head_sha(self.root)
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
                artifact_sha = (data.get("git") or {}).get("commit_sha")
                stale = bool(
                    head_sha and artifact_sha and artifact_sha != head_sha
                )
                entry: dict[str, Any] = {
                    "present": True,
                    "timestamp_utc": data.get("timestamp_utc"),
                    "commit_sha": artifact_sha,
                    "head_sha": head_sha,
                    "stale_vs_head": stale,
                    "exit_code": data.get("exit_code"),
                }
                # Writers emit pytest_summary; older artifacts may use summary.
                summary = (
                    data.get("pytest_summary")
                    or data.get("summary")
                    or {}
                )
                if not isinstance(summary, dict):
                    summary = {}
                for f in fields:
                    if f in summary:
                        entry[f] = summary[f]
                # Unverifiable freshness (missing SHA or HEAD) is not "current".
                if entry.get("exit_code") is None or not artifact_sha or not head_sha:
                    entry["evidence_completeness"] = "INCOMPLETE"
                else:
                    entry["evidence_completeness"] = "COMPLETE"
                test_health[key] = entry
            except Exception:
                test_health[key] = {"present": True, "error": "unparseable"}

        # 5. Storage growth: live store sizes in bytes.
        storage: dict[str, Any] = {}
        try:
            stores = {
                "e01_discovery": get_discovery_db_path(create_dir=False),
                "paper_trading": get_paper_trading_db_path(create_dir=False),
                "ahos_local": get_local_db_path(create_dir=False),
                "ahos_knowledge": get_knowledge_db_path(create_dir=False),
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

        # 7. Config health: validate-gate artifact + offline-mode observation.
        config_health: dict[str, Any] = {}
        vp = self.root / "reports" / "validate_imports_run.json"
        if vp.exists():
            try:
                data = json.loads(vp.read_text(encoding="utf-8"))
                artifact_sha = (data.get("git") or {}).get("commit_sha")
                head_sha = _git_head_sha(self.root)
                stale = bool(head_sha and artifact_sha and artifact_sha != head_sha)
                incomplete = not artifact_sha or not head_sha
                if data.get("exit_code") != 0:
                    cfg_status = "DEGRADED"
                elif stale or incomplete:
                    cfg_status = "UNKNOWN"
                else:
                    cfg_status = "HEALTHY"
                config_health = {
                    "status": cfg_status,
                    "stale_vs_head": stale,
                    "evidence_completeness": (
                        "INCOMPLETE" if incomplete else "COMPLETE"
                    ),
                    "evidence": [
                        f"validate_imports exit {data.get('exit_code')} "
                        f"@ {str(artifact_sha)[:8] if artifact_sha else 'NONE'} "
                        f"(head {str(head_sha)[:8] if head_sha else 'UNKNOWN'}; "
                        f"{'STALE' if stale else ('INCOMPLETE' if incomplete else 'current')})"
                    ],
                }
            except Exception:
                config_health = {"status": "UNKNOWN", "evidence": ["unparseable"]}
        else:
            config_health = {"status": "UNKNOWN", "evidence": ["no artifact"]}

        # offline-mode configuration (W37 phase 15): surface as OBSERVED state.
        try:
            from config.offline_mode import get_offline_config
            off = get_offline_config()
            config_health["offline_mode"] = {
                "active": off.offline_mode_active,
                "allow_external_http": off.allow_external_http,
                "source": "AHOS_OFFLINE_MODE env (default 0)",
                "enforcement": "OBSERVED_ONLY",
                "note": (
                    "offline_mode is observational config; providers/Telegram "
                    "are not automatically blocked by this flag"
                ),
            }
        except Exception:
            config_health["offline_mode"] = {"error": "NO_DATA"}

        return {
            "generated_utc": now_utc,
            "provider_failure_rates": provider_failures,
            "data_completeness": completeness,
            "calibration_state": calibration,
            "score_drift": score_drift,
            "test_health": test_health,
            "storage_growth": storage,
            "benchmark_health": benchmark_health,
            "config_health": config_health,
            "informational_note": (
                "self-observation is informational and does "
                "not drive the overall verdict"
            ),
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

        # PROVIDER_HEALTH: recent durable failures; lifetime census is informational.
        p_evidence: list[str] = []
        if isinstance(prov, dict) and prov.get("breaker_state_source") == "UNAVAILABLE":
            recent_fail = prov.get("durable_failure_event_recent_total")
            total_fail = prov.get("durable_failure_event_total")
            if isinstance(recent_fail, int) and recent_fail > 0:
                p_status = "DEGRADED"
                p_evidence.append(f"{recent_fail} recent durable failure events")
            elif "durable_failure_events_error" in prov:
                p_status = "UNKNOWN"
                p_evidence.append(f"failure-event read error: {prov['durable_failure_events_error']}")
            else:
                p_status = "UNKNOWN"
                p_evidence.append("no live breaker telemetry; zero recent durable failures")
            if isinstance(total_fail, int) and total_fail > 0:
                p_evidence.append(f"{total_fail} lifetime durable failure events (informational)")
            p_evidence.append(str(prov.get("note") or "breakers UNAVAILABLE"))
        elif isinstance(prov, dict) and prov.get("providers"):
            p_status = "HEALTHY"
            for pid, st in (prov.get("providers") or {}).items():
                state = (st or {}).get("state", "UNKNOWN")
                if state != "CLOSED":
                    p_status = "DEGRADED"
                p_evidence.append(f"{pid}: {state}")
        else:
            p_status = "UNKNOWN"
            p_evidence.append("no provider health data")
        pf = so.get("provider_failure_rates", {})
        if isinstance(pf, dict) and pf.get("total_failure_events"):
            # Lifetime self-obs census is informational — do not upgrade UNKNOWN→DEGRADED.
            p_evidence.append(f"{pf['total_failure_events']} durable failure events (self-obs lifetime)")
        dims["PROVIDER_HEALTH"] = {
            "status": p_status,
            "evidence": p_evidence,
            "explanation": (
                "provider health prefers durable failure events; "
                "fresh in-memory CLOSED breakers are never invented"
            ),
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

        # CALIBRATION_HEALTH: INSUFFICIENT_DATA is UNKNOWN (honest), not HEALTHY.
        latest = cal.get("latest_artifact") if isinstance(cal, dict) else None
        if latest:
            cal_status = latest.get("calibration_status")
            if cal_status == "DESCRIPTIVE_OK":
                c_status = "HEALTHY"
            elif cal_status == "INSUFFICIENT_DATA":
                c_status = "UNKNOWN"
            elif cal_status is None:
                c_status = "UNKNOWN"
            else:
                c_status = "DEGRADED"
            c_evidence = [
                f"latest {latest.get('artifact')}: {cal_status} "
                f"({latest.get('joined_pairs')} pairs)"
            ]
        else:
            c_status = "UNKNOWN"
            c_evidence = ["no calibration artifact yet"]
        dims["CALIBRATION_HEALTH"] = {
            "status": c_status,
            "evidence": c_evidence,
            "explanation": (
                "INSUFFICIENT_DATA means calibration is not demonstrated; "
                "report UNKNOWN, never inflate to HEALTHY"
            ),
        }

        # DRIFT_HEALTH: from calibration score_drift (populated explicitly).
        # INSUFFICIENT_DATA / NO_DATA => UNKNOWN (never fake HEALTHY).
        drift_verdict = drift.get("verdict") if isinstance(drift, dict) else None
        if drift_verdict == "DRIFT_DETECTED":
            d_status = "DEGRADED"
        elif drift_verdict == "NO_DRIFT_DETECTED":
            d_status = "HEALTHY"
        else:
            d_status = "UNKNOWN"
        dims["DRIFT_HEALTH"] = {
            "status": d_status,
            "evidence": (
                [f"drift verdict {drift_verdict}"]
                + ([drift.get("reason")] if drift.get("reason") else [])
                if isinstance(drift, dict) and drift_verdict
                else ["score_drift not available"]
            ),
            "explanation": "drift is a cohort diagnostic, not a live claim",
        }

        # RUNTIME_HEALTH: NO_RUNS_YET / missing heartbeat = UNKNOWN, not HEALTHY/DEGRADED.
        sched = snap.scheduler_status
        if not isinstance(sched, dict) or sched.get("error"):
            r_status = "UNKNOWN"
            r_evidence = [f"scheduler unreadable: {sched.get('error') if isinstance(sched, dict) else 'missing'}"]
        else:
            last_status = sched.get("last_run_status")
            if last_status in (None, "NO_RUNS_YET"):
                r_status = "UNKNOWN"
                r_evidence = ["no scheduler runs yet"]
            elif last_status == "SUCCESS":
                age = sched.get("heartbeat_age_seconds")
                if not isinstance(age, (int, float)):
                    r_status = "UNKNOWN"
                    r_evidence = [
                        f"last run {last_status}",
                        "heartbeat age missing — not live evidence",
                    ]
                elif age > 3600:
                    r_status = "DEGRADED"
                    r_evidence = [
                        f"last run {last_status}",
                        f"heartbeat age {age}s exceeds 1h (STALE)",
                    ]
                else:
                    r_status = "HEALTHY"
                    r_evidence = [
                        f"last run {last_status}",
                        f"heartbeat age {age}s",
                    ]
            else:
                r_status = "DEGRADED"
                r_evidence = [
                    f"last run {last_status}",
                    f"heartbeat age {sched.get('heartbeat_age_seconds')}s",
                ]
        dims["RUNTIME_HEALTH"] = {
            "status": r_status,
            "evidence": r_evidence,
            "explanation": "runtime health = scheduler evidence; absence is UNKNOWN",
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

        # TEST_HEALTH: committed gate artifacts; STALE/incomplete vs HEAD ≠ HEALTHY.
        t_evidence: list[str] = []
        t_status = "HEALTHY"
        for key in ("pytest", "validate"):
            entry = test.get(key)
            if not entry or not entry.get("present"):
                t_status = "UNKNOWN"
                t_evidence.append(f"{key}: no committed artifact")
                continue
            if entry.get("error"):
                t_status = "UNKNOWN"
                t_evidence.append(f"{key}: {entry.get('error')}")
                continue
            if entry.get("exit_code") not in (0, None) and entry.get("exit_code") is not None:
                t_status = "DEGRADED"
            if entry.get("exit_code") is None or entry.get("evidence_completeness") == "INCOMPLETE":
                if t_status == "HEALTHY":
                    t_status = "UNKNOWN"
            elif entry.get("stale_vs_head"):
                if t_status == "HEALTHY":
                    t_status = "UNKNOWN"
            t_evidence.append(
                f"{key}: exit {entry.get('exit_code')} "
                f"@ {str(entry.get('commit_sha'))[:8]} "
                f"{'(STALE vs HEAD)' if entry.get('stale_vs_head') else '(current/incomplete check)'}"
            )
        dims["TEST_HEALTH"] = {
            "status": t_status,
            "evidence": t_evidence,
            "explanation": (
                "test health = gate artifacts for CURRENT HEAD; "
                "stale or incomplete artifacts are UNKNOWN, not HEALTHY"
            ),
        }

        # ARCHITECTURE_HEALTH: Lane-A integrity + security invariants (None=UNKNOWN).
        lane = snap.lane_a_ok
        arch_status = "HEALTHY"
        arch_evidence: list[str] = []
        if lane is False:
            arch_status = "FAIL"
            arch_evidence.append(
                f"Lane-A integrity FAILED ({snap.lane_a_detail or 'drift'})"
            )
        elif lane is None:
            arch_status = "UNKNOWN"
            arch_evidence.append(
                f"Lane-A integrity UNKNOWN ({snap.lane_a_detail or 'unverifiable'})"
            )
        else:
            arch_evidence.append("Lane-A integrity intact")
        sec = snap.security_invariants
        # Epistemic/informational keys must not FAIL the architecture dimension.
        _SEC_INFO_KEYS = {
            "ahos_paper_only_env",
            "zero_secret_check_scope",
            "paper_only_explicit",
            "paper_only_unset",
            "live_trading_flags_absent",
        }
        if isinstance(sec, dict):
            for k, v in sec.items():
                if k in _SEC_INFO_KEYS or k.endswith("_scope") or k.endswith("_env"):
                    arch_evidence.append(f"{k}={v}")
                    continue
                arch_evidence.append(f"{k}={v}")
                if v is False:
                    arch_status = "FAIL"
                elif v is None and arch_status == "HEALTHY":
                    arch_status = "UNKNOWN"
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

        # TELEMETRY_HEALTH: metrics writer observability (never invent OK).
        tel = getattr(snap, "telemetry_health", None)
        tel = tel if isinstance(tel, dict) else {}
        tel_status_raw = tel.get("status")
        if tel_status_raw == "OK":
            tel_status = "HEALTHY"
        elif tel_status_raw == "DEGRADED":
            tel_status = "DEGRADED"
        else:
            tel_status = "UNKNOWN"
        dims["TELEMETRY_HEALTH"] = {
            "status": tel_status,
            "evidence": [
                f"source={tel.get('source')}",
                f"write_failures={tel.get('write_failures')}",
                *([tel["note"]] if tel.get("note") else []),
                *([tel["error"]] if tel.get("error") else []),
            ],
            "explanation": (
                "telemetry health observes metric-write failures; "
                "absence of a live tracker is UNKNOWN, never HEALTHY"
            ),
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

        # 6. provider breaker state -> provider health (only when live breakers exist)
        prov = snap.provider_health
        providers = {}
        if isinstance(prov, dict):
            providers = prov.get("providers") or {}
            if not providers and prov.get("breaker_state_source") != "UNAVAILABLE":
                # legacy shape: pid -> state dict
                providers = {
                    k: v for k, v in prov.items()
                    if isinstance(v, dict) and "state" in v
                }
        if providers and any(
            (st or {}).get("state", "UNKNOWN") != "CLOSED"
            for st in providers.values()
        ):
            out.append({
                "left": "circuit_breaker_state",
                "right": "provider_health",
                "direction": "breaker open/half-open -> provider health degraded",
                "label": "CORRELATION_ONLY",
                "evidence": (
                    f"{sum(1 for st in providers.values() if (st or {}).get('state', 'UNKNOWN') != 'CLOSED')} "
                    "non-CLOSED breakers"
                ),
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
