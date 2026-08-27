#!/usr/bin/env python3
"""AHOS Operator Validation Gate runner.

Produces a machine-readable report for G1–G12.
Never invents PASS for Windows/Telegram/n8n-live/soak when not executed.

Usage:
  python scripts/operator_validation_gate.py --platform agent-host \\
      --json-out reports/operator_validation_report_agent_host.json

  python scripts/operator_validation_gate.py --platform windows \\
      --json-out reports/operator_validation_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "ahos.operator_validation_report.v1"


def _gate(gid: str, name: str, status: str, detail: str,
          artifact: str | None = None, **extra: Any) -> dict[str, Any]:
    assert status in (
        "PASS", "FAIL", "BLOCKED", "NOT_VERIFIED", "OWNER_ACTION_REQUIRED",
        "STRUCTURAL_VALID", "SKIPPED",
    )
    out = {
        "id": gid,
        "name": name,
        "status": status,
        "detail": detail,
        "artifact": artifact,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out.update(extra)
    return out


def g1_environment() -> dict[str, Any]:
    issues = []
    py = sys.version.split()[0]
    if sys.version_info < (3, 10):
        issues.append(f"python_too_old:{py}")
    try:
        import architecture  # noqa: F401
    except Exception as e:  # noqa: BLE001
        issues.append(f"import_architecture:{type(e).__name__}")
    data = ROOT / "data"
    try:
        data.mkdir(parents=True, exist_ok=True)
        probe = data / ".ahos_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as e:
        issues.append(f"data_not_writable:{e}")
    node = subprocess.run(["node", "--version"], capture_output=True, text=True)
    npm = subprocess.run(["npm", "--version"], capture_output=True, text=True)
    detail = {
        "python": py,
        "platform": platform.platform(),
        "node": (node.stdout or node.stderr or "").strip() or None,
        "npm": (npm.stdout or npm.stderr or "").strip() or None,
        "issues": issues,
    }
    if issues:
        return _gate("G1", "Environment", "FAIL", json.dumps(detail), **detail)
    return _gate("G1", "Environment", "PASS", json.dumps(detail), **detail)


def g2_gateway(skip_network: bool) -> dict[str, Any]:
    if skip_network:
        return _gate(
            "G2", "Gateway", "NOT_VERIFIED",
            "skipped_network_probe; start npm run dev and re-run without --skip-network",
        )
    import urllib.error
    import urllib.request
    url = os.environ.get("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"message": "ping", "locale": "fa"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "ahos-opval/1"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read(400).decode("utf-8", "replace")
            return _gate(
                "G2", "Gateway", "PASS",
                f"http_{resp.status} from {url}",
                artifact=body[:200],
                http_status=resp.status,
                url=url,
            )
    except Exception as e:  # noqa: BLE001
        return _gate(
            "G2", "Gateway", "FAIL",
            f"{type(e).__name__}: {e}",
            url=url,
        )


def g3_providers(do_probe: bool) -> dict[str, Any]:
    if not do_probe:
        return _gate(
            "G3", "Discovery providers", "NOT_VERIFIED",
            "pass --probe-providers to execute live probe",
        )
    try:
        from architecture.providers.probe import probe_providers, render_table
        report = probe_providers(chain="solana")
        out_dir = ROOT / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        path = out_dir / f"provider_probe_opval_{stamp}.json"
        path.write_text(json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8")
        if report.any_success:
            names = [r.provider_id for r in report.successes]
            return _gate(
                "G3", "Discovery providers", "PASS",
                f"SUCCESS: {', '.join(names)}",
                artifact=str(path),
                status_counts=report.status_counts(),
            )
        return _gate(
            "G3", "Discovery providers", "FAIL",
            f"no SUCCESS; counts={report.status_counts()}",
            artifact=str(path),
            status_counts=report.status_counts(),
        )
    except Exception as e:  # noqa: BLE001
        return _gate("G3", "Discovery providers", "FAIL", f"{type(e).__name__}: {e}")


def g4_g5_g8_g9_evidence() -> list[dict[str, Any]]:
    from architecture.learning.prediction_lifecycle import lifecycle_status
    st = lifecycle_status()
    disc_obs = int(st.get("discovery_observations") or 0)
    prod_obs = int(st.get("production_observations") or 0)
    preds = int(st.get("local_predictions") or 0)
    active = sum(int(v) for v in (st.get("observation_state") or {}).values())
    labels = int(st.get("outcome_labels") or 0)

    g4 = _gate(
        "G4", "Evidence persistence",
        "PASS" if (disc_obs > 0 or prod_obs > 0) else "FAIL",
        f"discovery_observations={disc_obs} production_observations={prod_obs}",
        census=st,
    )
    g5 = _gate(
        "G5", "Scoring / predictions",
        "PASS" if preds > 0 else "NOT_VERIFIED",
        f"local_predictions={preds} (run --single-cycle --evidence-source local if 0)",
        local_predictions=preds,
    )
    g8 = _gate(
        "G8", "Prediction lifecycle registration",
        "PASS" if active > 0 else "FAIL",
        f"observation_state_total={active} states={st.get('observation_state')}",
    )
    g9 = _gate(
        "G9", "Observation lifecycle",
        "PASS" if disc_obs > 0 else "FAIL",
        f"discovery_observations={disc_obs} outcome_labels={labels} "
        f"(labels remain 0 until T+72h RESOLVED — expected)",
        outcome_labels=labels,
    )
    return [g4, g5, g8, g9]


def g6_security() -> dict[str, Any]:
    try:
        from architecture.security import assert_safe_environment
        env = assert_safe_environment()
        return _gate("G6", "Security / PAPER_ONLY", "PASS",
                     "assert_safe_environment ok", env=env if isinstance(env, dict) else str(env))
    except Exception as e:  # noqa: BLE001
        return _gate("G6", "Security / PAPER_ONLY", "FAIL", f"{type(e).__name__}: {e}")


def g7_lane_a() -> dict[str, Any]:
    try:
        from scripts import freeze_lane_a as freeze
        drift, missing, _ = freeze.verify(root=ROOT)
        if drift or missing:
            return _gate(
                "G7", "Lane-A freeze", "FAIL",
                f"drift={sorted(drift)} missing={sorted(missing)}",
            )
        return _gate("G7", "Lane-A freeze", "PASS", "Lane-A integrity OK (pinned)")
    except Exception as e:  # noqa: BLE001
        return _gate("G7", "Lane-A freeze", "FAIL", f"{type(e).__name__}: {e}")


def g10_restart(do_drill: bool) -> dict[str, Any]:
    if not do_drill:
        return _gate(
            "G10", "Restart/recovery", "NOT_VERIFIED",
            "pass --backup-drill to run sqlite_backup_restore drill",
        )
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sqlite_backup_restore.py"), "drill"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=120,
        )
        ok = r.returncode == 0
        return _gate(
            "G10", "Restart/recovery", "PASS" if ok else "FAIL",
            (r.stdout or r.stderr or "")[-500:],
            returncode=r.returncode,
        )
    except Exception as e:  # noqa: BLE001
        return _gate("G10", "Restart/recovery", "FAIL", f"{type(e).__name__}: {e}")


def g11_telegram(platform_name: str) -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return _gate(
            "G11", "Telegram live E2E", "OWNER_ACTION_REQUIRED",
            "TELEGRAM_BOT_TOKEN unset — follow docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md",
            platform=platform_name,
        )
    # Token present does not mean E2E ran — still require human transcript artifact.
    return _gate(
        "G11", "Telegram live E2E", "NOT_VERIFIED",
        "token present in env but live transcript artifact not provided to this runner",
        platform=platform_name,
    )


def g12_n8n() -> dict[str, Any]:
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tests" / "validate_n8n.py")],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60,
        )
        structural = r.returncode == 0
        return _gate(
            "G12", "n8n",
            "STRUCTURAL_VALID" if structural else "FAIL",
            (r.stdout or "")[-400:],
            structural_valid=structural,
            operational_valid=False,
            note="OPERATIONAL_VALID requires live n8n execution (OWNER_ACTION)",
        )
    except Exception as e:  # noqa: BLE001
        return _gate("G12", "n8n", "FAIL", f"{type(e).__name__}: {e}")


def classify(platform_name: str, gates: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {g["id"]: g for g in gates}
    # OPERATOR_READY requires Windows + G1–G10 PASS + G11 live PASS + G12 structural
    required = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11"]
    missing = []
    for gid in required:
        g = by_id.get(gid)
        if g is None:
            missing.append(f"{gid}:absent")
            continue
        st = g["status"]
        if gid == "G11" and st != "PASS":
            missing.append(f"{gid}:{st}")
        elif gid != "G11" and st not in ("PASS",):
            missing.append(f"{gid}:{st}")
    g12 = by_id.get("G12", {})
    if g12.get("status") not in ("PASS", "STRUCTURAL_VALID"):
        missing.append(f"G12:{g12.get('status')}")

    if platform_name != "windows":
        return {
            "classification": "INTEGRATION_READY",
            "operator_ready": False,
            "reason": "platform is not windows — OPERATOR_READY requires OPERATOR_WINDOWS_VERIFIED gates",
            "missing": missing,
        }
    if missing:
        return {
            "classification": "INTEGRATION_READY",
            "operator_ready": False,
            "reason": "required operator gates not all PASS",
            "missing": missing,
        }
    return {
        "classification": "OPERATOR_READY",
        "operator_ready": True,
        "reason": "all required Windows operator gates PASS with artifacts",
        "missing": [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", choices=("agent-host", "windows", "unknown"),
                    default="unknown")
    ap.add_argument("--json-out", default=str(ROOT / "reports" / "operator_validation_report.json"))
    ap.add_argument("--probe-providers", action="store_true")
    ap.add_argument("--skip-network", action="store_true",
                    help="Do not probe gateway HTTP")
    ap.add_argument("--backup-drill", action="store_true")
    args = ap.parse_args(argv)

    # Auto-detect platform hint
    plat = args.platform
    if plat == "unknown":
        plat = "windows" if sys.platform.startswith("win") else "agent-host"

    gates: list[dict[str, Any]] = []
    gates.append(g1_environment())
    gates.append(g2_gateway(skip_network=args.skip_network))
    gates.append(g3_providers(do_probe=args.probe_providers))
    gates.extend(g4_g5_g8_g9_evidence())
    gates.append(g6_security())
    gates.append(g7_lane_a())
    gates.append(g10_restart(do_drill=args.backup_drill))
    gates.append(g11_telegram(plat))
    gates.append(g12_n8n())

    summary = classify(plat, gates)
    report = {
        "schema": SCHEMA,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform_arg": args.platform,
        "platform_effective": plat,
        "host_platform": platform.platform(),
        "head_hint": _git_head(),
        "gates": gates,
        "summary": summary,
        "forbidden_claims": [
            "PRODUCTION_READY",
            "OPERATOR_READY without Windows G1-G11 PASS artifacts",
            "n8n OPERATIONAL_VALID from JSON alone",
            "Telegram live from unit tests alone",
            "Calibration validated with 0 joined_pairs",
        ],
    }

    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "summary": summary}, indent=2))
    for g in gates:
        print(f"{g['id']:4} {g['status']:22} {g['name']}: {g['detail'][:100]}")
    # Exit 0 even when not operator-ready — honesty is the product.
    return 0


def _git_head() -> str | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        )
        return (r.stdout or "").strip() or None
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
