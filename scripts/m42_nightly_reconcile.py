#!/usr/bin/env python3
"""M42 — the nightly reconcile over the single hash-chained ledger.

Usage:
    python scripts/m42_nightly_reconcile.py [--mission M13-GOLD-PAPER]
                                           [--ledger PATH] [--out PATH]
                                           [--broker-registry config/broker_registry.yaml]
                                           [--no-depeg] [--dry-run]

Vision M42: *"hash-chained ledger + nightly reconcile — extend
``architecture/mission/ledger.py`` and ``paper_trading/ledger.py`` into ONE
append-only, hash-chained ledger; reconcile against the broker, and a mismatch
is a HALT."* §7.0 adds: each broker ≤ 40%, and USDT depeg > 0.5% halts.

What this does, in one pass:

* verifies the ledger's own chain (a tamper breaks it);
* re-witnesses the frozen paper store against its last anchor on the chain,
  binding it on the first run;
* replays the paper track through the M42 judge (``architecture/markets/
  judge.py``) and checks the track's claims against its own re-derivation;
* checks the counterparty statement's arithmetic and the 40% concentration
  limit — no broker is declared today, so the leg reports UNMEASURED rather
  than inventing a statement;
* takes two independent keyless USDT quotes and applies the peg law;
* records the verdict on the single ledger and, on any measured breach,
  records a HALT that only an entry naming its own hash can release.

It is an alarm clock, not a component with authority: it reports and records,
promotes nothing, and closes nothing. PAPER_ONLY.

Exit codes: 0 CLEAN / 1 DISCREPANCY or UNKNOWN / 2 BROKEN_CHAIN. A non-zero
exit is the signal a watchdog or a cron should page on; it is not a crash.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.ledger import MissionLedger, default_ledger_path  # noqa: E402
from architecture.treasury.reconcile import (  # noqa: E402
    BROKEN_CHAIN, CLEAN, DISCREPANCY, HALTED, UNKNOWN, write_reconcile_report,
    run_reconcile,
)
from architecture.treasury.surveillance import (  # noqa: E402
    collect_usdt_quotes, exposures_from_registry, load_broker_registry,
)

AGENT = "engineering:m42-reconcile"
DEFAULT_MISSION = "M13-GOLD-PAPER"
DEFAULT_REGISTRY = ROOT / "config" / "broker_registry.yaml"


def _parse(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mission", default=DEFAULT_MISSION,
                   help=f"the paper mission to reconcile (default {DEFAULT_MISSION})")
    p.add_argument("--ledger", default=None,
                   help="path to the mission ledger jsonl (default: the live ledger)")
    p.add_argument("--out", default=None,
                   help="markdown report path (default reports/grok/M42/<day>_reconcile.md)")
    p.add_argument("--broker-registry", default=str(DEFAULT_REGISTRY),
                   help="config/broker_registry.yaml (owner-gated; empty today)")
    p.add_argument("--no-depeg", action="store_true",
                   help="skip the live USDT depeg leg (offline / no egress)")
    p.add_argument("--depeg-only", action="store_true",
                   help="report the peg leg and exit without touching the ledger")
    p.add_argument("--dry-run", action="store_true",
                   help="compute the verdict and write nothing to the ledger")
    p.add_argument("--bankroll", type=float, default=None,
                   help="opening balance for the absolute money identity, when the "
                        "checkpoints do not declare one")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    ledger_path = Path(args.ledger) if args.ledger else default_ledger_path(create=False)

    # The peg leg can be reported on its own, with no ledger at all — it is a
    # read-only market observation, and a paper soak that only wants the peg
    # should not need a ledger to get it.
    if args.depeg_only:
        quotes = collect_usdt_quotes()
        if not quotes:
            print("USDT depeg: UNMEASURED (no quote reachable)")
            return 1
        lo = min(q.price_usd for q in quotes)
        hi = max(q.price_usd for q in quotes)
        dev = (abs(sum(q.price_usd for q in quotes) / len(quotes)) - 1.0) * 100.0
        print(f"USDT quotes: " +
              ", ".join(f"{q.provider_id}={q.price_usd:.6f}" for q in quotes))
        print(f"spread {hi - lo:.6f} USD, mean deviation from $1 {dev:+.4f}% "
              f"({'within' if abs(dev) <= 0.5 else 'BEYOND'} the 0.5% halt threshold)")
        return 0 if abs(dev) <= 0.5 else 1

    if not ledger_path.is_file():
        print(f"M42 reconcile: the ledger {ledger_path} does not exist; nothing to "
              "reconcile. Run a paper track first.", file=sys.stderr)
        return 2
    ledger = MissionLedger(ledger_path)

    # The counterparty leg: the owner-gated broker registry. Empty today, which
    # the leg reports as UNMEASURED rather than inventing a statement.
    statement = None
    if Path(args.broker_registry).is_file():
        registry = load_broker_registry(args.broker_registry)
        exposures = exposures_from_registry(registry)
        statement = {"counterparty": "broker_registry.yaml",
                     "trades": [],
                     "exposures": {e.broker_id: e.exposure_usd for e in exposures}}

    quotes = None if args.no_depeg else collect_usdt_quotes()
    report = run_reconcile(ledger, mission_id=args.mission, statement=statement,
                           depeg_quotes=quotes, bankroll_usd=args.bankroll,
                           agent=AGENT, record=not args.dry_run)

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = Path(args.out) if args.out else ROOT / "reports" / "grok" / "M42" / f"{day}_reconcile.md"
    write_reconcile_report(report, out)
    print(f"M42 reconcile: verdict={report.verdict} entries={report.entries} "
          f"findings={len(report.findings)} recorded={report.recorded} "
          f"halt_recorded={report.halt_recorded}")
    print(f"  report: {out}")
    for finding in report.findings[:12]:
        print(f"  - {finding.code}: {finding.detail}")
    if report.notes:
        for note in report.notes:
            print(f"  note: {note}")

    if report.verdict == CLEAN:
        return 0
    if report.verdict in (DISCREPANCY, UNKNOWN, HALTED):
        return 1
    return 2


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main())
