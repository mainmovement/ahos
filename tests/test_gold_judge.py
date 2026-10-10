"""M42 paper judge — the independent reconcile over the recorded paper ledger.

Vision M42 (:1269): hash-chained ledger + nightly reconcile, mismatch = HALT.
DEDUP_MERGE_MAP v1.20 folds the daily digest (:12) and the paper double-entry
(:38) into M42, and names the M42 judge as one of M13's five acceptance gates.

Two classes of test here, and both matter:

* **Tamper** — editing, deleting or reordering a recorded entry breaks the hash
  chain, so the judge reports ``BROKEN_CHAIN``. The ledger's own cryptography
  is the first line of defence; these tests confirm the judge surfaces it.
* **A chain-intact ledger that lies** — the judge's real purpose. A track can
  write a perfectly valid hash chain and still record a number it did not earn,
  so these tests *craft* checkpoints (through the ledger's own append, so the
  chain stays intact) that mimic each dishonest or buggy shape, and pin that
  the judge catches it.
"""

from __future__ import annotations

import ast
import json

import pytest

from architecture.markets.gold_paper import (
    GOLD_PAPER_MISSION,
    GoldPaperTrack,
)
from architecture.markets.judge import (
    BROKEN_CHAIN,
    CLEAN,
    DISCREPANCY,
    Finding,
    JudgeReport,
    daily_digest,
    judge_paper_ledger,
    write_judge_report,
)
from architecture.mission.ledger import MissionLedger, canonical_json
from architecture.providers.gold import VERIFIED, GoldPriceWitness

NOW = 1_791_579_599.0          # 2026-10-09 ~20:53 UTC
STEP = 6 * 3600.0              # 6h: keeps the exit card's 6h freshness window live
ENTRY = 4200.0
EXIT_PRICE = 6400.0            # +52% from entry -> TAKE_PROFIT under PT-X1
BPS = 20.0
BANKROLL = 10_000.0
NOTIONAL = 1_000.0
HALF = BPS / 2.0 / 10_000.0

#: The entry half-cost the track charges, so crafted numbers match its own
#: arithmetic exactly rather than an approximation of it.
EXEC = ENTRY * (1.0 + HALF)
QTY = NOTIONAL / EXEC


def _witness(price: float | None, state: str = VERIFIED) -> GoldPriceWitness:
    return GoldPriceWitness(state=state, reason="synthetic",
                            price_usd=price, checked_at=NOW)


def _ledger(tmp_path, name="judge_ledger.jsonl") -> MissionLedger:
    ledger = MissionLedger(tmp_path / name)
    ledger.start(GOLD_PAPER_MISSION, phase="paper_trading",
                 task="M42 judge test surface", agent="AG:AG-28")
    return ledger


def _pos(entry_ts: float = NOW, price: float = ENTRY) -> dict:
    exec_price = price * (1.0 + HALF)
    return {"entry_ts": entry_ts, "entry_price": price,
            "exec_price": exec_price, "notional_usd": NOTIONAL,
            "qty_oz": NOTIONAL / exec_price, "cycle": 1}


def _cp(cycle: int, **over) -> dict:
    """A checkpoint payload in the exact shape the track records."""
    position = over.pop("position", None)
    exit_event = over.pop("exit_event", None)
    realized = over.pop("realized", None)
    price = over.pop("price", ENTRY)
    equity = over.pop("equity", BANKROLL)
    cumulative = over.pop("cumulative", 0.0)
    closed = over.pop("closed", 0)
    payload = {
        "market": "gold",
        "cycle": cycle,
        "witness": {"state": over.pop("witness_state", VERIFIED),
                    "reason": "crafted", "spread_pct": 0.1,
                    "tolerance_pct": 1.0, "quotes": []},
        "price_usd": price,
        "position": position,
        "exit": exit_event,
        "realized_pnl_usd": realized,
        "equity_usd": equity,
        "bankroll_usd": over.pop("bankroll", BANKROLL),
        "realizable_equity_usd": equity,
        "cumulative_realized_pnl_usd": cumulative,
        "closed_trades": closed,
        "unpriced_for_s": over.pop("unpriced", None),
        "open_unpriced": position is not None and price is None,
        "round_trip_bps": over.pop("bps", BPS),
        "exit_card": "PT-X1-v1",
        "paper_only": over.pop("paper_only", True),
    }
    assert not over, f"unknown craft keys: {sorted(over)}"
    return payload


