"""M13 gold paper cycle — real XAU data, fake money, recorded honestly.

The vision's ladder has gold at T0 and the two-source law is gold's safety gate:
these tests pin that the track never trades on a single or conflicting price,
never invents a PnL it cannot price, keeps its bankroll identity exact, and
records every cycle into the canonical mission ledger without creating a
store.
"""

from __future__ import annotations

import math

import pytest

from architecture.markets.gold_paper import (
    GOLD_PAPER_AGENT,
    GOLD_PAPER_MISSION,
    GOLD_ROUND_TRIP_BPS,
    GoldPaperTrack,
)
from architecture.markets.risk import PaperBreaker
from architecture.mission.ledger import MissionLedger
from architecture.providers.gold import (
    CONFLICT,
    UNRESOLVED,
    VERIFIED,
    GoldPriceWitness,
)

T0 = 1_791_579_599.0
HOUR = 3600.0


def _witness(state: str, price: float | None, *, reason: str = "test",
             spread: float | None = None) -> GoldPriceWitness:
    return GoldPriceWitness(
        state=state, reason=reason, price_usd=price, spread_pct=spread,
        checked_at=T0)


# ------------------------------------------------------------- entry gate ---


def test_a_verified_price_opens_a_paper_position():
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0)
    assert track.position is not None
    assert r.witness_state == VERIFIED and r.price_usd == pytest.approx(4200.0)
    assert track.position.entry_price == pytest.approx(4200.0)
    assert track.position.qty_oz > 0.0
    # Entry costs are charged, so the executed price is above the verified one.
    assert track.position.exec_price > track.position.entry_price
    assert r.recorded is False and r.ledger_error is None   # no ledger supplied


def test_an_unresolved_witness_never_opens_a_position():
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(UNRESOLVED, None), now=T0)
    assert track.position is None
    assert r.price_usd is None
    assert r.exit is None


def test_a_conflicting_witness_never_opens_a_position():
    """Law line 8: disagreement is CONFLICT, never a PASS into a trade."""
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(CONFLICT, None, reason="source_disagreement"),
                        now=T0)
    assert track.position is None
    assert r.witness_state == CONFLICT and r.price_usd is None


def test_a_stale_witness_is_treated_as_no_data():
    from architecture.providers.gold import STALE
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(STALE, None), now=T0)
    assert track.position is None
    assert r.witness_state == STALE


def test_entry_notional_is_the_declared_paper_size():
    track = GoldPaperTrack(notional_usd=500.0)
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    assert track.position.notional_usd == pytest.approx(500.0)


# ------------------------------------------------------------- exits -------


def test_take_profit_closes_at_the_corroborated_price():
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    tp = 4000.0 * (1 + track.cfg["take_profit_pct"])
    r = track.run_cycle(_witness(VERIFIED, tp * 1.01), now=T0 + HOUR)
    assert r.exit is not None and r.exit["reason"] == "TAKE_PROFIT"
    assert r.realized_pnl_usd is not None and r.realized_pnl_usd > 0.0
    assert track.position is None


def test_stop_loss_closes_and_loses_money():
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    sl = 4000.0 * (1 - track.cfg["stop_loss_pct"])
    r = track.run_cycle(_witness(VERIFIED, sl * 0.99), now=T0 + HOUR)
    assert r.exit is not None and r.exit["reason"] == "STOP_LOSS"
    assert r.realized_pnl_usd is not None and r.realized_pnl_usd < 0.0


def test_time_exit_fires_after_the_hold_horizon():
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    horizon_s = track.cfg["max_hold_hours"] * HOUR
    r = track.run_cycle(_witness(VERIFIED, 4000.0), now=T0 + horizon_s + 1)
    assert r.exit is not None and r.exit["reason"] == "TIME_EXIT"


def test_a_conflict_mid_position_is_a_security_event_that_invalidates_at_once():
    """Law line 8: active disagreement is a post-entry veto. PT-X1 invalidates
    a vetoed trade that has no fresh price rather than holding it open."""
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    r = track.run_cycle(_witness(CONFLICT, None, reason="source_disagreement"),
                        now=T0 + HOUR)
    assert r.exit is not None
    assert r.exit["reason"] == "INVALID_DATA_UNAVAILABLE"
    assert r.realized_pnl_usd == 0.0
    assert track.position is None


