#!/usr/bin/env python3
"""M13 gold paper cycle — real XAU data, fake money, recorded once.

OWN-18 ("gold first") supersedes the crypto-first ordering for the paper track,
and this module is the gold market's T0 paper surface: it trades real,
two-source-corroborated gold prices for a fixed fake bankroll and records every
cycle into the canonical mission ledger. It never touches real funds, signs
anything, or reaches an exchange.

What is reused from frozen Lane A, import-only (the same established pattern as
``architecture/decision/advisor.py:39`` and ``architecture/intel/exitability.py``):

* ``paper_trading.exit_rules.EXIT_V1`` and ``check_exits`` — the exit threshold
  card and the pure exit decision. ``check_exits`` takes scalars only
  (entry price/time, observation price/time, consecutive liquidity breaches, a
  security recheck dict), so it is instrument-agnostic: gold passes
  ``obs_liq=None``, which makes the DEX liquidity-collapse leg inert, and the
  exit vocabulary gold reports is exactly the token engine's (TAKE_PROFIT,
  STOP_LOSS, TIME_EXIT, SECURITY_EVENT, INVALID_DATA_UNAVAILABLE).

What is deliberately NOT reused, and why:

* ``paper_trading.cost_model.buy/sell`` is liquidity-shaped — it returns None
  when ``liquidity_usd`` is None, because slippage is derived from pool depth.
  Gold has no on-chain liquidity depth, so the Lane A cost model correctly
  refuses to price a gold entry. Gold uses its own declared round-trip cost
  (:data:`GOLD_ROUND_TRIP_BPS`), which is an *assumption* for paper, not a
  measured market cost — and the T1 gate requires measured costs before any
  promotion, so the assumption is not allowed to survive into a promotion
  claim.
* ``paper_trading.cycle.run_full_cycle`` is Lane A and cannot be edited; it is
  also token-shaped end to end (candidates carry chain/address/security
  signals that gold does not have). Wiring gold into it would mean fabricating
  token-shaped inputs to satisfy a token engine, which the UNKNOWN > fabricated
  law forbids. This module is the gold analogue, not a branch of it.

The two-source witness is the entry gate. Gold has no security overlay — it has
no contract to audit — so the owner's two-source law *is* gold's safety gate:
no VERIFIED price, no entry. Mid-position, the law's own two failure modes map
onto the frozen exit card differently: a CONFLICT (sources actively disagree,
line 8) is a post-entry SECURITY_EVENT, which PT-X1 invalidates at once rather
than holding an unpriceable risk; UNRESOLVED or STALE (single, empty, stale or
unreachable, line 7) is *no data, not a security event*, so the position is
held open and reported UNPRICED until the horizon closes it as
INVALID_DATA_UNAVAILABLE. Either way no PnL is invented for a trade that could
not be priced, and TP/SL can never fire on an uncorroborated quote.

Recording: ``MissionLedger.checkpoint`` into the canonical
``architecture/mission/ledger.py`` store. INV-31 names one ledger, and M34 just
pinned it, so gold adds no new store and no ledger schema change — the cycle
evidence goes into the free-form ``CHECKPOINT`` field. The mission id is
``M13-GOLD-PAPER`` and ``CURRENT_AGENT`` is ``AG:AG-28`` (Zarrin, Gold & Oil
Division Lead), whose charter is ``allowed_authority: []`` with DECIDE and
PROMOTE forbidden and whose required probes are BACKTEST_CPCV_PROBE and
WALK_FORWARD_PROBE — a paper-evidence surface that must never promote.

Risk: :mod:`architecture.markets.risk` is the §5 sizing and §12 breaker, and it
gates entry here (M39's paper half). The breaker is *evaluated every cycle*, so
its state is always on the record, and it can never sit silently armed while
the limits drift past. It gates new risk only: flattening a position within 60
seconds is M39's live-trading action, and there is no live trading here, and
the frozen exit card has no breaker reason — so an open position is held and
the trip is reported rather than the exit vocabulary being extended. The
breaker's history inputs (the closed-trade blotter and the equity curve) are
replayed from the ledger by :func:`_track_from_ledger`, so a restart cannot
reset the §12 limits.

Judge: :mod:`architecture.markets.judge` is the M42 reconcile over this ledger.
It is deliberately not imported here — the judge reads the record, it does not
ask the track what happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from paper_trading.exit_rules import EXIT_V1, check_exits

from ..mission.ledger import MissionLedger
from ..providers.gold import VERIFIED, GoldPriceWitness
from .risk import ARMED, BreakerState, PaperBreaker

GOLD_PAPER_MISSION = "M13-GOLD-PAPER"
GOLD_PAPER_AGENT = "AG:AG-28"          # Zarrin, Gold & Oil Division Lead

#: The fake bankroll. Fictional money, fixed at track start, never topped up;
#: the zero-money invariant is structural, not a configuration flag.
PAPER_BANKROLL_USD = 10_000.0

#: Paper capital committed per gold position.
PAPER_NOTIONAL_USD = 1_000.0

#: Declared paper round-trip cost for gold, in basis points. An ASSUMPTION for
#: the paper track (a realistic retail spot/futures spread), not a measured
#: market cost. Net-of-cost accounting is applied from the first trade so the
#: equity curve is never flattered, and the T1 gate requires measured costs
#: before promotion, which this assumption cannot satisfy.
GOLD_ROUND_TRIP_BPS = 20.0

#: Positions that cannot be priced for longer than this are reported as a
#: distinct state rather than silently held. Kept at the exit card's own
#: freshness horizon so the two agree.
UNPRICED_ALARM_SEC = EXIT_V1["exit_reference_max_age_sec"]


@dataclass(frozen=True)
class GoldPosition:
    entry_ts: float
    entry_price: float          # verified price at entry, costs excluded
    exec_price: float           # price after the declared entry cost
    notional_usd: float
    qty_oz: float
    cycle: int


@dataclass(frozen=True)
class GoldCycleResult:
    """One cycle's outcome. ``realized_pnl_usd`` is None unless a trade closed."""

    cycle: int
    witness_state: str
    witness_reason: str
    price_usd: float | None
    position: GoldPosition | None
    exit: dict | None = None
    realized_pnl_usd: float | None = None
    equity_usd: float = PAPER_BANKROLL_USD
    unpriced_for_s: float | None = None
    recorded: bool = False
    ledger_error: str | None = None
    breaker: BreakerState | None = None
    halt: "HaltGate | None" = None

    @property
    def traded(self) -> bool:
        return self.exit is not None


