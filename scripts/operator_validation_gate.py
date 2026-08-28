#!/usr/bin/env python3
"""AHOS Operator Validation Gate runner (Windows + agent-host).

Produces a machine-readable report for G1–G12.
Never invents PASS for live Windows/Telegram/n8n-ops/soak.

Exit codes
----------
  0  report written; no gate has status FAIL
  1  unexpected script/runtime error
  2  one or more gates have status FAIL
  3  --platform windows and operator_ready is still false
     (expected until all required Windows gates PASS)

Usage (PowerShell)
------------------
  .\\.venv\\Scripts\\Activate.ps1
  $env:AHOS_EVIDENCE_SOURCE = "local"
  python scripts\\operator_validation_gate.py --platform windows `
    --probe-providers --backup-drill `
    --json-out reports\\operator_validation_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "ahos.operator_validation_report.v1"
ALLOWED_STATUS = (
    "PASS", "FAIL", "BLOCKED", "NOT_VERIFIED", "OWNER_ACTION_REQUIRED",
    "STRUCTURAL_VALID", "SKIPPED",
)


def _gate(gid: str, name: str, status: str, detail: str,
          artifact: str | None = None, **extra: Any) -> dict[str, Any]:
    if status not in ALLOWED_STATUS:
        raise ValueError(f"invalid gate status {status!r}")
    out: dict[str, Any] = {
        "id": gid,
        "name": name,
        "status": status,
        "detail": detail,
        "artifact": artifact,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out.update(extra)
    return out


def _resolve_executable(name: str) -> str | None:
    """Resolve an executable for subprocess (Windows-safe for npm.cmd)."""
    if Path(name).exists():
        return name
    found = shutil.which(name)
    if found:
        return found
    if sys.platform.startswith("win"):
        for suffix in (".cmd", ".exe", ".bat"):
            found = shutil.which(f"{name}{suffix}")
            if found:
                return found
    return None


def _run_cmd(argv: list[str], timeout: float = 30.0) -> tuple[int | None, str, str]:
    """Run a command; return (returncode|None if missing, stdout, stderr)."""
    exe = argv[0]
    resolved = _resolve_executable(exe)
    if resolved is None:
        return None, "", f"executable_not_found:{exe}"

    run_argv: list[str] | str = list(argv)
    use_shell = False
    if isinstance(run_argv, list):
        run_argv[0] = resolved
        # Windows CreateProcess cannot launch .cmd/.bat without a shell.
        if sys.platform.startswith("win") and resolved.lower().endswith((".cmd", ".bat")):
            use_shell = True
            run_argv = subprocess.list2cmdline(run_argv)

    try:
        r = subprocess.run(
            run_argv,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=use_shell,
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except FileNotFoundError:
        return None, "", f"executable_not_found:{exe}"
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except OSError as e:
        return -1, "", f"{type(e).__name__}: {e}"


def g1_environment() -> dict[str, Any]:
    issues: list[str] = []
    blocked: list[str] = []
    py = sys.version.split()[0]
    # Operator handoff requires 3.11+ (matches AHOS_OPERATOR_QUICKSTART_WINDOWS).
    if sys.version_info < (3, 11):
        issues.append(f"python_too_old:{py}_need_3.11+")
    try:
        import architecture  # noqa: F401
    except Exception as e:  # noqa: BLE001
        issues.append(f"import_architecture:{type(e).__name__}:{e}")

    data = ROOT / "data"
    try:
        data.mkdir(parents=True, exist_ok=True)
        probe = data / ".ahos_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as e:
        issues.append(f"data_not_writable:{e}")

    node_rc, node_out, node_err = _run_cmd(["node", "--version"])
    npm_rc, npm_out, npm_err = _run_cmd(["npm", "--version"])
    node_ver = (node_out or "").strip() or None
    npm_ver = (npm_out or "").strip() or None
    if node_rc is None:
        blocked.append("node_not_installed_or_not_on_PATH")
    elif node_rc != 0:
        issues.append(f"node_failed:{node_err.strip() or node_rc}")
    if npm_rc is None:
        blocked.append("npm_not_installed_or_not_on_PATH")
    elif npm_rc != 0:
        issues.append(f"npm_failed:{npm_err.strip() or npm_rc}")

    detail = {
        "python": py,
        "executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "node": node_ver,
        "npm": npm_ver,
        "repo_root": str(ROOT),
        "issues": issues,
        "blocked": blocked,
    }
    if blocked and not issues:
        return _gate(
            "G1", "Environment", "BLOCKED",
            "missing prerequisites: " + ", ".join(blocked),
            **detail,
        )
    if issues or blocked:
        return _gate(
            "G1", "Environment", "FAIL",
            json.dumps({"issues": issues, "blocked": blocked}),
            **detail,
        )
    return _gate("G1", "Environment", "PASS", json.dumps(detail), **detail)


def g2_gateway(skip_network: bool) -> dict[str, Any]:
    if skip_network:
        return _gate(
            "G2", "Gateway", "NOT_VERIFIED",
            "skipped_network_probe; start 'npm run dev' then re-run without --skip-network",
        )
    if _resolve_executable("node") is None:
        return _gate(
            "G2", "Gateway", "BLOCKED",
            "node not on PATH — install Node.js LTS, then: npm install && npm run dev",
        )

    import urllib.error
    import urllib.request

    # Canonical One-Brain chat route (Next.js default port 3000). Not /health.
    raw_url = os.environ.get("AHOS_GATEWAY_URL")
    if raw_url is not None and not raw_url.strip():
        return _gate(
            "G2", "Gateway", "BLOCKED",
            "AHOS_GATEWAY_URL is set but empty — unset it or set "
            "http://127.0.0.1:3000/api/chat",
        )
    url = (raw_url or "http://127.0.0.1:3000/api/chat").strip()

    # One-Brain chat uses Postgres; missing DATABASE_URL yields HTTP 500 while
    # Next is up. Surface that as BLOCKED/OWNER_ACTION rather than "start npm".
    db_url = (os.environ.get("DATABASE_URL") or "").strip()

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"message": "ping", "locale": "fa"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "ahos-opval/1"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read(400).decode("utf-8", "replace")
            if resp.status >= 500:
                return _gate(
                    "G2", "Gateway", "FAIL",
                    f"http_{resp.status} from {url}"
                    + ("" if db_url else " — DATABASE_URL may be unset (required by One-Brain)"),
                    artifact=body[:200], http_status=resp.status, url=url,
                    database_url_set=bool(db_url),
                )
            return _gate(
                "G2", "Gateway", "PASS",
                f"http_{resp.status} from {url}",
                artifact=body[:200], http_status=resp.status, url=url,
                database_url_set=bool(db_url),
            )
    except urllib.error.HTTPError as e:
        # urlopen raises HTTPError for status >= 400 (never reaches resp.status above).
        body = ""
        try:
            body = e.read(400).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            body = ""
        code = int(getattr(e, "code", 0) or 0)
        if code >= 500:
            detail = (
                f"HTTPError {code} from {url}"
                + ("" if db_url else
                   " — set DATABASE_URL for One-Brain (Postgres) then restart npm run dev")
            )
            return _gate(
                "G2", "Gateway", "FAIL",
                detail,
                artifact=body[:200], http_status=code, url=url,
                database_url_set=bool(db_url),
            )
        # 4xx still proves the HTTP process is listening (route/method may differ).
        return _gate(
            "G2", "Gateway", "PASS",
            f"HTTPError {code} from {url} (process reachable; non-5xx)",
            artifact=body[:200], http_status=code, url=url,
            database_url_set=bool(db_url),
        )
    except urllib.error.URLError as e:
        reason = str(getattr(e, "reason", e))
        return _gate(
            "G2", "Gateway", "FAIL",
            f"URLError: {reason} — start One-Brain with: npm run dev "
            "(and set DATABASE_URL in .env)",
            url=url,
            database_url_set=bool(db_url),
        )
    except Exception as e:  # noqa: BLE001
        return _gate(
            "G2", "Gateway", "FAIL",
            f"{type(e).__name__}: {e}",
            url=url,
            database_url_set=bool(db_url),
        )


def g3_providers(do_probe: bool) -> dict[str, Any]:
    if not do_probe:
        return _gate(
            "G3", "Discovery providers", "NOT_VERIFIED",
            "live probe not requested — re-run with --probe-providers",
        )
    try:
        from architecture.providers.probe import probe_providers

        report = probe_providers(chain="solana")
        out_dir = ROOT / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        path = out_dir / f"provider_probe_opval_{stamp}.json"
        path.write_text(
            json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8",
        )
        # PASS only on real SUCCESS with tokens>0 (probe.any_success already encodes that)
        if report.any_success:
            names = [r.provider_id for r in report.successes]
            counts = {n: next(x.token_count for x in report.successes if x.provider_id == n)
                      for n in names}
            return _gate(
                "G3", "Discovery providers", "PASS",
                f"SUCCESS: {', '.join(names)} tokens={counts}",
                artifact=str(path),
                status_counts=report.status_counts(),
                successes=names,
            )
        return _gate(
            "G3", "Discovery providers", "FAIL",
            f"no provider SUCCESS with tokens>0; counts={report.status_counts()}",
            artifact=str(path),
            status_counts=report.status_counts(),
        )
    except Exception as e:  # noqa: BLE001
        return _gate("G3", "Discovery providers", "FAIL", f"{type(e).__name__}: {e}")


def g4_g5_g8_g9_evidence() -> list[dict[str, Any]]:
    try:
        from architecture.learning.prediction_lifecycle import lifecycle_status
        st = lifecycle_status()
    except Exception as e:  # noqa: BLE001
        err = _gate("G4", "Evidence persistence", "FAIL", f"lifecycle_status:{type(e).__name__}:{e}")
        return [
            err,
            _gate("G5", "Scoring / predictions", "FAIL", "skipped_due_to_G4"),
            _gate("G8", "Prediction lifecycle registration", "FAIL", "skipped_due_to_G4"),
            _gate("G9", "Observation lifecycle", "FAIL", "skipped_due_to_G4"),
        ]

    disc_obs = int(st.get("discovery_observations") or 0)
    prod_obs = int(st.get("production_observations") or 0)
    preds = int(st.get("local_predictions") or 0)
    active = sum(int(v) for v in (st.get("observation_state") or {}).values())
    labels = int(st.get("outcome_labels") or 0)

    g4 = _gate(
        "G4", "Evidence persistence",
        "PASS" if (disc_obs > 0 or prod_obs > 0) else "FAIL",
        f"discovery_observations={disc_obs} production_observations={prod_obs}"
        + ("" if (disc_obs or prod_obs) else
           " — run: python -m architecture.runtime --single-cycle "
           "--evidence-source local --limit 5"),
        census=st,
    )
    g5 = _gate(
        "G5", "Scoring / predictions",
        "PASS" if preds > 0 else "FAIL",
        f"local_predictions={preds}"
        + ("" if preds else
           " — run: python -m architecture.runtime --single-cycle --evidence-source local"),
        local_predictions=preds,
    )
    g8 = _gate(
        "G8", "Prediction lifecycle registration",
        "PASS" if active > 0 else "FAIL",
        f"observation_state_total={active} states={st.get('observation_state')}"
        + ("" if active else
           " — run single-cycle (lifecycle bridge) or: "
           "python scripts\\backfill_lane_a_from_production.py"),
    )
    g9 = _gate(
        "G9", "Observation lifecycle",
        "PASS" if disc_obs > 0 else "FAIL",
        f"discovery_observations={disc_obs} outcome_labels={labels} "
        f"(outcome_labels=0 is expected until T+72h RESOLVED — do not fabricate)",
        outcome_labels=labels,
    )
    return [g4, g5, g8, g9]


def g6_security() -> dict[str, Any]:
    try:
        from architecture.security import assert_safe_environment
        env = assert_safe_environment()
        return _gate(
            "G6", "Security / PAPER_ONLY", "PASS",
            "assert_safe_environment ok",
            env=env if isinstance(env, dict) else str(env),
        )
    except Exception as e:  # noqa: BLE001
        return _gate("G6", "Security / PAPER_ONLY", "FAIL", f"{type(e).__name__}: {e}")


def g7_lane_a() -> dict[str, Any]:
    try:
        from scripts import freeze_lane_a as freeze
        drift, missing, untracked = freeze.verify(root=ROOT)
        if drift or missing:
            return _gate(
                "G7", "Lane-A freeze", "FAIL",
                f"drift={sorted(drift)} missing={sorted(missing)}",
            )
        if untracked:
            return _gate(
                "G7", "Lane-A freeze", "FAIL",
                f"untracked={sorted(untracked)} (pending governance re-anchor)",
            )
        return _gate("G7", "Lane-A freeze", "PASS", "Lane-A integrity OK (pinned)")
    except Exception as e:  # noqa: BLE001
        return _gate("G7", "Lane-A freeze", "FAIL", f"{type(e).__name__}: {e}")


def g10_restart(do_drill: bool) -> dict[str, Any]:
    if not do_drill:
        return _gate(
            "G10", "Restart/recovery", "NOT_VERIFIED",
            "backup drill not requested — re-run with --backup-drill",
        )
    script = ROOT / "scripts" / "sqlite_backup_restore.py"
    if not script.is_file():
        return _gate("G10", "Restart/recovery", "BLOCKED", f"missing {script}")
    rc, out, err = _run_cmd([sys.executable, str(script), "drill"], timeout=180.0)
    if rc is None:
        return _gate("G10", "Restart/recovery", "BLOCKED", err)
    text = (out or err)[-500:]
    return _gate(
        "G10", "Restart/recovery", "PASS" if rc == 0 else "FAIL",
        text or f"returncode={rc}",
        returncode=rc,
    )


def g11_telegram(platform_name: str, e2e_artifact: str | None = None) -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return _gate(
            "G11", "Telegram live E2E", "OWNER_ACTION_REQUIRED",
            "TELEGRAM_BOT_TOKEN unset — set in .env (never commit); "
            "then follow docs\\TELEGRAM_OPERATOR_E2E_PROTOCOL.md and archive transcript",
            platform=platform_name,
        )

    # Owner may attest live E2E by pointing at an archived transcript.
    # File presence alone without --telegram-e2e-artifact does NOT auto-PASS.
    if e2e_artifact:
        art = Path(e2e_artifact)
        if not art.is_file():
            return _gate(
                "G11", "Telegram live E2E", "FAIL",
                f"telegram E2E artifact missing: {art}",
                platform=platform_name, artifact=str(art),
            )
        size = art.stat().st_size
        if size < 64:
            return _gate(
                "G11", "Telegram live E2E", "FAIL",
                f"telegram E2E artifact too small ({size} bytes): {art}",
                platform=platform_name, artifact=str(art),
            )
        return _gate(
            "G11", "Telegram live E2E", "PASS",
            "owner-supplied transcript artifact present "
            "(content honesty remains owner responsibility)",
            platform=platform_name, artifact=str(art), bytes=size,
        )

    return _gate(
        "G11", "Telegram live E2E", "NOT_VERIFIED",
        "token present but no --telegram-e2e-artifact supplied "
        "(archive reports\\telegram_e2e_<UTC>.md then re-run with that path)",
        platform=platform_name,
    )


def g12_n8n() -> dict[str, Any]:
    script = ROOT / "tests" / "validate_n8n.py"
    if not script.is_file():
        return _gate("G12", "n8n", "BLOCKED", f"missing {script}")
    rc, out, err = _run_cmd([sys.executable, str(script)], timeout=60.0)
    if rc is None:
        return _gate("G12", "n8n", "BLOCKED", err)
    structural = rc == 0
    return _gate(
        "G12", "n8n",
        "STRUCTURAL_VALID" if structural else "FAIL",
        (out or err)[-400:],
        structural_valid=structural,
        operational_valid=False,
        note="OPERATIONAL_VALID requires live n8n import+execute (OWNER_ACTION) — JSON valid ≠ operational",
    )


def _core_gates_pass(by_id: dict[str, dict[str, Any]]) -> bool:
    """G1–G10 must all be PASS for Windows pre-soak entry (not full OPERATOR_READY)."""
    for i in range(1, 11):
        gid = f"G{i}"
        g = by_id.get(gid)
        if g is None or g.get("status") != "PASS":
            return False
    return True


def classify(platform_name: str, gates: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {g["id"]: g for g in gates}
    required = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11"]
    missing: list[str] = []
    for gid in required:
        g = by_id.get(gid)
        if g is None:
            missing.append(f"{gid}:absent")
            continue
        st = g["status"]
        if gid == "G11":
            # Runner never auto-PASS Telegram; owner archives E2E then marks PASS.
            if st != "PASS":
                missing.append(f"{gid}:{st}")
        elif st != "PASS":
            missing.append(f"{gid}:{st}")
    g12 = by_id.get("G12", {})
    if g12.get("status") not in ("PASS", "STRUCTURAL_VALID"):
        missing.append(f"G12:{g12.get('status')}")

    g1_g10 = _core_gates_pass(by_id)
    # Pre-soak may start after Windows G1–G10 PASS; OPERATOR_READY still needs G11.
    pre_soak_entry_ok = platform_name == "windows" and g1_g10

    base = {
        "g1_g10_all_pass": g1_g10,
        "pre_soak_entry_ok": pre_soak_entry_ok,
        "missing": missing,
    }

    if platform_name != "windows":
        return {
            **base,
            "classification": "INTEGRATION_READY",
            "operator_ready": False,
            "reason": "platform is not windows — OPERATOR_READY requires Windows gate artifacts",
        }
    if missing:
        return {
            **base,
            "classification": "INTEGRATION_READY",
            "operator_ready": False,
            "reason": (
                "Windows G1–G10 PASS — pre-soak entry OK; G11 still required for OPERATOR_READY"
                if pre_soak_entry_ok
                else "required Windows operator gates not all PASS"
            ),
        }
    return {
        **base,
        "classification": "OPERATOR_READY",
        "operator_ready": True,
        "reason": "all required Windows operator gates PASS with artifacts",
        "missing": [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", choices=("agent-host", "windows", "unknown"),
                    default="unknown")
    ap.add_argument(
        "--json-out",
        default=None,
        help="Output JSON path. Default: reports/operator_validation_report_<platform>_<UTC>.json",
    )
    ap.add_argument("--probe-providers", action="store_true",
                    help="Required for G3 PASS — runs live provider probe")
    ap.add_argument("--skip-network", action="store_true",
                    help="Skip G2 HTTP probe (leaves G2 NOT_VERIFIED)")
    ap.add_argument("--backup-drill", action="store_true",
                    help="Required for G10 PASS — runs sqlite backup drill")
    ap.add_argument(
        "--telegram-e2e-artifact",
        default=None,
        help="Path to archived live Telegram transcript (owner attestation for G11 PASS)",
    )
    args = ap.parse_args(argv)

    plat = args.platform
    if plat == "unknown":
        plat = "windows" if sys.platform.startswith("win") else "agent-host"

    if args.json_out is None:
        stamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        args.json_out = str(
            ROOT / "reports" / f"operator_validation_report_{plat}_{stamp}.json"
        )

    try:
        gates: list[dict[str, Any]] = []
        gates.append(g1_environment())
        gates.append(g2_gateway(skip_network=args.skip_network))
        gates.append(g3_providers(do_probe=args.probe_providers))
        gates.extend(g4_g5_g8_g9_evidence())
        gates.append(g6_security())
        gates.append(g7_lane_a())
        gates.append(g10_restart(do_drill=args.backup_drill))
        gates.append(g11_telegram(plat, e2e_artifact=args.telegram_e2e_artifact))
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
            "exit_code_legend": {
                "0": "report written; no FAIL gates",
                "1": "unexpected script error",
                "2": "one or more FAIL gates",
                "3": "windows platform and operator_ready still false",
            },
            "forbidden_claims": [
                "PRODUCTION_READY",
                "OPERATOR_READY without Windows G1-G11 PASS artifacts",
                "n8n OPERATIONAL_VALID from JSON alone",
                "Telegram live from unit tests alone",
                "Calibration validated with 0 joined_pairs",
                "Agent-host SUCCESS as OPERATOR_WINDOWS_VERIFIED",
            ],
        }

        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"wrote": str(out), "summary": summary}, indent=2))
        for g in gates:
            print(f"{g['id']:4} {g['status']:22} {g['name']}: {g['detail'][:120]}")

        if any(g["status"] == "FAIL" for g in gates):
            return 2
        if plat == "windows" and not summary.get("operator_ready"):
            return 3
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"operator_validation_gate fatal: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


def _git_head() -> str | None:
    rc, out, _ = _run_cmd(["git", "rev-parse", "--short", "HEAD"], timeout=10.0)
    if rc == 0:
        return (out or "").strip() or None
    return None


if __name__ == "__main__":
    raise SystemExit(main())