def test_no_data_mid_position_is_held_open_and_reported_unpriced():
    """Law line 7: UNRESOLVED is no data, not a security event. The position is
    held, TP/SL cannot fire without a price, and it is reported UNPRICED."""
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    r = track.run_cycle(_witness(UNRESOLVED, None,
                                 reason="insufficient_independent_sources"),
                        now=T0 + HOUR)
    assert r.exit is None
    assert track.position is not None
    assert r.price_usd is None
    assert track.open_unpriced is True
    assert r.unpriced_for_s is not None and r.unpriced_for_s == pytest.approx(HOUR)


def test_an_held_unpriced_position_never_exits_on_the_last_verified_price():
    """The stale verified price cannot trigger TP/SL while the gate is down."""
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    # A price far past take profit arrives uncorroborated; it must not close.
    r = track.run_cycle(_witness(UNRESOLVED, None), now=T0 + HOUR)
    assert r.exit is None
    assert track.position is not None


def test_a_vetoed_position_with_no_price_times_out_as_invalidated():
    """The veto path lands on the time horizon as INVALID_DATA_UNAVAILABLE."""
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    horizon_s = track.cfg["max_hold_hours"] * HOUR
    r = track.run_cycle(_witness(UNRESOLVED, None,
                                 reason="insufficient_independent_sources"),
                        now=T0 + horizon_s + 1)
    assert r.exit is not None
    assert r.exit["reason"] == "INVALID_DATA_UNAVAILABLE"
    # No PnL is invented for a trade that could not be priced.
    assert r.realized_pnl_usd == 0.0
    assert track.position is None


def test_an_invalidated_trade_costs_nothing_and_invents_nothing():
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    horizon_s = track.cfg["max_hold_hours"] * HOUR
    before = track.equity_usd
    track.run_cycle(_witness(UNRESOLVED, None),
                    now=T0 + horizon_s + 1)
    assert track.equity_usd == pytest.approx(before)
    assert track.realized_pnl_usd == pytest.approx(0.0)


# ------------------------------------------------------------- accounting ---


def test_the_bankroll_identity_holds_on_every_path():
    """equity == bankroll + cumulative realised PnL, exactly, at every cycle."""
    track = GoldPaperTrack()
    seq = [4000.0, 4200.0, 3900.0, None, 4300.0, 4050.0]
    now = T0
    for price in seq:
        w = _witness(VERIFIED if price is not None else UNRESOLVED, price)
        track.run_cycle(w, now=now)
        now += 6 * HOUR
        assert track.equity_is_consistent is True


def test_costs_are_charged_round_trip():
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    # Exit at the identical price once the horizon closes it: the round-trip
    # cost must make the trade a loss, because costs are never waived.
    horizon_s = track.cfg["max_hold_hours"] * HOUR
    r = track.run_cycle(_witness(VERIFIED, 4000.0), now=T0 + horizon_s + 1)
    assert r.exit is not None and r.exit["reason"] == "TIME_EXIT"
    assert r.realized_pnl_usd is not None and r.realized_pnl_usd < 0.0
    # A flat trade at the entry price costs the declared round trip, computed
    # as a proportional spread on both legs: proceeds = N*(1-h)/(1+h) for
    # h = round_trip_bps/2. The compounding makes it marginally less than the
    # naive N*bps/1e4, and it can never exceed it.
    h = GOLD_ROUND_TRIP_BPS / 2.0 / 10_000.0
    proportional = track.notional_usd * ((1.0 - h) / (1.0 + h) - 1.0)
    assert r.realized_pnl_usd == pytest.approx(proportional, rel=1e-9)
    assert -r.realized_pnl_usd <= track.notional_usd * GOLD_ROUND_TRIP_BPS / 10_000.0


def test_realizable_equity_marks_an_open_position_to_the_current_price():
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4000.0), now=T0)
    flat = track.realizable_equity(None)
    assert flat == pytest.approx(track.equity_usd)
    marked = track.realizable_equity(4200.0)
    assert marked > track.equity_usd          # an unrealised gain is shown
    # and the mark is net of the exit cost
    qty = track.position.qty_oz
    exec_exit = 4200.0 * (1 - GOLD_ROUND_TRIP_BPS / 2e4)
    assert marked == pytest.approx(track.equity_usd + qty * exec_exit
                                   - track.notional_usd)


# ------------------------------------------------------------- ledger ------


@pytest.fixture()
def ledger(tmp_path) -> MissionLedger:
    return MissionLedger(tmp_path / "gold_paper_ledger.jsonl")


def _started(ledger: MissionLedger) -> None:
    ledger.start(GOLD_PAPER_MISSION, phase="paper", task="gold paper cycle",
                 agent=GOLD_PAPER_AGENT)


# --------------------------------------------------- M39 / §12 the breaker ---


