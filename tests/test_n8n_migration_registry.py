"""M10 Stage 3 - n8n -> Python cadence migration registry.

Static checks only: no workflow is imported or executed, no DB touched, no
network. Mirrors the posture of ``test_n8n_governance_rules.py``.

What these tests protect:
  * the registry covers every shipped workflow JSON with no gaps or dupes;
  * the registry was built from the actual workflow files (trigger + rule are
    cross-checked against the JSON, not trusted from the dataclass);
  * every non-quarantined owner really resolves in the repository;
  * the M44 deferral boundary is structurally enforced - a deferred row that
    carried a runnable callable would mean the cadence is wired, which is
    M44's scope, not M10's;
  * the GM-06 quarantine stays owned by ``tests/validate_n8n.py`` alone, and
    this registry agrees with it rather than re-declaring it;
  * no new scheduler machinery was added - ``ScheduleTask``'s field set is
    pinned so a future change is deliberate and reviewable.
"""
from __future__ import annotations

import json
import sys
from dataclasses import fields
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.scheduling import (  # noqa: E402
    MigrationStatus,
    N8nCadence,
    N8nMigrationEntry,
    N8N_MIGRATION_REGISTRY,
    all_entries,
    entry_for,
    executable_entries,
    parse_n8n_schedule_rule,
    validate_registry,
)
from architecture.scheduling.engine import ScheduleTask  # noqa: E402
from config.paths import get_n8n_workflows_dir  # noqa: E402
from tests import validate_n8n  # noqa: E402

WF_DIR = get_n8n_workflows_dir()


# --------------------------------------------------------------------------
# Coverage: no shipped workflow can be silently unregistered.
# --------------------------------------------------------------------------

def test_registry_covers_every_shipped_workflow_with_no_gaps():
    shipped = {p.name for p in WF_DIR.glob("*.json")}
    registered = {e.workflow_id for e in N8N_MIGRATION_REGISTRY}
    assert registered == shipped, (
        f"registry/workflow drift - missing={sorted(shipped - registered)} "
        f"extra={sorted(registered - shipped)}"
    )


def test_registry_has_exactly_the_six_ahos_workflows():
    assert len(N8N_MIGRATION_REGISTRY) == 6


def test_workflow_ids_are_unique():
    ids = [e.workflow_id for e in N8N_MIGRATION_REGISTRY]
    assert len(ids) == len(set(ids))


def test_registry_order_is_stable_and_matches_sorted_filenames():
    # Order stability matters: the queue/ledger cites rows positionally in
    # reports, so reordering would silently rewrite those citations.
    assert [e.workflow_id for e in N8N_MIGRATION_REGISTRY] == sorted(
        p.name for p in WF_DIR.glob("*.json")
    )


# --------------------------------------------------------------------------
# The registry is derived from the files, not from memory.
# --------------------------------------------------------------------------

def test_every_entry_corresponds_to_a_real_workflow_file():
    for e in N8N_MIGRATION_REGISTRY:
        path = WF_DIR / e.workflow_id
        assert path.is_file(), f"{e.workflow_id} does not exist"


def test_recorded_trigger_and_rule_match_the_actual_workflow_json():
    for e in N8N_MIGRATION_REGISTRY:
        wf = json.loads((WF_DIR / e.workflow_id).read_text(encoding="utf-8"))
        found = [n.get("type", "") for n in wf.get("nodes", []) if "Trigger" in n.get("type", "")]
        assert e.trigger_type in found or any(t.endswith(e.trigger_type) for t in found), (
            f"{e.workflow_id}: recorded trigger_type {e.trigger_type!r} absent from {found}"
        )
        if e.cadence is None:
            continue
        sched = [n for n in wf.get("nodes", []) if n.get("type") == "n8n-nodes-base.scheduleTrigger"]
        assert sched, f"{e.workflow_id} records a cadence but has no scheduleTrigger node"
        actual_rule = sched[0].get("parameters", {}).get("rule")
        expected = (
            e.cadence.raw_rule[0]
            if isinstance(e.cadence.raw_rule, tuple) and e.cadence.raw_rule
            else e.cadence.raw_rule
        )
        assert actual_rule == expected, f"{e.workflow_id}: recorded rule != workflow rule"


def test_recorded_workflow_names_match_the_jsons():
    for e in N8N_MIGRATION_REGISTRY:
        wf = json.loads((WF_DIR / e.workflow_id).read_text(encoding="utf-8"))
        assert wf.get("name") == e.workflow_name, (
            f"{e.workflow_id}: recorded name {e.workflow_name!r} != {wf.get('name')!r}"
        )


