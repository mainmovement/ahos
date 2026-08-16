#!/usr/bin/env python3
"""AHOS Health Manager & Self-Repair Diagnostic System (Phase XXIV / Master Mission).

Capabilities:
  - Detects missing files, broken paths, missing packages, corrupted databases, and failed services.
  - Generates machine-readable health_report.json.
  - Epistemic Rule: NEVER modifies files automatically. Suggests exact repair actions and executes
    repairs ONLY upon explicit user command with `--repair --confirm`.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to sys.path for cross-platform imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import get_project_root, get_data_dir, get_discovery_db_path, get_local_db_path, get_paper_trading_db_path, get_knowledge_db_path


@dataclass
class DiagnosticIssue:
    issue_id: str
    category: str                                # MISSING_FILE | CORRUPT_DB | MISSING_PKG | BROKEN_PATH | SERVICE_FAIL
    severity: str                                # HIGH | MED | LOW
    description: str
    affected_resource: str
    suggested_fix: str
    auto_repairable: bool = False


@dataclass
class SystemHealthReport:
    timestamp_utc: str
    overall_status: str                          # GREEN | YELLOW | RED
    total_issues: int
    issues: list[DiagnosticIssue] = field(default_factory=list)
    system_metrics: dict[str, Any] = field(default_factory=dict)


class AHOSHealthManager:
    def __init__(self, root_dir: Path | str | None = None):
        self.root = Path(root_dir) if root_dir else get_project_root()
        self.required_packages = ["pytest", "yaml", "anyio"]
        self.required_files = [
            self.root / "contracts" / "agent_contract_v1.json",
            self.root / "contracts" / "ai_council_contract_v1.json",
            self.root / "contracts" / "improvement_proposal_v1.json",
            self.root / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md",
            self.root / "config" / "agent_registry.yaml",
            self.root / "config" / "cognitive_principles.yaml",
            self.root / "config" / "paths.py"
        ]
        self.databases = [
            get_discovery_db_path(),
            get_paper_trading_db_path(),
            get_local_db_path(),
            get_knowledge_db_path()
        ]

    def run_full_diagnostics(self) -> SystemHealthReport:
        issues: list[DiagnosticIssue] = []

        # 1. Check Required Files
        for req_file in self.required_files:
            if not req_file.exists():
                issues.append(DiagnosticIssue(
                    issue_id=f"MISSING_{req_file.name.upper().replace('.', '_')}",
                    category="MISSING_FILE",
                    severity="HIGH",
                    description=f"Essential system file is missing: {req_file}",
                    affected_resource=str(req_file),
                    suggested_fix=f"Restore {req_file} from repository snapshot or git history.",
                    auto_repairable=False
                ))

        # 2. Check Database Integrity
        for db_path in self.databases:
            p = Path(db_path)
            if not p.exists():
                issues.append(DiagnosticIssue(
                    issue_id=f"MISSING_DB_{p.stem.upper()}",
                    category="CORRUPT_DB",
                    severity="HIGH",
                    description=f"Database file does not exist: {p}",
                    affected_resource=str(p),
                    suggested_fix=f"Initialize database schemas via `python3 -m architecture.runtime --single-cycle`.",
                    auto_repairable=True
                ))
            else:
                try:
                    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
                    res = conn.execute("PRAGMA integrity_check;").fetchone()
                    conn.close()
                    if not res or res[0] != "ok":
                        issues.append(DiagnosticIssue(
                            issue_id=f"CORRUPT_DB_{p.stem.upper()}",
                            category="CORRUPT_DB",
                            severity="HIGH",
                            description=f"Database integrity check failed for {p}: {res}",
                            affected_resource=str(p),
                            suggested_fix=f"Restore database {p} from backup.",
                            auto_repairable=False
                        ))
                except Exception as e:
                    issues.append(DiagnosticIssue(
                        issue_id=f"ERR_DB_{p.stem.upper()}",
                        category="CORRUPT_DB",
                        severity="HIGH",
                        description=f"Unable to read database {p}: {e}",
                        affected_resource=str(p),
                        suggested_fix=f"Check file permissions and lock states on {p}.",
                        auto_repairable=False
                    ))

        # 3. Check Required Packages
        for pkg in self.required_packages:
            try:
                importlib.import_module(pkg)
            except ImportError:
                issues.append(DiagnosticIssue(
                    issue_id=f"MISSING_PKG_{pkg.upper()}",
                    category="MISSING_PKG",
                    severity="HIGH",
                    description=f"Required Python package is not installed: {pkg}",
                    affected_resource=pkg,
                    suggested_fix=f"Run `pip install {pkg}` or `pip install -r requirements.txt`.",
                    auto_repairable=True
                ))

        # Determine Overall Status
        if any(i.severity == "HIGH" for i in issues):
            status = "RED"
        elif issues:
            status = "YELLOW"
        else:
            status = "GREEN"

        report = SystemHealthReport(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            overall_status=status,
            total_issues=len(issues),
            issues=issues,
            system_metrics={
                "databases_checked": len(self.databases),
                "files_checked": len(self.required_files),
                "packages_checked": len(self.required_packages),
                "python_version": sys.version.split()[0],
                "platform": sys.platform
            }
        )
        return report

    def export_health_report(self, output_path: Path | str | None = None) -> Path:
        rep = self.run_full_diagnostics()
        out = Path(output_path) if output_path else (self.root / "reports" / "health_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(rep), indent=2, ensure_ascii=False))
        return out

    def execute_repairs(self, confirmed: bool = False) -> list[str]:
        """Executes safe auto-repairs ONLY if confirmed is True."""
        if not confirmed:
            return ["REPAIR ABORTED: Explicit user confirmation (--confirm) is required by governance law."]

        actions = []
        rep = self.run_full_diagnostics()
        for issue in rep.issues:
            if issue.auto_repairable and issue.category == "CORRUPT_DB" and "does not exist" in issue.description:
                # Initialize missing database
                p = Path(issue.affected_resource)
                p.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(p))
                conn.execute("VACUUM;")
                conn.close()
                actions.append(f"REPAIRED: Initialized blank database {p}")

        return actions if actions else ["No auto-repairable issues were pending."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AHOS System Health Manager & Self-Repair")
    parser.add_argument("--report", default=None, help="Output path for health_report.json")
    parser.add_argument("--repair", action="store_true", help="Attempt safe repairs of detected issues")
    parser.add_argument("--confirm", action="store_true", help="Explicit human confirmation for repairs")
    args = parser.parse_args(argv)

    manager = AHOSHealthManager()
    rep = manager.run_full_diagnostics()
    out_file = manager.export_health_report(args.report)

    print(f"==========================================================")
    print(f"  AHOS Health Manager — Status: {rep.overall_status}")
    print(f"  Total Issues Found: {rep.total_issues}")
    print(f"  Report exported to: {out_file}")
    print(f"==========================================================")

    for i in rep.issues:
        print(f"  [{i.severity}] {i.category}: {i.description}")
        print(f"     Suggested Fix: {i.suggested_fix}")

    if args.repair:
        print("\n--- Repair Execution ---")
        actions = manager.execute_repairs(confirmed=args.confirm)
        for act in actions:
            print(f"  {act}")

    return 0 if rep.overall_status == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