def test_a_clean_cycle_arms_the_paper_breaker(ledger: MissionLedger):
    _started(ledger)
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    assert r.breaker is not None and r.breaker.state == "ARMED"
    assert r.breaker.allowed is True
    assert r.position is not None


def test_a_tripped_breaker_blocks_new_risk(ledger: MissionLedger):
    """A verified price and a flat track are not enough: the breaker decides."""
    _started(ledger)
    track = GoldPaperTrack(
        breaker=PaperBreaker(bankroll=10_000.0, daily_loss_limit_pct=0.0))
    track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    closed = track.run_cycle(_witness(VERIFIED, 2500.0), now=T0 + HOUR,
                             ledger=ledger)          # a stop loss
    assert closed.realized_pnl_usd is not None and closed.realized_pnl_usd < 0

    r = track.run_cycle(_witness(VERIFIED, 2500.0), now=T0 + 2 * HOUR,
                        ledger=ledger)
    assert r.breaker is not None and r.breaker.state == "TRIPPED"
    assert r.breaker.allowed is False
    assert any("daily loss" in reason for reason in r.breaker.reasons)
    assert r.position is None, "a tripped breaker must not take new risk"
    assert r.exit is None
    assert r.price_usd is not None, "the cycle still records the price"


def test_a_tripped_breaker_does_not_flatten_an_open_position(ledger: MissionLedger):
    """The paper breaker halts *new* risk; it does not close a position.

    Flattening within 60s is the live-trading action the vision assigns to
    M39, and there is no live trading here -- PAPER_ONLY. The frozen exit card
    has no breaker reason either, so inventing one would be fabricating an
    exit vocabulary Lane A does not have. The position is held and the trip is
    reported.
    """
    _started(ledger)
    track = GoldPaperTrack(
        breaker=PaperBreaker(bankroll=10_000.0, max_open_risk_pct=1.0))
    entered = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0,
                              ledger=ledger)
    assert entered.position is not None
    r = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0 + HOUR,
                        ledger=ledger)
    assert r.breaker is not None and r.breaker.state == "TRIPPED"
    assert r.position is not None, "an open position is held, not flattened"
    assert r.exit is None


def test_the_breaker_state_is_recorded_every_cycle(ledger: MissionLedger):
    _started(ledger)
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    cp = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]
    assert cp["breaker"]["state"] == "ARMED"
    assert cp["breaker"]["allowed"] is True
    assert cp["breaker"]["reasons"] == []


def test_only_settled_closes_enter_the_risk_blotter(ledger: MissionLedger):
    """An invalidated close carries no PnL distribution to bootstrap from, so
    it must not count toward the 30-trade threshold."""
    _started(ledger)
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    now = T0
    invalidated = None
    for _ in range(9):                                   # 48h at 6h steps
        now += 6 * HOUR
        r = track.run_cycle(_witness(UNRESOLVED, None), now=now,
                            ledger=ledger)
        if r.exit is not None:
            invalidated = r
    assert invalidated is not None, "the hold horizon should have invalidated"
    assert invalidated.exit["reason"] == "INVALID_DATA_UNAVAILABLE"
    assert invalidated.price_usd is None
    assert track.closed == 1, "the invalidation closed the position"
    assert track.closed_trades == [], "but it is not a settled trade"


def test_a_restarted_track_inherits_its_own_loss_history(tmp_path):
    """The risk history is replayed from the ledger, so restarting cannot
    reset the §12 limits."""
    import time

    from architecture.markets.gold_paper import _track_from_ledger

    ledger = MissionLedger(tmp_path / "restart.jsonl")
    _started(ledger)
    track = GoldPaperTrack(
        breaker=PaperBreaker(bankroll=10_000.0, daily_loss_limit_pct=0.0))
    start = time.time()
    track.run_cycle(_witness(VERIFIED, 4200.0), now=start, ledger=ledger)
    track.run_cycle(_witness(VERIFIED, 2500.0), now=start + 10.0,
                    ledger=ledger)                        # a stop loss

    rebuilt = _track_from_ledger(ledger)
    assert len(rebuilt.closed_trades) == 1
    assert rebuilt.closed_trades[0]["realized_pnl_usd"] < 0
    assert len(rebuilt.equity_curve) == 2
    assert rebuilt.position is None

    # Real wall-clock now, because the ledger's own timestamps are real.
    r = rebuilt.run_cycle(_witness(VERIFIED, 2500.0), now=time.time() + 20.0,
                          ledger=ledger)
    assert r.breaker is not None and r.breaker.state == "TRIPPED"
    assert r.position is None, (
        "the restarted track still enforces the loss limit it inherited")