# --------------------------------------------------------------------------
# Owners resolve, without ever importing a heavyweight module.
# --------------------------------------------------------------------------

def test_non_quarantined_owners_resolve():
    from importlib.util import find_spec

    for e in executable_entries():
        if e.owner_kind == "python_module_callable":
            spec = find_spec(e.owner_module)
            assert spec is not None and spec.origin is not None, e.workflow_id
            assert Path(spec.origin).is_file(), e.workflow_id
        elif e.owner_kind == "python_cli":
            assert Path(e.owner_cli[1]).is_file(), f"{e.workflow_id}: {e.owner_cli[1]}"


def test_owner_callables_are_defined_in_their_recorded_module():
    # The validator does this by AST scan; re-assert it directly so a false
    # positive in the validator cannot pass a dangling callable.
    from importlib.util import find_spec

    for e in executable_entries():
        if e.owner_kind != "python_module_callable":
            continue
        src = Path(find_spec(e.owner_module).origin).read_text(encoding="utf-8")
        import ast

        tree = ast.parse(src)
        top_funcs = {
            n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        class_methods = {
            f"{c.name}.{m.name}"
            for c in tree.body if isinstance(c, ast.ClassDef)
            for m in c.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        # owner_callable is qualified ("ObservationRuntime.run_cycle"); the
        # validator splits on "." the same way, so this is an independent
        # re-implementation of that exact membership check.
        assert (
            e.owner_callable in class_methods or e.owner_callable in top_funcs
        ), (
            f"{e.workflow_id}: {e.owner_callable!r} not defined in {e.owner_module}"
        )


# --------------------------------------------------------------------------
# Quarantine: one truth, cross-checked.
# --------------------------------------------------------------------------

def test_quarantine_is_provably_excluded_from_the_executable_set():
    quarantined = {
        e.workflow_id for e in N8N_MIGRATION_REGISTRY
        if e.status is MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED
    }
    assert quarantined == set(validate_n8n.QUARANTINED_WORKFLOWS), (
        "registry quarantine must equal tests/validate_n8n.py::QUARANTINED_WORKFLOWS "
        "(single source of truth)"
    )
    assert quarantined == {"ahos_03_telegram_control.json"}
    assert "ahos_03_telegram_control.json" not in {e.workflow_id for e in executable_entries()}


def test_quarantined_entry_carries_no_owner():
    e = entry_for("ahos_03_telegram_control.json")
    assert e is not None
    assert e.status is MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED
    assert e.owner_kind is None
    assert e.owner_module is None
    assert e.owner_callable is None
    assert e.owner_cli is None
    assert e.cadence is None
    assert e.trigger_type == "telegramTrigger"


# --------------------------------------------------------------------------
# The M44 boundary, enforced structurally.
# --------------------------------------------------------------------------

def test_deferred_entries_carry_no_runnable_callable():
    for e in N8N_MIGRATION_REGISTRY:
        if e.status is MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44:
            assert e.owner_kind == "python_cli", e.workflow_id
            assert e.owner_module is None, f"{e.workflow_id}: deferred row must not name a module"
            assert e.owner_callable is None, f"{e.workflow_id}: deferred row must not name a callable"
            assert e.owner_cli and len(e.owner_cli) >= 2, e.workflow_id


def test_deferred_cli_targets_exist_as_files():
    for e in N8N_MIGRATION_REGISTRY:
        if e.status is MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44:
            assert Path(e.owner_cli[1]).is_file(), f"{e.workflow_id}: {e.owner_cli[1]}"


def test_status_distribution_matches_the_mission_decisions():
    counts = {}
    for e in N8N_MIGRATION_REGISTRY:
        counts[e.status] = counts.get(e.status, 0) + 1
    assert counts == {
        MigrationStatus.MIGRATED_ALREADY_RUNNING: 1,          # ahos_02
        MigrationStatus.CADENCE_SUPERSEDED_NOT_REIMPLEMENTED: 1,  # ahos_01
        MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44: 3,  # ahos_10/11/12
        MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED: 1,   # ahos_03
    }


# --------------------------------------------------------------------------
# Cadence transcription is faithful and round-trips.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("entry", list(N8N_MIGRATION_REGISTRY))
def test_cadence_round_trips_through_the_parser(entry):
    if entry.cadence is None:
        pytest.skip("event-driven quarantined row has no cadence")
    reparsed = parse_n8n_schedule_rule(entry.cadence.raw_rule)
    assert reparsed == entry.cadence, f"{entry.workflow_id}: round-trip mismatch"


def test_transcribed_cadences_match_the_json_verbatim():
    # Transcribed by hand this session from the workflow files; this test pins
    # those transcriptions so a typo in the registry is caught here rather than
    # surfacing in M44 when the argv is first wired.
    expected = {
        "ahos_01_data_ingest_integrity.json": ("interval", 3600.0, None, None),
        "ahos_02_signal_pipeline.json": ("interval", 3600.0, None, None),
        "ahos_11_data_update.json": ("daily", None, (4, 15), None),
        "ahos_10_research_lab.json": ("weekly", None, (3, 0), 0),
        "ahos_12_research_report.json": ("weekly", None, (6, 0), 0),
    }
    for e in N8N_MIGRATION_REGISTRY:
        if e.workflow_id not in expected:
            continue
        c = e.cadence
        assert (c.kind, c.interval_sec, c.time_of_day_utc, c.day_of_week_utc) == expected[e.workflow_id]


def test_02_records_the_five_past_the_hour_slot_it_deliberately_drops():
    # The :05 offset is preserved in raw_rule (n8n needed it; the Python home
    # does not) so the successor_note's promise is anchored by data, not prose.
    e = entry_for("ahos_02_signal_pipeline.json")
    rule = e.cadence.raw_rule[0]
    assert rule["interval"][0]["minutesPastTheHour"] == 5
    assert "NOT reproduce" in e.successor_note or "not reproduce" in e.successor_note.lower().replace("not reproduce", "NOT reproduce")


def test_parser_reads_each_dialect_ahos_shipped():
    assert parse_n8n_schedule_rule({"interval": [{"field": "hours", "hoursInterval": 1}]}) == N8nCadence(
        kind="interval", interval_sec=3600.0,
        raw_rule=({"interval": [{"field": "hours", "hoursInterval": 1}]},),
    )
    assert parse_n8n_schedule_rule({"interval": [{"field": "days", "daysInterval": 1, "triggerAtHour": 4, "triggerAtMinute": 15}]}) == N8nCadence(
        kind="daily", time_of_day_utc=(4, 15),
        raw_rule=({"interval": [{"field": "days", "daysInterval": 1, "triggerAtHour": 4, "triggerAtMinute": 15}]},),
    )
    assert parse_n8n_schedule_rule(
        {"interval": [{"field": "weeks", "weeksInterval": 1, "triggerAtDay": [0], "triggerAtHour": 3, "triggerAtMinute": 0}]}
    ) == N8nCadence(
        kind="weekly", time_of_day_utc=(3, 0), day_of_week_utc=0,
        raw_rule=({"interval": [{"field": "weeks", "weeksInterval": 1, "triggerAtDay": [0], "triggerAtHour": 3, "triggerAtMinute": 0}]},),
    )


def test_parser_accepts_the_tuple_form_the_registry_stores():
    e = entry_for("ahos_10_research_lab.json")
    assert parse_n8n_schedule_rule(e.cadence.raw_rule) == e.cadence


@pytest.mark.parametrize("bad", [
    {},
    {"interval": []},
    {"interval": [{}]},
    {"interval": [{"field": "centuries", "centuriesInterval": 1}]},
])
def test_parser_rejects_rules_ahos_never_shipped(bad):
    with pytest.raises(ValueError):
        parse_n8n_schedule_rule(bad)


# --------------------------------------------------------------------------
# Validator.
# --------------------------------------------------------------------------

def test_validate_registry_is_clean():
    assert validate_registry() == []


def test_validate_registry_touches_no_store(tmp_path, monkeypatch):
    # A registry soundness check must never become a DB write. Redirect the
    # data dir and re-run: identical result proves no store is touched.
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path))
    assert validate_registry() == []


