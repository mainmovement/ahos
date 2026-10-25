#!/usr/bin/env python3
"""M42 — the nightly reconcile over the single hash-chained ledger.

Vision M42 (:1269): *"ledger زنجیرهٔ hash + تطبیق شبانه: extend
``architecture/mission/ledger.py`` and ``paper_trading/ledger.py`` (one
ledger); reconcile with the counterparty — a mismatch is a HALT."* Vision §7.0
adds the two checks that make the reconcile a treasury control rather than a
report: each broker ≤ 40%, and a USDT depeg beyond 0.5%.

What "reconcile" means here, in the order the driver runs it:

1. **The chain** — ``MissionLedger.verify()``. A tamper breaks it, and the
   verdict becomes ``BROKEN_CHAIN`` rather than a discrepancy, because a
   rewritten ledger is not evidence at all.
2. **The store** — ``architecture/markets/paper_anchor.py`` re-witnesses the
   frozen paper store against the last anchor recorded for it. The store is
   Lane A and cannot carry a chain column; the anchor is what makes it a
   branch of the one chain. The first run *takes* the anchor (binding the
   store is not a discrepancy); later runs check it.
3. **The paper book** — ``architecture/markets/judge.py`` replays the paper
   track from the bytes and checks the track's own claims against its
   re-derivation. This is the paper leg of the reconcile, and it is delegated
   rather than reimplemented: M13 built that judge as the M42 reconcile, and a
   second replay would be a second implementation of a concept that already
   has a home.
4. **The counterparty** — the broker's own statement is checked on its own
   arithmetic (each fill's PnL re-derives from its exec prices and costs) and
   on the concentration limit (no broker > 40%). A real broker adapter
   implements ``CounterpartyStatement``; until the owner declares brokers
   (§11.0.3) there is no counterparty, and the leg reports the gap instead of
   inventing a statement.
5. **The peg** — ``architecture/treasury/surveillance.py`` two-source USDT
   depeg check.

**A mismatch is a HALT, and the HALT is on the chain.** The ledger's own
``halt()`` records it, so a stop cannot be quietly dropped, and only
``clear_halt()`` — an entry naming the halt's own hash, with a written reason —
lifts it. The reconcile never lifts its own halt: the evidence that something
did not agree is exactly what the owner needs to see before releasing it.

**Unmeasured is not clean.** A leg that was requested and came back unable to
measure its limit makes the verdict ``UNKNOWN``, never ``CLEAN`` — the
reconcile reports an honest gap rather than a green light. But only a
*measured breach* sounds the HALT: an unmeasured limit is not a satisfied
limit, and it is not an emergency either.

PAPER_ONLY. Nothing here touches funds, keys or a broker API, and the reconcile
has no position to flatten — it reports, and the callers that read
``halted()`` are what stops new risk from being taken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence

from ..markets.judge import BROKEN_CHAIN, CLEAN, DISCREPANCY, JudgeReport, judge_paper_ledger
from ..markets.paper_anchor import (ANCHORED_MISMATCH, PAPER_STORE_ID, UNANCHORED,
                                    AnchorVerdict, anchor_paper_store, verify_paper_anchor)
from ..mission.ledger import KIND_RECONCILE, LedgerTamperError, MissionLedger
from .surveillance import (BREACH, DEPEG, UNMEASURED, ConcentrationVerdict, DepegVerdict,
                           StableQuote, concentration_check, depeg_check)

#: A verdict the driver adds when a prior, unreleased HALT governs the run.
HALTED = "HALTED"

#: A verdict for a reconcile that could not measure every leg it was asked to.
#: Deliberately neither CLEAN nor DISCREPANCY: an unmeasured limit is not a
#: satisfied limit and not a breach.
UNKNOWN = "UNKNOWN"

_TOL_REL = 1e-9


@dataclass(frozen=True)
class Finding:
    """One reconcile finding. ``code`` is stable so a caller can gate on it."""

    code: str
    detail: str


#: Finding codes that report a leg which could not measure its limit. These are
#: honest gaps, not breaches: they cannot leave the verdict CLEAN (the limit was
#: not certified) and they must not become a DISCREPANCY (nothing disagreed).
#:
#: The unmeasured codes are deliberately distinct from their measured
#: counterparts: a watchdog that pages on ``R-DEPEG`` pages on a peg that
#: *broke*, not on a feed that was unreachable. ``R-COUNTERPARTY`` covers the
#: statement that carried neither fills nor exposure.
UNMEASURED_CODES = frozenset({"R-COUNTERPARTY", "R-CONCENTRATION-UNMEASURED",
                              "R-DEPEG-UNMEASURED"})


@dataclass(frozen=True)
class ReconcileReport:
    """The nightly verdict over every leg."""

    verdict: str
    entries: int = 0
    anchor: AnchorVerdict | None = None
    paper: JudgeReport | None = None
    concentration: ConcentrationVerdict | None = None
    depeg: DepegVerdict | None = None
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    head_hash: str | None = None
    recorded: bool = False
    halt_recorded: bool = False

    @property
    def clean(self) -> bool:
        return self.verdict == CLEAN


# ------------------------------------------------------- the counterparty ----

class CounterpartyStatement(Protocol):
    """The counterparty's own view of the book it holds for us.

    A real broker adapter (vision M38/M41) implements this. The statement is
    the *counterparty's* claim; the reconcile checks it against itself and
    against the limits, then against the ledger — it never trusts it.
    """

    def statement(self) -> dict[str, Any]:
        """``{counterparty, as_of, trades: [StatementTrade...], exposures,
        equity_usd}`` where ``exposures`` is ``{broker_id: usd}``."""
        ...


@dataclass(frozen=True)
class StatementTrade:
    """One fill the counterparty says it executed for us."""

    external_ref: str               # the id the counterparty and we share
    qty: float
    entry_price_exec: float
    exit_price_exec: float | None
    notional_usd: float
    fee_total_usd: float
    net_pnl_usd: float | None = None
    broker_id: str | None = None


def _close(a: float, b: float) -> bool:
    scale = max(1.0, abs(a), abs(b))
    return abs(a - b) <= _TOL_REL * scale


def check_statement(trades: Sequence[StatementTrade] | None,
                    *, exposures: dict[str, float] | None = None,
                    limit_share: float | None = None
                    ) -> tuple[list[Finding], ConcentrationVerdict | None]:
    """The counterparty's arithmetic and its concentration, checked on its own.

    A broker's PnL is ``qty * (exit - entry) - costs`` — the counterparty's own
    identity, from exec prices, not from our model. A fill that does not
    re-derive is a discrepancy even before it is compared with our book,
    because the statement is then not internally consistent.
    """
    findings: list[Finding] = []
    kwargs = {"limit_share": limit_share} if limit_share is not None else {}
    if not trades:
        conc = concentration_check(exposures or None, **kwargs)
        if conc.state == UNMEASURED:
            findings.append(Finding("R-COUNTERPARTY",
                                    "the counterparty statement carries no fills "
                                    "and no exposure; the leg is unmeasured (no "
                                    "broker is declared — owner gate §11.0.3, "
                                    "M41 owns the key self-check)"))
        else:
            # A book with no fills can still breach the limit, and a breach that
            # raises no finding would leave the report's own "no discrepancy"
            # line contradicting a DISCREPANCY verdict.
            code = ("R-CONCENTRATION" if conc.state != UNMEASURED
                    else "R-CONCENTRATION-UNMEASURED")
            for f in conc.findings:
                findings.append(Finding(code, f))
        return findings, conc
    for t in trades:
        if t.exit_price_exec is None:
            continue                        # an open fill has no PnL to check
        expected = t.qty * (t.exit_price_exec - t.entry_price_exec) - t.fee_total_usd
        if t.net_pnl_usd is None or not _close(t.net_pnl_usd, expected):
            findings.append(Finding(
                "R-ARITHMETIC",
                f"fill {t.external_ref}: the statement's net PnL {t.net_pnl_usd} does "
                f"not equal qty {t.qty} x (exit {t.exit_price_exec} - entry "
                f"{t.entry_price_exec}) - costs {t.fee_total_usd} = {expected}"))
    per_broker: dict[str, float] = {}
    for t in trades:
        if t.broker_id is None:
            continue
        per_broker[t.broker_id] = per_broker.get(t.broker_id, 0.0) + t.notional_usd
    if exposures:
        for k, v in exposures.items():
            per_broker[k] = max(per_broker.get(k, 0.0), float(v))
    conc = concentration_check(per_broker or None, **kwargs)
    code = ("R-CONCENTRATION" if conc.state != UNMEASURED
            else "R-CONCENTRATION-UNMEASURED")
    for f in conc.findings:
        findings.append(Finding(code, f))
    return findings, conc


# -------------------------------------------------------------- the driver ----

def run_reconcile(
    ledger: MissionLedger,
    *,
    mission_id: str | None = None,
    statement: CounterpartyStatement | dict[str, Any] | None = None,
    depeg_quotes: Sequence[StableQuote] | None = None,
    bankroll_usd: float | None = None,
    limit_share: float | None = None,
    agent: str | None = None,
    record: bool = True,
) -> ReconcileReport:
    """Run every leg and record the verdict on the single ledger.

    A measured breach on any leg records a HALT the ledger's own ``halted()``
    reports. ``record=False`` is the dry-run path used by tests and by an
    operator who wants the verdict without writing it; nothing is written then.
    """
    findings: list[Finding] = []
    notes: list[str] = []
    anchor: AnchorVerdict | None = None
    paper: JudgeReport | None = None
    conc: ConcentrationVerdict | None = None
    depeg: DepegVerdict | None = None
    halt_sources: list[str] = []
    chain_head: str | None = None
    n_entries = 0

    # 0. An existing HALT governs: the reconcile reports it, it does not clear it.
    try:
        already_halted, halt_entry = ledger.halted()
    except LedgerTamperError as exc:
        return ReconcileReport(BROKEN_CHAIN,
                               findings=(Finding("R-CHAIN", str(exc)),))
    if already_halted:
        src = (halt_entry or {}).get("payload", {}).get("source", "halt")
        findings.append(Finding(
            "R-HALTED",
            f"a HALT is on record from {src} and was not released; this reconcile "
            "reports it and does not clear it (clear_halt() is an owner act)"))

    # 1. The chain. A break is the verdict, not a discrepancy: a rewritten
    #    ledger is not evidence at all.
    try:
        chain = ledger.verify()
        chain_head = chain["head_hash"]
        n_entries = chain["entries"]
        chain_ok = True
    except LedgerTamperError as exc:
        findings.append(Finding("R-CHAIN", str(exc)))
        halt_sources.append("m42:chain")
        chain_ok = False

    # 2. The frozen paper store, bound to the chain. The first run binds it; an
    #    unbound store is a binding, not tamper, so it is a note, not a finding.
    try:
        anchor = verify_paper_anchor(ledger)
        if anchor.state == UNANCHORED:
            if record:
                # Binding the store is a write, so a dry run leaves it unbound
                # and says so rather than half-binding the chain.
                binding = anchor_paper_store(ledger, agent=agent)
                # Re-witness, so the report's anchor leg stays an AnchorVerdict
                # (ANCHORED_CLEAN now) rather than the bare fingerprint the
                # binding returns -- the report renders an AnchorVerdict, and a
                # verdict that cannot be rendered cannot be recorded either.
                anchor = verify_paper_anchor(ledger)
                notes.append(
                    f"{PAPER_STORE_ID} had no anchor on record; the store is now "
                    f"bound to the chain at root {binding.root_hash[:16]}... over "
                    f"{sum(binding.tables.values())} rows in {len(binding.tables)} "
                    "tables. This is the binding, not a discrepancy.")
            else:
                notes.append(
                    f"{PAPER_STORE_ID} has no anchor on record; a live run binds it "
                    "to the chain (a dry run writes nothing). Unbound is "
                    "unmeasured, not tamper")
        elif anchor.state == ANCHORED_MISMATCH:
            halt_sources.append(f"m42:anchor:{PAPER_STORE_ID}")
            for f in anchor.findings:
                findings.append(Finding("R-ANCHOR", f))
        elif anchor.extensions:
            notes.append(f"{PAPER_STORE_ID} grew since the last anchor "
                         f"({', '.join(anchor.extensions)}); growth is not tamper "
                         "and the next anchor covers it")
    except Exception as exc:                        # noqa: BLE001 - reported, never fatal
        findings.append(Finding("R-ANCHOR",
                                f"the paper store could not be witnessed: "
                                f"{type(exc).__name__}: {exc}"))
        halt_sources.append(f"m42:anchor:{PAPER_STORE_ID}")

    # 3. The paper book, delegated to M13's judge, which replays the bytes.
    if mission_id is not None:
        try:
            paper = judge_paper_ledger(ledger, mission_id, bankroll_usd=bankroll_usd)
        except Exception as exc:                    # noqa: BLE001
            findings.append(Finding("R-PAPER",
                                    f"the paper judge failed: "
                                    f"{type(exc).__name__}: {exc}"))
            halt_sources.append(f"m42:paper:{mission_id}")
            paper = None
        else:
            if paper.verdict == BROKEN_CHAIN:
                findings.append(Finding("R-CHAIN", "the paper judge reports a "
                                        f"broken chain: {paper.findings}"))
                halt_sources.append("m42:chain")
            elif paper.verdict == DISCREPANCY:
                for f in paper.findings:
                    findings.append(Finding("R-PAPER", f"{f.code}: {f.detail}"))
                halt_sources.append(f"m42:paper:{mission_id}")

    # 4. The counterparty's own book: its arithmetic and its concentration.
    #    A statement is the one leg that arrives from outside the machine, so a
    #    statement that cannot be read is a broker API anomaly -- which vision
    #    §11.0 lists among the halt triggers alongside a ledger mismatch and a
    #    depeg. It reports and halts rather than raising, so a watchdog sees a
    #    verdict and a recorded stop instead of a traceback.
    if statement is not None:
        try:
            row = statement.statement() if not isinstance(statement, dict) else statement
            trades = [t if isinstance(t, StatementTrade) else StatementTrade(**t)
                      for t in (row.get("trades") or [])]
            stmt_findings, conc = check_statement(
                trades, exposures=row.get("exposures"),
                **({"limit_share": limit_share} if limit_share is not None else {}))
        except Exception as exc:                        # noqa: BLE001 - reported, never fatal
            findings.append(Finding(
                "R-COUNTERPARTY",
                f"the counterparty statement could not be read: "
                f"{type(exc).__name__}: {exc} (a broker API anomaly is a halt "
                "trigger, vision §11.0)"))
            halt_sources.append("m42:counterparty")
        else:
            findings.extend(stmt_findings)
            if any(f.code == "R-ARITHMETIC" for f in stmt_findings):
                halt_sources.append("m42:counterparty")
            if conc is not None and conc.state == BREACH:
                halt_sources.append("m42:concentration")

    # 5. The peg.
    if depeg_quotes is not None:
        depeg = depeg_check(depeg_quotes)
        # An unreachable feed is a gap, not a depeg -- a caller gating on
        # R-DEPEG is gating on a peg that broke.
        code = ("R-DEPEG" if depeg.state != UNMEASURED else "R-DEPEG-UNMEASURED")
        for f in depeg.findings:
            findings.append(Finding(code, f))
        if depeg.state == DEPEG:
            halt_sources.append("m42:depeg:USDT")

    # ---- the verdict, worst first -------------------------------------
    breaches = [f for f in findings if f.code not in UNMEASURED_CODES]
    if not chain_ok:
        verdict = BROKEN_CHAIN
    elif already_halted:
        verdict = HALTED
    elif breaches or halt_sources:
        # A measured breach: the counterparty disagreed, a limit was breached,
        # the store was rewritten or the peg broke. This is the vision's
        # "a mismatch is a HALT".
        verdict = DISCREPANCY
    elif findings or _unmeasured(conc, depeg):
        # A leg that was requested and could not measure its limit. It is not
        # CLEAN — the reconcile did not certify what it could not measure — and
        # it is not a DISCREPANCY, because nothing disagreed.
        verdict = UNKNOWN
    else:
        verdict = CLEAN

    # ---- record -------------------------------------------------------
    recorded = halt_recorded = False
    if record:
        try:
            ledger.record(KIND_RECONCILE, {
                "verdict": verdict,
                "mission_id": mission_id,
                "chain_head": chain_head,
                "entries": n_entries,
                "anchor": _anchor_payload(anchor),
                "paper": _paper_payload(paper),
                "concentration": _concentration_payload(conc),
                "depeg": _depeg_payload(depeg),
                "findings": [{"code": f.code, "detail": f.detail}
                             for f in findings],
                "notes": notes,
                "halt_sources": halt_sources,
                "paper_only": True,
            }, agent=agent)
            recorded = True
        except Exception as exc:                    # noqa: BLE001
            findings.append(Finding("R-RECORD",
                                   f"the verdict could not be recorded: "
                                   f"{type(exc).__name__}: {exc}"))
        for source in halt_sources:
            try:
                ledger.halt(source,
                            reason=f"M42 nightly reconcile breach: {source}",
                            detail="recorded by the M42 reconcile driver; release "
                                   "only with a written reason",
                            agent=agent)
                halt_recorded = True
            except Exception as exc:                # noqa: BLE001
                findings.append(Finding("R-RECORD",
                                       f"the HALT for {source} could not be "
                                       f"recorded: {type(exc).__name__}: {exc}"))

    return ReconcileReport(verdict, entries=n_entries, anchor=anchor, paper=paper,
                           concentration=conc, depeg=depeg,
                           findings=tuple(findings), notes=tuple(notes),
                           head_hash=chain_head, recorded=recorded,
                           halt_recorded=halt_recorded)


def _unmeasured(conc: ConcentrationVerdict | None,
                depeg: DepegVerdict | None) -> bool:
    """Did a requested leg come back unable to measure its limit?"""
    if conc is not None and conc.state == UNMEASURED:
        return True
    return depeg is not None and depeg.state == UNMEASURED


# ------------------------------------------------------- payload shaping -----

def _anchor_payload(a: AnchorVerdict | None) -> dict[str, Any] | None:
    if a is None:
        return None
    fp = a.fingerprint or a.anchored
    return {"state": a.state, "store": a.store,
            "root_hash": fp.root_hash if fp else None,
            "tables": dict(fp.tables) if fp else {},
            "rows": sum(fp.tables.values()) if fp else 0,
            "anchor_hash": a.anchor_hash,
            "findings": list(a.findings), "extensions": list(a.extensions)}


def _paper_payload(p: JudgeReport | None) -> dict[str, Any] | None:
    if p is None:
        return None
    return {"verdict": p.verdict, "entries": p.entries, "cycles": p.cycles,
            "findings": [{"code": f.code, "detail": f.detail} for f in p.findings],
            "summary": p.summary}


def _concentration_payload(c: ConcentrationVerdict | None) -> dict[str, Any] | None:
    if c is None:
        return None
    return {"state": c.state, "limit_share": c.limit_share, "shares": c.shares,
            "total_exposure_usd": c.total_exposure_usd,
            "worst_broker": c.worst_broker, "findings": list(c.findings)}


def _depeg_payload(d: DepegVerdict | None) -> dict[str, Any] | None:
    if d is None:
        return None
    return {"state": d.state, "deviation_pct": d.deviation_pct,
            "mean_price_usd": d.mean_price_usd,
            "quotes": [{"provider_id": q.provider_id, "price_usd": q.price_usd,
                        "observed_at": q.observed_at} for q in d.quotes],
            "findings": list(d.findings)}


# ------------------------------------------------------- written evidence ----

def write_reconcile_report(report: ReconcileReport, path: str | Path) -> Path:
    """Render the reconcile as markdown. A discrepancy is never styled clean."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M42 nightly reconcile",
        "",
        f"**Verdict: {report.verdict}**",
        "",
        f"- ledger entries: {report.entries}",
        f"- chain head: `{report.head_hash}`",
        f"- paper store anchor: {_short_anchor(report.anchor)}",
        f"- paper judge: {_short_paper(report.paper)}",
        f"- broker concentration: {_short_conc(report.concentration)}",
        f"- USDT depeg: {_short_depeg(report.depeg)}",
    ]
    if report.paper is not None and report.paper.summary:
        s = report.paper.summary
        lines += [
            "",
            "## The paper judge's own numbers",
            "",
            f"- cycles replayed: {s.get('cycles', 0)}",
            f"- closed trades: {s.get('closed_trades', 0)} "
            f"({s.get('settled', 0)} settled, {s.get('invalidated', 0)} invalidated)",
            f"- gross realized PnL: {s.get('gross_realized_pnl_usd', 0.0):.2f} (PAPER)",
            f"- equity: {s.get('equity_usd')}",
        ]
    if report.notes:
        lines += ["", "## Notes", ""]
        for note in report.notes:
            lines.append(f"- {note}")
    lines += ["", "## Findings", ""]
    if not report.findings:
        if report.verdict == CLEAN:
            lines.append("No discrepancy. Every measured leg agrees: the chain is "
                         "intact, the anchored store is unchanged, the paper book "
                         "re-derives from the recorded bytes, no broker exceeds the "
                         "concentration limit, and the peg is within the threshold.")
        else:
            # A non-CLEAN verdict with no finding is a gap, not a pass: the legs
            # that could not measure themselves are what the verdict rests on.
            lines.append(f"No measured leg disagreed, and the verdict is still "
                         f"{report.verdict}: a leg the reconcile asked for could "
                         "not certify its limit, so it is reported rather than "
                         "counted as clean. See the per-leg lines above.")
    else:
        for f in report.findings:
            lines.append(f"- **{f.code}** — {f.detail}")
    lines += [
        "",
        "PAPER_ONLY. This reconcile reports and records; it promotes nothing, "
        "and a HALT it records is released only by an entry naming the halt's "
        "own hash (`MissionLedger.clear_halt`) with a written reason.",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _short_anchor(a: AnchorVerdict | None) -> str:
    if a is None:
        return "not evaluated"
    fp = a.fingerprint or a.anchored
    rows = sum(fp.tables.values()) if fp else 0
    return f"{a.state} ({rows} anchored rows)"


def _short_paper(p: JudgeReport | None) -> str:
    if p is None:
        return "not evaluated"
    return f"{p.verdict} over {p.cycles} cycles, {len(p.findings)} finding(s)"


def _short_conc(c: ConcentrationVerdict | None) -> str:
    if c is None:
        return "not evaluated"
    return f"{c.state} (worst broker {c.worst_broker})"


def _short_depeg(d: DepegVerdict | None) -> str:
    if d is None:
        return "not evaluated"
    dev = f"{d.deviation_pct:.4f}%" if d.deviation_pct is not None else "—"
    return f"{d.state}, deviation {dev} from $1"


CASH_TOL_USD = 0.01
_MATCH_FIELDS = ("event", "symbol", "side")


def paper_cash_double_entry(root: Path) -> dict[str, Any]:
    """Compare paper OPEN/CLOSE cash with the one mission ledger. This does not record or halt.

    A close's cash is ``realized_pnl_usd``. The discrepancy is the jsonl sum minus the linked
    ledger sum. Unlinked rows stay in the report and keep the verdict off MEASURED_ZERO.
    """
    import json
    from datetime import datetime, timezone

    from architecture.mission.ledger import LedgerTamperError, MissionLedger

    root = Path(root)
    trades_path = root / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    ledger_path = root / "data" / "mission_ledger" / "mission_ledger.jsonl"
    rows: list[dict[str, Any]] = []
    if trades_path.is_file():
        for line in trades_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("event") in ("OPEN", "CLOSE"):
                rows.append(row)
    chain_verdict = "MISSING"
    fills: dict[str, dict[str, Any]] = {}
    if ledger_path.is_file():
        led = MissionLedger(ledger_path)
        try:
            chain = led.verify()
            chain_verdict = str(chain.get("verdict") or "CHAIN_INTACT")
        except LedgerTamperError as exc:
            chain_verdict = f"TAMPERED:{type(exc).__name__}"
        else:
            for entry in led.entries():
                payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
                if entry.get("kind") == "DECISION" and payload.get("type") == "PAPER_FILL":
                    fills[str(entry.get("entry_hash"))] = payload
    unlinked = 0
    mismatched = 0
    jsonl_pnl = 0.0
    ledger_pnl = 0.0
    linked_hashes: set[str] = set()
    for row in rows:
        digest = str(row.get("ledger_hash") or "")
        payload = fills.get(digest)
        if payload is None:
            unlinked += 1
            if row.get("event") == "CLOSE" and isinstance(row.get("realized_pnl_usd"), (int, float)):
                jsonl_pnl += float(row["realized_pnl_usd"])
            continue
        linked_hashes.add(digest)
        if any(payload.get(key) != row.get(key) for key in _MATCH_FIELDS):
            mismatched += 1
        if row.get("event") == "CLOSE":
            left = float(row.get("realized_pnl_usd") or 0.0)
            right = float(payload.get("realized_pnl_usd") or 0.0)
            jsonl_pnl += left
            ledger_pnl += right
            if abs(left - right) > CASH_TOL_USD:
                mismatched += 1
    orphans = len(set(fills) - linked_hashes)
    discrepancy = round(jsonl_pnl - ledger_pnl, 6)
    if not str(chain_verdict).startswith("CHAIN_INTACT"):
        verdict = "CHAIN_NOT_INTACT"
    elif unlinked or orphans or mismatched or abs(discrepancy) > CASH_TOL_USD:
        verdict = "MEASURED_NONZERO" if abs(discrepancy) > CASH_TOL_USD else "INCOMPLETE"
    else:
        verdict = "MEASURED_ZERO"
    snap = {
        "schema": "ahos.treasury.paper_cash_double_entry.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "recorded_on_ledger": False,
        "chain_verdict": chain_verdict,
        "open_close_rows": len(rows),
        "ledger_fills": len(fills),
        "unlinked_rows": unlinked,
        "orphan_fills": orphans,
        "field_mismatches": mismatched,
        "jsonl_realized_pnl_usd": round(jsonl_pnl, 6),
        "ledger_realized_pnl_usd": round(ledger_pnl, 6),
        "discrepancy_usd": discrepancy,
        "tolerance_usd": CASH_TOL_USD,
        "verdict": verdict,
    }
    path = root / "reports" / "grok" / "PAPER" / "paper_cash_double_entry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