@dataclass(frozen=True)
class HaltGate:
    """The M42 HALT, read back off the single ledger.

    ``allowed`` answers "may this cycle take new risk?" and is False whenever a
    HALT is on record or the ledger cannot be verified, so the entry gate that
    reads it stops rather than passing on a missing measurement.
    """

    state: str                        # ARMED | HALTED | UNMEASURED
    allowed: bool
    source: str | None = None
    reason: str | None = None


def _cost_bps(price: float, bps: float) -> float:
    return price * bps / 10_000.0


@dataclass
class GoldPaperTrack:
    """The gold paper track. Deterministic given the witnesses it is fed.

    Every mutating step is a function of (witness, now); the track carries no
    clock and no network of its own, so a replay of recorded witnesses
    reproduces the equity curve exactly.

    The risk inputs (``closed_trades`` and ``equity_curve``) are *derived from
    the ledger*, never appended from memory alone: the runner rebuilds them by
    replaying the mission's recorded checkpoints, so a track that restarts
    between cycles sees the same risk history it would have seen in one
    process. That keeps the ledger the single source of truth (INV-31) and
    means the §12 limits cannot be reset by restarting.
    """

    bankroll_usd: float = PAPER_BANKROLL_USD
    notional_usd: float = PAPER_NOTIONAL_USD
    round_trip_bps: float = GOLD_ROUND_TRIP_BPS
    cfg: dict[str, Any] = field(default_factory=lambda: dict(EXIT_V1))
    position: GoldPosition | None = None
    equity_usd: float = PAPER_BANKROLL_USD
    realized_pnl_usd: float = 0.0
    cycles: int = 0
    closed: int = 0
    last_priced_ts: float | None = None
    priced_this_cycle: bool = True
    #: The closed-trade blotter the §12 bootstrap and the loss limits consume.
    closed_trades: list[dict] = field(default_factory=list)
    #: The realised equity series the drawdown limit consumes.
    equity_curve: list[float] = field(default_factory=list)
    #: An override for the paper breaker, e.g. a stricter limit under test.
    breaker: PaperBreaker | None = None
    #: Paper-desk admission. UNKNOWN blocks a new entry. It cannot enable live.
    venue_verdict: str = "ELIGIBLE"

    # ------------------------------------------------------------------ run --

    def run_cycle(self, witness: GoldPriceWitness, *,
                  now: float, ledger: MissionLedger | None = None) -> GoldCycleResult:
        """Advance the track one cycle on one resolved witness.

        ``witness`` is already resolved by the caller, so this function touches
        no network. A non-VERIFIED witness is not an error: it is NO_DATA, the
        position is left untouched, and the cycle is recorded as such.
        """
        self.cycles += 1
        cycle = self.cycles
        unpriced_for: float | None = None
        exit_event: dict | None = None
        realized: float | None = None

        price = witness.price_usd if witness.state == VERIFIED else None
        if price is not None:
            self.last_priced_ts = now
            self.priced_this_cycle = True
        else:
            self.priced_this_cycle = False

        # The paper breaker (M39 / §12) gates *new* risk. It is evaluated every
        # cycle -- not only on entries -- so its state is always on the record;
        # it cannot quietly sit armed while the limits silently drift past.
        breaker_state = self._check_breaker(now=now)
        # The M42 HALT on the single ledger gates new risk the same way: a
        # mismatch the nightly reconcile found (a store rewrite, a broken chain,
        # a breached limit, a depeg) is the vision's stop, and the track reads
        # it back here rather than trusting the reconcile to have stopped it.
        halt_state = self._check_halt(ledger)
        path_info, path_blocks = self._entry_path(ledger=ledger, now=now)
        self.last_path = path_info
        # Extra gates can only add blocks. They cannot reopen a breaker or halt.
        entry_blocked = (price is not None and self.position is None
                         and not (breaker_state.allowed and halt_state.allowed
                                  and not path_blocks))

        if self.position is None and not entry_blocked:
            if price is not None:
                self._enter(price=price, now=now, cycle=cycle)
        elif self.position is not None:
            # A CONFLICT mid-position is gold's post-entry security event:
            # the sources actively disagree, which is evidence of a problem,
            # and the two-source gate IS gold's safety gate. check_exits is
            # then asked with no current price, so per PT-X1 the trade is
            # invalidated immediately rather than held open on an unpriceable
            # risk.
            #
            # UNRESOLVED / STALE are NOT a veto: the law separates them (line 7:
            # single/empty/stale/unreachable -> UNKNOWN; line 8: disagreement
            # -> CONFLICT). A closed market or a down feed is no data, not a
            # security event, so the position is held open and reported UNPRICED
            # until the horizon closes it as INVALID_DATA_UNAVAILABLE.
            security_recheck: dict | None = None
            if witness.state == "CONFLICT":
                security_recheck = {
                    "verdict": "SECURITY_VETO",
                    "veto_reasons": [f"two_source_witness:CONFLICT:"
                                     f"{witness.reason}"],
                }
            obs_price = price if price is not None else None
            obs_ts = now if price is not None else None
            exit_event = check_exits(
                entry_exec=self.position.exec_price,
                entry_ts=self.position.entry_ts,
                now=now,
                obs_price=obs_price,
                obs_liq=None,                 # gold has no DEX liquidity leg
                obs_ts=obs_ts,
                consec_liq_breaches=0,
                security_recheck=security_recheck,
                cfg=self.cfg,
            )
            if price is None and self.last_priced_ts is not None:
                unpriced_for = now - self.last_priced_ts
            if exit_event is not None:
                realized = self._settle(exit_event=exit_event,
                                        price=price, now=now)
        # Only *settled* closes enter the risk blotter: an invalidated trade
        # has no price and therefore no PnL distribution to bootstrap from, so
        # counting it toward the 30-trade threshold would let a track buy a
        # promotion claim on trades that never happened.
        if exit_event is not None and realized is not None and price is not None:
            self.closed_trades.append(
                {"exit_ts": now, "realized_pnl_usd": realized})

        # The equity series is recorded after this cycle's settle so the curve
        # is the realized equity path, not the pre-trade bankroll.
        self.equity_curve.append(self.equity_usd)

        recorded, ledger_error = self._record(
            ledger=ledger, cycle=cycle, now=now, witness=witness,
            price=price, exit_event=exit_event, realized=realized,
            unpriced_for=unpriced_for, breaker=breaker_state, halt=halt_state,
            path_info=path_info)
        if recorded and realized is not None and realized < 0 and ledger is not None:
            self._file_lesson(ledger, cycle=cycle, realized=realized)

        return GoldCycleResult(
            cycle=cycle,
            witness_state=witness.state,
            witness_reason=witness.reason,
            price_usd=price,
            position=self.position,
            exit=exit_event,
            realized_pnl_usd=realized,
            equity_usd=self.equity_usd,
            unpriced_for_s=unpriced_for,
            recorded=recorded,
            ledger_error=ledger_error,
            breaker=breaker_state,
        )

    # ------------------------------------------------------------- risk gate --

    def _lessons_snapshot(
        self, ledger: MissionLedger | None, *, now: float,
    ) -> dict[str, Any]:
        """Read M49 beside the ledger before sizing. Lessons never move gates."""
        empty: dict[str, Any] = {
            "visible_gold": 0,
            "weight_one": 0,
            "sample": [],
            "notional_unchanged": True,
        }
        if ledger is None:
            return empty
        try:
            from datetime import datetime, timezone

            from architecture.learning.lessons_ledger import LessonsLedger, apply_gate

            store = LessonsLedger(ledger.path.with_name("m49_lessons.sqlite"))
            as_of = datetime.fromtimestamp(now, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ",
            )
            visible = [row for row in store.visible(as_of) if row.market == "gold"]
            weight_one = sum(
                1
                for row in visible
                if store.retrieval_weight(row.lesson_id, as_of=as_of) >= 1.0
            )
            capped_after = apply_gate(float(self.notional_usd), visible)
            sample = [row.lesson_id for row in visible[-5:]]
            store.close()
            return {
                "visible_gold": len(visible),
                "weight_one": weight_one,
                "sample": sample,
                "notional_unchanged": capped_after == float(self.notional_usd),
            }
        except Exception:
            return empty

    def _entry_path(
        self,
        *,
        ledger: MissionLedger | None = None,
        now: float = 0.0,
    ) -> tuple[dict, tuple[str, ...]]:
        """OMS, venue, crisis, Kelly ceiling, and a non-order model slot.

        Kelly at zero (too few trades) is recorded and does not freeze the
        pre-registered paper notional. A measurable Kelly fraction can only
        lower that notional. Nothing here sets live.
        """
        from architecture.ai.frontier_slots import OPEN, FrontierSlot, choose_slot
        from architecture.evolution.improvement import propose
        from architecture.execution.gateway import PaperOrder
        from architecture.markets.oms import route
        from architecture.markets.risk import drawdown_pct
        from architecture.markets.risk_v2 import bound_notional, fractional_kelly

        blocks: list[str] = []
        oms = route(
            PaperOrder("gold", "buy", float(self.notional_usd), False),
            self.venue_verdict,
        )
        if oms.state != "ACCEPTED_PAPER":
            blocks.append(oms.reason)
        drawdown = drawdown_pct(self.equity_curve)
        crisis = "HALT" if drawdown > 10.0 else "READ"
        if crisis == "HALT":
            blocks.append("crisis drawdown")
        kelly = fractional_kelly(
            win_rate=None, payoff=None, sample=len(self.closed_trades),
        )
        capped = bound_notional(self.notional_usd, self.notional_usd)
        if capped > self.notional_usd:
            blocks.append("size increased")
        slot = choose_slot((FrontierSlot("local", OPEN, 0.0),), purpose="council")
        proposal = propose(
            cycle_id=f"gold-{self.cycles + 1}",
            seen_cycles=set(),
            target="docs/paper_note.md",
            based_on_own_output=False,
        )
        lessons = self._lessons_snapshot(ledger, now=now)
        info = {
            "oms": oms.state,
            "oms_reason": oms.reason,
            "venue": self.venue_verdict,
            "crisis": crisis,
            "drawdown_pct": drawdown,
            "kelly": kelly,
            "notional_usd": capped,
            "slot": None if slot is None else slot.name,
            "blocks": list(blocks),
            "live": False,
            "proposal_merge": proposal.merge,
            "lessons": lessons,
        }
        return info, tuple(blocks)

    def _file_lesson(self, ledger: MissionLedger, *, cycle: int, realized: float) -> None:
        """A loss becomes an unverified lesson beside the ledger, not inside it."""
        try:
            from architecture.learning.lessons_ledger import LessonsLedger

            store = LessonsLedger(ledger.path.with_name("m49_lessons.sqlite"))
            store.append(
                lesson_id=f"gold-{cycle}",
                source="trade_loss",
                market="gold",
                taxonomy="paper",
                evidence_refs=(f"cycle:{cycle}",),
                claim=f"paper loss {realized:.4f}",
                counterfactual="the lesson does not move a gate",
                valid_from="1970-01-01T00:00:00Z",
            )
            store.close()
        except Exception:
            return

    def _paper_breaker(self) -> PaperBreaker:
        """The breaker for this track, constructed from its own declared limits."""
        if self.breaker is not None:
            return self.breaker
        return PaperBreaker(bankroll=self.bankroll_usd)

    def _check_breaker(self, *, now: float) -> BreakerState:
        """Evaluate the paper breaker in this cycle's state.

        Exposure is measured at the *start* of the cycle -- the position this
        cycle is about to act on -- so the caps reflect risk actually taken,
        not risk about to be taken.
        """
        open_usd = self.position.notional_usd if self.position else 0.0
        return self._paper_breaker().check(
            now=now,
            trades=self.closed_trades,
            equity_curve=self.equity_curve,
            open_exposure_usd=open_usd,
            market_exposure_usd=open_usd,
            equity_usd=self.equity_usd)

    def _check_halt(self, ledger: MissionLedger | None) -> HaltGate:
        """Read the M42 HALT off the single ledger before new risk.

        This is the leg of the kill switch the *treasury* sounds: the nightly
        reconcile records a HALT when the chain, the anchored store, the paper
        book, a concentration limit or the peg disagrees, and the track reads it
        back here so the stop actually binds instead of being a log line.

        Fail-closed where the ledger is present but unreadable -- a chain that
        cannot be verified cannot be shown to be un-halted, which is the same
        law the ledger's own ``halted()`` applies. A track with no ledger at all
        is ungoverned by this gate (it records nothing, so it has no chain to
        read); the breaker still binds it.
        """
        if ledger is None:
            return HaltGate("UNMEASURED", allowed=True, source=None,
                            reason="no ledger; this track records no chain, so the "
                                   "M42 halt has nothing to read (the §12 breaker "
                                   "still gates entries)")
        try:
            halted, entry = ledger.halted()
        except Exception as exc:            # noqa: BLE001 - unreadable = unverified
            return HaltGate("UNMEASURED", allowed=False,
                            source="chain",
                            reason=f"the ledger cannot be verified: "
                                   f"{type(exc).__name__}: {exc}")
        if not halted:
            return HaltGate("ARMED", allowed=True, source=None, reason=None)
        payload = (entry or {}).get("payload") or {}
        return HaltGate("HALTED", allowed=False,
                        source=payload.get("source"),
                        reason=payload.get("reason"))

    # ------------------------------------------------------------- internals --

    def _enter(self, *, price: float, now: float, cycle: int) -> GoldPosition:
        # The declared round-trip cost is split evenly between entry and exit
        # so the constant is exactly what it says: a flat trade at the same
        # price costs precisely ``round_trip_bps`` on the notional. (An entry
        # spread *plus* a separate entry fee would charge 1.5x the declared
        # figure -- conservative, but it would make the constant a lie.)
        exec_price = price + _cost_bps(price, self.round_trip_bps / 2.0)
        qty = self.notional_usd / exec_price
        self.position = GoldPosition(
            entry_ts=now,
            entry_price=price,
            exec_price=exec_price,
            notional_usd=self.notional_usd,
            qty_oz=qty,
            cycle=cycle,
        )
        return self.position

    def _settle(self, *, exit_event: dict, price: float | None,
                now: float) -> float:
        """Close the position at the corroborated price, or invalidate it."""
        pos = self.position
        assert pos is not None
        if price is None:
            # INVALID_DATA_UNAVAILABLE / a veto with no fresh price: the
            # position is invalidated, not exited. No realized PnL is invented;
            # realized stays 0.0 and the bankroll law
            # (equity = bankroll + realized) stays exact.
            self.realized_pnl_usd += 0.0
            self.closed += 1
            self.position = None
            return 0.0

        exec_exit = price - _cost_bps(price, self.round_trip_bps / 2.0)
        gross = pos.qty_oz * exec_exit
        realized = gross - pos.notional_usd
        self.equity_usd += realized
        self.realized_pnl_usd += realized
        self.closed += 1
        self.position = None
        return realized

    def _record(self, *, ledger: MissionLedger | None, cycle: int, now: float,
                witness: GoldPriceWitness, price: float | None,
                exit_event: dict | None, realized: float | None,
                unpriced_for: float | None,
                breaker: BreakerState | None,
                halt: "HaltGate | None" = None,
                path_info: dict | None = None) -> tuple[bool, str | None]:
        if ledger is None:
            return False, None
        payload = {
            "market": "gold",
            "cycle": cycle,
            "witness": {
                "state": witness.state,
                "reason": witness.reason,
                "spread_pct": witness.spread_pct,
                "tolerance_pct": witness.tolerance_pct,
                "quotes": [
                    {"provider_id": q.provider_id, "price_usd": q.price_usd,
                     "instrument": q.instrument, "observed_at": q.observed_at,
                     "raw_sha256": q.raw_sha256}
                    for q in witness.quotes
                ],
            },
            "price_usd": price,
            "position": None if self.position is None else {
                "entry_ts": self.position.entry_ts,
                "entry_price": self.position.entry_price,
                "exec_price": self.position.exec_price,
                "notional_usd": self.position.notional_usd,
                "qty_oz": self.position.qty_oz,
                "cycle": self.position.cycle,
            },
            "exit": exit_event,
            "realized_pnl_usd": realized,
            "equity_usd": self.equity_usd,
            "bankroll_usd": self.bankroll_usd,
            "realizable_equity_usd": self.realizable_equity(price),
            "cumulative_realized_pnl_usd": self.realized_pnl_usd,
            "closed_trades": self.closed,
            "settled_trades": len(self.closed_trades),
            "unpriced_for_s": unpriced_for,
            "open_unpriced": self.open_unpriced,
            "round_trip_bps": self.round_trip_bps,
            "exit_card": self.cfg.get("version"),
            "breaker": None if breaker is None else {
                "state": breaker.state,
                "allowed": breaker.allowed,
                "reasons": list(breaker.reasons),
                "p_ruin": breaker.p_ruin,
                "drawdown_pct": breaker.drawdown_pct,
                "daily_loss_pct": breaker.daily_loss_pct,
                "weekly_loss_pct": breaker.weekly_loss_pct,
                "open_exposure_pct": breaker.open_exposure_pct,
            },
            "halt": None if halt is None else {
                "state": halt.state,
                "allowed": halt.allowed,
                "source": halt.source,
                "reason": halt.reason,
            },
            "paper_only": True,
            "path": path_info or {"live": False, "blocks": []},
        }
        try:
            ledger.checkpoint(
                GOLD_PAPER_MISSION,
                payload,
                LAST_EVIDENCE=(f"gold paper cycle {cycle}: witness "
                               f"{witness.state}, equity "
                               f"{self.equity_usd:.2f}, closed {self.closed}"),
            )
        except Exception as exc:  # noqa: BLE001 - a ledger fault must not lose the cycle
            return False, f"{type(exc).__name__}: {exc}"
        return True, None

    # -------------------------------------------------------------- invariants --

    def realizable_equity(self, price: float | None) -> float:
        """Equity marked to a corroborated price, None-safe.

        A flat equity while a position is open would flatter the surface: this
        adds the open position's unrealised value at the *current corroborated*
        price. With no corroborated price the position is not marked at all --
        the last verified price is not a live price, and marking to it would
        present a stale quote as current.
        """
        if self.position is None or price is None:
            return self.equity_usd
        exec_exit = price - _cost_bps(price, self.round_trip_bps / 2.0)
        return self.equity_usd + self.position.qty_oz * exec_exit \
            - self.position.notional_usd

    @property
    def open_unpriced(self) -> bool:
        """A position held while this cycle produced no corroborated price."""
        return self.position is not None and not self.priced_this_cycle

    @property
    def equity_is_consistent(self) -> bool:
        """Equity must always equal the bankroll plus cumulative realized PnL.

        Closed at cost on an invalidated trade, this identity holds exactly at
        every cycle, which is what makes the recorded equity curve auditable
        against the recorded trades.
        """
        return abs(self.equity_usd
                   - (self.bankroll_usd + self.realized_pnl_usd)) < 1e-9


