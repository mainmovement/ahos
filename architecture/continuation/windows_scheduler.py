"""Register and report Windows Task Scheduler jobs for AHOS PAPER_ONLY cadence."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_REL = Path("reports") / "grok" / "CONTINUATION" / "windows_scheduled_tasks.json"
RUNS_DIR_REL = Path("reports") / "grok" / "CONTINUATION" / "scheduled_runs"

TASK_SPECS: list[dict[str, Any]] = [
    {
        "task_name": "AHOS_arxiv_scout_daily",
        "script": "scripts/scheduled/run_arxiv_scout_daily.py",
        "schedule_type": "DAILY",
        "start_time": "04:00",
    },
    {
        "task_name": "AHOS_pipeline_6h",
        "script": "scripts/scheduled/run_pipeline_6h.py",
        "schedule_type": "HOURLY",
        "modifier": "6",
    },
    {
        "task_name": "AHOS_university_exam_sat",
        "script": "scripts/scheduled/run_university_exam_sat.py",
        "schedule_type": "WEEKLY",
        "days": "SAT",
        "start_time": "09:00",
    },
    {
        "task_name": "AHOS_negahban_daily",
        "script": "scripts/scheduled/run_negahban_daily.py",
        "schedule_type": "DAILY",
        "start_time": "05:30",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_run_receipt(root: Path, task_name: str, payload: dict[str, Any]) -> Path:
    root = Path(root)
    out_dir = root / RUNS_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = task_name.replace("/", "_")
    path = out_dir / f"{safe}.json"
    doc = {"schema": "ahos.scheduled_run_receipt.v1", "task_name": task_name, "finished_at": _utc_now(), **payload}
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def register_windows_tasks(root: Path | None = None) -> dict[str, Any]:
    """Invoke register_ahos_scheduled_tasks.ps1 (schtasks /Create)."""
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    ps1 = root / "scripts" / "windows" / "register_ahos_scheduled_tasks.ps1"
    if not ps1.is_file():
        raise FileNotFoundError(ps1)
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        capture_output=True,
        text=True,
        cwd=str(root),
        timeout=300,
    )
    reg = load_task_registry(root)
    reg["registered_at"] = _utc_now()
    reg["register_exit_code"] = proc.returncode
    reg["register_stdout"] = (proc.stdout or "")[-4000:]
    reg["register_stderr"] = (proc.stderr or "")[-2000:]
    out = root / REGISTRY_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"register_ahos_scheduled_tasks.ps1 failed: {proc.stderr or proc.stdout}")
    return reg


def load_task_registry(root: Path) -> dict[str, Any]:
    root = Path(root)
    from config.paths import resolve_ahos_python_exe

    py = str(resolve_ahos_python_exe(root))
    tasks = []
    for spec in TASK_SPECS:
        tr = f'"{py}" "{root / spec["script"]}"'
        tasks.append({**spec, "command": tr, "repo_root": str(root)})
    return {
        "schema": "ahos.windows_scheduled_tasks.v1",
        "paper_only": True,
        "repo_root": str(root),
        "python_exe": py,
        "tasks": tasks,
    }


def query_schtasks() -> str:
    sch = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "schtasks.exe"
    proc = subprocess.run(
        [str(sch), "/Query", "/FO", "LIST", "/V"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    lines = proc.stdout.splitlines()
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in lines:
        if line.startswith("Folder:") and cur:
            blocks.append(cur)
            cur = [line]
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)
    ahos_blocks = [b for b in blocks if any("AHOS_" in ln for ln in b)]
    return "\n\n".join("\n".join(b) for b in ahos_blocks) or proc.stdout[-8000:]