def _craft(ledger: MissionLedger, payload: dict) -> None:
    """Append one crafted checkpoint through the ledger, so the chain holds."""
    ledger.checkpoint(GOLD_PAPER_MISSION, payload,
                      LAST_EVIDENCE=f"crafted cycle {payload['cycle']}")


def _expected_pnl(price: float = EXIT_PRICE) -> float:
    return QTY * price * (1.0 - HALF) - NOTIONAL


# ------------------------------------------------------------- independence --


def test_the_judge_does_not_import_the_track_it_audits():
    """DEDUP:141 — a fresh reviewer with no shared history. If the judge read
    the track's in-memory state it would believe it by construction."""
    src = ast.parse(open("architecture/markets/judge.py", encoding="utf-8").read())
    modules: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(src):
        if isinstance(node, ast.Import):
            for a in node.names:
                modules.add(a.name)
                names.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    assert not any("gold_paper" in m for m in modules), (
        "the judge must not import the gold track; it reads the ledger")
    assert not any(m.startswith("paper_trading") for m in modules), (
        "the judge must not import Lane A")
    assert "GoldPaperTrack" not in {
        n.id for n in ast.walk(src) if isinstance(n, ast.Name)}


# --------------------------------------------------------- a faithful ledger --


def _faithful(tmp_path) -> MissionLedger:
    """Enter, take profit, re-enter, then run out of data and invalidate."""
    ledger = _ledger(tmp_path)
    track = GoldPaperTrack()
    t = NOW
    for price in (ENTRY, EXIT_PRICE, EXIT_PRICE,
                  None, None, None, None, None, None, None, None):
        track.run_cycle(_witness(price), now=t, ledger=ledger)
        t += STEP
    return ledger


def test_a_faithful_ledger_reconciles_clean(tmp_path):
    ledger = _faithful(tmp_path)
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert r.verdict == CLEAN
    assert r.findings == ()
    assert r.cycles == 11
    assert r.summary["closed_trades"] == 2          # one settled, one invalidated
    assert r.summary["settled"] == 1
    assert r.summary["invalidated"] == 1
    assert r.head_hash is not None and len(r.head_hash) == 64


def test_the_chain_head_is_the_ledgers_own(tmp_path):
    ledger = _faithful(tmp_path)
    assert ledger.verify()["head_hash"] == judge_paper_ledger(
        ledger, GOLD_PAPER_MISSION).head_hash


def test_the_judge_reproduces_the_tracks_own_numbers(tmp_path):
    """The judge and the track agree on a faithful ledger -- the positive case
    that makes the negative tests meaningful."""
    ledger = _faithful(tmp_path)
    track_entries = [e for e in ledger.history(GOLD_PAPER_MISSION)
                     if e["event"] == "CHECKPOINT"]
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert r.verdict == CLEAN
    assert r.summary["gross_realized_pnl_usd"] == pytest.approx(
        _expected_pnl())
    assert r.summary["equity_usd"] == pytest.approx(
        BANKROLL + _expected_pnl())
    assert r.summary["closed_trades"] == track_entries[-1]["state"]["CHECKPOINT"]["closed_trades"]


# ------------------------------------------------------------ tamper = HALT --


def _rewrite(ledger: MissionLedger, mutate) -> MissionLedger:
    """Rewrite the ledger file after mutating each record's CHECKPOINT, then
    re-hash only the mutated line -- the shape of an in-place edit that hopes
    the chain will not be re-derived."""
    lines = [ln for ln in ledger.path.read_text(encoding="utf-8").split("\n") if ln]
    out = []
    for ln in lines:
        rec = json.loads(ln)
        mutate((rec.get("state") or {}).get("CHECKPOINT"))
        out.append(rec)
    text = "\n".join(json.dumps(r) for r in out) + "\n"
    ledger.path.write_text(text, encoding="utf-8")
    return MissionLedger(ledger.path)