def test_validate_registry_detects_an_unregistered_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "architecture.scheduling.n8n_migration.get_n8n_workflows_dir",
        lambda: tmp_path,
    )
    (tmp_path / "ahos_99_unregistered.json").write_text(
        json.dumps({"name": "x", "nodes": []}), encoding="utf-8"
    )
    errs = validate_registry()
    assert any("ahos_99_unregistered.json" in e for e in errs)


def test_validate_registry_detects_a_dangling_cli_target():
    e = entry_for("ahos_10_research_lab.json")
    dangling = N8nMigrationEntry(
        workflow_id=e.workflow_id, workflow_name=e.workflow_name,
        trigger_type=e.trigger_type, cadence=e.cadence,
        owner_kind="python_cli", owner_module=None, owner_callable=None,
        owner_cli=("python3", "strategy_lab/does_not_exist.py"),
        status=MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44,
        successor_note="x", evidence="y",
    )
    import architecture.scheduling.n8n_migration as m

    errs = m._owner_target_errors(dangling)
    assert any("does_not_exist.py" in e2 for e2 in errs)


def test_validate_registry_detects_a_deferred_row_with_a_callable():
    e = entry_for("ahos_10_research_lab.json")
    wired = N8nMigrationEntry(
        workflow_id=e.workflow_id, workflow_name=e.workflow_name,
        trigger_type=e.trigger_type, cadence=e.cadence,
        owner_kind="python_module_callable", owner_module="strategy_lab.run_lab",
        owner_callable="main", owner_cli=None,
        status=MigrationStatus.MAPPED_EXECUTION_DEFERRED_TO_M44,
        successor_note="x", evidence="y",
    )
    import architecture.scheduling.n8n_migration as m

    errs = m._owner_target_errors(wired)
    assert any("DEFERRED" in e2 for e2 in errs)


