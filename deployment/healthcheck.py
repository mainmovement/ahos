#!/usr/bin/env python3
"""AHOS Production Container Healthcheck Probe."""
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from architecture.runtime.lifecycle import ApplicationLifecycleManager


def main() -> int:
    try:
        app = ApplicationLifecycleManager(workspace_root=Path(__file__).resolve().parents[1])
        report = app.health.run_checks()
        if report.healthy or report.status in ("OK", "DEGRADED"):
            sys.exit(0)
        else:
            sys.stderr.write(f"Healthcheck FAILED: {report.details}\n")
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Healthcheck Exception: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