def _rewrite_preserving_hashes(ledger: MissionLedger, mutate) -> MissionLedger:
    """Mutate records and recompute each entry_hash, leaving prev_hash alone.

    This is what an attacker who controls the file would do: the chain then
    breaks at the first rewritten entry, because its ``prev_hash`` no longer
    matches the recomputed hash of the entry before it.
    """
    from architecture.mission.ledger import _sha
    lines = [ln for ln in ledger.path.read_text(encoding="utf-8").split("\n") if ln]
    out = []
    for ln in lines:
        rec = json.loads(ln)
        mutate((rec.get("state") or {}).get("CHECKPOINT"))
        body = {k: v for k, v in rec.items() if k != "entry_hash"}
        rec["entry_hash"] = _sha(canonical_json(body))
        out.append(rec)
    ledger.path.write_text("\n".join(json.dumps(r) for r in out) + "\n",
                           encoding="utf-8")
    return MissionLedger(ledger.path)


def test_an_edit_to_a_recorded_number_breaks_the_chain(tmp_path):
    ledger = _faithful(tmp_path)

    def _bump(cp):
        if cp is not None:
            cp["equity_usd"] = cp.get("equity_usd", 0.0) + 500.0
    r = judge_paper_ledger(_rewrite(ledger, _bump), GOLD_PAPER_MISSION)
    assert r.verdict == BROKEN_CHAIN
    assert r.findings[0].code == "J-CHAIN"
    assert r.clean is False


def test_a_rehashed_edit_still_breaks_the_chain(tmp_path):
    """Recomputing every entry_hash does not help: prev_hash no longer chains."""
    ledger = _faithful(tmp_path)

    def _bump(cp):
        if cp is not None:
            cp["equity_usd"] = cp.get("equity_usd", 0.0) + 500.0
    assert judge_paper_ledger(_rewrite_preserving_hashes(ledger, _bump),
                              GOLD_PAPER_MISSION).verdict == BROKEN_CHAIN


def test_a_deleted_entry_breaks_the_chain(tmp_path):
    ledger = _faithful(tmp_path)
    lines = [ln for ln in ledger.path.read_text(encoding="utf-8").split("\n") if ln]
    ledger.path.write_text("\n".join(lines[:1] + lines[2:]) + "\n",
                           encoding="utf-8")
    assert judge_paper_ledger(MissionLedger(ledger.path),
                              GOLD_PAPER_MISSION).verdict == BROKEN_CHAIN


def test_a_reordered_ledger_breaks_the_chain(tmp_path):
    ledger = _faithful(tmp_path)
    lines = [ln for ln in ledger.path.read_text(encoding="utf-8").split("\n") if ln]
    ledger.path.write_text("\n".join([lines[0], lines[2], lines[1]]) + "\n",
                           encoding="utf-8")
    assert judge_paper_ledger(MissionLedger(ledger.path),
                              GOLD_PAPER_MISSION).verdict == BROKEN_CHAIN


# --------------------------------------- a chain-intact ledger that lies -----

def test_an_equity_number_the_track_did_not_earn_is_caught(tmp_path):
    """The money identity: equity moves only through a recorded realized PnL."""
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1))
    _craft(ledger, _cp(2, equity=BANKROLL + 123.0))     # no trade closed
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert r.verdict == DISCREPANCY
    assert any(f.code == "J-EQUITY" for f in r.findings)


def test_a_pnl_that_does_not_rederive_is_a_double_entry_finding(tmp_path):
    """§49 / DEDUP:38: the recorded realized must equal the position's debit
    against the corroborated credit."""
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    lied = _expected_pnl() + 1.0
    _craft(ledger, _cp(2, position=None, price=EXIT_PRICE,
                       exit_event={"reason": "TAKE_PROFIT"},
                       realized=lied, equity=BANKROLL + lied,
                       cumulative=lied, closed=1))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-DOUBLE" for f in r.findings)
    assert r.summary["settled"] == 1
    assert "double-entry recomputation" in next(
        f.detail for f in r.findings if f.code == "J-DOUBLE")


