"""M9 batch driver: run pytest on a list of files and record a structured result."""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(batch: str, out: Path, timeout: int) -> dict:
    files = [l.strip() for l in (ROOT / batch).read_text().splitlines() if l.strip()]
    cmd = [
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m", "pytest", "-q", "-p", "no:cacheprovider",
        "--timeout=300", "-rfE", "--tb=line",
    ] + files
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    dt = round(time.time() - t0, 1)
    out.write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8")
    # parse the summary line
    summary = {}
    for line in proc.stdout.splitlines():
        if line.startswith(" ") and "passed" in line:
            summary["line"] = line.strip()
    fails = [l for l in proc.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))]
    return {
        "batch": batch,
        "exit": proc.returncode,
        "seconds": dt,
        "summary": summary.get("line"),
        "failures": fails,
    }


if __name__ == "__main__":
    batch, outname = sys.argv[1], sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
    res = run(batch, ROOT / outname, timeout)
    print(json.dumps(res, ensure_ascii=False))
