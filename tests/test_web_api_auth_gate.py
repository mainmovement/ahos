#!/usr/bin/env python3
"""Static + Telegram wiring checks for Lane-B web API auth gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import telegram_ai.service as svc_mod
from telegram_ai.service import TelegramDomainService
from telegram_ai.response_contract import FOOTER_MANDATED

API_ROUTES = sorted((ROOT / "app" / "api").glob("*/route.ts"))


def test_all_api_routes_call_authorize_web_api():
    assert API_ROUTES, "expected app/api/*/route.ts"
    for path in API_ROUTES:
        text = path.read_text(encoding="utf-8")
        assert "authorizeWebApi" in text, f"{path.name} missing authorizeWebApi"
        assert "from \"@/web_api_auth\"" in text or "from '@/web_api_auth'" in text


def test_command_center_uses_web_api_client():
    text = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")
    assert "webApiFetch" in text
    assert 'fetch("/api/' not in text


def test_package_json_binds_next_to_loopback():
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "--hostname 127.0.0.1" in pkg["scripts"]["dev"]
    assert "--hostname 127.0.0.1" in pkg["scripts"]["start"]


def test_windows_ensure_web_api_token_script_exists():
    path = ROOT / "scripts" / "windows_ensure_web_api_token.ps1"
    text = path.read_text(encoding="utf-8")
    assert "AHOS_WEB_API_TOKEN" in text
    assert "NEXT_PUBLIC_AHOS_WEB_API_TOKEN" in text
    assert "db:migrate" in text.lower() or "Will NOT migrate" in text


def test_windows_ops_toward_pre_soak_script_exists():
    path = ROOT / "scripts" / "windows_ops_toward_pre_soak.ps1"
    text = path.read_text(encoding="utf-8")
    assert "web_api_auth.ts" in text
    assert "windows_ensure_web_api_token.ps1" in text
    assert "operator_validation_gate.py" in text
    assert "OPERATOR_READY" in text


def test_windows_run_operator_gate_script_exists():
    path = ROOT / "scripts" / "windows_run_operator_gate.ps1"
    text = path.read_text(encoding="utf-8")
    assert "--platform" in text and "windows" in text
    assert "operator_validation_gate.py" in text
    assert "probe-providers" in text
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in text
    assert "LATEST_WINDOWS_GATE.txt" in text
    assert "Set-Clipboard" in text
    assert "notepad.exe" in text
    assert "Env:AHOS_WEB_API_TOKEN" in text or 'Set-Item -Path ("Env:"' in text
    assert "windows_post_gate_paste_gh.ps1" in text or "gh pr comment" in text
    assert "windows_telegram_send_gate_paste.ps1" in text
    assert "OWNER_PASTE_WINDOWS_GATE_SLIM" in text


def test_windows_telegram_send_gate_paste_script_exists():
    path = ROOT / "scripts" / "windows_telegram_send_gate_paste.ps1"
    text = path.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "TELEGRAM_ALLOWED_CHAT_IDS" in text
    assert "sendDocument" in text
    assert "OPERATOR_READY" in text or "NOT OPERATOR_READY" in text or "NOT READY" in text
    assert "db:migrate" in text.lower() or "Does not migrate" in text


def test_windows_g11_telegram_e2e_helper_exists():
    path = ROOT / "scripts" / "windows_g11_telegram_e2e_helper.ps1"
    text = path.read_text(encoding="utf-8")
    assert "telegram_e2e_" in text
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "TelegramE2eArtifact" in text or "telegram-e2e-artifact" in text
    assert "OPERATOR_READY" in text
    assert "db:migrate" in text.lower()


def test_windows_preflight_ops_script_exists():
    path = ROOT / "scripts" / "windows_preflight_ops.ps1"
    text = path.read_text(encoding="utf-8")
    assert "AHOS_WEB_API_TOKEN" in text
    assert "DATABASE_URL" in text
    assert "web_api_auth.ts" in text
    assert "db:migrate" in text.lower() or "do NOT db:migrate" in text
    assert "sqlite_evidence" in text or "e01_discovery" in text
    assert "pg_isready" in text


def test_windows_ops_bat_auto_starts_next_and_runs_gate():
    text = (ROOT / "AHOS_WINDOWS_OPS.bat").read_text(encoding="utf-8", errors="replace")
    assert "windows_post_merge_reconcile.ps1" in text
    assert "KeepCurrentBranch" in text
    assert "windows_preflight_ops.ps1" in text
    assert "windows_restart_next_dev.ps1" in text or "npm run dev" in text
    assert "127.0.0.1:3000" in text
    assert "/api/chat" in text
    assert "windows_seed_local_evidence.ps1" in text
    assert "windows_wait_for_web_api.ps1" in text or "/api/chat" in text
    assert "windows_ensure_postgres_win.ps1" in text
    assert "windows_run_operator_gate.ps1" in text
    assert "windows_ops_last_run.log" in text or "LOG=" in text
    assert "windows_write_ops_failure_paste.ps1" in text or "failpaste" in text
    assert "windows_validate_ps1_parse.ps1" in text
    assert 'checkout origin/main -- "scripts/windows_*.ps1"' in text or "force-sync" in text.lower() or "windows_*.ps1" in text
    assert "AHOS_PRE_SOAK_NOW.bat" in text  # force-sync unlock launcher too
    assert "one recovery" in text.lower() or "Recovery warm" in text
    assert "db:migrate" in text.lower()
    assert "OPERATOR_READY" in text


def test_windows_validate_ps1_parse_script_exists():
    path = ROOT / "scripts" / "windows_validate_ps1_parse.ps1"
    text = path.read_bytes()
    assert text.startswith(b"\xef\xbb\xbf"), "validator should have UTF-8 BOM"
    body = text[3:].decode("utf-8")
    assert "Parser]::ParseFile" in body or "ParseFile" in body
    assert "PARSE_PREFLIGHT_OK" in body
    assert "db:migrate" in body.lower()
    assert "OPERATOR_READY" in body or "READY" in body


def test_windows_publish_owner_paste_helper_exists():
    path = ROOT / "scripts" / "windows_publish_owner_paste.ps1"
    text = path.read_text(encoding="utf-8")
    assert "AHOS_PASTE_TO_CURSOR.txt" in text
    assert "Desktop" in text
    assert "Set-Clipboard" in text
    assert "notepad.exe" in text


def test_windows_push_gate_evidence_helper_exists():
    path = ROOT / "scripts" / "windows_push_gate_evidence.ps1"
    text = path.read_text(encoding="utf-8-sig")
    assert "windows-gate-evidence-4bde" in text
    assert "windows_gate_evidence" in text
    assert "force-with-lease" in text
    assert "commit-tree" in text
    assert "GIT_INDEX_FILE" in text or "ahos-evidence-index" in text
    assert "checkout -B" not in text  # must not leave owner branch
    assert "OPERATOR_READY" in text
    assert "db:migrate" in text.lower() or "no migrate" in text.lower()
    # Lease against fetched origin tip so laptop pushes do not silently no-op
    assert "origin/" in text and "fetch origin" in text
    assert "NOTIFY_UNLOCK" in text or "gh pr comment" in text
    runner = (ROOT / "scripts" / "windows_run_operator_gate.ps1").read_text(encoding="utf-8")
    assert "windows_push_gate_evidence.ps1" in runner


def test_windows_ops_bat_pulls_current_branch_too():
    text = (ROOT / "AHOS_WINDOWS_OPS.bat").read_text(encoding="utf-8", errors="replace")
    assert "git pull origin main" in text
    assert "CURBRANCH" in text or "abbrev-ref" in text
    assert "windows_publish_owner_paste.ps1" in (ROOT / "scripts" / "windows_run_operator_gate.ps1").read_text(encoding="utf-8")
    # Regression: main historically wrote OWNER_PASTE then exited without pushing
    # evidence — agents never woke. End-of-run + failpaste must push.
    assert "windows_push_gate_evidence.ps1" in text
    assert text.lower().count("windows_push_gate_evidence.ps1") >= 2
    assert "evidence push" in text.lower()


def test_windows_main_first_bat_exists():
    bat = (ROOT / "AHOS_MAIN_FIRST.bat").read_text(encoding="utf-8")
    assert "git pull origin main" in bat
    assert "windows_ensure_web_api_token.ps1" in bat
    assert "AHOS_PRE_SOAK_NOW.bat" in bat
    assert "db:migrate" in bat.lower()
    assert "windows_push_gate_evidence.ps1" in bat
    # Overlay tip OPS before PRE_SOAK so mid-run push works when main lacks it
    assert "AHOS_WINDOWS_OPS.bat" in bat
    assert "windows-main-evidence-push-4bde" in bat
    assert "named files" in bat.lower() or "TIPREF" in bat


def test_windows_pre_soak_now_prefers_evidence_push_tip():
    bat = (ROOT / "AHOS_PRE_SOAK_NOW.bat").read_text(encoding="utf-8")
    assert "windows-main-evidence-push-4bde" in bat
    # Prefer evidence-push tip ahead of older unlocks already on main
    idx_push = bat.find("windows-main-evidence-push-4bde")
    idx_old = bat.find("windows-g2-empty-gateway-default-4bde")
    assert idx_push != -1 and idx_old != -1 and idx_push < idx_old


def test_windows_fix_g2_and_gate_on_same_tip():
    bat = (ROOT / "AHOS_FIX_G2_AND_GATE.bat").read_text(encoding="utf-8")
    assert "windows-main-evidence-push-4bde" in bat
    assert "windows_fix_g2_empty_and_gate.ps1" in bat
    assert "db:migrate" in bat.lower()
    fix = (ROOT / "scripts" / "windows_fix_g2_empty_and_gate.ps1").read_text(
        encoding="utf-8-sig"
    )
    assert "windows-main-evidence-push-4bde" in fix
    assert "windows_checkout_unlock_tip.ps1" in fix
    assert "windows_recover_g2_warm.ps1" in fix
    assert "windows_restart_next_dev.ps1" in fix
    assert "restart Next so .env" in fix
    assert "windows_run_operator_gate.ps1" in fix
    assert "windows_push_gate_evidence.ps1" in fix
    assert "db:migrate" in fix.lower()


def test_windows_checkout_unlock_tip_uses_ls_tree():
    text = (ROOT / "scripts" / "windows_checkout_unlock_tip.ps1").read_text(
        encoding="utf-8-sig"
    )
    assert "ls-tree" in text
    assert "windows_*.ps1" in text
    assert "AHOS_WINDOWS_OPS.bat" in text
    assert "db:migrate" in text.lower()


def test_windows_bootstrap_presoak_script_exists():
    text = (ROOT / "scripts" / "windows_bootstrap_presoak.ps1").read_text(
        encoding="utf-8-sig"
    )
    assert "windows-main-evidence-push-4bde" in text
    assert "AHOS_PRE_SOAK_NOW.bat" in text
    assert "db:migrate" in text.lower()
    assert "ls-tree" in text


def test_windows_ensure_database_url_realigns_via_docker_exec():
    text = (ROOT / "scripts" / "windows_ensure_database_url.ps1").read_text(
        encoding="utf-8-sig"
    )
    assert "ALTER ROLE" in text
    assert "docker exec" in text
    assert "db:migrate" in text.lower()
    assert "ahos_postgres_win" in text


def test_api_chat_retries_transient_pg_once():
    text = (ROOT / "app" / "api" / "chat" / "route.ts").read_text(encoding="utf-8")
    assert "isTransientPgError" in text
    assert "one retry" in text.lower() or "750" in text
    assert "windows_recover_g2_warm" in text



def test_owner_card_and_one_liner_point_at_pr58():
    card = (ROOT / "reports" / "OWNER_CARD_WEB_API_AUTH_PRE_SOAK_FA.md").read_text(encoding="utf-8")
    assert "windows-main-evidence-push-4bde" in card
    assert "AHOS_RUN_TIP.ps1" in card
    assert "#56" in card
    one = (ROOT / "OWNER_ONE_LINER.txt").read_text(encoding="utf-8")
    assert "AHOS_RUN_TIP.cmd" in one or "AHOS_RUN_TIP.ps1" in one
    assert "AHOS_MAIN_CLEAR_G2.cmd" in one
    assert "windows-main-evidence-push-4bde" in one
    assert "db:migrate" in one.lower()
    assert "AHOS_MAIN_FIRST.bat" in one
    assert "220318" in one or "#45" in one
    push = (ROOT / "scripts" / "windows_push_gate_evidence.ps1").read_text(encoding="utf-8-sig")
    assert "windows-main-evidence-push-4bde" in push


def test_ahos_main_clear_g2_cmd_is_crlf_main_only():
    raw = (ROOT / "AHOS_MAIN_CLEAR_G2.cmd").read_bytes()
    assert b"\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")
    text = raw.decode("ascii")
    assert "git pull origin main" in text
    assert "git checkout origin/main --" in text
    assert "windows_ensure_web_api_token.ps1" in text
    assert "windows_run_operator_gate.ps1" in text
    assert "validate_n8n.py" in text  # G12 charmap fix on main
    assert "windows_restart_next_dev.ps1" in text
    assert "windows_wait_for_web_api.ps1" in text
    assert "restart Next so .env" in text
    assert "PYTHONUTF8=1" in text
    assert "AHOS_GATE_PR=56" in text
    assert "windows_post_gate_paste_gh.ps1" in text
    assert "db:migrate" in text.lower()
    assert "OWNER_PASTE" in text
    assert "#56" in text
    # Runtime path must not git-fetch the tip branch (curl URL / SHA pin for overlay is ok)
    runtime = "\n".join(
        ln for ln in text.splitlines() if not ln.strip().upper().startswith("REM")
    )
    assert "git fetch origin cursor/" not in runtime
    # May curl tip SHA for post_gate overlay, but must not require tip branch git fetch
    assert "git fetch origin cursor/windows-main-evidence-push-4bde" not in runtime
    # Refuse pre-#45 gate (empty AHOS_GATEWAY_URL BLOCKED last Windows paste).
    assert "must NOT BLOCK" in text
    assert "AHOS_UNLOCK_SHA" in text
    assert "windows_scrub_empty_gateway.ps1" in text
    assert "windows_ensure_postgres_win.ps1" in text
    assert "SeedEvidenceIfNeeded" in text
    assert "windows_seed_local_evidence.ps1" in text


def test_ahos_run_tip_cmd_is_crlf_and_tls12():
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.cmd -text" in attrs
    raw = (ROOT / "AHOS_RUN_TIP.cmd").read_bytes()
    assert b"\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")
    text = raw.decode("ascii")
    assert "Tls12" in text or "TLS" in text
    assert "AHOS_RUN_TIP.ps1" in text
    assert "OWNER_PASTE" in text
    assert "db:migrate" in text.lower()


def test_ahos_run_tip_ps1_is_crlf_safe_entry():
    raw = (ROOT / "AHOS_RUN_TIP.ps1").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "windows-main-evidence-push-4bde" in text
    assert "AHOS_SKIP_GIT_PULL" in text
    assert "windows_fix_g2_empty_and_gate.ps1" in text
    assert "Install-TipViaRaw" in text or "raw.githubusercontent.com" in text
    assert "Tls12" in text or "TLS" in text
    assert "AHOS_MAIN_FIRST.bat" in text
    assert 'Mode = "fix_g2"' in text or "fix_g2" in text
    assert "db:migrate" in text.lower()
    main_first = (ROOT / "AHOS_MAIN_FIRST.bat").read_text(encoding="utf-8")
    assert "AHOS_SKIP_GIT_PULL" in main_first
    pre = (ROOT / "AHOS_PRE_SOAK_NOW.bat").read_text(encoding="utf-8")
    assert "AHOS_SKIP_GIT_PULL" in pre


def test_bat_files_are_crlf_in_working_tree_for_cmd():
    """cmd.exe needs CRLF; *.bat is -text so blobs keep CRLF for raw.githubusercontent.com."""
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.bat -text" in attrs
    assert "raw.githubusercontent.com" in attrs or "LF-only" in attrs or "curl" in attrs.lower()
    for name in (
        "AHOS_MAIN_FIRST.bat",
        "AHOS_FIX_G2_AND_GATE.bat",
        "AHOS_WINDOWS_OPS.bat",
        "AHOS_PRE_SOAK_NOW.bat",
        "AHOS_MAIN_CLEAR_G2.cmd",
        "AHOS_RUN_TIP.cmd",
    ):
        raw = (ROOT / name).read_bytes()
        assert b"\r\n" in raw, name + " missing CRLF"
        # No bare LF line endings mixed in (allow final content)
        assert raw.count(b"\n") == raw.count(b"\r\n"), name + " has LF-only lines"


def test_windows_ps1_scripts_are_ascii_for_ps51():
    """PS 5.1: ASCII codepoints + UTF-8 BOM so file decode is correct."""
    bom = b"\xef\xbb\xbf"
    bad = []
    for path in sorted((ROOT / "scripts").glob("windows_*.ps1")):
        raw = path.read_bytes()
        if not raw.startswith(bom):
            bad.append(f"{path.name}: missing UTF-8 BOM")
            body = raw
        else:
            body = raw[3:]
        text = body.decode("utf-8")
        non_ascii = sorted({ch for ch in text if ord(ch) > 127})
        if non_ascii:
            bad.append(f"{path.name}: {non_ascii!r}")
    assert not bad, "Windows PS1 encoding issues:\n" + "\n".join(bad)


def test_windows_wait_for_web_api_script_exists():
    path = ROOT / "scripts" / "windows_wait_for_web_api.ps1"
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "wait script needs UTF-8 BOM for WinPS 5.1"
    text = raw.decode("utf-8-sig")
    assert "/api/chat" in text
    assert "AHOS_WEB_API_TOKEN" in text
    assert "Invoke-WebRequest" in text
    assert "FAIL-FAST" in text
    assert "WEB_API_LOCKED_NO_TOKEN" in text or "401" in text
    # Docker-up + DATABASE_URL: tolerate longer 5xx window for PRE_SOAK G2
    assert "$limit = 30" in text
    assert "Test-DockerDaemonUp" in text or "docker info" in text
    assert "db:migrate" in text.lower()


def test_windows_ensure_postgres_win_script_exists():
    path = ROOT / "scripts" / "windows_ensure_postgres_win.ps1"
    text = path.read_text(encoding="utf-8-sig")
    assert "ahos_postgres_win" in text
    assert "docker compose" in text
    assert "pg_isready" in text
    assert "docker restart" in text  # one recovery for unhealthy/stuck without wipe
    assert "db:migrate" in text.lower() or "Never db:migrate" in text


def test_windows_diagnose_docker_health_script_exists():
    path = ROOT / "scripts" / "windows_diagnose_docker_health.ps1"
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "ahos_postgres_win" in text
    assert "pg_isready" in text
    assert "ahos_runtime_win" in text
    assert "NOT a G2 blocker" in text or "not a G2 blocker" in text.lower()
    assert "tcp_5432" in text or "5432" in text
    assert "DATABASE_URL" in text
    assert "db:migrate" in text.lower()


def test_windows_g2_validate_helpers_exist():
    bat = (ROOT / "AHOS_VALIDATE_G2_NOW.bat").read_text(encoding="utf-8", errors="replace")
    assert "windows_validate_g2.ps1" in bat
    assert "windows_g2_probe.py" in bat  # must checkout .py (glob is windows_*.ps1 only)
    assert "AHOS_PRE_SOAK_NOW.bat" in bat  # chains to full G1-G10 after G2 PASS
    assert "db:migrate" in bat.lower()
    assert "READY" in bat
    ps1 = (ROOT / "scripts" / "windows_validate_g2.ps1").read_bytes()
    assert ps1.startswith(b"\xef\xbb\xbf")
    body = ps1[3:].decode("utf-8")
    assert "windows_g2_probe.py" in body
    assert "windows_diagnose_docker_health.ps1" in body
    assert "db:migrate" in body.lower()
    assert "ahos-runtime" not in body.lower() or "no-healthcheck" in body
    assert "--no-healthcheck" in body or "no-healthcheck" in body
    assert "windows_push_gate_evidence.ps1" in body
    probe = (ROOT / "scripts" / "windows_g2_probe.py").read_text(encoding="utf-8")
    assert "g2_gateway" in probe
    assert "ahos.g2_validate.v1" in probe
    assert "PRE_SOAK" in probe


def test_windows_compose_postgres_healthcheck_uses_container_env():
    compose = (ROOT / "deployment" / "docker-compose.windows.yml").read_text(encoding="utf-8")
    assert "$$POSTGRES_USER" in compose or '"$$POSTGRES_USER"' in compose
    assert "start_period" in compose
    assert "postgresql_schema.sql" in compose
    assert "db:migrate" not in compose
    # PAPER_ONLY: disable noisy Dockerfile HEALTHCHECK on ahos-runtime
    assert "healthcheck:" in compose
    assert "disable: true" in compose
    assert "service_started" in compose


def test_windows_seed_local_evidence_script_exists():
    path = ROOT / "scripts" / "windows_seed_local_evidence.ps1"
    text = path.read_text(encoding="utf-8")
    assert "lifecycle_status" in text
    assert "single-cycle" in text
    assert "OPERATOR_READY" in text
    assert "db:migrate" in text.lower() or "Never migrates" in text
    assert "observation_state_total" in text
    assert "sum(int(v)" in text or "observation_state" in text
    assert "after_seed" in text or "re-read" in text.lower() or "after seed" in text.lower()


def test_windows_gate_runner_posts_via_multi_pr_helper():
    text = (ROOT / "scripts" / "windows_run_operator_gate.ps1").read_text(encoding="utf-8")
    assert "OWNER_PASTE_WINDOWS_GATE_SLIM" in text
    assert "BEGIN WINDOWS GATE PASTE" in text
    assert "windows_post_gate_paste_gh.ps1" in text
    helper = (ROOT / "scripts" / "windows_post_gate_paste_gh.ps1").read_text(encoding="utf-8-sig")
    assert "gh pr comment" in helper
    assert '"45"' in helper  # unlock PR sink for subscribed agents
    assert '"37"' in helper or "37" in helper
    assert '"36"' in helper or "36" in helper
    assert "db:migrate" in helper.lower() or "READY" in helper



def test_windows_recover_g2_warm_script_and_ops_bat():
    recover = ROOT / "scripts" / "windows_recover_g2_warm.ps1"
    text = recover.read_text(encoding="utf-8-sig")
    assert "windows_ensure_database_url.ps1" in text
    assert "windows_chat_500_forensics.ps1" in text
    assert "db:migrate" in text.lower()
    ops = (ROOT / "AHOS_WINDOWS_OPS.bat").read_text(encoding="utf-8")
    assert "windows_recover_g2_warm.ps1" in ops
    assert "for %%R in (" in ops
    g2 = (ROOT / "scripts" / "windows_validate_g2.ps1").read_text(encoding="utf-8-sig")
    assert "windows_recover_g2_warm.ps1" in g2
    vbat = (ROOT / "AHOS_VALIDATE_G2_NOW.bat").read_text(encoding="utf-8")
    assert "windows-presoak-unblock-4bde" in vbat
    push_bat = (ROOT / "AHOS_PUSH_EVIDENCE_NOW.bat").read_text(encoding="utf-8")
    assert "windows_push_gate_evidence.ps1" in push_bat
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in push_bat
    pull = (ROOT / "AHOS_PULL_OPS_UNLOCK.bat").read_text(encoding="utf-8")
    assert "windows-presoak-unblock-4bde" in pull
    paste = (ROOT / "scripts" / "windows_post_gate_paste_gh.ps1").read_text(encoding="utf-8-sig")
    assert "windows-evidence-inbox-stay-open-4bde" in paste
    assert "windows-evidence-inbox-open-sink-4bde" in paste or '"56"' in paste or "Add-Target \"56\"" in paste
    push = (ROOT / "scripts" / "windows_push_gate_evidence.ps1").read_text(encoding="utf-8-sig")
    assert "38" in push
    assert '"56"' in push or "Add(\"56\")" in push or "notifyTargets.Add(\"56\")" in push
    assert "AHOS_GATE_PR" in push
    assert "open-sink" in push or "windows-evidence-inbox-open-sink-4bde" in push
    assert "windows-ops-evidence-push-main-4bde" in push


def test_windows_run_this_first_points_at_ops_bat():
    text = (ROOT / "WINDOWS_RUN_THIS_FIRST.txt").read_text(encoding="utf-8")
    assert "AHOS_WINDOWS_OPS.bat" in text or "AHOS_MAIN_CLEAR_G2.cmd" in text
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in text
    assert "db:migrate" in text.lower()
    assert (
        "AHOS_RUN_TIP.ps1" in text
        or "AHOS_RUN_TIP.cmd" in text
        or "AHOS_MAIN_CLEAR_G2.cmd" in text
        or "AHOS_MAIN_FIRST.bat" in text
        or "windows_bootstrap_presoak.ps1" in text
        or "AHOS_APPLY_TIP.bat" in text
    )
    start_ps1 = (ROOT / "start_ahos.ps1").read_text(encoding="utf-8")
    assert (
        "AHOS_MAIN_CLEAR_G2.cmd" in start_ps1
        or "AHOS_RUN_TIP.ps1" in start_ps1
        or "AHOS_RUN_TIP.cmd" in start_ps1
        or "AHOS_WINDOWS_OPS.bat" in start_ps1
    )
    assert "OWNER_PASTE_WINDOWS_GATE.txt" in start_ps1
    start_bat = (ROOT / "start_ahos.bat").read_bytes()
    assert b"\r\n" in start_bat
    assert start_bat.count(b"\n") == start_bat.count(b"\r\n")
    assert b"AHOS_MAIN_CLEAR_G2.cmd" in start_bat
    assert b"db:migrate" in start_bat.lower()


def test_windows_restart_next_dev_script_exists():
    path = ROOT / "scripts" / "windows_restart_next_dev.ps1"
    text = path.read_text(encoding="utf-8")
    assert "Stop-Process" in text
    assert "npm run dev" in text
    assert "3000" in text


def test_post_merge_reconcile_supports_keep_current_branch():
    text = (ROOT / "scripts" / "windows_post_merge_reconcile.ps1").read_text(encoding="utf-8")
    assert "KeepCurrentBranch" in text
    assert "windows_ensure_web_api_token.ps1" in text
    assert "web_api_auth.ts" in text
    assert "operator_validation_gate.py" in text or "windows_run_operator_gate.ps1" in text


def test_install_windows_gate_cli_matches_runner():
    text = (ROOT / "install_windows.ps1").read_text(encoding="utf-8", errors="replace")
    assert "--repo-root" not in text
    assert "--require-owner-action" not in text
    assert "windows_run_operator_gate.ps1" in text or "AHOS_MAIN_CLEAR_G2.cmd" in text
    assert "AHOS_MAIN_CLEAR_G2.cmd" in text
    assert "db:migrate" in text.lower()
    # token ensure still documented in installer body / MAIN_CLEAR path
    assert "windows_ensure_web_api_token.ps1" in text or "MAIN_CLEAR" in text


def test_env_example_documents_web_api_token_keys():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "AHOS_WEB_API_TOKEN=" in text
    assert "NEXT_PUBLIC_AHOS_WEB_API_TOKEN=" in text
    assert "AHOS_WEB_API_ALLOW_OPEN_ACCESS=0" in text


def test_gateway_sends_authorization_when_web_token_set(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "unit-test-web-token")
    captured: dict = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {
                    "text": "ok",
                    "intent": "GREETING",
                    "focus_token": None,
                    "evidence": {},
                }
            ).encode("utf-8")

    def _urlopen(req, timeout=None):
        captured["headers"] = dict(req.headers)
        return _Resp()

    monkeypatch.setattr(svc_mod.urllib.request, "urlopen", _urlopen)
    r = TelegramDomainService().handle_message("سلام")
    assert r["status"] == "OK"
    assert r["source"] == "conversation_gateway"
    assert FOOTER_MANDATED in r["text"]
    auth = captured["headers"].get("Authorization") or captured["headers"].get(
        "authorization"
    )
    assert auth == "Bearer unit-test-web-token"


def test_gateway_omits_authorization_when_web_token_unset(monkeypatch):
    monkeypatch.setattr(svc_mod, "AHOS_GATEWAY_URL", "http://127.0.0.1:9/api/chat")
    monkeypatch.delenv("AHOS_WEB_API_TOKEN", raising=False)
    captured: dict = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"text": "ok", "intent": "GREETING"}).encode("utf-8")

    def _urlopen(req, timeout=None):
        captured["headers"] = dict(req.headers)
        return _Resp()

    monkeypatch.setattr(svc_mod.urllib.request, "urlopen", _urlopen)
    TelegramDomainService().handle_message("سلام")
    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert "authorization" not in headers


def test_windows_scrub_empty_gateway_ps1_exists():
    path = ROOT / "scripts" / "windows_scrub_empty_gateway.ps1"
    assert path.is_file()
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "AHOS_GATEWAY_URL" in text
    assert "127.0.0.1:3000/api/chat" in text


def test_windows_wait_for_web_api_aligns_non5xx_with_g2():
    path = ROOT / "scripts" / "windows_wait_for_web_api.ps1"
    text = path.read_text(encoding="utf-8-sig")
    assert "G2-aligned non-5xx" in text
    assert "401" in text


def test_windows_fix_g2_has_postgres_and_seed():
    """RUN_TIP surgical path must match MAIN_CLEAR cold-laptop coverage."""
    path = ROOT / "scripts" / "windows_fix_g2_empty_and_gate.ps1"
    text = path.read_text(encoding="utf-8-sig")
    assert "windows_ensure_postgres_win.ps1" in text
    assert "SeedEvidenceIfNeeded" in text
    assert "windows_scrub_empty_gateway.ps1" in text
    assert "AHOS_GATE_PR" in text
    assert "56" in text
    assert "windows_restart_next_dev.ps1" in text
    assert "db:migrate" in text.lower()
