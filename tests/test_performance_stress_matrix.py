#!/usr/bin/env python3
"""AHOS Deterministic Performance, Stress, and Concurrency Matrix Tests (Phase XXI)."""
import sys, time, threading, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.scoring.engine import OpportunityScorer
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask
from architecture.positions.manager import PaperPositionManager
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED


def test_batch_scoring_performance_100_tokens():
    """Evaluates 100 candidate tokens in batch under 500ms with full explainability."""
    scorer = OpportunityScorer()
    candidates = []
    for i in range(100):
        cand = NormalizedTokenCandidate(
            chain="solana",
            address=f"StressTok{i:04d}1111111111111111111111111111",
            symbol=f"STK{i}",
            name=f"Stress Token {i}",
            metrics=MarketMetrics(
                price_usd=0.01 * (i + 1),
                liquidity_usd=1000.0 * (i + 1),
                volume_1h=500.0 * (i + 1),
                txns_1h_buys=20 + i,
                txns_1h_sells=10
            ),
            security=SecuritySignals(
                is_honeypot=(i % 10 == 0),
                is_contract_verified=True
            ),
            source_provider="dexscreener"
        )
        candidates.append(cand)

    t0 = time.time()
    reports = [scorer.evaluate(c) for c in candidates]
    dt = (time.time() - t0) * 1000.0

    assert len(reports) == 100
    assert dt < 500.0  # Must be fast and strictly sub-linear
    # 10% honeypots must receive critical veto
    honeypots = [r for r in reports if r.risk_level == "CRITICAL"]
    assert len(honeypots) == 10


def test_scheduler_concurrent_worker_lease_contention(tmp_path):
    """Simulates 10 concurrent worker threads attempting to acquire the same schedule lease."""
    local_db = tmp_path / "concurrent_local.sqlite"
    scheduler = ProductionScheduler(db_path=str(local_db))

    acquired_runs = []
    lock = threading.Lock()

    def _worker_attempt(worker_id: int):
        now = 1000.0
        run_id = f"worker_{worker_id}"
        if scheduler.acquire_lease("HEAVY_CYCLE_LOCK", run_id, now):
            with lock:
                acquired_runs.append(run_id)

    threads = [threading.Thread(target=_worker_attempt, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly ONE worker must have acquired the lease
    assert len(acquired_runs) == 1


def test_paper_positions_stress_and_event_sourcing(tmp_path):
    """Opens and monitors 50 distinct paper positions verifying event-sourcing integrity."""
    db_file = tmp_path / "stress_positions.sqlite"
    manager = PaperPositionManager(str(db_file))

    positions = []
    for i in range(50):
        pos = manager.open_position(
            chain="solana",
            token_address=f"StressPosTok{i:03d}111111111111111111111111",
            symbol=f"POS{i}",
            allocated_usd=10.0 + i,
            entry_price_usd=1.0 + (i * 0.1)
        )
        positions.append(pos)

    assert len(positions) == 50

    # Evaluate all positions
    now = time.time()
    evaluations = []
    for i, pos in enumerate(positions):
        # 10 hit TP, 10 hit SL, 10 hit invalidation, 20 hold
        if i < 10:
            current_px = pos.entry_price_usd * 1.60  # +60% -> TP
            is_hp = False
        elif i < 20:
            current_px = pos.entry_price_usd * 0.70  # -30% -> SL
            is_hp = False
        elif i < 30:
            current_px = pos.entry_price_usd
            is_hp = True  # Honeypot -> Invalidation exit
        else:
            current_px = pos.entry_price_usd * 1.05  # +5% -> Hold
            is_hp = False

        res = manager.evaluate_position(
            position_id=pos.position_id,
            current_price_usd=current_px,
            last_obs_ts=now,
            is_honeypot=is_hp,
            now=now
        )
        evaluations.append(res)

    tp_count = sum(1 for e in evaluations if e.action_taken == "TP_EXIT")
    sl_count = sum(1 for e in evaluations if e.action_taken == "SL_EXIT")
    inv_count = sum(1 for e in evaluations if e.action_taken == "INVALIDATION_EXIT")
    hold_count = sum(1 for e in evaluations if e.action_taken == "HOLD")

    assert tp_count == 10
    assert sl_count == 10
    assert inv_count == 10
    assert hold_count == 20

    # Verify event audit trail count
    conn = sqlite3.connect(str(db_file))
    events_count = conn.execute("SELECT COUNT(*) FROM paper_position_events").fetchone()[0]
    assert events_count == 100  # 50 ENTRY + 50 EVALUATION events
    conn.close()


def test_telegram_service_rapid_request_handling(tmp_path):
    """Tests TelegramDomainService under 50 rapid sequential query requests."""
    service = TelegramDomainService(
        discovery_db_path=str(ROOT_DIR / "data" / "e01_discovery.sqlite"),
        ledger_db_path=str(tmp_path / "stress_telegram.sqlite")
    )
    queries = [
        "راهنما",
        "آخرین وضعیت بازار چیست؟",
        "بهترین فرصت‌های امروز",
        "فرصت‌های جدید",
        "من ۵ میلیون تومان از این خریدم"
    ] * 10  # 50 total queries

    t0 = time.time()
    results = [service.handle_message(q) for q in queries]
    dt = (time.time() - t0) * 1000.0

    assert len(results) == 50
    assert all(FOOTER_MANDATED in r["text"] for r in results)
    assert dt < 1000.0  # sub-second for 50 queries
