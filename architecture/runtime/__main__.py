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
import os
import signal
import sys
import time
from pathlib import Path

from .lifecycle import ApplicationLifecycleManager, RuntimeState
from .logging import get_logger
from .observation_loop import ObservationRuntime, STATUS_BLOCKED
from ..collector.engine import CollectorEngine
from ..scheduling.engine import ProductionScheduler, ScheduleTask
from ..pipeline.orchestrator import OpportunityPipelineOrchestrator
from telegram_ai.adapter import MockTelegramAdapter, ProductionTelegramAdapter, TelegramSecurityGate
from telegram_ai.bot import TelegramBotRunner
from telegram_ai.service import TelegramDomainService


from .metrics import OperationalMetricsTracker
from config.paths import get_project_root, get_discovery_db_path, get_local_db_path


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
    args = parser.parse_args(argv)

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

    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        telegram_adapter=telegram_adapter,
        target_chat_id=allowed_chats[0] if allowed_chats else None
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
            f"candidates={rep.candidates_collected}, scores={rep.scores_generated}, alerts={rep.alerts_emitted}"
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
    try:
        if args.single_cycle:
            sched_res = scheduler.execute_scheduled_cycle("SINGLE_CYCLE", cycle_tasks)
            logger.info(f"Single cycle completed with status: {sched_res['status']}")
            app.shutdown(reason="Single cycle complete")
            return 0 if sched_res["status"] == "SUCCESS" else 1

        logger.info(f"AHOS Daemon started. Interval: {args.interval_sec}s")
        while running:
            sched_res = scheduler.execute_scheduled_cycle("DAEMON_CYCLE", cycle_tasks)
            if not running:
                break
            time.sleep(args.interval_sec)

        app.shutdown(reason="Daemon stopped")
        return 0
    except Exception as e:
        logger.error(f"Fatal runtime exception: {e}")
        app.shutdown(reason=f"Exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
