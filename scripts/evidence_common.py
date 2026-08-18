#!/usr/bin/env python3
"""Shared evidence metadata for AHOS command/state artifacts.

No secrets. No network. Used by record_test_run, system_state_snapshot,
and reliability_challenge so every artifact carries the same identity fields.
"""
from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git_meta(cwd: Path | None = None) -> dict:
    repo = cwd or ROOT

    def _run(args: list[str]) -> str:
        try:
            proc = subprocess.run(
                args, cwd=str(repo), capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return proc.stdout.strip() if proc.returncode == 0 else ""

    porcelain = _run(["git", "status", "--porcelain"])
    return {
        "commit_sha": _run(["git", "rev-parse", "HEAD"]) or "UNKNOWN",
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "UNKNOWN",
        "working_tree_clean": porcelain == "",
    }


def environment_fingerprint() -> dict:
    """Non-secret host fingerprint. Env vars are names-only (values never copied)."""
    env_names = sorted(
        name for name in os.environ
        if name.startswith("AHOS_") or name in {
            "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "ALL_PROXY", "HTTPS_PROXY",
        }
    )
    uname = platform.uname()
    blob = "|".join([
        sys.version, platform.platform(), uname.system, uname.release,
        uname.machine, sys.executable,
    ]).encode("utf-8")
    return {
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": uname.machine,
        "system": uname.system,
        "executable": sys.executable,
        "cwd": str(Path.cwd()),
        "ahos_related_env_names": env_names,
        "fingerprint_sha256": hashlib.sha256(blob).hexdigest(),
    }


def observation_event(*, event_type: str, severity: str, evidence_path: str,
                      detail: str, commit_sha: str) -> dict:
    return {
        "timestamp_utc": utc_now(),
        "commit_sha": commit_sha,
        "event_type": event_type,
        "severity": severity,
        "evidence_path": evidence_path,
        "detail": detail,
    }
