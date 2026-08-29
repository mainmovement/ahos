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
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=use_shell,
            env={
                **os.environ,
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8",
            },
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
        "database_url_set": bool((os.environ.get("DATABASE_URL") or "").strip()),
        "web_api_token_set": bool((os.environ.get("AHOS_WEB_API_TOKEN") or "").strip()),
        "web_api_auth_module_present": (ROOT / "web_api_auth.ts").is_file(),
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


def _web_api_auth_blocked(code: int, body: str, url: str, *,
                          token_set: bool, db_url_set: bool) -> dict[str, Any] | None:
    """401 from Lane-B fail-closed gate is NOT a usable gateway PASS."""
    if code != 401:
        return None
    blob = (body or "").upper()
    if "WEB_API_LOCKED_NO_TOKEN" in blob:
        return _gate(
            "G2", "Gateway", "BLOCKED",
            "HTTP 401 WEB_API_LOCKED_NO_TOKEN — set AHOS_WEB_API_TOKEN and "
            "NEXT_PUBLIC_AHOS_WEB_API_TOKEN (same value) in .env, or run "
            "scripts\\windows_ensure_web_api_token.ps1, then restart npm run dev",
            artifact=body[:200], http_status=code, url=url,
            database_url_set=db_url_set, web_api_token_set=token_set,
        )
    if "WEB_API_UNAUTHORIZED" in blob or "WEB_API" in blob:
        return _gate(
            "G2", "Gateway", "BLOCKED",
            "HTTP 401 WEB_API_UNAUTHORIZED — probe must send Authorization: Bearer "
            "matching AHOS_WEB_API_TOKEN (loaded from .env). Restart Next after "
            "setting the token.",
            artifact=body[:200], http_status=code, url=url,
            database_url_set=db_url_set, web_api_token_set=token_set,
        )
    return None


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
    # Empty AHOS_GATEWAY_URL= (common from older .env.example) must NOT BLOCK:
    # treat blank as unset and use the local PAPER_ONLY default.
    raw_url = (os.environ.get("AHOS_GATEWAY_URL") or "").strip()
    url = raw_url or "http://127.0.0.1:3000/api/chat"

    # One-Brain chat uses Postgres; missing DATABASE_URL yields HTTP 500 while
    # Next is up. Surface that as BLOCKED/OWNER_ACTION rather than "start npm".
    db_url = (os.environ.get("DATABASE_URL") or "").strip()
    web_token = (os.environ.get("AHOS_WEB_API_TOKEN") or "").strip()
    open_raw = (os.environ.get("AHOS_WEB_API_ALLOW_OPEN_ACCESS") or "").strip().lower()
    open_access = open_raw in {"1", "true", "yes", "on"}
    # After Lane-B auth land, empty token without open-access cannot PASS G2.
    if (ROOT / "web_api_auth.ts").is_file() and not web_token and not open_access:
        return _gate(
            "G2", "Gateway", "BLOCKED",
            "AHOS_WEB_API_TOKEN unset and AHOS_WEB_API_ALLOW_OPEN_ACCESS not enabled — "
            "run: powershell -ExecutionPolicy Bypass -File "
            ".\\scripts\\windows_ensure_web_api_token.ps1 then restart npm run dev",
            url=url,
            database_url_set=bool(db_url),
            web_api_token_set=False,
            web_api_open_access=False,
        )
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ahos-opval/1",
    }
    if web_token:
        headers["Authorization"] = f"Bearer {web_token}"

    # When DATABASE_URL is set, retries cover Docker/Postgres just-became-ready
    # races and Next restart after windows_recover_g2_warm (STATE B: no invent PASS).
    attempts = 8 if db_url else 1
    last_fail: dict[str, Any] | None = None

    def _artifact_snippet(raw: str) -> str:
        text = (raw or "")[:800]
        # Prefer structured chat 500 fields when present.
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                bits = []
                for k in ("error", "message", "stack_top", "code"):
                    v = obj.get(k)
                    if v:
                        bits.append(f"{k}={v}")
                if bits:
                    return "; ".join(bits)[:800]
        except Exception:  # noqa: BLE001
            pass
        return text

    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({"message": "ping", "locale": "fa"}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read(1200).decode("utf-8", "replace")
                if resp.status >= 500:
                    last_fail = _gate(
                        "G2", "Gateway", "FAIL",
                        f"http_{resp.status} from {url}"
                        + ("" if db_url else
                           " -- DATABASE_URL may be unset (required by One-Brain)"),
                        artifact=_artifact_snippet(body), http_status=resp.status, url=url,
                        database_url_set=bool(db_url), web_api_token_set=bool(web_token),
                        attempt=attempt,
                    )
                else:
                    return _gate(
                        "G2", "Gateway", "PASS",
                        f"http_{resp.status} from {url}",
                        artifact=body[:200], http_status=resp.status, url=url,
                        database_url_set=bool(db_url), web_api_token_set=bool(web_token),
                        attempt=attempt,
                    )
        except urllib.error.HTTPError as e:
            # urlopen raises HTTPError for status >= 400 (never reaches resp.status above).
            body = ""
            try:
                body = e.read(1200).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                body = ""
            code = int(getattr(e, "code", 0) or 0)
            blocked = _web_api_auth_blocked(
                code, body, url, token_set=bool(web_token), db_url_set=bool(db_url),
            )
            if blocked is not None:
                return blocked
            if code >= 500:
                detail = f"HTTPError {code} from {url}"
                if not db_url:
                    detail += (
                        " -- set DATABASE_URL for One-Brain (Postgres) then restart npm run dev"
                    )
                else:
                    detail += (
                        " -- DATABASE_URL is set but Postgres unreachable; start Docker Desktop "
                        "Linux Engine + ahos_postgres_win (STATE B: no db:migrate/db:push), "
                        "then run scripts\\windows_recover_g2_warm.ps1"
                    )
                snip = _artifact_snippet(body)
                if snip:
                    detail += f" | {snip}"
                last_fail = _gate(
                    "G2", "Gateway", "FAIL",
                    detail,
                    artifact=snip or body[:200], http_status=code, url=url,
                    database_url_set=bool(db_url), web_api_token_set=bool(web_token),
                    attempt=attempt,
                )
            else:
                # Other 4xx still proves the HTTP process is listening.
                return _gate(
                    "G2", "Gateway", "PASS",
                    f"HTTPError {code} from {url} (process reachable; non-5xx)",
                    artifact=body[:200], http_status=code, url=url,
                    database_url_set=bool(db_url), web_api_token_set=bool(web_token),
                    attempt=attempt,
                )
        except urllib.error.URLError as e:
            reason = str(getattr(e, "reason", e))
            last_fail = _gate(
                "G2", "Gateway", "FAIL",
                f"URLError: {reason} -- start One-Brain with: npm run dev "
                "(and set DATABASE_URL in .env)",
                url=url,
                database_url_set=bool(db_url), web_api_token_set=bool(web_token),
                attempt=attempt,
            )
        except Exception as e:  # noqa: BLE001
            return _gate(
                "G2", "Gateway", "FAIL",
                f"{type(e).__name__}: {e}",
                url=url,
                database_url_set=bool(db_url), web_api_token_set=bool(web_token),
                attempt=attempt,
            )

        if attempt < attempts:
            time.sleep(2)

    return last_fail or _gate(
        "G2", "Gateway", "FAIL",
        f"no successful probe of {url} after {attempts} attempt(s)",
        url=url,
        database_url_set=bool(db_url), web_api_token_set=bool(web_token),
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


def remediation_actions(gates: list[dict[str, Any]]) -> list[str]:
    """Concrete owner next steps for non-PASS gates (Windows console-safe ASCII)."""
    by = {g["id"]: g for g in gates}
    out: list[str] = []
    g2 = by.get("G2") or {}
    if g2.get("status") in ("BLOCKED", "FAIL", "NOT_VERIFIED"):
        d = (g2.get("detail") or "")
        if "WEB_API" in d or "AHOS_WEB_API_TOKEN" in d:
            out.append(
                "G2: run scripts\\windows_ensure_web_api_token.ps1, restart npm run dev, "
                "re-run gate (do NOT db:migrate)."
            )
        elif "DATABASE_URL" in d or (g2.get("http_status") or 0) >= 500:
            out.append(
                "G2: powershell -ExecutionPolicy Bypass -File "
                ".\\scripts\\windows_recover_g2_warm.ps1 "
                "(forensics + ensure-pg + DATABASE_URL probe-first + Next restart; "
                "Docker health PASS is not enough — Next needs working DATABASE_URL; "
                "STATE B: no migrate)."
            )
        elif g2.get("status") == "NOT_VERIFIED":
            out.append("G2: start npm run dev on 127.0.0.1:3000 then re-run without --skip-network.")
        else:
            out.append(
                "G2: ensure npm run dev is up and AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat."
            )
    g3 = by.get("G3") or {}
    if g3.get("status") != "PASS":
        out.append("G3: re-run with --probe-providers and working HTTPS (DexScreener/Gecko).")
    for gid, hint in (
        ("G4", "G4: python -m architecture.runtime --single-cycle --evidence-source local --limit 5"),
        ("G5", "G5: same single-cycle until local_predictions > 0"),
        ("G8", "G8: single-cycle / lifecycle bridge until observation_state_total > 0"),
        ("G9", "G9: need discovery_observations > 0 (outcome_labels=0 OK until T+72h)"),
        ("G6", "G6: set AHOS_PAPER_ONLY=1; unset live-trading flags"),
        ("G7", "G7: Lane-A freeze drift — do not edit discovery/ or paper_trading/"),
        ("G10", "G10: re-run with --backup-drill"),
    ):
        g = by.get(gid) or {}
        if g.get("status") not in (None, "PASS"):
            out.append(hint)
    g11 = by.get("G11") or {}
    if g11.get("status") != "PASS":
        out.append(
            "G11: set TELEGRAM_BOT_TOKEN + allowlist, archive E2E transcript, "
            "re-run with --telegram-e2e-artifact reports\\telegram_e2e_<UTC>.md "
            "(needed for OPERATOR_READY; pre-soak only needs G1-G10)."
        )
    if not out:
        out.append("All remediated gates clear — if Windows G1-G10 PASS, follow docs\\PRE_SOAK_PROTOCOL.md.")
    out.append("Never claim OPERATOR_READY without Windows G1-G11 PASS artifacts.")
    out.append("STATE B: never db:migrate / db:push without Cursor classification.")
    return out


def classify(
    platform_name: str,
    gates: list[dict[str, Any]],
    *,
    host_is_windows: bool | None = None,
) -> dict[str, Any]:
    """Classify gate results.

    PRE_SOAK / OPERATOR_READY require BOTH ``platform_name==\"windows\"`` AND a
    real Windows host. Claiming ``--platform windows`` on Linux/macOS must not
    invent pre_soak_entry_ok or OPERATOR_READY.
    """
    if host_is_windows is None:
        host_is_windows = sys.platform.startswith("win")

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
    claimed_windows = platform_name == "windows"
    windows_attested = claimed_windows and bool(host_is_windows)
    if claimed_windows and not host_is_windows:
        missing.append("host:not_windows(--platform windows on non-Windows host)")

    # Pre-soak may start after attested Windows G1–G10 PASS; OPERATOR_READY still needs G11.
    pre_soak_entry_ok = windows_attested and g1_g10
    remediations = remediation_actions(gates)

    base = {
        "g1_g10_all_pass": g1_g10,
        "pre_soak_entry_ok": pre_soak_entry_ok,
        "missing": missing,
        "remediation_actions": remediations,
        "host_is_windows": bool(host_is_windows),
        "windows_attested": windows_attested,
    }

    if not claimed_windows:
        return {
            **base,
            "classification": "INTEGRATION_READY",
            "operator_ready": False,
            "reason": "platform is not windows — OPERATOR_READY requires Windows gate artifacts",
        }
    if not host_is_windows:
        return {
            **base,
            "classification": "INTEGRATION_READY",
            "operator_ready": False,
            "reason": (
                "--platform windows on non-Windows host — refusing PRE_SOAK/OPERATOR_READY "
                "(run the gate on the Windows laptop)"
            ),
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

    # Load root .env so AHOS_WEB_API_TOKEN / DATABASE_URL reach G2 without manual $env.
    # Force-overwrite auth/DB keys so a stale shell export cannot beat .env (G2 401 trap).
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

    # Normalize empty AHOS_GATEWAY_URL= from older .env.example (G2 must not BLOCK).
    if not (os.environ.get("AHOS_GATEWAY_URL") or "").strip():
        os.environ["AHOS_GATEWAY_URL"] = "http://127.0.0.1:3000/api/chat"
        if _persist_env_key(ROOT / ".env", "AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat"):
            print(
                "Normalized empty AHOS_GATEWAY_URL in .env -> "
                "http://127.0.0.1:3000/api/chat",
                flush=True,
            )

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

        summary = classify(plat, gates, host_is_windows=sys.platform.startswith("win"))
        report = {
            "schema": SCHEMA,
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform_arg": args.platform,
            "platform_effective": plat,
            "host_platform": platform.platform(),
            "host_is_windows": sys.platform.startswith("win"),
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
        latest_paths: list[Path] = []
        if plat == "windows":
            pointer_body = "\n".join(
                [
                    f"report={out.resolve()}",
                    f"pre_soak_entry_ok={summary.get('pre_soak_entry_ok')}",
                    f"operator_ready={summary.get('operator_ready')}",
                    f"classification={summary.get('classification')}",
                    "Paste this report JSON into Cursor.",
                    "STATE B: do not db:migrate / db:push.",
                    "",
                ]
            )
            # Prefer beside the JSON (tests + custom --json-out); also pin under reports/.
            for latest in (
                out.parent / "LATEST_WINDOWS_GATE.txt",
                ROOT / "reports" / "LATEST_WINDOWS_GATE.txt",
            ):
                try:
                    if latest.resolve() in {p.resolve() for p in latest_paths}:
                        continue
                except OSError:
                    pass
                latest.parent.mkdir(parents=True, exist_ok=True)
                latest.write_text(pointer_body, encoding="utf-8")
                latest_paths.append(latest)
            try:
                status_path = _write_pre_soak_status(summary, gates)
                print(f"PRE_SOAK_STATUS: {status_path}", flush=True)
            except OSError as e:
                print(f"PRE_SOAK_STATUS write skipped: {e}", flush=True)
        print(json.dumps({"wrote": str(out), "summary": summary}, indent=2))
        for g in gates:
            print(f"{g['id']:4} {g['status']:22} {g['name']}: {g['detail'][:120]}")
        print("===== OWNER_NEXT (paste with JSON into Cursor) =====")
        for line in summary.get("remediation_actions") or []:
            print(f"- {line}")
        print("===== END OWNER_NEXT =====")
        if latest_paths:
            print(f"LATEST_POINTER: {latest_paths[0]}")

        if any(g["status"] == "FAIL" for g in gates):
            return 2
        if plat == "windows" and not summary.get("operator_ready"):
            return 3
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"operator_validation_gate fatal: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


def _persist_env_key(env_path: Path, key: str, value: str) -> bool:
    """Set KEY=value in .env (create/replace line). ASCII-safe. Returns True if wrote."""
    try:
        raw = ""
        if env_path.is_file():
            raw = env_path.read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines()
        prefix = key + "="
        out: list[str] = []
        found = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("#"):
                out.append(line)
                continue
            if stripped.startswith(prefix) or line.startswith(prefix):
                out.append(prefix + value)
                found = True
            else:
                out.append(line)
        if not found:
            if out and out[-1].strip() != "":
                out.append("")
            out.append(prefix + value)
        env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def _write_pre_soak_status(summary: dict[str, Any], gates: list[dict[str, Any]]) -> Path:
    """ASCII status file for Windows owner — does not invent READY."""
    reports = ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / "PRE_SOAK_STATUS.txt"
    by = {g["id"]: g for g in gates}
    lines = [
        "AHOS PRE_SOAK STATUS (PAPER_ONLY)",
        "================================",
        f"host_is_windows={summary.get('host_is_windows')}",
        f"pre_soak_entry_ok={summary.get('pre_soak_entry_ok')}",
        f"operator_ready={summary.get('operator_ready')}",
        f"classification={summary.get('classification')}",
        "STATE B: do not db:migrate / db:push",
        "",
        "G1-G10 (need all PASS for PRE_SOAK):",
    ]
    for i in range(1, 11):
        gid = f"G{i}"
        g = by.get(gid) or {}
        lines.append(f"  {gid} {g.get('status', 'MISSING')}")
    lines.append(
        f"  G11 {((by.get('G11') or {}).get('status', 'MISSING'))} (OPERATOR_READY only)"
    )
    lines.append(
        f"  G12 {((by.get('G12') or {}).get('status', 'MISSING'))} (informational)"
    )
    lines.append("")
    if summary.get("pre_soak_entry_ok"):
        lines.append("VERDICT: PRE_SOAK entry OK on this Windows host.")
        lines.append("Paste reports\\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38.")
    else:
        lines.append("VERDICT: NOT PRE_SOAK yet.")
        for line in summary.get("remediation_actions") or []:
            lines.append(f"- {line}")
        lines.append("")
        lines.append("Owner unlock (try main first, then tip):")
        lines.append("  git pull origin main")
        lines.append(
            "  powershell -NoProfile -ExecutionPolicy Bypass -File "
            ".\\scripts\\windows_ensure_web_api_token.ps1"
        )
        lines.append("  AHOS_PRE_SOAK_NOW.bat")
        lines.append("  Or tip surgical:")
        lines.append(
            "  curl.exe -L -o AHOS_FIX_G2_AND_GATE.bat "
            "https://raw.githubusercontent.com/mainmovement/ahos/"
            "cursor/windows-evidence-notify-retarget-4bde/AHOS_FIX_G2_AND_GATE.bat"
        )
        lines.append("  AHOS_FIX_G2_AND_GATE.bat")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _git_head() -> str | None:
    rc, out, _ = _run_cmd(["git", "rev-parse", "--short", "HEAD"], timeout=10.0)
    if rc == 0:
        return (out or "").strip() or None
    return None


if __name__ == "__main__":
    raise SystemExit(main())
