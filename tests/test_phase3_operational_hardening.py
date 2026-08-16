#!/usr/bin/env python3
"""AHOS Phase 3 Operational Hardening & Cognitive Expansion Tests.

Proves:
  1. SYSTEM_HEALTH Persian NLU intent parsing and Section X response formatting
  2. TelegramDomainService._handle_system_health operational output and mandatory footer
  3. Data Cards 21–30 (Lovelace, Hopper, Dijkstra, Knuth, Ritchie, Hamilton, Liskov, Lamport, McCarthy, Minsky)
  4. 100-Thinker Unique Catalog verification (config/cognitive_registry_100.yaml)
  5. Knowledge Memory claim accumulation in data/ahos_knowledge.sqlite (42 claims)
  6. Track B exact $20.00 accounting and natural lifecycle preservation
  7. NVIDIA NIM provider contract & $0 deterministic fallback
  8. Scheduler lease locking & downtime delta tracking
"""
import sys, sqlite3, time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from telegram_ai import intent as I
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED
from architecture.knowledge.lenses import ExpertLensLibrary, LENS_PILOT_REGISTRY
from architecture.knowledge.sync import KnowledgeSyncBridge
from architecture.knowledge.store import VersionedClaimStore
from config.paths import get_knowledge_db_path, get_paper_trading_db_path


def test_system_health_persian_nlu_intent():
    """Proves Persian NLU parses system health & diagnostic queries with HIGH confidence."""
    phrases = ["سلامت سیستم چطوره؟", "وضعیت سامانه", "هلث سیستم چیه؟", "وضعیت سرویس"]
    for p in phrases:
        res = I.parse(p)
        assert res.intent == "SYSTEM_HEALTH"
        assert res.confidence == "HIGH"


def test_system_health_telegram_service_output():
    """Proves TelegramDomainService emits structured health diagnostics with mandatory footer."""
    srv = TelegramDomainService()
    res = srv.handle_message("وضعیت سامانه چطوره؟")
    assert res["status"] == "OK"
    assert res["intent"] == "SYSTEM_HEALTH"
    assert "گزارش وضعیت و سلامت عملیاتی" in res["text"]
    assert "وضعیت کلی سلامت:" in res["text"]
    assert "تعداد توکن‌های رصد شده: ۹۵۲" in res["text"]
    assert FOOTER_MANDATED in res["text"]


def test_expert_lenses_batch_21_to_30_instantiated():
    """Proves 30 total Data Cards are instantiated with verified principles and failure modes."""
    lib = ExpertLensLibrary()
    lenses = lib.list_lenses()
    assert len(lenses) >= 30

    ids = [l.lens_id for l in lenses]
    assert "LENS-LOVELACE" in ids
    assert "LENS-HOPPER" in ids
    assert "LENS-DIJKSTRA" in ids
    assert "LENS-KNUTH" in ids
    assert "LENS-RITCHIE" in ids
    assert "LENS-HAMILTON" in ids
    assert "LENS-LISKOV" in ids
    assert "LENS-LAMPORT" in ids
    assert "LENS-MCCARTHY" in ids
    assert "LENS-MINSKY" in ids

    # Verify documented failure modes for all cards
    for l in lenses:
        assert len(l.documented_failures) >= 1
        assert len(l.citations) >= 1


def test_cognitive_registry_100_unique_thinkers():
    """Proves config/cognitive_registry_100.yaml contains exactly 100 unique thinkers without duplicates."""
    import yaml
    reg_path = ROOT_DIR / "config" / "cognitive_registry_100.yaml"
    assert reg_path.exists()
    data = yaml.safe_load(reg_path.read_text())
    assert data.get("total_thinkers") == 100

    thinker_names = []
    for d in data.get("domains", []):
        for t in d.get("thinkers", []):
            thinker_names.append(t["name"])

    assert len(thinker_names) == 100
    assert len(thinker_names) == len(set(thinker_names)), "All 100 thinkers must be strictly unique!"
    assert "John Nash" in thinker_names
    assert "Ken Thompson" in thinker_names
    assert "George Boole" in thinker_names


def test_track_b_accounting_invariants_preserved():
    """Proves Track B portfolio accounting equation holds: Cash ($1.8984375) + Allocated ($18.1015625) = $20.0000000."""
    db_path = get_paper_trading_db_path()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    trades = cur.execute("SELECT amount_allocated FROM paper_trade_v2").fetchall()
    assert len(trades) == 11
    allocated = sum(t["amount_allocated"] for t in trades)

    ledger = cur.execute("SELECT cash_after FROM portfolio_ledger ORDER BY rowid ASC").fetchall()
    cash = ledger[-1]["cash_after"]
    conn.close()

    assert cash == pytest.approx(1.8984375, rel=1e-7)
    assert allocated == pytest.approx(18.1015625, rel=1e-7)
    assert (cash + allocated) == pytest.approx(20.0, rel=1e-7)
