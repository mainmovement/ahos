#!/usr/bin/env python3
"""Repository-backed execution-state recorder (M5).

`MASTER_DIRECTIVE_v1.md` (ratified by owner 2026-08-13, R-42, sha-pinned, CI-enforced)
mandates a 12-step wave protocol "executed and evidenced at every session/wave start
before any other work", and its OPERATIONAL REGISTRATION §3 says the verification facts
"are logged in the wave's ledger entry". That logging had never been mechanised: the
steps existed only in doctrine prose and in a hand-written paragraph of the R-series
entry, so every session re-derived them by reading documents. This tool composes them.

It computes steps 1-5 as structured facts and writes one machine-readable record, so a
future session can determine the current valid execution state from the repository
instead of asking the human for facts the repository already holds.

  1. VERIFY WORKSPACE      -> git branch / HEAD / working tree
  2. VERIFY MASTER VERSION -> doctrine registry laws (the same five tests/test_master_directive pins)
  3. VERIFY EXPERIMENT STATE -> persistence stores + Lane-A freeze
  4. VERIFY GOVERNANCE       -> registry + freeze + register presence
  5. VERIFY OPEN RISKS       -> gap-register open counts + implementable-now list

What this record is, and is not:

  * It DESCRIBES state. It does not decide, grants no authority, unlocks no gate, and
    selects no mission. The step-6 "implementable now" list repeats what the register
    already says; the choice remains with the human.
  * It is read-only. It starts no daemon, writes no store, touches no Lane-A file.
  * It never fabricates: UNKNOWN beats invented, missing stores read NO_DATA, and a
    fact that cannot be verified is recorded as not verified rather than assumed.

Verdict vocabulary: VERIFIED / DEGRADED / NOT_VERIFIED. There is deliberately no PASS --
the gap register's own law (line 7) forbids "PASS without an artifact", and a description
is not an artifact of the thing described.

Usage:
    python scripts/execution_state.py
    python scripts/execution_state.py --out reports/execution_state_<utc>.json --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402

SCHEMA = "ahos.execution_state.v1"
CANON = ROOT / "docs" / "canonical"
REGISTRY_PATH = CANON / "master_directive_registry.json"
ISSUE_REGISTER = ROOT / "AHOS_ISSUE_REGISTER.md"
GAP_REGISTER = ROOT / "AHOS_GAP_REGISTER.md"

# The directive registers its own sha in the issue register; this tool only reads.
STORES = {
    "ahos_local": "get_local_db_path",
    "e01_discovery": "get_discovery_db_path",
    "paper_trading": "get_paper_trading_db_path",
    "ahos_knowledge": "get_knowledge_db_path",
    "ahos_cognitive_memory": "get_cognitive_memory_db_path",
}


def _sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------- step 1

def verify_workspace() -> dict:
    """Step 1. Where the repository physically is right now.

    git_meta is the shared anchor (also used by record_test_run and the system-state
    snapshot), so every artifact in reports/ agrees about commit and branch.
    """
    meta = git_meta()
    return {
        "branch": meta["branch"],
        "commit_sha": meta["commit_sha"],
        "working_tree_clean": meta["working_tree_clean"],
        "verified": meta["commit_sha"] != "UNKNOWN",
    }


# ------------------------------------------------------------- step 2

def verify_master_version() -> dict:
    """Step 2. The doctrine registry laws, evaluated rather than asserted.

    These are the same five invariants tests/test_master_directive.py pins. Re-stating
    them here as computed facts means the record reports the state of the constitution
    instead of assuming it.
    """
    facts: dict = {"verified": False}

    if not REGISTRY_PATH.is_file():
        facts["error"] = "registry missing"
        return facts
    try:
        reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        facts["error"] = f"registry unreadable: {exc.__class__.__name__}"
        return facts

    directives = reg.get("directives")
    if not isinstance(directives, list) or not directives:
        facts["error"] = "registry has no directives"
        return facts

    versions = [d.get("version") for d in directives]
    active = [d for d in directives if d.get("status") == "ACTIVE"]

    on_disk = {p.name for p in CANON.glob("MASTER_DIRECTIVE_v*.md")}
    listed = {d.get("file") for d in directives}

    sha_ok = True
    for d in directives:
        f = CANON / str(d.get("file"))
        if not f.is_file() or _sha(f) != d.get("sha256"):
            sha_ok = False

    register_text = ""
    if ISSUE_REGISTER.is_file():
        try:
            register_text = ISSUE_REGISTER.read_text(encoding="utf-8")
        except OSError:
            register_text = ""

    registered_ok = True
    for d in directives:
        if d.get("sha256") not in register_text:
            registered_ok = False

    laws = {
        "exactly_one_active": len(active) == 1,
        "active_is_highest": bool(active) and active[0].get("version") == max(versions),
        "no_orphan_doctrine_files": on_disk == listed,
        "every_sha_matches_disk": sha_ok,
        "every_sha_in_issue_register": registered_ok,
    }
    facts.update({
        "active_version": active[0].get("version") if active else None,
        "active_file": active[0].get("file") if active else None,
        "doctrine_files_on_disk": sorted(on_disk),
        "laws": laws,
        "verified": all(laws.values()),
    })
    return facts


# ------------------------------------------------------------- step 3

def _store_status(getter_name: str) -> dict:
    """One persistence store, read-only. Absent is NO_DATA, never a invented ok.

    Mirrors scripts/system_state_snapshot.py: a missing store is the honest state of a
    host that has never run the daemon, and it must not be rounded up to healthy.
    """
    try:
        from config import paths as config_paths
        from scripts.sqlite_backup_restore import integrity_check, table_row_counts
    except ImportError as exc:
        return {"error": f"dependency unavailable: {exc.__class__.__name__}"}

    getter = getattr(config_paths, getter_name, None)
    if getter is None:
        return {"error": f"unknown path getter {getter_name!r}"}
    try:
        # create_dir=False: inspecting a store must never create one.
        path = Path(getter(create_dir=False))
    except TypeError:
        path = Path(getter())
    except Exception as exc:  # a path resolver that raises must not kill the record
        return {"error": f"path resolution failed: {exc.__class__.__name__}"}

    if not path.is_file():
        return {"path": str(path), "exists": False, "integrity_check": "NO_DATA", "row_total": "NO_DATA"}

    try:
        counts = table_row_counts(path)
        integrity = integrity_check(path)
    except Exception as exc:
        return {"path": str(path), "exists": True, "integrity_check": f"READ_ERROR", "row_total": "NO_DATA",
                "error": f"{exc.__class__.__name__}"}
    return {
        "path": str(path),
        "exists": True,
        "integrity_check": integrity,
        "row_counts": counts,
        "row_total": sum(counts.values()) if counts else 0,
    }


def verify_experiment_state() -> dict:
    """Step 3. What the experiment actually holds, plus the frozen scientific surface."""
    from scripts.freeze_lane_a import load_baseline, verify as lane_a_verify

    drift, missing, untracked = lane_a_verify(root=ROOT)
    stores = {name: _store_status(fn) for name, fn in STORES.items()}

    store_errors = [n for n, s in stores.items() if "error" in s]
    present = [s for s in stores.values() if "error" not in s and s.get("exists")]
    # Only PRESENT stores can fail integrity. An absent store is NO_DATA -- the honest
    # state of a host that never ran the daemon -- and must not be scored as a failure,
    # or the record reads DEGRADED on every clean checkout.
    present_integrity_ok = all(s.get("integrity_check") == "ok" for s in present)
    absent = sorted(n for n, s in stores.items()
                    if "error" not in s and not s.get("exists"))

    return {
        "stores": stores,
        "lane_a": {
            "drift": drift,
            "missing": missing,
            "untracked": untracked,
            "ok": (not drift and not missing and not untracked),
            "pinned_files": len(load_baseline(root=ROOT)),
        },
        "any_store_present": bool(present),
        "absent_stores": absent,
        "all_present_stores_integrity_ok": present_integrity_ok if present else None,
        "store_resolution_errors": store_errors,
        "verified": (
            not store_errors
            and present_integrity_ok
            and not drift
            and not missing
        ),
    }


# ------------------------------------------------------------- step 5

# Summary-table row shape: | M-GAP-NNN | ... | **STATUS** |
_STATUS_CELL = re.compile(r"\*\*([A-Z][A-Z _-]{2,})\*\*")


def _parse_gap_register(text: str) -> tuple[dict, list[str]]:
    """Counts by status from the register's own summary table.

    Deliberately conservative: the register is a hand-maintained markdown table whose
    cells carry long prose annotations, so this reads only the table's rows and only the
    final bolded token of each row. Anything it cannot classify is reported as
    UNCLASSIFIED rather than silently dropped or counted.
    """
    counts: dict[str, int] = {}
    unclassified: list[str] = []
    for line in text.splitlines():
        if not line.startswith("| M-GAP-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 10:
            continue
        gap_id = cells[0].strip()
        status_cell = cells[-1]
        m = _STATUS_CELL.findall(status_cell)
        # take the LAST bolded token: prose annotations precede the verdict, e.g.
        # "**OPEN** — re-verified 2026-08-20: ..." -> OPEN
        if not m:
            unclassified.append(gap_id)
            continue
        status = m[0].strip().rstrip(".")
        counts[status] = counts.get(status, 0) + 1
    return counts, unclassified


_IMPLEMENTABLE_MARKERS = ("IMPLEMENTABLE NOW",)


def _implementable_now(text: str) -> list[str]:
    """Gaps the register itself marks as doable without owner/env input.

    This is the only 'next action' signal in the record, and it is the register's words,
    not an assessment made here. Step 6 of the directive -- SELECT HIGHEST-VALUE SAFE
    NEXT ACTION -- stays a human choice; this list only removes the re-reading.

    The marker is the register's exact phrase "IMPLEMENTABLE NOW" (used in its own
    staleness verdict: "The 2026-08-27 sentence 'no remaining gap is IMPLEMENTABLE NOW'
    is stale"). Looser substrings such as "IMPLEMENTED" match historical prose inside a
    row -- "adapter IMPLEMENTED" on M-GAP-011 -- and produce false positives.
    """
    out: list[str] = []
    for line in text.splitlines():
        if not line.startswith("| M-GAP-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 10:
            continue
        status = cells[-1]
        if "**CLOSED**" in status or "**RESOLVED**" in status:
            continue
        if any(marker in status for marker in _IMPLEMENTABLE_MARKERS):
            out.append(cells[0].strip())
    return out


def verify_open_risks() -> dict:
    """Step 5. Open risk surface, from the register that owns it."""
    if not GAP_REGISTER.is_file():
        return {"error": "gap register missing", "verified": False}
    try:
        text = GAP_REGISTER.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": f"gap register unreadable: {exc.__class__.__name__}", "verified": False}

    counts, unclassified = _parse_gap_register(text)
    resolved = counts.get("CLOSED", 0) + counts.get("RESOLVED", 0)
    # OPTIONAL is the register's own "not an acceptance item" class (M-GAP-012), so it is
    # not counted as an open risk; it is reported separately rather than dropped.
    optional = counts.get("OPTIONAL", 0)
    open_total = sum(v for k, v in counts.items()
                     if k not in ("CLOSED", "RESOLVED", "OPTIONAL"))

    return {
        "status_counts": counts,
        "open_total": open_total,
        "optional_total": optional,
        "resolved_total": resolved,
        "unclassified_rows": unclassified,
        "implementable_now": _implementable_now(text),
        "owner_blocked": _owner_blocked(text),
        "verified": True,
    }


# The register states these in the owner/action column (col 8), not the status column --
# e.g. M-GAP-003's status reads OPEN while its action column reads "USER: keep laptop
# awake 168h". Searching only the status cell misses five of six.
_OWNER_MARKERS = ("USER ACTION", "USER:", "REQUIRES CREDENTIAL")


def _owner_blocked(text: str) -> list[str]:
    """Gaps explicitly waiting on a user action, credential, or environment.

    Surfacing these separately matters for the record's honesty: an open gap blocked on
    the owner is not work a session can pick up, and lumping it into 'open' would make
    the register look more actionable than it is.
    """
    out: list[str] = []
    for line in text.splitlines():
        if not line.startswith("| M-GAP-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 10:
            continue
        status = cells[-1]
        if "**CLOSED**" in status or "**RESOLVED**" in status:
            continue
        # owner/action column is index 7; status is last
        if any(m in cells[7] for m in _OWNER_MARKERS) or "REQUIRES USER ACTION" in status:
            out.append(cells[0].strip())
    return sorted(set(out))


# ------------------------------------------------------------- composition

def build_state() -> dict:
    workspace = verify_workspace()
    master = verify_master_version()
    experiment = verify_experiment_state()
    risks = verify_open_risks()

    # Step 4: governance is the composition of the constitution and the freeze, plus the
    # presence of the two registers that record both. It is not an independent probe --
    # re-deriving it from the facts above is what keeps the record self-consistent.
    registers_present = {
        "issue_register": ISSUE_REGISTER.is_file(),
        "gap_register": GAP_REGISTER.is_file(),
        "master_directive_registry": REGISTRY_PATH.is_file(),
    }
    governance = {
        "registers_present": registers_present,
        "doctrine_registry_ok": master.get("verified", False),
        "lane_a_integrity_ok": experiment["lane_a"]["ok"],
        "verified": (
            all(registers_present.values())
            and master.get("verified", False)
            and experiment["lane_a"]["ok"]
        ),
    }

    step_verdicts = {
        "1_verify_workspace": workspace.get("verified", False),
        "2_verify_master_version": master.get("verified", False),
        "3_verify_experiment_state": experiment.get("verified", False),
        "4_verify_governance": governance.get("verified", False),
        "5_verify_open_risks": risks.get("verified", False),
    }
    ok = sum(step_verdicts.values())

    # VERIFIED only when all five steps hold. DEGRADED when the record is complete but
    # the repository is in a state a session should notice. NOT_VERIFIED when a step
    # could not even be computed -- the record is then incomplete, not merely unhealthy.
    uncomputable = ("error" in master) or ("error" in risks) or workspace.get("commit_sha") == "UNKNOWN"
    degraded_signals = [
        name for name, flag in (
            ("working_tree_not_clean", not workspace.get("working_tree_clean", False)),
            ("lane_a_untracked_files_present", bool(experiment["lane_a"]["untracked"])),
            ("present_store_integrity_not_ok",
             experiment.get("any_store_present")
             and experiment.get("all_present_stores_integrity_ok") is False),
        ) if flag
    ]

    if uncomputable:
        verdict = "NOT_VERIFIED"
    elif ok == 5:
        verdict = "DEGRADED" if degraded_signals else "VERIFIED"
    else:
        verdict = "DEGRADED"

    return {
        "schema": SCHEMA,
        "timestamp_utc": utc_now(),
        "command": "python scripts/execution_state.py",
        "git": git_meta(),
        "environment": environment_fingerprint(),
        "directive_protocol": {
            "source": "docs/canonical/MASTER_DIRECTIVE_v1.md OPERATIONAL REGISTRATION §3",
            "steps_recorded": [1, 2, 3, 4, 5],
            "note": ("steps 6-12 are execution and remain a human choice; this record "
                     "describes state and selects nothing"),
        },
        "steps": {
            "1_verify_workspace": workspace,
            "2_verify_master_version": master,
            "3_verify_experiment_state": experiment,
            "4_verify_governance": governance,
            "5_verify_open_risks": risks,
        },
        "step_verdicts": step_verdicts,
        "verdict": verdict,
        "degraded_signals": degraded_signals,
        "honest_limitations": [
            "This record is a description, not an authorisation. It grants nothing.",
            "A missing persistence store reads NO_DATA -- the honest state of a host "
            "that has not run the daemon, never an invented ok.",
            "Step 6 (select highest-value safe next action) is deliberately not "
            "automated; 'implementable_now' repeats the gap register's own words.",
            "The gap-register parse reads the summary table only. Addendum prose is "
            "not counted, so open_total is a floor, not a census.",
        ],
    }


def default_out_path() -> Path:
    stamp = utc_now().replace(":", "").replace("-", "")
    return ROOT / "reports" / f"execution_state_{stamp}.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS execution-state recorder (Master Directive steps 1-5)")
    ap.add_argument("--out", default=None,
                    help="artifact path (default: reports/execution_state_<utc>.json)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing artifact. Off by default: evidence is "
                         "append-only and reports/ is committed, so reusing --out would "
                         "silently destroy a prior record (M-GAP-036's lesson).")
    ap.add_argument("--json", action="store_true", help="print the full record, not just a summary")
    args = ap.parse_args(argv)

    out_path = Path(args.out) if args.out else default_out_path()
    if out_path.exists() and not args.force:
        print(
            f"refuse to overwrite existing artifact {out_path}; evidence is append-only. "
            "Re-run without --out (a UTC timestamp is appended), or pass --force to overwrite.",
            file=sys.stderr,
        )
        return 3

    state = build_state()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Pinned UTF-8: the record carries the repo's non-ASCII (em-dashes, arrows) and
    # cp1252 would corrupt it on a Windows host -- the M-GAP-033 class.
    out_path.write_text(json.dumps(state, indent=2, default=str) + "\n", encoding="utf-8")

    summary = {
        "verdict": state["verdict"],
        "artifact": str(out_path),
        "commit_sha": state["git"]["commit_sha"],
        "branch": state["git"]["branch"],
        "working_tree_clean": state["git"]["working_tree_clean"],
        "steps_ok": sum(state["step_verdicts"].values()),
        "degraded_signals": state["degraded_signals"],
        "open_gaps": state["steps"]["5_verify_open_risks"].get("open_total"),
        "implementable_now": state["steps"]["5_verify_open_risks"].get("implementable_now"),
    }
    print(json.dumps(state if args.json else summary, indent=2, default=str))
    # A recorder that fails to record is worse than no record. Exit 0 even when the
    # state it found is bad: the verdict is data, not a signal that recording failed.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