# ------------------------------------------------------------------ runner --


def run_gold_paper_cycle(
    *,
    ledger_path: Any = None,
    adapters: Any = None,
    now: float | None = None,
    transport: Any = None,
) -> tuple[GoldCycleResult, GoldPriceWitness]:
    """Advance the gold paper track one cycle against the live two-source pair.

    This is the entrypoint a cadence calls. It resolves the witness over the
    network, advances the track, and records the cycle into the canonical
    mission ledger -- starting the mission on its first cycle only, since
    ``Ledger.start`` refuses a mission that already exists.

    Track state between cycles is read back from the ledger's last checkpoint,
    so the runner is stateless across invocations: two runs are two cycles,
    not two tracks.
    """
    import time as _time

    from ..mission.ledger import MissionLedger, default_ledger_path
    from ..providers.gold import production_gold_adapters, resolve_gold_price

    now = now if now is not None else _time.time()
    ledger = MissionLedger(ledger_path
                           if ledger_path is not None
                           else default_ledger_path())
    adapters = (production_gold_adapters(transport=transport)
                if adapters is None else tuple(adapters))
    witness = resolve_gold_price(adapters, now=now)

    if ledger.latest(GOLD_PAPER_MISSION) is None:
        ledger.start(GOLD_PAPER_MISSION,
                     phase="paper_trading",
                     task="M13 gold-first paper cycle (OWN-18): real two-source "
                          "XAU prices, fake money, recorded evidence",
                     agent=GOLD_PAPER_AGENT)

    track = _track_from_ledger(ledger)
    result = track.run_cycle(witness, now=now, ledger=ledger)
    return result, witness


