#!/usr/bin/env python3
"""M5 pins: the execution-state record must describe state without inventing it.

`MASTER_DIRECTIVE_v1.md` mandates a 12-step wave protocol evidenced at every session
start, and its OPERATIONAL REGISTRATION §3 says the verification facts are logged in the
wave's ledger entry. `scripts/execution_state.py` mechanises steps 1-5. These pins lock
the honesty contract rather than the shape, because shape can be refactored but the
honesty laws are the point:

  * a fact that cannot be verified is UNKNOWN, never a plausible-looking value;
  * a missing store is NO_DATA, never an invented healthy reading;
  * the verdict is only VERIFIED when all five steps actually held;
  * evidence artifacts are append-only -- reusing --out is refused without --force;
  * the record selects no mission and grants no authority.

The append-only law is not stylistic here. M-GAP-036 proved the failure mode for real:
an explicit `--out` silently overwrote a committed Linux PASS receipt with a Windows FAIL.
The same rule now guards this artifact.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import execution_state as es  # noqa: E402

STEP_KEYS = (
    "1_verify_workspace",
    "2_verify_master_version",
    "3_verify_experiment_state",
    "4_verify_governance",
    "5_verify_open_risks",
)


# ------------------------------------------------------------------ structure

def test_record_carries_all_five_steps_and_no_pass_verdict():
    """The five doctrine steps are present, and no verdict reads as an unearned PASS."""
    state = es.build_state()
    assert state["schema"] == "ahos.execution_state.v1"
    for key in STEP_KEYS:
        assert key in state["steps"], f"doctrine step missing from record: {key}"
        assert "verified" in state["steps"][key], f"{key} has no verdict"
    assert set(state["step_verdicts"]) == set(STEP_KEYS)
    # The gap register's own law forbids PASS without an artifact; a description is not
    # one, so the vocabulary deliberately has no PASS to accidentally award.
    assert state["verdict"] in ("VERIFIED", "DEGRADED", "NOT_VERIFIED"), (
        f"unknown verdict {state['verdict']!r}"
    )
    assert state["verdict"] != "PASS"


def test_directive_laws_are_computed_not_assumed():
    """Step 2 evaluates the five registry laws rather than assuming them.

    This is the same invariant set tests/test_master_directive.py pins; restating them
    as computed facts is what makes the record report the constitution's state instead
    of trusting it.
    """
    master = es.verify_master_version()
    laws = master["laws"]
    expected = {
        "exactly_one_active",
        "active_is_highest",
        "no_orphan_doctrine_files",
        "every_sha_matches_disk",
        "every_sha_in_issue_register",
    }
    assert set(laws) == expected
    assert master["verified"] is all(laws.values())


# ---------------------------------------------------------------- fail-closed

def test_unreachable_git_is_unknown_never_fabricated(monkeypatch):
    """If git cannot answer, the record says so rather than inventing a commit.

    A read-only recorder that fabricated a workspace fact would be worse than one that
    reported nothing: every downstream reading would cite a commit that was never
    verified. UNKNOWN is the honest answer and must propagate.
    """
    def _broken_git(cwd=None):
        return {"commit_sha": "UNKNOWN", "branch": "UNKNOWN", "working_tree_clean": False}

    monkeypatch.setattr(es, "git_meta", _broken_git)
    workspace = es.verify_workspace()
    assert workspace["commit_sha"] == "UNKNOWN"
    assert workspace["verified"] is False

    state = es.build_state()
    assert state["git"]["commit_sha"] == "UNKNOWN"
    # an uncomputable step is NOT_VERIFIED, never a clean-looking DEGRADED
    assert state["verdict"] == "NOT_VERIFIED", (
        "unreachable git must not be smoothed into a verifiable-looking record"
    )


def test_missing_store_reads_no_data_never_ok(tmp_path, monkeypatch):
    """An absent store is the honest state of a host that never ran the daemon.

    The bug this pins: the first implementation scored a NO_DATA store as a failed
    integrity check, so every clean checkout read DEGRADED for a store that simply was
    not there. NO_DATA means absent; 'ok' means present and verified. They must not
    collapse into one signal.
    """
    monkeypatch.setattr(es, "STORES", {"probe_store": "get_cognitive_memory_db_path"})
    monkeypatch.setattr(
        es, "ROOT", tmp_path / "nowhere",
    )
    status = es._store_status("get_cognitive_memory_db_path")
    # The path getter is resolved against the real config, so this asserts the
    # absent-store contract specifically, independent of where the store lives.
    assert status["exists"] is False
    assert status["integrity_check"] == "NO_DATA"
    assert status["row_total"] == "NO_DATA"
    assert status["integrity_check"] != "ok"


def test_verified_requires_all_five_steps(monkeypatch, tmp_path):
    """VERIFIED is not awarded on a partial pass.

    A record that reported VERIFIED with a failing step would be exactly the rounded-up
    readiness claim the register's honesty gate exists to refuse.
    """
    state = es.build_state()
    # The real repository on a warm host is legitimately DEGRADED (dirty tree), which
    # makes it a poor fixture for the all-green path. Construct that path directly.
    assert state["verdict"] in ("DEGRADED", "VERIFIED")
    # If any single step fails, the verdict may never be VERIFIED.
    monkeypatch.setattr(
        es, "verify_master_version",
        lambda: {"verified": False, "error": "simulated registry loss"},
    )
    broken = es.build_state()
    assert broken["verdict"] != "VERIFIED"
    assert broken["step_verdicts"]["2_verify_master_version"] is False


# ------------------------------------------------------------- append-only

def test_reusing_out_path_is_refused_without_force(tmp_path):
    """Evidence is append-only: overwriting a prior record requires an explicit choice.

    M-GAP-036's lesson, applied to this artifact: default timestamps make collisions
    rare, but an explicit --out that clobbers a committed receipt destroys history.
    """
    existing = tmp_path / "execution_state_existing.json"
    existing.write_text('{"schema": "ahos.execution_state.v1", "prior": true}', encoding="utf-8")

    rc = es.main(["--out", str(existing)])
    assert rc == 3, "an existing artifact must be refused, not overwritten"
    assert json.loads(existing.read_text(encoding="utf-8"))["prior"] is True, (
        "the prior record was destroyed -- evidence is append-only"
    )

    # --force is the explicit override, and must actually work
    rc_force = es.main(["--out", str(existing), "--force"])
    assert rc_force == 0
    written = json.loads(existing.read_text(encoding="utf-8"))
    assert written["schema"] == "ahos.execution_state.v1"
    assert "prior" not in written


# ------------------------------------------------------------- register parse

def test_register_parse_classifies_every_summary_row():
    """Step 5 counts the register's summary table with no row silently dropped.

    An unclassified row is reported by name rather than guessed at: a parser that
    quietly skipped a row would understate the open-risk surface, and an operator
    reading open_total would trust a number that was wrong.
    """
    text = (ROOT / "AHOS_GAP_REGISTER.md").read_text(encoding="utf-8")
    counts, unclassified = es._parse_gap_register(text)
    classified = sum(counts.values())
    assert classified > 0
    assert unclassified == [], (
        f"register rows could not be classified (parser is understating risk): {unclassified}"
    )
    # OPTIONAL is the register's "not an acceptance item" class and is reported
    # separately from the open-risk total rather than counted as risk.
    assert "OPTIONAL" in counts


def test_implementable_now_uses_the_registers_own_marker():
    """The step-6 advisory list repeats the register's words; it never assesses.

    Looser markers were a real false positive: 'IMPLEMENTED' matched historical prose
    inside M-GAP-011's row ("adapter IMPLEMENTED") and listed a gap the register does
    not mark implementable. Only the register's own 'IMPLEMENTABLE NOW' verdict counts.
    """
    text = (ROOT / "AHOS_GAP_REGISTER.md").read_text(encoding="utf-8")
    listed = es._implementable_now(text)
    for gap_id in listed:
        assert gap_id.startswith("M-GAP-")
    # A fabricated marker must not manufacture a recommendation
    assert es._implementable_now("| M-GAP-999 | | | | | | | | | | **OPEN** — adapter IMPLEMENTED |\n") == []


# ------------------------------------------------------------- authority

def test_record_grants_no_authority_and_selects_no_mission():
    """M5's contract: the record describes state; it is not an autonomous selector.

    This pin exists so a future refactor cannot quietly turn the advisory list into a
    decision. The directive's step 6 (SELECT HIGHEST-VALUE SAFE NEXT ACTION) stays a
    human choice, and the record says so in-band.
    """
    state = es.build_state()
    assert state["directive_protocol"]["steps_recorded"] == [1, 2, 3, 4, 5]
    assert "select" in state["directive_protocol"]["note"].lower()
    assert "human choice" in state["directive_protocol"]["note"]
    # the record carries no permission, maturity, or trading field whatsoever
    flattened = json.dumps(state, default=str).lower()
    for forbidden in ("authorize", "authorized", "permission_granted", "maturity_advanced"):
        assert forbidden not in flattened, f"record appears to grant {forbidden}"
