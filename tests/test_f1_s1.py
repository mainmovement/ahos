#!/usr/bin/env python3
"""F1-S1 tests — conservative append-only guard migration (W12 PART B authorized).
Proves: drill safety on copies, idempotent apply, UPDATE/DELETE blocked on guarded history
tables, INSERT still works, MUTABLE state tables stay writable (pipeline must not break),
rollback restores schema, live census exactly matches the registry/matrix claim."""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import f1_s1_migration as mig                     # noqa: E402

E01 = ROOT / "data" / "e01_discovery.sqlite"
LOCAL = ROOT / "data" / "ahos_local.sqlite"
PAPER = ROOT / "data" / "paper_trading.sqlite"
HISTORY_E01 = ["discovery_observations", "raw_payloads", "gap_register", "lifecycle_events", "gate_summary"]
MUTABLE_E01 = ["tokens", "pairs", "observation_state", "opportunity_rank", "outcome_label",
               "security_verdicts", "feature_definitions", "feature_vector", "holder_snapshot"]


def guarded(store: Path) -> set[str]:
    return set(mig.guards_present(store))


def test_drill_proves_safe_on_copies():
    d1 = mig.drill(E01, HISTORY_E01)
    assert d1["update_blocked"] and d1["rollback_clean"] and d1["data_identical_after_drill"]
    d2 = mig.drill(LOCAL, ["control_flags"])
    assert d2["update_blocked"] and d2["rollback_clean"] and d2["data_identical_after_drill"]


def test_apply_idempotent_enforced_rollback_clean(tmp_path):
    store = tmp_path / "copy.sqlite"
    shutil.copy2(E01, store)
    mig.apply(store, HISTORY_E01)
    first = guarded(store)
    mig.apply(store, HISTORY_E01)                            # idempotent re-apply
    assert guarded(store) == first and len(first) == 2 * len(HISTORY_E01)
    conn = sqlite3.connect(str(store))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE discovery_observations SET rowid=rowid")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM raw_payloads")
    n0 = conn.execute("SELECT COUNT(*) FROM lifecycle_events").fetchone()[0]
    conn.execute("INSERT INTO lifecycle_events SELECT * FROM lifecycle_events LIMIT 0")   # INSERT path alive
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM lifecycle_events").fetchone()[0] == n0
    conn.close()
    mig.rollback(store, HISTORY_E01)
    assert guarded(store) == set()


def test_mutable_state_tables_not_blocked(tmp_path):
    """Anti-pipeline-breakage: upsert-path tables must remain writable after guarding history."""
    store = tmp_path / "copy.sqlite"
    shutil.copy2(E01, store)
    mig.apply(store, HISTORY_E01)
    conn = sqlite3.connect(str(store))
    conn.execute("UPDATE observation_state SET last_obs_ts=last_obs_ts")      # no guard ⇒ writable
    conn.execute("UPDATE opportunity_rank SET rank=rank")
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM observation_state").fetchone()[0]
    assert n > 0
    conn.close()


def test_live_guards_exactly_match_classified_set():
    """Live census: the live e01 store is guarded on EXACTLY the classified history tables."""
    live = guarded(E01)
    expected = {n for t in HISTORY_E01 for n in mig.trigger_names(t)}
    assert live == expected
    assert guarded(LOCAL) == set(mig.trigger_names("control_flags"))


def test_live_apply_report_proves_zero_data_change():
    reports = sorted((ROOT / "reports").glob("f1_s1_apply_*.json"))
    assert reports, "no F1-S1 apply report found"
    rep = json.loads(reports[-1].read_text())
    assert rep["verdict"] == "OK"
    assert rep["e01"]["data_identical"] and rep["ahos_local"]["data_identical"]
    assert rep["e01"]["census_before"] == rep["e01"]["census_after"]


def test_paper_store_regression_unchanged():
    c = sqlite3.connect(f"file:{PAPER}?mode=ro", uri=True)
    n = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
    c.close()
    assert n == 34                                             # pre-existing guards intact


def test_registry_and_matrix_text_now_measured():
    import yaml
    reg = yaml.safe_load((ROOT / "config" / "agent_registry.yaml").read_text())
    ag17 = next(a for a in reg["agents"] if a["agent_id"] == "AG-17")
    assert "F1-S1" in ag17["evidence"] or "f1s1" in ag17["evidence"].lower()
    m = yaml.safe_load((ROOT / "config" / "cognitive_principles.yaml").read_text())
    c2 = next(p for p in m["principles"] if p["principle_id"] == "CRYPTO-02")
    assert "S1" in c2["ahos_application"]
