"""Run the light science jobs one at a time, then exit.

This process is not the paper trader and not the soak. It does not read .env.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.research.nightly_science import (  # noqa: E402
    ALLOWED,
    build_report,
    free_ram_mb,
    install_plan,
    publish,
    scipy_job,
    statsmodels_job,
    us_closes,
)


def _install(package: str) -> dict:
    plan = install_plan(package)
    plan["ram_after_mb"] = free_ram_mb()
    if plan["action"] != "INSTALL":
        plan["installed"] = False
        return plan
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        cwd=str(ROOT),
        check=False,
    )
    plan["installed"] = completed.returncode == 0
    plan["ram_after_mb"] = free_ram_mb()
    plan["pip_exit"] = completed.returncode
    return plan


def _job(name: str) -> dict:
    rows = us_closes(ROOT)
    if name == "scipy":
        doc = scipy_job(rows)
    elif name == "statsmodels":
        doc = statsmodels_job(rows)
    else:
        raise SystemExit(2)
    path = ROOT / "reports" / "grok" / "PAPER" / f"nightly_job_{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(name, doc.get("pid"), doc.get("peak_ram_mb"), doc.get("status"))
    return doc


def main(argv: list[str]) -> int:
    if "--job" in argv:
        _job(argv[argv.index("--job") + 1])
        return 0
    installs = [_install(package) for package in ALLOWED] if "--install" in argv else []
    if not installs:
        prior = ROOT / "reports" / "grok" / "PAPER" / "nightly_science_us.json"
        if prior.is_file():
            try:
                installs = list(json.loads(prior.read_text(encoding="utf-8")).get("installs") or [])
            except json.JSONDecodeError:
                installs = []
    jobs = []
    for name in ALLOWED:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__)), "--job", name],
            cwd=str(ROOT),
            check=False,
        )
        path = ROOT / "reports" / "grok" / "PAPER" / f"nightly_job_{name}.json"
        if path.is_file():
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        else:
            jobs.append({"package": name, "status": "FAILED", "pip_exit": completed.returncode, "promoted": False})
    report = build_report(ROOT, installs, jobs)
    report["parent_pid"] = report["pid"]
    publish(ROOT, report)
    print("parent", report["parent_pid"], "libs_used", report["libs_used"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
