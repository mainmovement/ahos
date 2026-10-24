#!/usr/bin/env python3
"""M13 gold 7-day paper soak — the cadence runner.

OWN-18 puts gold first on the paper track, and the owner's 00:01 decision asks for
the M13 soak to run on its own as a background scheduled job: paper cycles plus a
daily judge report in reports/grok/M13_SOAK/, while the dashboard work continues
in the foreground.

This module owns **no trading logic at all — it is an alarm clock.** Every cycle
is `architecture.markets.gold_paper.run_gold_paper_cycle`, which trades fake money
against real two-source-corroborated XAU prices and records into the one canonical
mission ledger (INV-31, M34). The daily report is `architecture.markets.judge`,
which replays those recorded bytes and never asks the track what happened. Nothing
here can promote, size, or close a real position: there is no live path, no key,
no exchange, and no funds to reach. PAPER_ONLY is structural in the modules this
calls, not a flag this script sets.

Failure handling is the point of a soak. A cycle that raises — a down feed, a
network blip, a ledger hiccup — is logged and the cadence continues; a soak that
died on its first transient would soak nothing. The one exception is the daily
report, which is written *after* a failure as well as after a success, because a
day with no judge report is worse than a judge report over a thin day.

Cadence: 15 minutes by default. The exit card prices an exit only on an
observation ≤ 6h old (`exit_reference_max_age_sec`), so the interval must stay
well inside that or the soak would spend its time in INVALID_DATA_UNAVAILABLE
rather than in the exit vocabulary the soak exists to exercise.

Usage::

    python scripts/m13_gold_soak.py            # the 7-day cadence, foreground
    python scripts/m13_gold_soak.py --once      # one cycle, then exit
    python scripts/m13_gold_soak.py --report-only
    python scripts/m13_gold_soak.py --days 7 --interval-sec 900
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Run from the repo root, not from wherever the interpreter was launched from, so
# `architecture` and `config` resolve the same way `pythonpath = .` makes them
# resolve under pytest.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: Where the daily judge reports, digests and status live.
SOAK_DIR = ROOT / "reports" / "grok" / "M13_SOAK"

#: The soak's length, in days. The owner's 00:01 note says seven.
DEFAULT_DAYS = 7.0

#: Cycle interval. Must stay well inside the exit card's 6h price freshness, so
#: the soak exercises exits rather than unpriceable ones.
DEFAULT_INTERVAL_SEC = 900

#: The mission this soak advances, named once by the track itself.
GOLD_PAPER_MISSION = "M13-GOLD-PAPER"


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _ledger_path_summary(ledger_path: Path | None) -> dict[str, Any]:
    """Read wiring fields from the last checkpoint (read-only). Best-effort for runlog ops."""
    if ledger_path is None:
        return {}
    try:
        from architecture.markets.gold_paper import GOLD_PAPER_MISSION
        from architecture.mission.ledger import MissionLedger

        cp = (MissionLedger(ledger_path).latest(GOLD_PAPER_MISSION) or {}).get("CHECKPOINT") or {}
        if not isinstance(cp, dict):
            return {}
        path = cp.get("path") if isinstance(cp.get("path"), dict) else {}
        halt = cp.get("halt") if isinstance(cp.get("halt"), dict) else {}
        close_eval = cp.get("close_eval") if isinstance(cp.get("close_eval"), dict) else {}
        m51 = path.get("m51") if isinstance(path.get("m51"), dict) else {}
        return {
            "path_oms": path.get("oms"),
            "path_blocks_n": len(path.get("blocks") or []),
            "path_m51_merge": m51.get("merge"),
            "halt_state": halt.get("state"),
            "close_eval_hit": close_eval.get("hit"),
        }
    except Exception:  # noqa: BLE001 - runlog enrichment must not break the soak
        return {}


def _cycle(ledger_path: Path | None) -> dict[str, Any]:
    """Advance one paper cycle. Never raises — a failed cycle is a record."""
    from architecture.markets.gold_paper import run_gold_paper_cycle

    started = time.time()
    record: dict[str, Any] = {
        "ts": _utc_stamp(),
        "kind": "cycle",
        "ok": False,
    }
    try:
        result, witness = run_gold_paper_cycle(ledger_path=ledger_path)
        record.update(
            ok=True,
            cycle=result.cycle,
            witness_state=result.witness_state,
            witness_reason=result.witness_reason,
            price_usd=result.price_usd,
            spread_pct=witness.spread_pct,
            equity_usd=result.equity_usd,
            position_open=result.position is not None,
            exit=result.exit,
            realized_pnl_usd=result.realized_pnl_usd,
            unpriced_for_s=result.unpriced_for_s,
            recorded=result.recorded,
            ledger_error=result.ledger_error,
            breaker=None if result.breaker is None else {
                "state": result.breaker.state,
                "allowed": result.breaker.allowed,
                "reasons": list(result.breaker.reasons),
            },
        )
        if ledger_path is not None:
            record.update(_ledger_path_summary(ledger_path))
    except Exception as exc:  # noqa: BLE001 - a soak continues past a bad cycle
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc(limit=3)
    record["duration_s"] = round(time.time() - started, 2)
    return record


def _daily_report(soak_dir: Path, ledger_path: Path | None,
                  *, day: str | None = None) -> dict[str, Any]:
    """Run the M42 judge over the soak's mission and write the day's report.

    The judge is imported fresh each call and reads only the ledger, so a long
    running soak cannot drift into auditing its own memory.
    """
    from architecture.mission.ledger import MissionLedger
    from architecture.markets.judge import (
        daily_digest,
        judge_paper_ledger,
        write_judge_report,
    )

    day = day if day is not None else _utc_day()
    # `run_gold_paper_cycle` resolves a None ledger path itself; the judge does
    # not, so resolve the same default here rather than assume one.
    from architecture.mission.ledger import MissionLedger, default_ledger_path

    ledger = MissionLedger(ledger_path
                           if ledger_path is not None
                           else default_ledger_path())
    report = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    path = soak_dir / f"{day}_judge.md"
    write_judge_report(report, path)

    digest_path = soak_dir / f"{day}_digest.json"
    digest = daily_digest(ledger, GOLD_PAPER_MISSION, day=day)
    if digest is not None:
        digest_path.write_text(
            json.dumps(digest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    try:
        import subprocess

        for script in (
            "export_m49_lessons_snapshot.py",
            "export_message_hub_snapshot.py",
            "export_self_eval_snapshot.py",
            "export_capability_lab_snapshot.py",
            "export_university_exam_radar_snapshots.py",
            "export_skill_market_snapshot.py",
            "export_oil_paper_snapshot.py",
            "export_newsroom_snapshot.py",
            "export_whitehat_audit.py",
        ):
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / script)],
                cwd=str(ROOT),
                timeout=120,
                check=False,
            )
    except Exception:  # noqa: BLE001 - Arena export must not block the judge
        pass
    return {
        "ts": _utc_stamp(),
        "kind": "daily",
        "day": day,
        "verdict": report.verdict,
        "findings": len(report.findings),
        "entries": report.entries,
        "cycles": report.cycles,
        "judge_md": str(path),
        "digest_json": str(digest_path) if digest is not None else None,
        "head_hash": report.head_hash,
        "summary": report.summary,
    }


def _tier_report(soak_dir: Path, ledger_path: Path | None,
                 *, day: str | None = None) -> dict[str, Any]:
    """Evaluate the T0 -> T1 promotion gate over the soak's ledger (M13).

    The gate measures the ten vision-11.0 exit criteria against the recorded
    trades and reports which are met, unmet and *unmeasurable as specified*. It
    never promotes -- promotion is an owner act plus the three gate agents -- so
    a day with no closed trades reports `0/200 trades, NOT READY`, which is the
    honest state of a young soak and the successful outcome here. A report that
    said \"ready\" would be proof the gate is broken.

    Like the judge, this reads only the ledger it is handed. It is wrapped so a
    fault in the gate cannot kill the cadence: the soak survives a bad report
    the same way it survives a bad cycle.
    """
    record: dict[str, Any] = {
        "ts": _utc_stamp(),
        "kind": "tier_gate",
        "day": day if day is not None else _utc_day(),
        "ok": False,
    }
    try:
        from architecture.mission.ledger import MissionLedger, default_ledger_path
        from architecture.markets.gold_paper import GOLD_PAPER_MISSION, paper_history
        from architecture.markets.tier_gate import evaluate_tier_gate, write_gate_report

        ledger = MissionLedger(ledger_path
                               if ledger_path is not None
                               else default_ledger_path())
        history = paper_history(ledger)
        from architecture.markets.gate_inputs import tier_gate_kwargs

        report = evaluate_tier_gate(
            market="gold",
            trades=list(history.trades),
            months_of_data=history.months_of_data,
            **tier_gate_kwargs(),
        )
        path = soak_dir / f"{record['day']}_tier_gate.md"
        write_gate_report(report, path)
        record.update(
            ok=True,
            tier=report.tier_today,
            promoted=report.promoted,
            trades=len(history.trades),
            months_of_data=history.months_of_data,
            measurable_passed=report.measurable_and_passed,
            measurable_total=report.measurable_total,
            unmeasurable=list(report.unmeasurable),
            ready_for_owner_review=report.ready_for_owner_review,
            open_questions=list(report.open_questions),
            gate_md=str(path),
        )
    except Exception as exc:  # noqa: BLE001 - a soak continues past a bad report
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc(limit=3)
    return record


def _reconcile_report(soak_dir: Path, ledger_path: Path | None,
                      *, day: str | None = None) -> dict[str, Any]:
    """Run the M42 nightly reconcile over the soak's ledger (vision M42).

    This is the reconcile the vision makes halt-capable: the chain, the frozen
    paper store bound to it by anchor, this soak's own paper book through the
    judge, and the §7.0 treasury checks (each broker <= 40%, USDT depeg > 0.5%).
    It runs in-process, so the soak stays the ledger's single writer — a
    second process appending to the same chain could interleave an entry with
    a cycle's checkpoint and break the chain the soak records.

    On a measured breach it records a HALT on the ledger, which the paper track
    reads back before taking new risk. It is wrapped like the tier gate: a
    reconcile that cannot run is reported, and the cadence continues, because a
    soak that stopped on a reporting fault would soak nothing.
    """
    record: dict[str, Any] = {
        "ts": _utc_stamp(),
        "kind": "m42_reconcile",
        "day": day if day is not None else _utc_day(),
        "ok": False,
    }
    try:
        from architecture.mission.ledger import MissionLedger, default_ledger_path
        from architecture.treasury.reconcile import run_reconcile, write_reconcile_report
        from architecture.treasury.surveillance import collect_usdt_quotes

        ledger = MissionLedger(ledger_path
                               if ledger_path is not None
                               else default_ledger_path())
        report = run_reconcile(
            ledger,
            mission_id=GOLD_PAPER_MISSION,
            depeg_quotes=collect_usdt_quotes(),
            agent="engineering:m13-soak",
        )
        path = soak_dir / f"{record['day']}_reconcile.md"
        write_reconcile_report(report, path)
        record.update(
            ok=True,
            verdict=report.verdict,
            findings=len(report.findings),
            entries=report.entries,
            head_hash=report.head_hash,
            recorded=report.recorded,
            halt_recorded=report.halt_recorded,
            reconcile_md=str(path),
        )
    except Exception as exc:  # noqa: BLE001 - a soak continues past a bad report
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc(limit=3)
    return record


def _write_status(soak_dir: Path, status: dict[str, Any]) -> None:
    soak_dir.mkdir(parents=True, exist_ok=True)
    try:
        pt_status_path = ROOT / "reports" / "grok" / "PAPER" / "paper_trader_status.json"
        if pt_status_path.is_file():
            pt_st = json.loads(pt_status_path.read_text(encoding="utf-8"))
            status["unified_100usd_gold_desk"] = {
                "UnifiedBrain": "architecture.markets.paper_trader",
                "initial_capital_usd": pt_st.get("initial_capital_usd", 100.0),
                "mark_to_market_equity_usd": pt_st.get("mark_to_market_equity_usd"),
                "gold_desk_realized_pnl_usd": (pt_st.get("per_desk_realized_pnl_usd") or {}).get("GOLD", 0.0),
                "gold_witness": (pt_st.get("witness") or {}).get("XAU"),
                "gold_open_position": (pt_st.get("open_positions") or {}).get("XAU"),
                "updated_at": pt_st.get("updated_at"),
                "paper_only": True,
            }
    except Exception:
        pass
    path = soak_dir / "soak_status.json"
    path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _latest_state(ledger_path: Path | None) -> dict[str, Any] | None:
    """The soak's recorded position, for the status file. Read-only."""
    try:
        from architecture.mission.ledger import MissionLedger, default_ledger_path

        ledger = MissionLedger(ledger_path
                               if ledger_path is not None
                               else default_ledger_path())
        latest = ledger.latest(GOLD_PAPER_MISSION)
        if latest is None:
            return None
        cp = latest.get("CHECKPOINT")
        return cp if isinstance(cp, dict) else None
    except Exception:  # noqa: BLE001 - status is best effort
        return None


