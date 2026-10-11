"""M13 gold soak cadence — the runner's own contract.

The soak runner owns no trading logic, so what is worth pinning here is the two
properties that make it a soak at all: it survives a failing cycle instead of
dying on the first transient, and its daily report reads only the ledger it is
handed, with no network of its own. Everything else is delegated to modules that
have their own tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import architecture.markets.gold_paper as gp
import scripts.m13_gold_soak as soak
from architecture.markets.gold_paper import (
    GOLD_PAPER_AGENT,
    GOLD_PAPER_MISSION,
    GoldCycleResult,
    GoldPaperTrack,
)
from architecture.mission.ledger import MissionLedger
from architecture.providers.gold import VERIFIED, GoldPriceWitness

T0 = 1_791_579_599.0


def _verified(price: float) -> GoldPriceWitness:
    return GoldPriceWitness(state=VERIFIED, reason="test", price_usd=price,
                            checked_at=T0)


def _raise(**kwargs):
    raise RuntimeError("feed unreachable")


@pytest.fixture
def soak_dir(tmp_path: Path) -> Path:
    d = tmp_path / "M13_SOAK"
    d.mkdir()
    return d


@pytest.fixture
def populated_ledger(tmp_path: Path) -> Path:
    """A ledger with a recorded cycle that closes through the time horizon.

    The frozen exit card's TP/SL are the *token* card's — +50% / -35% — and gold
    does not move 50% in a week, so a gold position reaches the 48h TIME_EXIT
    rather than a profit or stop. The fixture builds that path on purpose: it is
    the one the soak will actually walk, and the judge's double-entry has to hold
    on it.

    Built by the real track against the real ledger, not fabricated.
    """
    path = tmp_path / "mission_ledger" / "ledger.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger = MissionLedger(path)
    ledger.start(GOLD_PAPER_MISSION, phase="paper_trading",
                 task="test soak cadence", agent=GOLD_PAPER_AGENT)
    track = GoldPaperTrack()
    track.run_cycle(_verified(4200.0), now=T0, ledger=ledger)
    track.run_cycle(_verified(4180.0), now=T0 + 47 * 3600.0, ledger=ledger)
    # 48h horizon reached, on an observation inside the 6h freshness window:
    # TIME_EXIT, priced honestly.
    track.run_cycle(_verified(4180.0), now=T0 + 48.5 * 3600.0, ledger=ledger)
    track.run_cycle(_verified(4200.0), now=T0 + 50 * 3600.0, ledger=ledger)
    return path


# ------------------------------------------------------- a soak keeps going --


def test_a_failing_cycle_is_recorded_not_raised(monkeypatch, soak_dir):
    """A soak that died on its first network blip would soak nothing."""
    monkeypatch.setattr(gp, "run_gold_paper_cycle", _raise)

    record = soak._cycle(Path("does-not-exist.jsonl"))

    assert record["ok"] is False
    assert "feed unreachable" in record["error"]
    assert "RuntimeError" in record["traceback"]
    # The runlog carries the failure, so a bad cycle stays visible afterwards.
    soak._append_jsonl(soak_dir / "runlog.jsonl", record)
    lines = (soak_dir / "runlog.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[-1])["ok"] is False


def test_a_cycle_records_its_duration_so_the_cadence_stays_exact(monkeypatch):
    """The caller subtracts this from the sleep, so a slow cycle cannot shorten it."""
    monkeypatch.setattr(gp, "run_gold_paper_cycle", _raise)
    record = soak._cycle(Path("nope.jsonl"))
    assert isinstance(record["duration_s"], float)


def test_the_cycle_result_is_carried_verbatim(monkeypatch):
    """The runlog is the soak's evidence, so nothing is dropped on the way."""
    result = GoldCycleResult(
        cycle=3, witness_state=VERIFIED, witness_reason="test",
        price_usd=4200.0, position=None, exit=None, realized_pnl_usd=None,
        equity_usd=10_000.0)
    monkeypatch.setattr(gp, "run_gold_paper_cycle",
                        lambda **kw: (result, _verified(4200.0)))

    record = soak._cycle(Path("nope.jsonl"))
    assert record["ok"] is True
    assert record["cycle"] == 3
    assert record["price_usd"] == 4200.0
    assert record["equity_usd"] == 10_000.0
    assert record["witness_state"] == VERIFIED


# ----------------------------------------------------- the daily judge reads --


def test_report_only_writes_the_judge_without_a_cycle(populated_ledger, soak_dir):
    """--report-only reconciles what was recorded and names the day it covered."""
    assert soak.main(["--report-only", "--soak-dir", str(soak_dir),
                      "--ledger-path", str(populated_ledger)]) == 0

    reports = sorted(soak_dir.glob("*_judge.md"))
    assert reports, "no judge report was written"
    digests = sorted(soak_dir.glob("*_digest.json"))
    assert digests, "no digest was written"
    assert digests[0].stem.replace("_digest", "") == reports[0].stem.replace("_judge", "")

    text = reports[0].read_text(encoding="utf-8")
    assert "PAPER_ONLY" in text
    # The judge reports the TIME_EXIT the fixture closed, not an empty ledger.
    assert "closed trades: 1" in text
    assert "(1 settled, 0 invalidated)" in text
    digest = json.loads(digests[0].read_text(encoding="utf-8"))
    assert digest["mission_id"] == GOLD_PAPER_MISSION
    assert digest["signed"] is False
    assert digest["head_hash"]


def test_report_only_touches_no_network(populated_ledger, soak_dir, monkeypatch):
    """A network call inside the daily report would make it unrunnable on a
    machine with no egress, which is exactly when a soak's report matters most."""
    import urllib.request

    def no_network(*args, **kwargs):
        raise AssertionError("the daily report must not touch the network")

    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    assert soak.main(["--report-only", "--soak-dir", str(soak_dir),
                      "--ledger-path", str(populated_ledger)]) == 0


# ------------------------------------------------------------- the argument --


def test_the_interval_must_be_positive(soak_dir):
    with pytest.raises(SystemExit):
        soak.main(["--interval-sec", "0", "--soak-dir", str(soak_dir)])


def test_once_and_report_only_are_mutually_exclusive(soak_dir):
    with pytest.raises(SystemExit):
        soak.main(["--report-only", "--once", "--soak-dir", str(soak_dir)])
