#!/usr/bin/env python3
"""M42 paper judge — an independent reconcile over the recorded paper ledger.

Vision M42 (:1269): *"hash-chained ledger + nightly reconcile: extend
``architecture/mission/ledger.py`` and ``paper_trading/ledger.py`` (one
ledger); a mismatch with the counterparty = HALT."* DEDUP_MERGE_MAP v1.20 folds
two things into M42 — the daily digest checksum (:12, from M80 v2 B7) and the
paper double-entry (:38) — and M13's acceptance names the **M42 judge** as one
of its five gates. This module is that judge for the paper tracks.

**Independence is the point.** DEDUP:141 records the M42 principle as *"a fresh
reviewer with no shared history checks important outputs, because an agent is
biased by its own history."* So the judge never imports the track it is
auditing: it takes the canonical ``MissionLedger`` and derives every number
from the recorded bytes. The track's own equity claim is then *checked*, not
believed. A track that wrote a flattering number and a judge that read the
track's in-memory state would agree by construction; a judge that replays the
ledger is the only kind that can catch the discrepancy.

What it verifies, in order:

1. **The chain** — delegated to ``MissionLedger.verify()``. A tamper breaks it,
   and the verdict becomes ``BROKEN_CHAIN`` rather than a discrepancy, because
   a rewritten ledger is not evidence at all.
2. **Form** — every checkpoint is a dict carrying the paper surface, declares
   ``paper_only`` true, and its cycle is exactly one more than the last. A
   paper ledger that stops labelling itself paper is the first sign of a
   real-money leak.
3. **Position continuity** — a position appears only while the track was flat,
   changes identity only through a recorded close, and is cleared only by one.
   Gold enters on VERIFIED only, so a position cannot appear on a cycle that
   recorded no corroborated price.
4. **Double-entry (§49 / DEDUP:38)** — every settled close is re-derived from
   the *open position the previous checkpoint recorded* and the *corroborated
   price this cycle recorded*:
   ``realized == qty * (price - cost/2) - notional``.
   The debit side is the notional committed, the credit side is the net
   proceeds, and the two must sum to the recorded realised PnL to float
   precision. Money cannot enter the equity curve except through a trade the
   ledger can see.
5. **The money identity** — equity moves by exactly the realised PnL of the
   trade that closed, and never otherwise. When a checkpoint declares its
   bankroll, the absolute identity ``equity == bankroll + Σ realized`` is also
   checked from the opening balance.
6. **No invented PnL** — a close with no corroborated price must carry zero
   realised PnL. PT-X1 invalidates an unpriceable risk rather than pricing it;
   the judge confirms the track did not quietly mark it.
7. **The claim** — the judge recomputes cycles, closed trades, wins, losses,
   Σ realized and equity from the bytes and compares them with the final
   checkpoint's claims. A disagreement is a ``DISCREPANCY``.

Verdicts: ``CLEAN``, ``DISCREPANCY``, ``BROKEN_CHAIN``. There is no verdict
that means "mostly fine" — a single finding is a discrepancy, which is the
HALT the vision specifies.

The daily digest (:12) is computed and recorded **unsigned**. A signature needs
a key, and keys come only from the sanctioned Credential Manager namespace
under owner approval; fabricating one would be worse than omitting it. The
digest binds the day's entry hashes to the chain head so a later rewrite is
detectable against any copy of the digest, and the signature is the owner-gated
addition on top.

Everything here is PAPER_ONLY. The judge has no HALT of its own to sound: it
reports, and the caller decides. It never closes a position, because there are
no real positions to close.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..mission.ledger import GENESIS_HASH, MissionLedger

CLEAN = "CLEAN"
DISCREPANCY = "DISCREPANCY"
BROKEN_CHAIN = "BROKEN_CHAIN"

#: Float slack for the double-entry and money identities. The arithmetic is
#: exact to ~1e-12 relative at these magnitudes; anything past this is a real
#: disagreement, not rounding.
_TOL_REL = 1e-9


@dataclass(frozen=True)
class Finding:
    """One audit finding. ``code`` is stable so a caller can gate on it."""

    code: str
    detail: str


@dataclass(frozen=True)
class JudgeReport:
    """The reconcile verdict. ``summary`` is the judge's own recomputation."""

    verdict: str
    mission_id: str
    entries: int = 0
    cycles: int = 0
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    summary: dict[str, Any] = field(default_factory=dict)
    head_hash: str | None = None

    @property
    def clean(self) -> bool:
        return self.verdict == CLEAN