def test_cycles_are_recorded_into_the_canonical_ledger(ledger: MissionLedger):
    _started(ledger)
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    assert r.recorded is True and r.ledger_error is None
    entries = ledger.history(GOLD_PAPER_MISSION)
    assert len(entries) >= 1
    last = ledger.latest(GOLD_PAPER_MISSION)
    cp = last["CHECKPOINT"]
    assert cp["market"] == "gold" and cp["cycle"] == 1
    assert cp["witness"]["state"] == VERIFIED
    assert cp["price_usd"] == pytest.approx(4200.0)
    assert cp["paper_only"] is True
    assert last["CURRENT_AGENT"] == GOLD_PAPER_AGENT


def test_a_no_data_cycle_is_recorded_as_no_data_not_as_a_trade(ledger: MissionLedger):
    _started(ledger)
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(UNRESOLVED, None), now=T0, ledger=ledger)
    assert r.recorded is True
    cp = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]
    assert cp["witness"]["state"] == UNRESOLVED
    assert cp["price_usd"] is None
    assert cp["position"] is None
    assert cp["exit"] is None


def test_quote_provenance_is_carried_into_the_ledger(ledger: MissionLedger):
    _started(ledger)
    track = GoldPaperTrack()
    track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    cp = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]
    assert "quotes" in cp["witness"]
    assert isinstance(cp["witness"]["quotes"], list)


def test_a_ledger_fault_does_not_silently_drop_a_cycle(ledger: MissionLedger):
    """No start() called -> MissionNotFoundError surfaces on the result."""
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0, ledger=ledger)
    assert r.recorded is False
    assert r.ledger_error is not None and "MissionNotFound" in r.ledger_error


def test_no_new_store_is_created_by_the_track(ledger: MissionLedger):
    """INV-31: gold records into the one canonical ledger, not a new store."""
    _started(ledger)
    track = GoldPaperTrack()
    for i in range(3):
        track.run_cycle(_witness(VERIFIED, 4200.0), now=T0 + i * HOUR,
                        ledger=ledger)
    events = {e["event"] for e in ledger.history(GOLD_PAPER_MISSION)}
    kinds = {e["kind"] for e in ledger.history(GOLD_PAPER_MISSION)}
    # The ledger's own vocabulary: every row is kind=STATE, distinguished by
    # event. Gold introduced no new kind and no new store.
    assert kinds == {"STATE"}
    assert events <= {"START", "CHECKPOINT"}


# ------------------------------------------------------------- paper only ---


def test_the_track_has_no_execution_surface():
    """The zero-money invariant: no signing, no order, no exchange client.

    Checked over the module's AST rather than its text: docstrings honestly
    say the words "never signs anything", and a text grep would flag that
    prose and make the invariant meaningless.
    """
    import ast
    import inspect

    from architecture.markets import gold_paper as gp
    tree = ast.parse(inspect.getsource(gp))
    identifiers: set[str] = set()
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                imported.add(a.asname or a.name)
        elif isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
    banned = ("sign", "private_key", "place_order", "create_order", "web3",
              "eth_account", "ccxt", "send_transaction", "transfer")
    for name in banned:
        assert name not in imported, f"gold paper track imports {name!r}"
        assert name not in identifiers, f"gold paper track calls {name!r}"
    # The only Lane A (paper_trading) import is the frozen exit discipline.
    lane_a = {a.asname or a.name
              for node in ast.walk(tree)
              if isinstance(node, ast.ImportFrom)
              and (node.module or "").startswith("paper_trading")
              for a in node.names}
    assert lane_a == {"check_exits", "EXIT_V1"}, (
        f"unexpected Lane A imports: {lane_a}")


def test_the_exit_vocabulary_is_the_token_engine_vocabulary():
    """Gold reuses the frozen Lane A exit card rather than inventing rules."""
    from paper_trading.exit_rules import EXIT_V1
    track = GoldPaperTrack()
    assert track.cfg["version"] == EXIT_V1["version"]
    assert track.cfg["take_profit_pct"] == EXIT_V1["take_profit_pct"]
    assert track.cfg["stop_loss_pct"] == EXIT_V1["stop_loss_pct"]


def test_math_is_finite_on_a_normal_cycle():
    track = GoldPaperTrack()
    r = track.run_cycle(_witness(VERIFIED, 4200.0), now=T0)
    assert math.isfinite(r.equity_usd)
    assert track.position is None or math.isfinite(track.position.qty_oz)
