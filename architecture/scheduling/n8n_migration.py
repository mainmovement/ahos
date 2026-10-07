#!/usr/bin/env python3
"""M10 Stage 3 — authoritative n8n -> Python cadence migration registry.

The six AHOS n8n workflows are retired by M10. This module is the durable
record of *where each cadence went* — which Python surface owns it now, which
ones are deliberately not reimplemented, and which are deferred to M44.

What this module is NOT
-----------------------
It is not a scheduler, and it wires nothing. ``OWNER_DIRECTIVE_MISSION_PLAN``
says the n8n workflows "move to existing Python/Node schedulers
(``architecture/scheduling/engine.py``, ``observation_loop.py``); don't write a
new scheduler." Honouring that literally:

- No wall-clock / hour-of-day / day-of-week ``due()`` primitive is added here
  or anywhere else. ``ProductionScheduler`` is offset-from-cycle-start only,
  and that contract is unchanged (see ``tests/test_n8n_migration_registry.py``
  which pins ``ScheduleTask``'s field set).
- No ``ScheduleTask`` is registered, no CLI is invoked, no subprocess spawned.
- Cadence is recorded as *data* (``N8nCadence``), forward-complete for M44.

Why the statuses are split the way they are
-------------------------------------------
The live n8n database has **zero imported workflows** (M10 Stage 1 inventory,
``reports/grok/DECKER_N8N_MIGRATION.md`` §0). Nothing was firing, so "absorb"
means *recording ownership*, not hot-swapping a live timer. Two rows still need
distinct labels, because the honest situations differ:

- ``ahos_02`` has a genuine, running Python mirror — the canonical decision
  authority runs every daemon cycle. ``MIGRATED_ALREADY_RUNNING``.
- ``ahos_01``'s *shape* (periodic fetch -> integrity gate -> upsert -> audit ->
  alert) is superseded by the daemon's 60s cycles, but its specific write leg
  (OHLCV into the Postgres ``market_data`` table) has **no Python consumer** —
  grep for ``market_data`` over ``.py``/``.ts`` hits only providers, tools and
  tests, never ``db/`` or ``app/``. That table retired with Postgres.
  ``CADENCE_SUPERSEDED_NOT_REIMPLEMENTED`` records the shape as covered and the
  write leg as deliberately dropped, so nobody later "restores" a leg that had
  no reader.

Quarantine
----------
``ahos_03_telegram_control.json`` is GM-06 quarantined. The single source of
truth for that is ``tests/validate_n8n.py::QUARANTINED_WORKFLOWS``; this
registry **cross-references** it and never re-declares it, so the quarantine
cannot drift between two places. The test asserts the two agree.

Sequencing trap
---------------
``config/paths.py::get_n8n_workflows_dir()`` is this registry's read path, and
the coverage test derives the workflow set from it. The workflow JSONs do not
move until Stage 5's archive step; when they do, ``get_n8n_workflows_dir()``,
this registry's evidence paths and ``engine/doc_hygiene.py`` must move in the
**same commit**, or a green coverage test becomes a silent lie.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from importlib.util import find_spec
from pathlib import Path
from typing import Literal

from config.paths import get_n8n_workflows_dir


class MigrationStatus(Enum):
    """Why a retired n8n cadence does or does not have a running Python owner."""

    MIGRATED_ALREADY_RUNNING = "MIGRATED_ALREADY_RUNNING"
    # Python home exists AND is executed by the daemon today.

    CADENCE_SUPERSEDED_NOT_REIMPLEMENTED = "CADENCE_SUPERSEDED_NOT_REIMPLEMENTED"
    # A higher-frequency Python cycle covers the cadence's shape; the
    # n8n-specific write target had no consumer and is retired, not mirrored.

    MAPPED_EXECUTION_DEFERRED_TO_M44 = "MAPPED_EXECUTION_DEFERRED_TO_M44"
    # Owner recorded as exact CLI argv; wiring the run is M44's job
    # (AHOS_AUTONOMOUS_VISION.md §14.10.0).

    QUARANTINED_NEVER_REIMPLEMENTED = "QUARANTINED_NEVER_REIMPLEMENTED"
    # GM-06: must never be re-implemented 1:1. No owner, by design.


@dataclass(frozen=True)
class N8nCadence:
    """A trigger cadence, transcribed from the n8n scheduleTrigger dialect.

    ``raw_rule`` is the verbatim n8n ``rule`` object so the record round-trips
    through ``parse_n8n_schedule_rule``; that is what keeps the registry
    provably derived from the workflow files rather than from memory.
    """

    kind: Literal["interval", "daily", "weekly"]
    interval_sec: float | None = None
    # kind == "interval". Always recorded, even when a successor deliberately
    # does not reproduce it (see the :05 slot on ahos_02).
    time_of_day_utc: tuple[int, int] | None = None
    # (hour, minute); daily | weekly. n8n triggerAtHour/triggerAtMinute.
    day_of_week_utc: int | None = None
    # 0=Sunday..6=Saturday (n8n triggerAtDay); weekly only.
    raw_rule: tuple = ()
    # Verbatim n8n rule, frozen as a tuple so the dataclass stays hashable.


@dataclass(frozen=True)
class N8nMigrationEntry:
    """One retired n8n workflow and its Python successor surface."""

    workflow_id: str
    # Exact filename, e.g. "ahos_10_research_lab.json".
    workflow_name: str
    # "AHOS-10 Research Lab (weekly validation battery)".
    trigger_type: str
    # "scheduleTrigger" | "telegramTrigger".
    cadence: N8nCadence | None
    # None only for the event-driven quarantined entry.
    owner_kind: Literal["python_module_callable", "python_cli"] | None
    owner_module: str | None
    # find_spec-checked at validation, never imported by this registry.
    owner_callable: str | None
    # "ObservationRuntime.run_cycle".
    owner_cli: tuple[str, ...] | None
    # ("python3", "engine/acquire_3yr.py", "--start", "2023-01-01").
    status: MigrationStatus
    successor_note: str
    # Mandatory, non-empty: what replaced it AND, where relevant, what did not.
    evidence: str
    # File:line citations proving the successor is real.


N8N_MIGRATION_REGISTRY: tuple[N8nMigrationEntry, ...] = (
    N8nMigrationEntry(
        workflow_id="ahos_01_data_ingest_integrity.json",
        workflow_name="AHOS-01 Data Ingest + Integrity Gate",
        trigger_type="scheduleTrigger",
        cadence=N8nCadence(
            kind="interval",
            interval_sec=3600.0,
            raw_rule=({"interval": [{"field": "hours", "hoursInterval": 1}]},),
        ),
        owner_kind="python_module_callable",
        owner_module="architecture.runtime.observation_loop",
        owner_callable="ObservationRuntime.run_cycle",
        owner_cli=None,
        status=MigrationStatus.CADENCE_SUPERSEDED_NOT_REIMPLEMENTED,
        successor_note=(
            "Shape (periodic fetch -> integrity/coverage gate -> audit -> "
            "alert-on-failure) is superseded at HIGHER frequency by the "
            "daemon's 60s OPPORTUNITY_CYCLE and --observation-cycle tasks, "
            "which run CollectorEngine.collect_candidates and "
            "ObservationRuntime.run_cycle. The n8n workflow's specific write "
            "leg — OHLCV upserted into the Postgres market_data table — is "
            "NOT reimplemented: that table has zero Python/TypeScript readers "
            "(only providers/tools/tests reference it) and retired with "
            "Postgres in M10. This is a deliberate non-reimplementation, not "
            "an oversight."
        ),
        evidence=(
            "architecture/runtime/__main__.py:448-528 (tasks), :319 "
            "(--interval-sec default 60); architecture/runtime/observation_loop.py:184-215 "
            "(run_cycle + gate.check + DEGRADED accounting); "
            "architecture/pipeline/orchestrator.py:101 (collect_candidates)"
        ),
    ),
    N8nMigrationEntry(
        workflow_id="ahos_02_signal_pipeline.json",
        workflow_name="AHOS-02 Signal + Risk Gate Pipeline",
        trigger_type="scheduleTrigger",
        cadence=N8nCadence(
            kind="interval",
            interval_sec=3600.0,
            raw_rule=({
                "interval": [
                    {"field": "hours", "hoursInterval": 1, "minutesPastTheHour": 5}
                ]
            },),
        ),
        owner_kind="python_module_callable",
        owner_module="engine.dryrun_simulation",
        owner_callable="signal_eval",
        owner_cli=None,
        status=MigrationStatus.MIGRATED_ALREADY_RUNNING,
        successor_note=(
            "The Strategy+Risk Gate node logic is mirrored in "
            "engine/dryrun_simulation.signal_eval (kill_switch_active -> "
            "NO_TRADE) and executed authoritatively every 60s as the canonical "
            "decision authority inside OPPORTUNITY_CYCLE (identity -> security "
            "-> score -> decision). The n8n :05-past-the-hour offset is "
            "deliberately NOT reproduced: n8n needed it only because its "
            "trigger fired discretely once per hour; the Python home is a "
            "continuous 60s daemon, so restoring a slot would be an artifact, "
            "not a feature."
        ),
        evidence=(
            "engine/dryrun_simulation.py:25-33 (docstring: 'Mirror of n8n "
            "Strategy+Risk Gate node logic', kill_switch_active -> NO_TRADE); "
            "architecture/pipeline/orchestrator.py:193-201 "
            "(decision_authority.decide); architecture/runtime/__main__.py:513-519"
        ),
    ),
    N8nMigrationEntry(
        workflow_id="ahos_03_telegram_control.json",
        workflow_name="AHOS-03 Telegram Control + Kill Switch",
        trigger_type="telegramTrigger",
        cadence=None,
        owner_kind=None,
        owner_module=None,
        owner_callable=None,
        owner_cli=None,
        status=MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED,
        successor_note=(
            "GM-06 quarantine (2026-10-02): external Telegram input "
            "interpolated into SQL, audit-row DELETE on /reset, /approve "
            "mutating trade_decisions.execution_status outside the canonical "
            "decision authority. Never re-implemented 1:1. The safe, "
            "read-only interaction surfaces already live in run_bot.py; the "
            "kill switch is M39; human-gate routing stays with the Canonical "
            "Decision Authority."
        ),
        evidence=(
            "tests/validate_n8n.py:18-24 (QUARANTINED_WORKFLOWS, the single "
            "quarantine truth); reports/grok/GM06_N8N_QUARANTINE.md"
        ),
    ),
    N8nMigrationEntry(
        workflow_id="ahos_10_research_lab.json",
        workflow_name="AHOS-10 Research Lab (weekly validation battery)",
        trigger_type="scheduleTrigger",
        cadence=N8nCadence(
            kind="weekly",
            interval_sec=None,
            time_of_day_utc=(3, 0),
            day_of_week_utc=0,
            raw_rule=({
                "interval": [
                    {
                        "field": "weeks",
                        "weeksInterval": 1,
                        "triggerAtDay": [0],
                        "triggerAtHour": 3,
                        "triggerAtMinute": 0,
                    }
                ]
            },),
        ),
        owner_kind="python_cli",
        owner_module=None,
        owner_callable=None,
        owner_cli=("python3", "strategy_lab/run_lab.py"),
        status=MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44,
        successor_note=(
            "Weekly Sunday 03:00 UTC battery. The n8n node ran "
            "'cd /opt/ahos && python3 strategy_lab/run_lab.py 2>&1 | tail -40'; "
            "the exact argv is recorded above so M44's wiring is a lookup, not "
            "an archaeology project. M10 records only; M44 adds the run."
        ),
        evidence="strategy_lab/run_lab.py (exists, defines main() at :96)",
    ),
    N8nMigrationEntry(
        workflow_id="ahos_11_data_update.json",
        workflow_name="AHOS-11 Research Data Update (nightly incremental)",
        trigger_type="scheduleTrigger",
        cadence=N8nCadence(
            kind="daily",
            interval_sec=None,
            time_of_day_utc=(4, 15),
            day_of_week_utc=None,
            raw_rule=({
                "interval": [
                    {"field": "days", "daysInterval": 1, "triggerAtHour": 4, "triggerAtMinute": 15}
                ]
            },),
        ),
        owner_kind="python_cli",
        owner_module=None,
        owner_callable=None,
        owner_cli=(
            "python3", "engine/acquire_3yr.py", "--start", "2023-01-01",
            "&&", "python3", "engine/data_audit.py", "research/data",
        ),
        status=MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44,
        successor_note=(
            "Nightly 04:15 UTC incremental acquire plus integrity re-check. "
            "Recorded as exact argv from the two n8n executeCommand nodes. The "
            "third n8n node was an inline pandas re-scan of "
            "research/data/*_1h_3yr.csv; engine/data_audit.py already covers "
            "the same integrity role, so the inline snippet is not carried "
            "forward. M44 wires the run."
        ),
        evidence="engine/acquire_3yr.py, engine/data_audit.py (both exist)",
    ),
    N8nMigrationEntry(
        workflow_id="ahos_12_research_report.json",
        workflow_name="AHOS-12 Research Report (weekly digest from registry)",
        trigger_type="scheduleTrigger",
        cadence=N8nCadence(
            kind="weekly",
            interval_sec=None,
            time_of_day_utc=(6, 0),
            day_of_week_utc=0,
            raw_rule=({
                "interval": [
                    {
                        "field": "weeks",
                        "weeksInterval": 1,
                        "triggerAtDay": [0],
                        "triggerAtHour": 6,
                        "triggerAtMinute": 0,
                    }
                ]
            },),
        ),
        owner_kind="python_cli",
        owner_module=None,
        owner_callable=None,
        owner_cli=("python3", "engine/research_report_bot.py"),
        status=MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44,
        successor_note=(
            "Weekly Sunday 06:00 UTC digest. The n8n node ran "
            "'cd /opt/ahos && python3 engine/research_report_bot.py 2>&1 | tail -30'. "
            "Recorded as CLI form (module form would also resolve — main() "
            "exists at :47 — but CLI keeps the three deferred rows uniform, "
            "which is what makes the M44 boundary structurally enforceable)."
        ),
        evidence="engine/research_report_bot.py (exists, defines main() at :47)",
    ),
)


# --------------------------------------------------------------------------
# Pure accessors. No DB, no network, no file writes, no execution.
# --------------------------------------------------------------------------

def all_entries() -> tuple[N8nMigrationEntry, ...]:
    """The full registry, order-stable."""
    return N8N_MIGRATION_REGISTRY


def entry_for(workflow_id: str) -> N8nMigrationEntry | None:
    """Lookup by exact workflow filename, or None."""
    for e in N8N_MIGRATION_REGISTRY:
        if e.workflow_id == workflow_id:
            return e
    return None


def executable_entries() -> tuple[N8nMigrationEntry, ...]:
    """Everything except the quarantined row.

    The quarantined workflow has no owner by design; it must never appear in a
    set that a caller treats as runnable.
    """
    return tuple(
        e for e in N8N_MIGRATION_REGISTRY
        if e.status is not MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED
    )


def parse_n8n_schedule_rule(rule: dict | tuple) -> N8nCadence:
    """The single place the n8n scheduleTrigger ``rule`` dialect is read.

    n8n expresses every cadence as ``rule.interval[0]`` with a ``field`` of
    ``seconds``/``minutes``/``hours``/``days``/``weeks``; time-of-day and
    day-of-week are optional refinements on the day/week fields. Kept
    deliberately narrow to exactly the six dialects AHOS shipped: broadening it
    would be speculative support for workflows that do not exist here.
    """
    if isinstance(rule, tuple) and len(rule) == 1:
        rule = rule[0]
    if not isinstance(rule, dict):
        raise ValueError(f"n8n rule must be a dict, got {type(rule).__name__}")
    intervals = rule.get("interval")
    if not isinstance(intervals, list) or not intervals:
        raise ValueError("n8n rule missing 'interval' list")
    iv = intervals[0]
    if not isinstance(iv, dict) or "field" not in iv:
        raise ValueError("n8n rule.interval[0] missing 'field'")

    field = iv["field"]
    raw = (rule,) if isinstance(rule, dict) else rule

    if field == "seconds":
        return N8nCadence(kind="interval", interval_sec=float(iv.get("secondsInterval", 1)), raw_rule=raw)
    if field == "minutes":
        return N8nCadence(kind="interval", interval_sec=float(iv.get("minutesInterval", 1)) * 60.0, raw_rule=raw)
    if field == "hours":
        return N8nCadence(kind="interval", interval_sec=float(iv.get("hoursInterval", 1)) * 3600.0, raw_rule=raw)
    if field == "days":
        hour, minute = int(iv.get("triggerAtHour", 0)), int(iv.get("triggerAtMinute", 0))
        return N8nCadence(kind="daily", time_of_day_utc=(hour, minute), raw_rule=raw)
    if field == "weeks":
        days = iv.get("triggerAtDay") or [0]
        hour, minute = int(iv.get("triggerAtHour", 0)), int(iv.get("triggerAtMinute", 0))
        return N8nCadence(
            kind="weekly",
            time_of_day_utc=(hour, minute),
            day_of_week_utc=int(days[0]),
            raw_rule=raw,
        )
    raise ValueError(f"unsupported n8n interval field: {field!r}")


# --------------------------------------------------------------------------
# Validation. Static, side-effect-free, safe in a bare interpreter.
# --------------------------------------------------------------------------

def _owner_target_errors(entry: N8nMigrationEntry) -> list[str]:
    """Resolve the recorded owner WITHOUT importing or executing it.

    ``find_spec`` resolves a module to its file without executing the leaf
    module, so a check here cannot accidentally pull pandas/numpy or otherwise
    mutate state. That matters because ``engine/`` and ``strategy_lab/`` are
    namespace packages whose modules have heavyweight imports.
    """
    errs: list[str] = []
    if entry.status is MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED:
        if any(
            v is not None
            for v in (entry.owner_kind, entry.owner_module, entry.owner_callable, entry.owner_cli)
        ):
            errs.append(
                f"{entry.workflow_id}: quarantined entry must carry no owner "
                f"(a runnable owner would contradict the quarantine)"
            )
        return errs

    if entry.status is MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44:
        # Deferred rows record exact CLI argv and deliberately no callable: a
        # callable would mean the cadence is wired, which is M44's scope.
        if entry.owner_module is not None or entry.owner_callable is not None:
            errs.append(
                f"{entry.workflow_id}: a DEFERRED row must not carry a module "
                f"callable (that would mean it is wired)"
            )
        if entry.owner_cli is None or not entry.owner_cli:
            errs.append(f"{entry.workflow_id}: a DEFERRED row must record owner_cli argv")
        else:
            script = Path(entry.owner_cli[1])
            if not script.is_file():
                errs.append(f"{entry.workflow_id}: deferred CLI target does not exist: {script}")
        return errs

    # MIGRATED_ALREADY_RUNNING / CADENCE_SUPERSEDED_NOT_REIMPLEMENTED
    if entry.owner_kind != "python_module_callable":
        errs.append(f"{entry.workflow_id}: expected owner_kind python_module_callable")
        return errs
    if not entry.owner_module or not entry.owner_callable:
        errs.append(f"{entry.workflow_id}: missing owner_module/owner_callable")
        return errs
    try:
        spec = find_spec(entry.owner_module)
    except Exception as exc:  # ImportError family, or a parent without __init__
        errs.append(f"{entry.workflow_id}: owner_module {entry.owner_module!r} unresolvable: {exc}")
        return errs
    if spec is None or spec.origin is None:
        errs.append(f"{entry.workflow_id}: owner_module {entry.owner_module!r} has no origin")
        return errs
    if not Path(spec.origin).is_file():
        errs.append(f"{entry.workflow_id}: owner_module origin is not a file: {spec.origin}")
        return errs
    # Prove the callable is real WITHOUT importing it: an AST scan of the
    # owner module's source. This is what keeps the check honest in a bare
    # interpreter -- engine.dryrun_simulation pulls pandas/numpy on import, so
    # importing to validate would make the registry's soundness depend on the
    # environment instead of on the repository.
    if not _callable_exists_in_source(Path(spec.origin), entry.owner_callable):
        errs.append(
            f"{entry.workflow_id}: owner_callable {entry.owner_callable!r} not defined "
            f"in {spec.origin}"
        )
    return errs


def _callable_exists_in_source(path: Path, qualified: str) -> bool:
    """True if 'Class.method' or a top-level 'function' is defined in ``path``.

    Parsed, never executed, never imported.
    """
    import ast

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if "." not in qualified:
        return any(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == qualified
            for n in tree.body
        )
    cls_name, _, method_name = qualified.partition(".")
    cls = next(
        (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls_name),
        None,
    )
    if cls is None:
        return False
    return any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method_name
        for n in cls.body
    )


def validate_registry() -> list[str]:
    """Human-readable soundness errors for the registry. Empty list = sound.

    Deliberately touches no store: pointed at a redirected ``AHOS_DATA_DIR`` in
    the test to prove it, so a registry check can never become a DB write.
    """
    errs: list[str] = []

    ids = [e.workflow_id for e in N8N_MIGRATION_REGISTRY]
    if len(ids) != len(set(ids)):
        errs.append(f"duplicate workflow_id in registry: {sorted(i for i in ids if ids.count(i) > 1)}")

    # Coverage: every shipped workflow JSON is registered exactly once, and no
    # registry row points at a file that is not shipped. Derived from the
    # helper, not listed, so a seventh JSON can never be silently unregistered.
    shipped: set[str]
    try:
        shipped = {p.name for p in get_n8n_workflows_dir().glob("*.json")}
    except Exception as exc:
        errs.append(f"cannot list n8n workflows dir: {exc}")
        shipped = set()
    if shipped:
        missing = sorted(shipped - set(ids))
        extra = sorted(set(ids) - shipped)
        if missing:
            errs.append(f"shipped workflows missing from registry: {missing}")
        if extra:
            errs.append(f"registry rows without a shipped workflow file: {extra}")

    for e in N8N_MIGRATION_REGISTRY:
        if not e.successor_note or not e.successor_note.strip():
            errs.append(f"{e.workflow_id}: successor_note must be non-empty")
        if not e.evidence or not e.evidence.strip():
            errs.append(f"{e.workflow_id}: evidence must be non-empty")
        if not e.workflow_name or not e.trigger_type:
            errs.append(f"{e.workflow_id}: workflow_name and trigger_type required")

        if e.cadence is None:
            if e.trigger_type != "telegramTrigger":
                errs.append(
                    f"{e.workflow_id}: cadence is None but trigger_type is "
                    f"{e.trigger_type!r} (only the event-driven quarantined row "
                    f"has no cadence)"
                )
        else:
            # The recorded cadence must re-parse from its own verbatim rule.
            try:
                reparsed = parse_n8n_schedule_rule(e.cadence.raw_rule)
            except Exception as exc:
                errs.append(f"{e.workflow_id}: cadence.raw_rule fails to re-parse: {exc}")
                reparsed = None
            if reparsed is not None and reparsed != e.cadence:
                errs.append(
                    f"{e.workflow_id}: cadence does not round-trip through "
                    f"parse_n8n_schedule_rule (recorded {e.cadence} vs parsed {reparsed})"
                )

        # Cross-check the recorded trigger against the actual workflow JSON, so
        # the registry is provably built from the files and not from memory.
        path = get_n8n_workflows_dir() / e.workflow_id
        if path.is_file():
            try:
                wf = json.loads(path.read_text(encoding="utf-8"))
                found = [
                    n.get("type", "")
                    for n in wf.get("nodes", [])
                    if "Trigger" in n.get("type", "")
                ]
                # scheduleTrigger / telegramTrigger / n8nTrigger all contain
                # "Trigger"; the registry records the primary one.
                if e.trigger_type not in found and not any(
                    t.endswith(e.trigger_type) for t in found
                ):
                    errs.append(
                        f"{e.workflow_id}: recorded trigger_type "
                        f"{e.trigger_type!r} not found in workflow nodes {found}"
                    )
                if e.cadence is not None:
                    sched = [
                        n for n in wf.get("nodes", [])
                        if n.get("type") == "n8n-nodes-base.scheduleTrigger"
                    ]
                    if not sched:
                        errs.append(f"{e.workflow_id}: workflow has no scheduleTrigger node")
                    else:
                        actual = sched[0].get("parameters", {}).get("rule")
                        expected = (
                            e.cadence.raw_rule[0]
                            if isinstance(e.cadence.raw_rule, tuple) and e.cadence.raw_rule
                            else e.cadence.raw_rule
                        )
                        if actual != expected:
                            errs.append(
                                f"{e.workflow_id}: recorded cadence rule does not "
                                f"match the workflow's scheduleTrigger rule"
                            )
            except Exception as exc:
                errs.append(f"{e.workflow_id}: cannot read/parse workflow JSON: {exc}")

        errs.extend(_owner_target_errors(e))

    return errs


def registry_summary() -> dict[str, object]:
    """Counts by status, for reporting. Non-exhaustive summary, not a check."""
    counts: dict[str, int] = {}
    for e in N8N_MIGRATION_REGISTRY:
        counts[e.status.value] = counts.get(e.status.value, 0) + 1
    return {
        "total_workflows": len(N8N_MIGRATION_REGISTRY),
        "by_status": counts,
        "schedulable_kinds": sorted({
            e.cadence.kind for e in N8N_MIGRATION_REGISTRY if e.cadence is not None
        }),
    }


__all__ = [
    "MigrationStatus",
    "N8nCadence",
    "N8nMigrationEntry",
    "N8N_MIGRATION_REGISTRY",
    "all_entries",
    "entry_for",
    "executable_entries",
    "parse_n8n_schedule_rule",
    "validate_registry",
    "registry_summary",
]


def _self_check() -> None:
    """``python3 -m architecture.scheduling.n8n_migration`` — static report."""
    errs = validate_registry()
    print(f"registry: {len(N8N_MIGRATION_REGISTRY)} workflows")
    print(json.dumps(registry_summary(), indent=2, ensure_ascii=False))
    for e in N8N_MIGRATION_REGISTRY:
        print(f"  [{e.status.value}] {e.workflow_id}")
    if errs:
        print(f"\nINVALID — {len(errs)} problem(s):")
        for e in errs:
            print(f"  - {e}")
        raise SystemExit(1)
    print("\nOK — registry is sound (static checks only; nothing imported or executed)")


if __name__ == "__main__":
    _self_check()