def test_a_double_entry_that_rederives_exactly_is_clean(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    exact = _expected_pnl()
    _craft(ledger, _cp(2, position=None, price=EXIT_PRICE,
                       exit_event={"reason": "TAKE_PROFIT"},
                       realized=exact, equity=BANKROLL + exact,
                       cumulative=exact, closed=1))
    assert judge_paper_ledger(ledger, GOLD_PAPER_MISSION).verdict == CLEAN


def test_a_pnl_invented_on_an_unpriceable_close_is_caught(tmp_path):
    """PT-X1 invalidates an unpriceable risk; the ledger must not price it."""
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    _craft(ledger, _cp(2, position=_pos(), price=None,
                       witness_state="UNRESOLVED", unpriced=STEP))
    _craft(ledger, _cp(3, position=None, price=None,
                       witness_state="UNRESOLVED",
                       exit_event={"reason": "INVALID_DATA_UNAVAILABLE"},
                       realized=5.0, equity=BANKROLL + 5.0,
                       cumulative=5.0, closed=1, unpriced=2 * STEP))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-INVENTED" for f in r.findings)
    assert r.summary["invalidated"] == 1


def test_an_honest_zero_pnl_invalidation_is_clean(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    _craft(ledger, _cp(2, position=_pos(), price=None,
                       witness_state="UNRESOLVED", unpriced=STEP))
    _craft(ledger, _cp(3, position=None, price=None,
                       witness_state="UNRESOLVED",
                       exit_event={"reason": "INVALID_DATA_UNAVAILABLE"},
                       realized=0.0, equity=BANKROLL, cumulative=0.0,
                       closed=1, unpriced=2 * STEP))
    assert judge_paper_ledger(ledger, GOLD_PAPER_MISSION).verdict == CLEAN


def test_a_position_appearing_without_a_corroborated_price_is_caught(tmp_path):
    """The gold law enters only on a verified price; this is that law's audit."""
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=None,
                       witness_state="UNRESOLVED"))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-POSITION" for f in r.findings)


def test_a_position_vanishing_without_an_exit_is_caught(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    _craft(ledger, _cp(2, position=None, price=ENTRY))       # no exit recorded
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-POSITION" for f in r.findings)


def test_an_exit_recorded_while_flat_is_caught(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=None, price=ENTRY))
    _craft(ledger, _cp(2, position=None, price=EXIT_PRICE,
                       exit_event={"reason": "TAKE_PROFIT"},
                       realized=_expected_pnl(), equity=BANKROLL + _expected_pnl(),
                       cumulative=_expected_pnl(), closed=1))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-POSITION" for f in r.findings)


def test_a_position_changing_identity_mid_flight_is_caught(tmp_path):
    """The gold track enters only while flat; a second position cannot appear
    under an open one."""
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(entry_ts=NOW), price=ENTRY))
    _craft(ledger, _cp(2, position=_pos(entry_ts=NOW + STEP), price=ENTRY))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-POSITION" for f in r.findings)


def test_a_gap_in_the_cycle_numbers_is_reported(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1))
    _craft(ledger, _cp(2))
    _craft(ledger, _cp(4))                       # cycle 3 is missing
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-CYCLE" for f in r.findings)


def test_a_checkpoint_that_stops_calling_itself_paper_is_flagged(tmp_path):
    """A paper ledger must keep labelling itself paper; losing the label is the
    first sign of a real-money path creeping in."""
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1))
    _craft(ledger, _cp(2, paper_only=False))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-PAPER" for f in r.findings)


def test_the_final_claimed_counters_disagreeing_with_the_ledger_is_caught(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    exact = _expected_pnl()
    _craft(ledger, _cp(2, position=None, price=EXIT_PRICE,
                       exit_event={"reason": "TAKE_PROFIT"},
                       realized=exact, equity=BANKROLL + exact,
                       cumulative=exact, closed=7))          # claims 7 closes
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-CLAIM" for f in r.findings)


def test_an_undeclared_bankroll_is_reported_not_assumed(tmp_path):
    """A ledger that never declares its opening balance cannot have its
    absolute money identity checked; that is reported, not waved through."""
    ledger = _ledger(tmp_path)
    _craft(ledger, {k: v for k, v in _cp(1).items() if k != "bankroll_usd"})
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-BANKROLL" for f in r.findings)
    assert r.verdict == DISCREPANCY


def test_a_supplied_bankroll_makes_the_absolute_identity_evaluable(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, {k: v for k, v in _cp(1).items() if k != "bankroll_usd"})
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION, bankroll_usd=BANKROLL)
    assert not any(f.code == "J-BANKROLL" for f in r.findings)
    assert r.summary["bankroll_usd"] == BANKROLL
    assert r.verdict == CLEAN


