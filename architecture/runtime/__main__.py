#!/usr/bin/env python3
"""AHOS Production Unified Runtime Application Entrypoint (Phase XXI).

Usage:
  python3 -m architecture.runtime --single-cycle
  python3 -m architecture.runtime --daemon --interval-sec 60
  python3 -m architecture.runtime --chain solana --limit 20
  python3 -m architecture.runtime --daemon --observation-cycle
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .lifecycle import ApplicationLifecycleManager, RuntimeState
from .logging import get_logger

logger = get_logger("ahos.main")
from .observation_loop import ObservationRuntime, STATUS_BLOCKED
from ..collector.engine import CollectorEngine
from ..learning.score_ledger import ScoreLedger
from ..scheduling.engine import ProductionScheduler, ScheduleTask
from ..pipeline.orchestrator import OpportunityPipelineOrchestrator
from telegram_ai.adapter import MockTelegramAdapter, ProductionTelegramAdapter, TelegramSecurityGate
from telegram_ai.bot import TelegramBotRunner
from telegram_ai.service import TelegramDomainService


from .metrics import OperationalMetricsTracker
from config.paths import get_project_root, get_discovery_db_path, get_local_db_path


def write_soak_snapshots(*, local_db: str, discovery_db: str,
                         window_hours: float, probe_providers: bool,
                         reports_dir: Path, now: float | None = None) -> list[Path]:
    """Write soak + system-state + canonical health snapshots (read-only
    evidence) and return the artifact paths. Never raises: a snapshot failure
    must not end a daemon — the caller logs it. Empty on failure.

    First production consumer of scripts/soak_snapshot.snapshot(),
    scripts/system_state_snapshot.build_snapshot() and
    HealthSnapshotEngine.generate_snapshot() from the runtime — this is what
    makes the 168h soak protocol's 6h snapshot cadence automatic, and closes
    the self-observation loop (mission W36 phase 2): the canonical health
    snapshot (with its self_observation block) is written alongside the soak
    and system-state artifacts every cadence.
    """
    import json
    import time as _time

    from scripts import soak_snapshot
    from scripts import system_state_snapshot
    from .observability_snapshot import HealthSnapshotEngine

    ts = _time.time() if now is None else now
    out: list[Path] = []
    try:
        snap = soak_snapshot.snapshot(local_db, discovery_db,
                                      window_hours=window_hours, now=ts)
        utc = snap.get("snapshot_utc") or _time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", _time.gmtime(ts))
        path = reports_dir / f"soak_snapshot_{utc.replace(':', '').replace('-', '')}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snap, indent=2, ensure_ascii=False, default=str),
                        encoding="utf-8")
        out.append(path)
    except Exception as e:
        logger.warning("automatic soak snapshot failed: %s", e)

    try:
        report = system_state_snapshot.build_snapshot(
            probe_providers=probe_providers, window_hours=window_hours)
        utc2 = (report.get("timestamp_utc") or report.get("snapshot_utc")
                or _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(ts)))
        path2 = reports_dir / f"system_state_snapshot_{utc2.replace(':', '').replace('-', '')}.json"
        path2.parent.mkdir(parents=True, exist_ok=True)
        path2.write_text(json.dumps(report, indent=2, default=str) + "\n",
                         encoding="utf-8")
        out.append(path2)
    except Exception as e:
        logger.warning("automatic system-state snapshot failed: %s", e)

    try:
        health = HealthSnapshotEngine().generate_snapshot(now=ts)
        utc3 = health.timestamp_utc.replace(":", "").replace("-", "")
        path3 = reports_dir / f"canonical_health_{utc3}.json"
        path3.parent.mkdir(parents=True, exist_ok=True)
        path3.write_text(json.dumps(asdict(health), indent=2,
                                    ensure_ascii=False, default=str),
                         encoding="utf-8")
        out.append(path3)
    except Exception as e:
        logger.warning("automatic canonical health snapshot failed: %s", e)

    return out


def write_evidence_package(*, local_db: str, discovery_db: str,
                           window_hours: float, probe_providers: bool,
                           reports_dir: Path, now: float | None = None) -> list[Path]:
    """Coherent evidence package (W37 phase 2): the canonical snapshot triple
    PLUS snapshot-to-snapshot regression against the previous comparable
    health snapshot, PLUS per-dimension health-scorecard trends.

    Returns every artifact path written. Never raises: each stage is isolated
    so one diagnostic failure cannot crash the daemon. The package index is
    written first so a partial package is still discoverable; every artifact
    carries its own timestamp + schema + provenance.
    """
    import json
    import time as _time

    ts = _time.time() if now is None else now
    ts_utc = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(ts))
    out: list[Path] = []

    # 1. canonical triple (soak / system-state / health) via the existing writer
    triple = write_soak_snapshots(
        local_db=local_db, discovery_db=discovery_db,
        window_hours=window_hours, probe_providers=probe_providers,
        reports_dir=reports_dir, now=ts)
    out.extend(triple)

    # 2. health scorecard + regression + trend (from the just-written health
    #    snapshot; absent triple => honest NOT_COMPARABLE, never invented)
    health_path = next((p for p in triple
                        if p.name.startswith("canonical_health_")), None)
    if health_path is not None:
        try:
            from .observability_snapshot import HealthSnapshotEngine
            engine = HealthSnapshotEngine()
            health = json.loads(health_path.read_text(encoding="utf-8"))
            scorecard = engine._build_scorecard(type(
                "Snap", (), {"timestamp_utc": health.get("timestamp_utc", ts_utc),
                             "overall_verdict": health.get("overall_verdict", "UNKNOWN"),
                             "self_observation": health.get("self_observation", {}),
                             "database_integrity": health.get("database_integrity", {}),
                             "provider_health": health.get("provider_health", {}),
                             "scheduler_status": health.get("scheduler_status", {}),
                             "security_invariants": health.get("security_invariants", {}),
                             "lane_a_ok": True})())
            score_path = reports_dir / f"health_scorecard_{ts_utc.replace(':', '').replace('-', '')}.json"
            score_path.parent.mkdir(parents=True, exist_ok=True)
            score_path.write_text(json.dumps(scorecard, indent=2,
                                             ensure_ascii=False, default=str),
                                  encoding="utf-8")
            out.append(score_path)

            # snapshot-to-snapshot regression vs the previous health snapshot
            prev = sorted(reports_dir.glob("canonical_health_*.json"),
                          key=lambda p: p.stat().st_mtime)
            prev = [p for p in prev if p != health_path]
            regression_path = reports_dir / f"regression_{ts_utc.replace(':', '').replace('-', '')}.json"
            regression_path.parent.mkdir(parents=True, exist_ok=True)
            if prev:
                from scripts.regression_report import build_regression_report
                reg = build_regression_report(prev[-1], health_path)
                reg["generated_utc"] = ts_utc
                reg["previous_artifact"] = prev[-1].name
                reg["current_artifact"] = health_path.name
                regression_path.write_text(json.dumps(reg, indent=2,
                                                      ensure_ascii=False) + "\n",
                                           encoding="utf-8")
            else:
                regression_path.write_text(json.dumps({
                    "schema": "ahos.regression_report.v1",
                    "generated_utc": ts_utc,
                    "verdict": "NOT_COMPARABLE",
                    "findings": [{"source": "snapshots", "metric": "baseline",
                                  "before": None, "after": None, "delta": None,
                                  "kind": "NOT_COMPARABLE",
                                  "evidence": "no previous comparable snapshot "
                                              "(first evidence package)"}],
                    "note": "first package: no baseline to compare yet",
                }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            out.append(regression_path)
        except Exception as e:
            logger.warning("automatic evidence package regression failed: %s", e)

    # 2b. automatic diagnostic findings from the health snapshot (W37 P5):
    #     derived, never invented; a finding alone never changes anything.
    if health_path is not None:
        try:
            from ..evolution.findings import derive_findings
            findings = [f.as_dict() for f in derive_findings(health)]
            findings_path = reports_dir / f"findings_{ts_utc.replace(':', '').replace('-', '')}.json"
            findings_path.parent.mkdir(parents=True, exist_ok=True)
            findings_path.write_text(json.dumps({
                "schema": "ahos.diagnostic_findings.v1",
                "generated_utc": ts_utc,
                "findings": findings,
                "note": "derived findings are informational; acting on them "
                        "requires a governed proposal + human gate",
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            out.append(findings_path)
        except Exception as e:
            logger.warning("automatic diagnostic findings failed: %s", e)

    # 2c. health-scorecard trends (W37 P4 / W38 Candidate C): compare the
    #     current scorecard against the previous committed one. First package
    #     => every dimension NOT_COMPARABLE (no invented baseline).
    if health_path is not None:
        try:
            from .observability_snapshot import HealthSnapshotEngine
            engine = HealthSnapshotEngine()
            score_path = next((p for p in out
                               if p.name.startswith("health_scorecard_")), None)
            if score_path is not None:
                current_sc = json.loads(score_path.read_text(encoding="utf-8"))
                prev_scs = sorted(reports_dir.glob("health_scorecard_*.json"),
                                  key=lambda p: p.stat().st_mtime)
                prev_scs = [p for p in prev_scs if p != score_path]
                previous_sc = (json.loads(prev_scs[-1].read_text(encoding="utf-8"))
                               if prev_scs else None)
                trends = HealthSnapshotEngine.trend_dimensions(current_sc,
                                                               previous_sc)
                trends_path = reports_dir / f"health_trends_{ts_utc.replace(':', '').replace('-', '')}.json"
                trends_path.parent.mkdir(parents=True, exist_ok=True)
                trends_path.write_text(json.dumps({
                    "schema": "ahos.health_trends.v1",
                    "generated_utc": ts_utc,
                    "previous_scorecard": prev_scs[-1].name if prev_scs else None,
                    "current_scorecard": score_path.name,
                    "dimensions": trends,
                    "note": "per-dimension trends observed from committed "
                            "scorecards; NOT_COMPARABLE without a previous one",
                }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                out.append(trends_path)
        except Exception as e:
            logger.warning("automatic health trends failed: %s", e)

    # 2d. architecture graph (W38 Candidate A): deterministic stdlib module
    #     graph — new cycles/orphans become visible per cadence.
    try:
        from scripts.architecture_graph import build_graph
        graph = build_graph()
        graph["generated_utc"] = ts_utc
        graph_path = reports_dir / f"architecture_graph_{ts_utc.replace(':', '').replace('-', '')}.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_text(json.dumps(graph, indent=2,
                                         ensure_ascii=False) + "\n",
                              encoding="utf-8")
        out.append(graph_path)
    except Exception as e:
        logger.warning("automatic architecture graph failed: %s", e)

    # 2d2. doc <-> code drift (W38 Candidate H): canonical docs referencing
    #     missing files are diagnosed per cadence (WARN-only; a doc may
    #     legitimately reference planned artifacts — see the ignore list).
    try:
        from scripts.doc_drift import scan_docs
        drift = scan_docs()
        drift_count = sum(len(v) for v in drift.values())
        drift_path = reports_dir / f"doc_drift_{ts_utc.replace(':', '').replace('-', '')}.json"
        drift_path.parent.mkdir(parents=True, exist_ok=True)
        drift_path.write_text(json.dumps({
            "schema": "ahos.doc_drift.v1",
            "generated_utc": ts_utc,
            "stale_reference_count": drift_count,
            "stale_references": drift,
            "note": "WARN-only diagnostic; intentional refs are ignored with "
                    "reasons (scripts/doc_drift.py)",
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out.append(drift_path)
    except Exception as e:
        logger.warning("automatic doc-drift check failed: %s", e)

    # 2e. benchmark state (W38 Candidate A): reference the committed baseline
    #     so the package exposes benchmark health without re-running the suite.
    try:
        bench = (health.get("self_observation", {}).get("benchmark_health", {})
                 if health_path is not None else {})
        bench_path = reports_dir / f"benchmark_state_{ts_utc.replace(':', '').replace('-', '')}.json"
        bench_path.parent.mkdir(parents=True, exist_ok=True)
        bench_path.write_text(json.dumps({
            "schema": "ahos.benchmark_state.v1",
            "generated_utc": ts_utc,
            "baseline_present": bool(bench.get("baseline_present")),
            "baseline_artifact": bench.get("baseline_artifact"),
            "note": ("baseline reference only; run "
                     "scripts/benchmark_performance.py compare for deltas"),
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out.append(bench_path)
    except Exception as e:
        logger.warning("automatic benchmark state failed: %s", e)

    # 3. package index (written last, lists what actually landed)
    index = {
        "schema": "ahos.evidence_package.v1",
        "generated_utc": ts_utc,
        "window_hours": window_hours,
        "artifacts": [str(p.relative_to(reports_dir) if p.is_relative_to(reports_dir)
                          else p) for p in out],
        "artifact_count": len(out),
        "note": "coherent daemon evidence package; each artifact is self-describing",
    }
    index_path = reports_dir / f"evidence_package_{ts_utc.replace(':', '').replace('-', '')}.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    out.append(index_path)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AHOS Production Runtime Entrypoint")
    parser.add_argument("--workspace", default=str(get_project_root()), help="AHOS workspace root directory")
    parser.add_argument("--chain", default="solana", help="Primary discovery chain (solana, ethereum, bsc, base)")
    parser.add_argument("--limit", type=int, default=10, help="Candidate limit per cycle")
    parser.add_argument("--single-cycle", action="store_true", help="Execute exactly one complete cycle and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as background daemon")
    parser.add_argument("--interval-sec", type=float, default=60.0, help="Interval between daemon cycles in seconds")
    parser.add_argument("--observation-cycle", action="store_true",
                        help="Also run the E-01 observation cycle (frozen Lane-A poller) in each cycle")
    parser.add_argument("--observation-max-tokens", type=int, default=40,
                        help="Max tokens attempted per observation cycle")
    parser.add_argument("--evidence-source", default=None,
                        choices=["local", "sandbox", "test", "synthetic"],
                        help="Evidence namespace for persisted predictions. "
                             "Only 'local' is calibration-eligible. Defaults to "
                             "$AHOS_EVIDENCE_SOURCE, else 'sandbox'.")
    parser.add_argument("--probe-providers", action="store_true",
                        help="Probe every provider for live reachability, print a "
                             "classified status table, and exit (no scoring, no writes)")
    parser.add_argument("--snapshot-interval-hours", type=float, default=0.0,
                        help="In daemon mode, write soak + system-state snapshot "
                             "evidence every N hours (first one immediately at "
                             "start). 0 disables. Use 6 for the 168h soak protocol.")
    parser.add_argument("--snapshot-probe-providers", action="store_true",
                        help="Include the live provider probe inside each "
                             "automatic system-state snapshot (requires egress; "
                             "failures are recorded honestly)")
    args = parser.parse_args(argv)

    # Provider probe is a pure read-only diagnostic: it must run without
    # booting the runtime, touching a database, or emitting a prediction.
    if args.probe_providers:
        from ..providers.probe import probe_providers, render_table

        report = probe_providers(chain=args.chain)
        print(render_table(report))
        out = Path(args.workspace) / "reports" / (
            f"provider_probe_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")
            print(f"\nartifact: {out}")
        except OSError as e:
            print(f"\nWARNING: could not write probe artifact: {e}")
        # Exit 0 = probe completed. A provider outage is evidence, not a crash;
        # exit 3 distinguishes "ran, found nothing live" for scripted operators.
        return 0 if report.any_success else 3

    root = Path(args.workspace)
    app = ApplicationLifecycleManager(workspace_root=root)
    logger = get_logger("ahos.main", run_id=app.run_id)
    metrics_tracker = OperationalMetricsTracker(db_path=get_local_db_path())

    # 1. Startup & Validation
    if not app.startup():
        logger.error("Application startup failed validation! Aborting.")
        return 1

    # 2. Wire Production Subsystems
    discovery_db = get_discovery_db_path()
    local_db = get_local_db_path()
    ledger_db = get_local_db_path()

    scheduler = ProductionScheduler(db_path=local_db, discovery_db_path=discovery_db)
    collector = CollectorEngine(db_path=discovery_db)

    # Setup Telegram Adapter
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if bot_token and ":" in bot_token:
        telegram_adapter = ProductionTelegramAdapter(bot_token=bot_token)
    else:
        telegram_adapter = MockTelegramAdapter()

    # Canonical name is TELEGRAM_ALLOWED_CHAT_IDS (used by .env.example,
    # run_bot.py and the docs). TELEGRAM_ALLOWED_CHATS is the legacy spelling
    # this module used to read on its own -- the mismatch meant proactive
    # alerts silently had no destination for anyone following the quickstart.
    _raw_chats = (os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS")
                  or os.environ.get("TELEGRAM_ALLOWED_CHATS", ""))
    allowed_chats = [c.strip() for c in _raw_chats.split(",") if c.strip()]
    gate = TelegramSecurityGate(allowed_chat_ids=allowed_chats if allowed_chats else None)
    telegram_service = TelegramDomainService(discovery_db_path=discovery_db, ledger_db_path=ledger_db)
    bot_runner = TelegramBotRunner(adapter=telegram_adapter, service=telegram_service, gate=gate)

    # Predictions land in the local operational store alongside scheduler and
    # metrics history, so a single laptop backup captures the whole evidence set.
    #
    # The evidence namespace is resolved from AHOS_EVIDENCE_SOURCE (or --evidence
    # -source). It deliberately defaults to `sandbox`, NOT `local`: only a run
    # the operator explicitly declares as laptop evidence may feed calibration.
    score_ledger = ScoreLedger(db_path=local_db, source=args.evidence_source)
    logger.info(f"Prediction evidence namespace: {score_ledger.source}"
                + ("" if score_ledger.source == "local"
                   else "  (NOT calibration-eligible)"))

    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        telegram_adapter=telegram_adapter,
        target_chat_id=allowed_chats[0] if allowed_chats else None,
        score_ledger=score_ledger
    )

    # Observation runtime (Phase 6): wraps the frozen Lane-A poller; every
    # cycle re-asserts the paper-only safety laws before anything executes.
    observation_runtime = ObservationRuntime(
        workspace_root=root, metrics_tracker=metrics_tracker)

    # Register Graceful Shutdown
    running = True

    def _sig_handler(signum, frame):
        nonlocal running
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        running = False

    try:
        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)
    except Exception:
        pass

    # Execution Task
    def _execute_full_cycle():
        now = time.time()
        logger.info(f"Executing Opportunity Intelligence Cycle (chain={args.chain})")
        # 1. Run pipeline
        rep = orchestrator.run_pipeline(chain=args.chain, limit=args.limit, now=now)
        logger.info(
            f"Pipeline executed in {rep.duration_ms:.2f}ms: "
            f"candidates={rep.candidates_collected}, scores={rep.scores_generated}, "
            f"persisted={rep.scores_persisted}, alerts={rep.alerts_emitted}, "
            f"lane_a_registered={getattr(rep, 'lane_a_registered', 0)}, "
            f"lane_a_obs={getattr(rep, 'lane_a_observations_written', 0)}"
        )
        # A prediction that was scored but NOT written down is a silent hole in
        # the learning loop -- surface it rather than letting it pass as normal.
        if rep.scores_generated and rep.scores_persisted < rep.scores_generated:
            logger.warning(
                f"score ledger dropped "
                f"{rep.scores_generated - rep.scores_persisted} of "
                f"{rep.scores_generated} predictions this cycle "
                f"(total write failures: {score_ledger.write_failures})"
            )
        # Record operational metrics
        metrics_tracker.record_metric(
            run_id=app.run_id, component="pipeline",
            metric_name="cycle_duration_ms", metric_value=rep.duration_ms,
            evidence_refs=[rep.run_id]
        )
        metrics_tracker.record_metric(
            run_id=app.run_id, component="scoring",
            metric_name="scores_generated", metric_value=float(rep.scores_generated),
            evidence_refs=[rep.run_id]
        )
        metrics_tracker.record_metric(
            run_id=app.run_id, component="alerts",
            metric_name="alerts_emitted", metric_value=float(rep.alerts_emitted),
            evidence_refs=[rep.run_id]
        )
        metrics_tracker.record_metric(
            run_id=app.run_id, component="learning",
            metric_name="scores_persisted", metric_value=float(rep.scores_persisted),
            status="OK" if rep.scores_persisted >= rep.scores_generated else "WARN",
            evidence_refs=[rep.run_id]
        )
        # 2. Process Telegram updates
        processed_updates = bot_runner.process_pending_updates()
        if processed_updates > 0:
            logger.info(f"Processed {processed_updates} Telegram updates")

    # Observation task: fail-closed by the runtime safety gate (a vetoed cycle
    # is reported as BLOCKED and never touches the discovery store).
    def _execute_observation_cycle():
        rep = observation_runtime.run_cycle(max_tokens=args.observation_max_tokens)
        if rep.status == STATUS_BLOCKED:
            logger.warning(f"Observation cycle BLOCKED by safety gate: {rep.safety.reasons}")
            return
        logger.info(
            f"Observation cycle completed in {rep.duration_ms:.2f}ms: "
            f"status={rep.status}, attempted={rep.attempted}, recorded={rep.recorded}, "
            f"failures={rep.failures}, tracked={rep.tracked_size}"
        )

    # Define Scheduled Tasks
    pipeline_task = ScheduleTask(
        task_id="OPPORTUNITY_CYCLE",
        target_offset_sec=0.0,
        tolerance_sec=300.0,
        action_fn=_execute_full_cycle,
        label="Opportunity Intelligence Cycle"
    )
    cycle_tasks = [pipeline_task]
    if args.observation_cycle:
        cycle_tasks.append(ScheduleTask(
            task_id="OBSERVATION_CYCLE",
            target_offset_sec=0.0,
            tolerance_sec=300.0,
            action_fn=_execute_observation_cycle,
            label="E-01 Observation Cycle"
        ))

    # 3. Main Loop
    snapshot_every = args.snapshot_interval_hours or 0.0
    last_snapshot_ts: float | None = None
    daemon_started_ts = time.time()
    reports_dir = root / "reports"

    try:
        if args.single_cycle:
            sched_res = scheduler.execute_scheduled_cycle("SINGLE_CYCLE", cycle_tasks)
            logger.info(f"Single cycle completed with status: {sched_res['status']}")
            app.shutdown(reason="Single cycle complete")
            return 0 if sched_res["status"] == "SUCCESS" else 1

        logger.info(f"AHOS Daemon started. Interval: {args.interval_sec}s"
                    + (f", soak snapshots every {snapshot_every:.1f}h"
                       if snapshot_every > 0 else ", snapshots disabled"))
        while running:
            sched_res = scheduler.execute_scheduled_cycle("DAEMON_CYCLE", cycle_tasks)
            if not running:
                break

            # Automatic soak evidence (M-GAP-003 support): the first snapshot
            # lands immediately at t=0 (protocol §6 row t=0), then every N
            # hours. Failure is logged, never fatal.
            if snapshot_every > 0:
                now_ts = time.time()
                due = (last_snapshot_ts is None
                       or now_ts - last_snapshot_ts >= snapshot_every * 3600.0)
                if due:
                    written = write_evidence_package(
                        local_db=local_db,
                        discovery_db=discovery_db,
                        window_hours=max(0.0, (now_ts - daemon_started_ts) / 3600.0),
                        probe_providers=args.snapshot_probe_providers,
                        reports_dir=reports_dir,
                        now=now_ts,
                    )
                    last_snapshot_ts = now_ts
                    if written:
                        logger.info(
                            "soak snapshot evidence written: %s",
                            ", ".join(str(p) for p in written))
                    else:
                        logger.warning(
                            "soak snapshot cycle produced no artifacts "
                            "(see snapshot warnings above)")
            time.sleep(args.interval_sec)

        app.shutdown(reason="Daemon stopped")
        return 0
    except Exception as e:
        logger.error(f"Fatal runtime exception: {e}")
        app.shutdown(reason=f"Exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