def run_soak(*, interval_sec: float, days: float, soak_dir: Path,
             ledger_path: Path | None, once: bool = False,
             report_only: bool = False) -> int:
    soak_dir.mkdir(parents=True, exist_ok=True)
    runlog = soak_dir / "soak_runlog.jsonl"

    if report_only:
        record = _daily_report(soak_dir, ledger_path)
        _append_jsonl(runlog, record)
        print(f"[m13-soak] daily report: {record['verdict']} "
              f"({record['findings']} findings) -> {record['judge_md']}")
        tier = _tier_report(soak_dir, ledger_path)
        _append_jsonl(runlog, tier)
        if tier["ok"]:
            print(f"[m13-soak] tier gate: {tier['tier']} "
                  f"{tier['measurable_passed']}/{tier['measurable_total']} "
                  f"measurable, {len(tier['unmeasurable'])} unmeasurable "
                  f"-> {tier['gate_md']}", flush=True)
        else:
            print(f"[m13-soak] tier gate FAILED: {tier.get('error')}", flush=True)
        reconcile = _reconcile_report(soak_dir, ledger_path)
        _append_jsonl(runlog, reconcile)
        if reconcile["ok"]:
            print(f"[m13-soak] M42 reconcile: {reconcile['verdict']} "
                  f"({reconcile['findings']} findings, "
                  f"halt_recorded={reconcile['halt_recorded']}) "
                  f"-> {reconcile['reconcile_md']}", flush=True)
        else:
            print(f"[m13-soak] M42 reconcile FAILED: {reconcile.get('error')}",
                  flush=True)
        bad = record["verdict"] == "BROKEN_CHAIN" or reconcile.get("verdict") == "BROKEN_CHAIN"
        return 0 if not bad else 1

    deadline = (time.time() + days * 86400.0) if days and days > 0 else None
    last_day: str | None = None
    tier: dict[str, Any] | None = None
    reconcile: dict[str, Any] | None = None
    cycles_ok = cycles_fail = 0
    latched_halt = False

    while True:
        if latched_halt:
            # Paper entries stay refused. The cadence process keeps its log;
            # it does not flatten a live account (there is none) and it does
            # not clear HOLD. Only an owner unhalt, outside this loop, lifts it.
            record = {
                "ts": _utc_stamp(),
                "kind": "cycle",
                "ok": False,
                "skipped": True,
                "error": "M47 HALT latched; new paper cycles refused until owner unhalt",
                "duration_s": 0.0,
                "breaker": {"state": "HALTED", "allowed": False, "reasons": ["M47 HALT"]},
            }
        else:
            record = _cycle(ledger_path)
        _append_jsonl(runlog, record)
        if record.get("skipped"):
            print(f"[m13-soak] cycle skipped: {record.get('error')}", flush=True)
        elif record["ok"]:
            cycles_ok += 1
            print(f"[m13-soak] cycle {record.get('cycle')} "
                  f"witness={record.get('witness_state')} "
                  f"price={record.get('price_usd')} "
                  f"equity={record.get('equity_usd')}", flush=True)
        else:
            cycles_fail += 1
            print(f"[m13-soak] cycle FAILED: {record.get('error')}", flush=True)

        # The daily judge runs whenever the UTC day rolls over, and also on the
        # first cycle of a soak whose day is already old (a --once smoke). The
        # tier gate runs beside it, so the T0 -> T1 machinery turns over on the
        # same evidence the judge just reconciled.
        today = _utc_day()
        if last_day is None or today != last_day:
            daily = _daily_report(soak_dir, ledger_path, day=today)
            _append_jsonl(runlog, daily)
            last_day = today
            print(f"[m13-soak] daily judge for {today}: {daily['verdict']} "
                  f"({daily['findings']} findings)", flush=True)
            tier = _tier_report(soak_dir, ledger_path, day=today)
            _append_jsonl(runlog, tier)
            if tier["ok"]:
                print(f"[m13-soak] tier gate for {today}: {tier['tier']} "
                      f"{tier['measurable_passed']}/{tier['measurable_total']} "
                      f"measurable, {len(tier['unmeasurable'])} unmeasurable",
                      flush=True)
            else:
                print(f"[m13-soak] tier gate for {today} FAILED: "
                      f"{tier.get('error')}", flush=True)
            # The M42 reconcile runs beside the judge on the same ledger, so a
            # mismatch the judge finds is a HALT on the chain the soak records.
            reconcile = _reconcile_report(soak_dir, ledger_path, day=today)
            _append_jsonl(runlog, reconcile)
            if reconcile["ok"]:
                print(f"[m13-soak] M42 reconcile for {today}: "
                      f"{reconcile['verdict']} ({reconcile['findings']} findings, "
                      f"halt_recorded={reconcile['halt_recorded']})", flush=True)
            else:
                print(f"[m13-soak] M42 reconcile for {today} FAILED: "
                      f"{reconcile.get('error')}", flush=True)

        state = _latest_state(ledger_path)
        status: dict[str, Any] = {
            "soak": "M13-GOLD-PAPER",
            "paper_only": True,
            "started_hint": _utc_stamp(),
            "cycle_interval_sec": interval_sec,
            "planned_days": days,
            "cycles_ok": cycles_ok,
            "cycles_failed": cycles_fail,
            "last_day_report": last_day,
            "last_cycle": record,
            "last_tier_gate": tier,
            "last_m42_reconcile": reconcile,
            "ledger_state": state,
        }
        from architecture.health.monitor import assess_soak_health, latch_halt

        health = assess_soak_health(status)
        latched_halt = latch_halt(latched_halt, health.level)
        status["health"] = {
            "level": "HALT" if latched_halt else health.level,
            "assessed": health.level,
            "reasons": list(health.reasons),
            "latched": latched_halt,
            "paper_only": True,
        }
        status["entries_allowed"] = not latched_halt
        _write_status(soak_dir, status)

        if once:
            return 0 if record["ok"] else 1
        if deadline is not None and time.time() >= deadline:
            print(f"[m13-soak] {days} day(s) elapsed; soak complete. "
                  f"{cycles_ok} cycles ok, {cycles_fail} failed.", flush=True)
            _daily_report(soak_dir, ledger_path)
            return 0

        # Sleep the remainder of the interval, so a slow cycle does not shorten
        # the cadence. Woken early on Ctrl+C, which ends the soak cleanly.
        remaining = interval_sec - record.get("duration_s", 0.0)
        if remaining > 0:
            try:
                time.sleep(remaining)
            except KeyboardInterrupt:
                print("[m13-soak] interrupted; ending the soak.", flush=True)
                _daily_report(soak_dir, ledger_path)
                return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="M13 gold paper soak cadence (PAPER_ONLY — an alarm clock, "
                    "not a trader)")
    ap.add_argument("--interval-sec", type=float,
                    default=DEFAULT_INTERVAL_SEC,
                    help=f"seconds between paper cycles (default {DEFAULT_INTERVAL_SEC}; "
                         f"must stay well inside the exit card's 6h freshness)")
    ap.add_argument("--days", type=float, default=DEFAULT_DAYS,
                    help=f"how long the soak runs (default {DEFAULT_DAYS}; 0 = forever)")
    ap.add_argument("--soak-dir", default=str(SOAK_DIR),
                    help="where the daily reports and status are written")
    ap.add_argument("--ledger-path", default=None,
                    help="override the canonical mission ledger path")
    ap.add_argument("--once", action="store_true",
                    help="advance one cycle and exit (smoke / manual advance)")
    ap.add_argument("--report-only", action="store_true",
                    help="write today's judge report without running a cycle")
    args = ap.parse_args(argv)

    if args.interval_sec <= 0:
        ap.error("--interval-sec must be positive")
    if args.report_only and args.once:
        ap.error("--report-only and --once are mutually exclusive")

    soak_dir = Path(args.soak_dir)
    ledger_path = Path(args.ledger_path) if args.ledger_path else None
    return run_soak(interval_sec=args.interval_sec, days=args.days,
                    soak_dir=soak_dir, ledger_path=ledger_path,
                    once=args.once, report_only=args.report_only)


if __name__ == "__main__":  # pragma: no cover - operator entrypoint
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[m13-soak] interrupted.", file=sys.stderr)
        raise SystemExit(130)