def test_an_equity_that_denies_the_declared_bankroll_is_caught(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1))
    _craft(ledger, _cp(2, equity=BANKROLL * 2))       # money from nowhere
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-EQUITY" for f in r.findings)
    assert r.summary["bankroll_usd"] == BANKROLL


def test_an_unknown_mission_is_not_reported_clean(tmp_path):
    ledger = _ledger(tmp_path)
    r = judge_paper_ledger(ledger, "M13-NO-SUCH-MISSION")
    assert r.verdict == DISCREPANCY
    assert r.cycles == 0


def test_the_cumulative_pnl_counter_is_checked_against_the_closes(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, position=_pos(), price=ENTRY))
    exact = _expected_pnl()
    _craft(ledger, _cp(2, position=None, price=EXIT_PRICE,
                       exit_event={"reason": "TAKE_PROFIT"},
                       realized=exact, equity=BANKROLL + exact,
                       cumulative=exact * 3, closed=1))
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert any(f.code == "J-EQUITY" and "cumulative" in f.detail
               for f in r.findings)


# ------------------------------------------------------------ the digest -----


def test_a_digest_is_recorded_unsigned_with_its_reason(tmp_path):
    ledger = _faithful(tmp_path)
    d = daily_digest(ledger, GOLD_PAPER_MISSION)
    assert d is not None, "the fixture wrote entries today"
    assert d["signed"] is False
    assert "Credential Manager" in d["unsigned_reason"]
    assert len(d["digest_sha256"]) == 64
    assert d["head_hash"] == ledger.verify()["head_hash"]
    assert d["entries"] >= 1


def test_a_digest_of_a_day_with_no_entries_is_none(tmp_path):
    ledger = _faithful(tmp_path)
    assert daily_digest(ledger, GOLD_PAPER_MISSION, day="2000-01-01") is None


def test_no_digest_over_a_broken_chain(tmp_path):
    ledger = _faithful(tmp_path)
    lines = [ln for ln in ledger.path.read_text(encoding="utf-8").split("\n") if ln]
    ledger.path.write_text("\n".join(lines[:1]) + "\n", encoding="utf-8")
    assert daily_digest(MissionLedger(ledger.path),
                        GOLD_PAPER_MISSION, day="2026-10-09") is None


def test_the_digest_is_stable(tmp_path):
    ledger = _faithful(tmp_path)
    a = daily_digest(ledger, GOLD_PAPER_MISSION)
    b = daily_digest(ledger, GOLD_PAPER_MISSION)
    assert a and b and a["digest_sha256"] == b["digest_sha256"]


# ------------------------------------------------------------- rendering -----


def test_a_clean_report_says_clean(tmp_path):
    ledger = _faithful(tmp_path)
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert r.verdict == CLEAN
    out = tmp_path / "judge.md"
    write_judge_report(r, out)
    text = out.read_text(encoding="utf-8")
    assert "**Verdict: CLEAN**" in text
    assert "PAPER_ONLY" in text
    assert "No discrepancy" in text


def test_a_broken_chain_report_names_the_break_and_never_says_clean(tmp_path):
    r = JudgeReport(BROKEN_CHAIN, GOLD_PAPER_MISSION,
                    findings=(Finding("J-CHAIN", "tampered"),))
    out = tmp_path / "broken.md"
    write_judge_report(r, out)
    text = out.read_text(encoding="utf-8")
    assert "**Verdict: BROKEN_CHAIN**" in text
    assert "J-CHAIN" in text
    assert "**Verdict: CLEAN**" not in text


def test_a_discrepancy_report_lists_every_finding(tmp_path):
    ledger = _ledger(tmp_path)
    _craft(ledger, _cp(1, paper_only=False))
    _craft(ledger, _cp(3))                       # both J-PAPER and J-CYCLE
    r = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert r.verdict == DISCREPANCY
    out = tmp_path / "discrepancy.md"
    write_judge_report(r, out)
    text = out.read_text(encoding="utf-8")
    assert "**Verdict: DISCREPANCY**" in text
    assert "J-PAPER" in text and "J-CYCLE" in text
    assert "**Verdict: CLEAN**" not in text