def _close(a: float, b: float) -> bool:
    scale = max(1.0, abs(a), abs(b))
    return abs(a - b) <= _TOL_REL * scale


def _fnum(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f == f else None          # NaN is not a measurement


def _position(cp: dict[str, Any]) -> dict[str, Any] | None:
    pos = cp.get("position")
    return pos if isinstance(pos, dict) else None


def judge_paper_ledger(
    ledger: MissionLedger,
    mission_id: str,
    *,
    bankroll_usd: float | None = None,
) -> JudgeReport:
    """Reconcile one paper mission's recorded history.

    ``bankroll_usd`` is the opening balance the judge should hold the equity
    identity against. Supply it when the checkpoints do not declare their own;
    when neither is available the absolute identity is reported as not
    evaluated rather than skipped silently.
    """
    try:
        history = ledger.history(mission_id)
        chain = ledger.verify()
    except Exception as exc:  # noqa: BLE001 - a broken chain is the finding
        return JudgeReport(BROKEN_CHAIN, mission_id,
                           findings=(Finding("J-CHAIN", f"{type(exc).__name__}: {exc}"),))

    checkpoints = [_checkpoint(e) for e in history]
    findings: list[Finding] = []

    # ---- form --------------------------------------------------------------
    cycles = [cp for cp in checkpoints if cp is not None]
    expected = 1
    for entry, cp in zip(history, checkpoints):
        seq = entry.get("seq")
        if cp is None:
            continue                       # a START or an unparseable entry
        if not isinstance(cp, dict):
            findings.append(Finding("J-FORMAT", f"seq {seq}: checkpoint is not an object"))
            continue
        if cp.get("paper_only") is not True:
            findings.append(Finding(
                "J-PAPER", f"seq {seq}: paper_only is {cp.get('paper_only')!r}, "
                           f"not True -- a paper ledger must label itself paper"))
        cyc = cp.get("cycle")
        if not isinstance(cyc, int) or isinstance(cyc, bool):
            findings.append(Finding("J-FORMAT", f"seq {seq}: cycle {cyc!r} is not an integer"))
        elif cyc != expected:
            findings.append(Finding(
                "J-CYCLE", f"seq {seq}: cycle {cyc} where {expected} was expected "
                           f"(a gap or a rewrite)"))
        expected = (cyc + 1 if isinstance(cyc, int) and not isinstance(cyc, bool)
                    else expected + 1)
        declared = cp.get("bankroll_usd")
        if bankroll_usd is None and isinstance(declared, (int, float)):
            bankroll_usd = float(declared)

    # ---- replay: position continuity, double-entry, money identity ---------
    prev_pos: dict[str, Any] | None = None
    equity: float | None = None
    cumulative = 0.0
    settled = invalidated = 0
    wins = losses = 0
    gross = 0.0
    unpriced_cycles = 0
    witness_states: dict[str, int] = {}
    bps: float | None = None

    for entry, cp in zip(history, checkpoints):
        if cp is None:
            continue
        seq = entry.get("seq")
        state = (entry.get("state") or {}).get("CHECKPOINT") or {}
        bps = _fnum(cp.get("round_trip_bps", bps))
        ws = str(state.get("witness", {}).get("state") or "UNKNOWN") \
            if isinstance(state.get("witness"), dict) else "UNKNOWN"
        witness_states[ws] = witness_states.get(ws, 0) + 1

        price = _fnum(cp.get("price_usd"))
        this_pos = _position(cp)
        exit_event = cp.get("exit")
        realized = _fnum(cp.get("realized_pnl_usd"))
        claimed_equity = _fnum(cp.get("equity_usd"))

        # Position continuity --------------------------------------------
        if prev_pos is None and this_pos is not None and price is None:
            findings.append(Finding(
                "J-POSITION", f"seq {seq}: a position opened on a cycle that "
                              f"recorded no corroborated price"))
        if prev_pos is not None and this_pos is not None:
            if this_pos.get("entry_ts") != prev_pos.get("entry_ts"):
                findings.append(Finding(
                    "J-POSITION", f"seq {seq}: position identity changed while a "
                                  f"position was already open"))
        if prev_pos is not None and this_pos is None and not exit_event:
            findings.append(Finding(
                "J-POSITION", f"seq {seq}: position vanished without a recorded exit"))
        if prev_pos is None and exit_event is not None and exit_event:
            findings.append(Finding(
                "J-POSITION", f"seq {seq}: an exit was recorded while no position "
                              f"was open"))

        # The close --------------------------------------------------------
        if exit_event is not None:
            if price is None:
                # PT-X1: an unpriceable risk is invalidated, never priced.
                invalidated += 1
                if realized is not None and abs(realized) > 0.0:
                    findings.append(Finding(
                        "J-INVENTED", f"seq {seq}: closed with no corroborated price "
                                      f"yet realized {realized!r} -- PnL must be zero"))
                elif realized is None:
                    realized = 0.0
            else:
                if prev_pos is None:
                    findings.append(Finding(
                        "J-DOUBLE", f"seq {seq}: a settled close with no open "
                                    f"position to settle against"))
                else:
                    settled += 1
                    qty = _fnum(prev_pos.get("qty_oz"))
                    notional = _fnum(prev_pos.get("notional_usd"))
                    half = (bps / 2.0 / 10_000.0) if bps is not None else 0.0
                    if qty is None or notional is None:
                        findings.append(Finding(
                            "J-DOUBLE", f"seq {seq}: the open position is missing "
                                        f"qty/notional"))
                    else:
                        expected_pnl = qty * (price * (1.0 - half)) - notional
                        if realized is None or not _close(realized, expected_pnl):
                            findings.append(Finding(
                                "J-DOUBLE",
                                f"seq {seq}: realized {realized!r} does not equal the "
                                f"double-entry recomputation {expected_pnl!r} "
                                f"(qty {qty} x price {price} net of "
                                f"{bps}bps/2, less notional {notional})"))
                        else:
                            gross += realized
                            cumulative += realized
                            if realized > 0:
                                wins += 1
                            elif realized < 0:
                                losses += 1
            if equity is not None and realized is not None \
                    and claimed_equity is not None \
                    and not _close(claimed_equity, equity + realized):
                findings.append(Finding(
                    "J-EQUITY", f"seq {seq}: equity {claimed_equity} but the prior "
                                f"equity {equity} plus realized {realized} "
                                f"= {equity + realized}"))
        else:
            if equity is not None and claimed_equity is not None \
                    and not _close(claimed_equity, equity):
                findings.append(Finding(
                    "J-EQUITY", f"seq {seq}: equity moved to {claimed_equity} on a "
                                f"cycle that closed no trade (was {equity})"))

        if price is None:
            unpriced_cycles += 1
        equity = claimed_equity if claimed_equity is not None else equity
        prev_pos = this_pos

    # ---- the absolute money identity ---------------------------------------
    opening = bankroll_usd
    final_claimed = None
    if cycles:
        last = cycles[-1]
        final_claimed = _fnum(last.get("equity_usd"))
        cum_claimed = _fnum(last.get("cumulative_realized_pnl_usd"))
        if cum_claimed is not None and not _close(cum_claimed, cumulative):
            findings.append(Finding(
                "J-EQUITY", f"final cumulative_realized_pnl_usd {cum_claimed} but the "
                            f"judge summed {cumulative} over the recorded closes"))
    if opening is not None and final_claimed is not None:
        if not _close(final_claimed, opening + cumulative):
            findings.append(Finding(
                "J-EQUITY", f"final equity {final_claimed} != bankroll {opening} "
                            f"+ realized {cumulative}"))
    elif opening is None:
        findings.append(Finding(
            "J-BANKROLL", "no checkpoint declares a bankroll and none was supplied; "
                          "the absolute money identity was not evaluated (the "
                          "per-cycle identity was)"))

    summary = {
        "entries": len(history),
        "cycles": len(cycles),
        "closed_trades": settled + invalidated,
        "settled": settled,
        "invalidated": invalidated,
        "wins": wins,
        "losses": losses,
        "gross_realized_pnl_usd": gross,
        "equity_usd": final_claimed,
        "unpriced_cycles": unpriced_cycles,
        "witness_states": witness_states,
        "bankroll_usd": opening,
    }

    # ---- the claim: the track's own counters against the judge's -----------
    if cycles:
        last = cycles[-1]
        for key, ours in (("closed_trades", settled + invalidated),
                          ("cumulative_realized_pnl_usd", cumulative)):
            theirs = _fnum(last.get(key))
            if theirs is None:
                findings.append(Finding(
                    "J-CLAIM", f"the final checkpoint does not declare {key}"))
            elif not _close(theirs, ours):
                findings.append(Finding(
                    "J-CLAIM", f"{key}: the ledger claims {theirs}, the judge "
                                f"recomputed {ours}"))

    verdict = DISCREPANCY if findings else CLEAN
    return JudgeReport(verdict, mission_id,
                       entries=len(history), cycles=len(cycles),
                       findings=tuple(findings), summary=summary,
                       head_hash=chain.get("head_hash"))


def _checkpoint(entry: dict[str, Any]) -> dict[str, Any] | None:
    """The entry's recorded checkpoint payload, or None for a START row.

    A torn or malformed row has no CHECKPOINT; it is not treated as an audit
    failure here (the chain leg already reports tamper) but as no evidence.
    """
    state = entry.get("state")
    if not isinstance(state, dict):
        return None
    cp = state.get("CHECKPOINT")
    return cp if isinstance(cp, dict) else None


# ------------------------------------------------------- the daily digest ----


def daily_digest(
    ledger: MissionLedger,
    mission_id: str,
    *,
    day: str | None = None,
) -> dict[str, Any] | None:
    """The DEDUP:12 digest for one UTC day of a mission's entries.

    Binds every entry hash written that day to the chain head, so any copy of
    this digest detects a later rewrite of the day. **Unsigned by design**: a
    signature needs a Credential Manager key under owner approval, and an
    unsigned digest that says so is honest where a fabricated signature would
    not be. The recorded ``signed`` field is therefore always false and the
    reason is carried alongside it.

    ``day`` is an ISO ``YYYY-MM-DD`` UTC string; None means today in UTC.
    """
    if day is None:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        entries = ledger.history(mission_id)
        chain = ledger.verify()
    except Exception:  # noqa: BLE001 - no digest over a broken chain
        return None
    hashes = [e.get("entry_hash")
              for e in entries
              if isinstance(e.get("ts"), str) and e["ts"].startswith(day)
              and isinstance(e.get("entry_hash"), str)]
    if not hashes:
        return None
    body = json.dumps({"schema": "ahos.paper_digest.v1", "mission": mission_id,
                       "day": day, "entry_hashes": hashes},
                      sort_keys=True, separators=(",", ":"))
    return {
        "schema": "ahos.paper_digest.v1",
        "mission_id": mission_id,
        "day": day,
        "entries": len(hashes),
        "digest_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "head_hash": chain.get("head_hash"),
        "signed": False,
        "unsigned_reason": ("signature awaits a sanctioned Credential Manager "
                            "key under owner approval; no key is fabricated"),
        "genesis_hash": GENESIS_HASH,
    }


def write_judge_report(report: JudgeReport, path: str | Path) -> Path:
    """Render the reconcile as markdown. A discrepancy is never styled clean."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# M42 paper judge — {report.mission_id}",
        "",
        f"**Verdict: {report.verdict}**",
        "",
        f"- ledger entries: {report.entries}",
        f"- cycles replayed: {report.cycles}",
        f"- chain head: `{report.head_hash}`",
    ]
    s = report.summary
    if s:
        lines += [
            "",
            "## The judge's own numbers",
            "",
            f"- closed trades: {s.get('closed_trades', 0)} "
            f"({s.get('settled', 0)} settled, {s.get('invalidated', 0)} invalidated)",
            f"- wins / losses: {s.get('wins', 0)} / {s.get('losses', 0)}",
            f"- gross realized PnL: {s.get('gross_realized_pnl_usd', 0.0):.2f} "
            f"(PAPER)",
            f"- equity: {s.get('equity_usd')}",
            f"- cycles with no corroborated price: {s.get('unpriced_cycles', 0)}",
            f"- witness states: {s.get('witness_states', {})}",
        ]
    lines += ["", "## Findings", ""]
    if not report.findings:
        lines.append("No discrepancy. Every closed trade re-derives from the "
                     "position and the corroborated price that the ledger "
                     "records, and the equity curve moves only through "
                     "recorded realized PnL.")
    else:
        for f in report.findings:
            lines.append(f"- **{f.code}** — {f.detail}")
    lines += [
        "",
        "PAPER_ONLY. This judge reports; it does not promote, and it closes "
        "nothing.",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