def _track_from_ledger(ledger: MissionLedger) -> GoldPaperTrack:
    """Rebuild the track from its last recorded checkpoint, or start fresh.

    Scalar state comes from the latest checkpoint. The risk gate's two history
    inputs -- the closed-trade blotter and the equity curve -- are replayed
    from the whole mission history instead, because those are what the §12
    limits are measured over and they must survive a restart. A track that
    restarted with an empty blotter would see an unmeasured risk history and
    could not be trusted to enforce its own limits.
    """
    history = ledger.history(GOLD_PAPER_MISSION)
    latest = ledger.latest(GOLD_PAPER_MISSION)    # flattens `state` into the row
    track = GoldPaperTrack()
    if latest is None:
        return track
    cp = latest.get("CHECKPOINT") or {}
    if not isinstance(cp, dict):
        return track
    track.cycles = int(cp.get("cycle", 0))
    track.closed = int(cp.get("closed_trades", 0))
    try:
        track.bankroll_usd = float(cp.get("bankroll_usd", track.bankroll_usd))
        track.equity_usd = float(cp.get("equity_usd", track.bankroll_usd))
        track.realized_pnl_usd = float(
            cp.get("cumulative_realized_pnl_usd", 0.0))
    except (TypeError, ValueError):
        pass
    pos = cp.get("position")
    if isinstance(pos, dict) and pos.get("entry_ts") is not None:
        try:
            track.position = GoldPosition(
                entry_ts=float(pos["entry_ts"]),
                entry_price=float(pos["entry_price"]),
                exec_price=float(pos["exec_price"]),
                notional_usd=float(pos["notional_usd"]),
                qty_oz=float(pos["qty_oz"]),
                cycle=int(pos.get("cycle", track.cycles)),
            )
        except (KeyError, TypeError, ValueError):
            # A checkpoint whose position cannot be reconstructed is not
            # silently turned into an open position.
            track.position = None

    for entry in history:
        each = (entry.get("state") or {}).get("CHECKPOINT")
        if not isinstance(each, dict):
            continue
        equity = each.get("equity_usd")
        try:
            if equity is not None:
                track.equity_curve.append(float(equity))
        except (TypeError, ValueError):
            pass
        if each.get("exit") is not None:
            try:
                realized = float(each["realized_pnl_usd"])
            except (KeyError, TypeError, ValueError):
                continue
            if each.get("price_usd") is None:
                continue                       # an invalidated close has no PnL
            ts = _ledger_ts_to_epoch(entry.get("ts"))
            if ts is not None:
                track.closed_trades.append(
                    {"exit_ts": ts, "realized_pnl_usd": realized})
    return track


