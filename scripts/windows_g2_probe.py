#!/usr/bin/env python3
"""Focused G2 probe for Windows PAPER_ONLY validation.

Does NOT claim PRE_SOAK or OPERATOR_READY.
Does NOT migrate. Lane-A untouched.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = ROOT / "reports" / "g2_validate_windows_latest.json"
    if "--json-out" in argv:
        i = argv.index("--json-out")
        if i + 1 < len(argv):
            out = Path(argv[i + 1])

    os.environ.setdefault("AHOS_PAPER_ONLY", "1")
    os.environ.setdefault("AHOS_EVIDENCE_SOURCE", "local")
    try:
        from run_bot import load_dotenv

        loaded = load_dotenv(ROOT / ".env")
        for key in (
            "AHOS_WEB_API_TOKEN",
            "NEXT_PUBLIC_AHOS_WEB_API_TOKEN",
            "AHOS_WEB_API_ALLOW_OPEN_ACCESS",
            "DATABASE_URL",
            "AHOS_GATEWAY_URL",
            "AHOS_PAPER_ONLY",
            "AHOS_EVIDENCE_SOURCE",
        ):
            if key in loaded:
                os.environ[key] = loaded[key]
    except Exception:  # noqa: BLE001
        pass

    if not (os.environ.get("AHOS_GATEWAY_URL") or "").strip():
        os.environ["AHOS_GATEWAY_URL"] = "http://127.0.0.1:3000/api/chat"

    from scripts.operator_validation_gate import g2_gateway

    g = g2_gateway(skip_network=False)
    report = {
        "schema": "ahos.g2_validate.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host_is_windows": sys.platform.startswith("win"),
        "host_platform": platform.platform(),
        "focus": "G2_only",
        "forbidden_claims": ["PRE_SOAK", "OPERATOR_READY"],
        "note": "G2 PASS alone is not PRE_SOAK; run AHOS_WINDOWS_OPS.bat / AHOS_PRE_SOAK_NOW.bat for G1-G10.",
        "gate": g,
        "g2_pass": g.get("status") == "PASS",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"G2_STATUS={g.get('status')}")
    print(f"G2_DETAIL={g.get('detail')}")
    print(f"json_out={out}")
    return 0 if g.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
