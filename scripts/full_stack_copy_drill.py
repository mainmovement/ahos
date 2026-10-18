#!/usr/bin/env python3
"""One-shot drill on a ledger copy: wiring probe, tier gate, judge. Never the live path."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ledger copy drill (gold wiring + tier gate)")
    ap.add_argument("--source", type=Path, default=None)
    ap.add_argument("--settle-tp", action="store_true")
    args = ap.parse_args(argv)
    py = sys.executable
    dest = Path(tempfile.gettempdir()) / "ahos_full_stack_drill.jsonl"
    cmd_probe = [py, str(ROOT / "scripts" / "prove_wiring_on_ledger_copy.py"), "--dest", str(dest)]
    if args.source:
        cmd_probe.extend(["--source", str(args.source)])
    if args.settle_tp:
        cmd_probe.append("--settle-tp")
    probe = subprocess.run(cmd_probe, cwd=str(ROOT), capture_output=True, text=True, timeout=180)
    if probe.returncode != 0:
        print(probe.stderr or probe.stdout, file=sys.stderr)
        return probe.returncode
    wiring = json.loads(probe.stdout)
    tier = subprocess.run(
        [py, str(ROOT / "scripts" / "tier_gate_scratch.py"), "--ledger", str(dest)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = {
        "dest": str(dest),
        "wiring": wiring,
        "tier_gate_stdout": tier.stdout.strip(),
        "tier_gate_rc": tier.returncode,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if wiring.get("judge") == "CLEAN" and tier.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