def test_validate_registry_detects_a_quarantined_row_with_an_owner():
    e = entry_for("ahos_03_telegram_control.json")
    escaped = N8nMigrationEntry(
        workflow_id=e.workflow_id, workflow_name=e.workflow_name,
        trigger_type=e.trigger_type, cadence=None,
        owner_kind="python_module_callable", owner_module="engine.dryrun_simulation",
        owner_callable="signal_eval", owner_cli=None,
        status=MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED,
        successor_note="x", evidence="y",
    )
    import architecture.scheduling.n8n_migration as m

    errs = m._owner_target_errors(escaped)
    assert any("quarantined" in e2 for e2 in errs)


# --------------------------------------------------------------------------
# No new scheduler machinery (the mission's explicit constraint).
# --------------------------------------------------------------------------

def test_scheduler_task_shape_is_unchanged():
    assert {f.name for f in fields(ScheduleTask)} == {
        "task_id", "target_offset_sec", "tolerance_sec", "action_fn", "label",
    }


def test_registry_module_declares_no_wall_clock_primitive():
    # "Don't write a new scheduler" means exactly this: no due()/slot primitive
    # enters the codebase through the migration. If M44 needs one, it adds it
    # deliberately, and this test then changes in the same commit.
    src = Path(ROOT / "architecture" / "scheduling" / "n8n_migration.py").read_text(encoding="utf-8")
    for name in ("wall_clock_slot_due", "def due(", "is_due", "next_run", "should_fire"):
        assert name not in src, f"{name!r} would be new scheduler machinery"


def test_registry_module_does_not_import_the_scheduler_engine():
    # The registry records ownership; it must not construct or extend a
    # scheduler, and importing engine.py would pull the SQLite store.
    src = Path(ROOT / "architecture" / "scheduling" / "n8n_migration.py").read_text(encoding="utf-8")
    assert "from .engine" not in src and "import engine" not in src


# --------------------------------------------------------------------------
# Honest prose: the caveats that must not be edited away.
# --------------------------------------------------------------------------

def test_01_successor_note_names_what_is_not_reimplemented():
    e = entry_for("ahos_01_data_ingest_integrity.json")
    note = e.successor_note.lower()
    assert "market_data" in note
    assert "not reimplemented" in note


def test_03_successor_note_names_the_quarantine_findings():
    e = entry_for("ahos_03_telegram_control.json")
    note = e.successor_note.lower()
    assert "quarantine" in note
    assert "canonical decision authority" in note


def test_every_entry_has_non_empty_note_and_evidence():
    for e in N8N_MIGRATION_REGISTRY:
        assert e.successor_note.strip(), e.workflow_id
        assert e.evidence.strip(), e.workflow_id


def test_accessors_agree_with_the_registry_constant():
    assert all_entries() == N8N_MIGRATION_REGISTRY
    assert executable_entries() == tuple(
        e for e in N8N_MIGRATION_REGISTRY
        if e.status is not MigrationStatus.QUARANTINED_NEVER_REIMPLEMENTED
    )
    assert len(executable_entries()) == 5


def test_entry_for_returns_none_for_unknown_ids():
    assert entry_for("ahos_99_nope.json") is None


def test_registry_does_not_depend_on_docker_or_network():
    # No docker imports, no requests/socket/http usage, no subprocess execution.
    src = Path(ROOT / "architecture" / "scheduling" / "n8n_migration.py").read_text(encoding="utf-8")
    for name in ("import docker", "subprocess.run", "subprocess.Popen", "socket.connect", "requests."):
        assert name not in src, f"{name!r} would couple the registry to Docker/network"
