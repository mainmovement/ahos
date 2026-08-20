#!/usr/bin/env python3
"""Documentation <-> implementation drift detection (W38 Candidate H).

The operator-docs tests pin the four operator runbooks, but the CANONICAL
architecture documents (docs/canonical, docs/architecture, root AHOS_*.md)
are not systematically checked. A canonical doc that references a deleted or
renamed repository file is stale documentation — a self-diagnosis gap
(master directive: documentation must describe reality).

This script scans the canonical documents for repository-relative file
references and reports those that no longer exist:

  * `scripts/foo.py`, `architecture/bar.py`, `tests/test_x.py`,
    `docs/...`, `config/...` path tokens
  * `engine/run_all_checks.sh` etc.

Honesty rules:
  * WARN-level, never a hard gate failure (a doc may reference a
    deliberately-removed historical file with a superseded marker).
  * Deterministic, read-only, stdlib-only.
  * Only path-like tokens are checked — prose claims about behavior are
    out of scope (they need human review, not regex).

Usage:
    python scripts/doc_drift.py
    python scripts/doc_drift.py --stdout
Exit codes:
    0 = scan completed (drift is WARN, not a failure)
    2 = invocation error
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Canonical documentation surfaces to scan.
CANONICAL_DOCS = sorted(
    list((ROOT / "docs" / "canonical").glob("*.md"))
    + list((ROOT / "docs" / "architecture").glob("*.md"))
    + [p for p in ROOT.glob("*.md") if p.name.startswith("AHOS_")]
)

#: Path token pattern: a repo-relative path with a known extension. The
#: trailing \b prevents truncation (e.g. `.sql` must not match inside
#: `.sqlite`, `.json` inside `.jsonl`); longest extensions are listed first.
PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.])((?:architecture|scripts|tests|docs|config|engine|"
    r"discovery|paper_trading|telegram_ai|strategy_lab|research|contracts|"
    r"deployment|database|proposals|reports|data)/[A-Za-z0-9_./\-]+"
    r"\.(?:jsonl|sqlite|json|yaml|yml|sql|py|sh|md|txt|toml|ini|ps1|bat|"
    r"service|timer|csv))\b"
)


#: Double-extension corruption patterns (e.g. a `.sql` -> `.sqlite` replace
#: applied inside an existing `.sqlite` yields `.sqliteite`). These are
#: invisible to the path regex (no matching extension) but are clearly
#: corruption; scan for them explicitly.
CORRUPTION_PATTERNS: dict[str, str] = {
    "sqliteite": "double extension (replace applied inside .sqlite)",
    "jsonlson": "double extension (replace applied inside .jsonl)",
    "jsonjson": "double extension (replace applied inside .json)",
    ".sql.sqlite": "double extension",
    ".json.json": "double extension",
}


#: Intentional references that are NOT drift — each with a reason. A
#: reference is ignored only when it appears in this exact set; anything
#: else that does not exist is reported.
INTENTIONAL_REFS: dict[str, str] = {
    "reports/nightly_backup_series.json": "planned artifact produced by "
        "scripts/sqlite_backup_restore.py nightly runs (7 distinct days)",
    "reports/local_soak_interruptions.json": "planned artifact produced "
        "during the laptop soak (AHOS_LOCAL_SOAK_PROTOCOL.md)",
    "reports/local_soak_interruptions.jsonl": "operator-logged soak interruptions (protocol section: log UTC in this file)",
    "data/control_plane_ledger.sqlite": "future run-ledger artifact, marked (future) in agent_matrix_v2",
    "reports/calibration_20260820T0800Z.json": "historical evidence citation "
        "in the wave ledger; superseded by later calibration artifacts",
    "reports/calibration_all_20260820T0800Z.json": "historical evidence "
        "citation in the wave ledger; superseded by later artifacts",
    "reports/observe_active_20260813_win_1..4.json": "range notation in the "
        "issue register; individual win_N artifacts exist",
    "paper_trading/runs/cycle_001_20260812.json": "historical wave-ledger "
        "record of a cycle artifact not retained in git",
}


def _exists(rel: str) -> bool:
    """Existence check, tolerant of trailing characters (commas, parens,
    code spans, backticks)."""
    token = rel.strip().rstrip(",.;:)]}'\">`")
    return (ROOT / token).exists()


def scan_docs(docs: list[Path] | None = None) -> dict[str, list[dict[str, str]]]:
    """doc path -> list of {reference, reason} for drift: references to
    missing files AND double-extension corruption (e.g. `.sqliteite`)."""
    out: dict[str, list[dict[str, str]]] = {}
    for doc in docs or CANONICAL_DOCS:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore")
        seen: set[str] = set()
        drift: list[dict[str, str]] = []

        # missing-file references
        for m in PATH_RE.finditer(text):
            ref = m.group(1)
            if ref in seen:
                continue
            seen.add(ref)
            if not _exists(ref):
                if ref in INTENTIONAL_REFS:
                    continue
                drift.append({"reference": ref,
                              "reason": "referenced path does not exist in "
                                        "the repository"})

        # double-extension corruption
        for pattern, reason in CORRUPTION_PATTERNS.items():
            if pattern in text:
                drift.append({"reference": pattern, "reason": reason})

        if drift:
            out[doc.relative_to(ROOT).as_posix()] = drift
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS doc <-> code drift check")
    ap.add_argument("--stdout", action="store_true", help="print the drift report")
    args = ap.parse_args(argv)

    drift = scan_docs()
    total = sum(len(v) for v in drift.values())
    print(f"doc-drift scan: {len(CANONICAL_DOCS)} canonical docs scanned, "
          f"{total} stale reference(s)")
    for doc, refs in sorted(drift.items()):
        for r in refs:
            print(f"  STALE {doc}: {r['reference']} ({r['reason']})")
    if not drift:
        print("  no stale file references in canonical docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