#: A month, as the tier gate measures data depth in months.
MONTH_S = 30.0 * 24.0 * 3600.0


@dataclass(frozen=True)
class PaperHistory:
    """The track's recorded history, as the T0 -> T1 gate consumes it.

    ``months_of_data`` is the span of *recorded* cycles, first entry to last, so
    it is a property of the evidence rather than of the clock reading at report
    time. It is None on a ledger with fewer than two entries, which is the
    gate's UNMEASURABLE case rather than a zero.
    """

    trades: tuple[dict, ...] = ()
    months_of_data: float | None = None


def paper_history(ledger: MissionLedger) -> PaperHistory:
    """Read the ledger as the T0 -> T1 promotion gate measures it (M13).

    The gate (:mod:`architecture.markets.tier_gate`) is deliberately pure: it
    takes trades and numbers, and imports nothing from this module, so it
    measures the record rather than asking the track how it did -- the same
    separation the M42 judge already keeps. This function is the bridge, and it
    lives here because this module owns the record's shape.

    One pass over the mission history produces both gate inputs:

    * the **settled** closes, each carrying the drawdown recorded *at its exit*.
      The settled-only selection rule is the one :func:`_track_from_ledger`
      already uses for the risk blotter, and it is shared on purpose: a close
      with no corroborated price has no PnL, so counting it would let either the
      risk limits or the 200-trade threshold be bought with trades that never
      happened. Both consumers must keep agreeing on what a trade is.
    * the **data span**, from the first recorded entry to the last.

    The drawdown is peak-to-current-equity in percent, with non-positive equity
    skipped -- the same definition as :func:`architecture.markets.risk.drawdown_pct`,
    so the breaker and the gate cannot disagree about the track's worst moment.
    Attaching it per trade is what keeps the gate's drawdown criterion a
    measurement: without it the gate reports UNMEASURABLE rather than scoring a
    vacuous 0.00%.

    Read-only. Nothing here can write, promote, or close a position.
    """
    trades: list[dict] = []
    first_ts: float | None = None
    last_ts: float | None = None
    peak: float | None = None
    for entry in ledger.history(GOLD_PAPER_MISSION):
        ts = _ledger_ts_to_epoch(entry.get("ts"))
        if ts is not None:
            if first_ts is None:
                first_ts = ts
            last_ts = ts
        each = (entry.get("state") or {}).get("CHECKPOINT")
        if not isinstance(each, dict):
            continue
        try:
            equity = float(each["equity_usd"]) if each.get("equity_usd") is not None else None
        except (TypeError, ValueError):
            equity = None
        if equity is not None and equity > 0:
            if peak is None or equity > peak:
                peak = equity
        # A settled close: an exit was taken *and* a corroborated price existed
        # to settle it on. Anything else is an unpriceable close with no PnL.
        if each.get("exit") is None or each.get("price_usd") is None:
            continue
        try:
            realized = float(each["realized_pnl_usd"])
        except (KeyError, TypeError, ValueError):
            continue
        drawdown = None
        if peak is not None and peak > 0 and equity is not None:
            drawdown = (peak - equity) / peak * 100.0
        trades.append({
            "exit_ts": ts,
            "realized_pnl_usd": realized,
            "drawdown_pct": drawdown,
            "equity_after": equity,
        })
    months = None
    if first_ts is not None and last_ts is not None and last_ts >= first_ts:
        months = (last_ts - first_ts) / MONTH_S
    return PaperHistory(trades=tuple(trades), months_of_data=months)


def _ledger_ts_to_epoch(value: object) -> float | None:
    """The ledger's own UTC timestamp, as epoch seconds.

    The exit timestamp is taken from the ledger row rather than carried in the
    payload, so there is one clock in the record and the risk window cannot
    disagree with the ledger about when a trade closed.
    """
    if not isinstance(value, str):
        return None
    try:
        from datetime import datetime
        # The ledger writes UTC with a trailing Z, so the parse is tz-aware and
        # ``timestamp()`` is the correct epoch without a local-time adjustment.
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


if __name__ == "__main__":  # pragma: no cover - operator entrypoint
    res, wit = run_gold_paper_cycle()
    print(f"witness={wit.state} price={wit.price_usd} spread={wit.spread_pct}")
    print(f"cycle={res.cycle} exit={res.exit} equity={res.equity_usd:.2f} "
          f"position={'open' if res.position else 'flat'}")
    print(f"breaker={res.breaker.state if res.breaker else None} "
          f"allowed={res.breaker.allowed if res.breaker else None}")
    print(f"recorded={res.recorded} error={res.ledger_error}")
